"""Mermaid renderer backed by the kroki.io public web service."""

from __future__ import annotations

from scribpy.core.kroki_http import kroki_render
from scribpy.errors import MermaidRenderError


class KrokiRenderer:
    """Render Mermaid diagrams via the kroki.io public web service.

    The diagram source is encoded into a GET request. No external dependencies
    beyond the Python standard library are required.
    """

    def render(self, diagram: str) -> bytes:
        """Render a Mermaid diagram to PNG via kroki.io.

        Args:
            diagram: Mermaid diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            MermaidRenderError: If the HTTP request fails or returns a
                non-200 status.
        """
        return kroki_render("mermaid", diagram, MermaidRenderError)
