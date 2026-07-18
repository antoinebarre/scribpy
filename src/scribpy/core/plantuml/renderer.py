"""PlantUML renderer protocol and factory."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from scribpy.core.plantuml.configuration import DEFAULT_PLANTUML_SERVER_URL
from scribpy.core.plantuml.kroki import KrokiRenderer
from scribpy.core.plantuml.local import LocalRenderer
from scribpy.core.plantuml.server import PlantUmlServerRenderer

_DEFAULT_BACKEND = "plantuml_server"


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


RendererFactory = Callable[[str], PlantUmlRenderer]


def _make_kroki(server_url: str) -> PlantUmlRenderer:
    """Create a Kroki renderer while accepting the shared factory input.

    Args:
        server_url: Unused PlantUML Server URL.

    Returns:
        Kroki renderer.
    """
    del server_url
    return KrokiRenderer()


def _make_local(server_url: str) -> PlantUmlRenderer:
    """Create a local renderer while accepting the shared factory input.

    Args:
        server_url: Unused PlantUML Server URL.

    Returns:
        Local renderer.
    """
    del server_url
    return LocalRenderer()


def _make_plantuml_server(server_url: str) -> PlantUmlRenderer:
    """Create a renderer for one PlantUML Server URL.

    Args:
        server_url: PlantUML Server base URL.

    Returns:
        PlantUML Server renderer.
    """
    return PlantUmlServerRenderer(server_url)


_BACKENDS: dict[str, RendererFactory] = {
    "web": _make_kroki,
    "kroki": _make_kroki,
    "plantuml_server": _make_plantuml_server,
    "local": _make_local,
}


def make_renderer(
    backend: str = _DEFAULT_BACKEND,
    *,
    server_url: str = DEFAULT_PLANTUML_SERVER_URL,
) -> PlantUmlRenderer:
    """Instantiate a PlantUML renderer for the given backend name.

    Args:
        backend: Backend identifier. Accepted values: ``"plantuml_server"``
            (default), ``"web"``, ``"kroki"`` and ``"local"``.
        server_url: Base URL used by the ``plantuml_server`` backend.

    Returns:
        A renderer instance for the requested backend.

    Raises:
        ValueError: If *backend* is not a known identifier.
    """
    factory = _BACKENDS.get(backend)
    if factory is None:
        known = ", ".join(sorted(_BACKENDS))
        msg = f"Unknown PlantUML backend {backend!r}. Known backends: {known}."
        raise ValueError(msg)
    return factory(server_url)
