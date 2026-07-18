"""Mermaid renderer protocol and factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from scribpy.core.mermaid.cli import MermaidCliRenderer
from scribpy.core.mermaid.kroki import KrokiRenderer

_DEFAULT_BACKEND = "kroki"
_DEFAULT_COMMAND = "mmdc"


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


RendererFactory = Callable[[str], MermaidRenderer]


def _make_kroki(command: str) -> MermaidRenderer:
    """Create a Kroki renderer while accepting shared factory input.

    Args:
        command: Unused Mermaid CLI executable.

    Returns:
        Kroki renderer.
    """
    del command
    return KrokiRenderer()


def _make_mermaid_cli(command: str) -> MermaidRenderer:
    """Create an official Mermaid CLI renderer.

    Args:
        command: Mermaid CLI executable name or path.

    Returns:
        Mermaid CLI renderer.
    """
    return MermaidCliRenderer(command)


_BACKENDS: dict[str, RendererFactory] = {
    "web": _make_kroki,
    "kroki": _make_kroki,
    "mermaid_cli": _make_mermaid_cli,
    "local": _make_mermaid_cli,
}


def make_renderer(
    backend: str = _DEFAULT_BACKEND,
    *,
    command: str = _DEFAULT_COMMAND,
) -> MermaidRenderer:
    """Instantiate a Mermaid renderer for the given backend name.

    Args:
        backend: Backend identifier. Accepted values: ``"kroki"`` (default),
            ``"web"``, ``"mermaid_cli"`` and ``"local"``.
        command: Executable used by local Mermaid CLI rendering.

    Returns:
        A renderer instance for the requested backend.

    Raises:
        ValueError: If *backend* is not a known identifier.
    """
    factory = _BACKENDS.get(backend)
    if factory is None:
        known = ", ".join(sorted(_BACKENDS))
        msg = f"Unknown Mermaid backend {backend!r}. Known backends: {known}."
        raise ValueError(msg)
    return factory(command)
