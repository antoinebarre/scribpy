"""PlantUML renderer backed by the kroki.io public web service."""

from __future__ import annotations

from scribpy.core.kroki_http import kroki_render
from scribpy.errors import PlantUmlRenderError


class KrokiRenderer:
    """Render PlantUML diagrams via the kroki.io public web service.

    The diagram source is zlib-compressed and base64url-encoded, then sent
    as a GET request.  No external dependencies beyond the Python standard
    library are required.
    """

    def render(self, diagram: str) -> bytes:
        """Render a PlantUML diagram to PNG via kroki.io.

        Args:
            diagram: PlantUML diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            PlantUmlRenderError: If the HTTP request fails or returns a
                non-200 status.
        """
        return kroki_render("plantuml", diagram, PlantUmlRenderError)
