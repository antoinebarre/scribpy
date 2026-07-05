"""PlantUML renderer protocol and factory."""

from __future__ import annotations

from typing import Protocol

from scribpy.core.plantuml.local import LocalRenderer
from scribpy.core.plantuml.web_server import WebServerRenderer

_BACKENDS: dict[str, type[PlantUmlRenderer]] = {
    "web": WebServerRenderer,
    "local": LocalRenderer,
}

_DEFAULT_BACKEND = "web"


class PlantUmlRenderer(Protocol):
    """Render a PlantUML diagram source to PNG bytes.

    Implementations must be stateless and thread-safe.
    """

    def render(self, diagram: str) -> bytes:
        """Render a PlantUML diagram to PNG bytes.

        Args:
            diagram: PlantUML diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            PlantUmlRenderError: If the rendering backend fails.
        """
        ...


def make_renderer(backend: str = _DEFAULT_BACKEND) -> PlantUmlRenderer:
    """Instantiate a PlantUML renderer for the given backend name.

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
        msg = f"Unknown PlantUML backend {backend!r}. Known backends: {known}."
        raise ValueError(msg)
    return renderer_cls()
