"""Mermaid renderer protocol and factory."""

from __future__ import annotations

from typing import Protocol

from scribpy.core.mermaid.kroki import KrokiRenderer
from scribpy.core.mermaid.local import LocalRenderer

_BACKENDS: dict[str, type[MermaidRenderer]] = {
    "web": KrokiRenderer,
    "local": LocalRenderer,
}

_DEFAULT_BACKEND = "web"


class MermaidRenderer(Protocol):
    """Render a Mermaid diagram source to PNG bytes.

    Implementations must be stateless and thread-safe.
    """

    def render(self, diagram: str) -> bytes:
        """Render a Mermaid diagram to PNG bytes.

        Args:
            diagram: Mermaid diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            MermaidRenderError: If the rendering backend fails.
        """
        ...


def make_renderer(backend: str = _DEFAULT_BACKEND) -> MermaidRenderer:
    """Instantiate a Mermaid renderer for the given backend name.

    Args:
        backend: Backend identifier. Accepted values: ``"web"`` (default),
            ``"local"``.

    Returns:
        A renderer instance for the requested backend.

    Raises:
        ValueError: If *backend* is not a known identifier.
    """
    renderer_cls = _BACKENDS.get(backend)
    if renderer_cls is None:
        known = ", ".join(sorted(_BACKENDS))
        msg = f"Unknown Mermaid backend {backend!r}. Known backends: {known}."
        raise ValueError(msg)
    return renderer_cls()
