"""Mermaid web renderer backend."""

from __future__ import annotations

from typing import cast
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scribpy.assets.mermaid_encoding import encode_mermaid_payload
from scribpy.assets.mermaid_types import MermaidRenderError
from scribpy.logging import get_logger

logger = get_logger(__name__)


class WebMermaidRenderer:
    """Render Mermaid diagrams through a Mermaid web service."""

    _USER_AGENT = "scribpy-mermaid"

    def __init__(self, server_url: str, theme: str = "default") -> None:
        """Create the web renderer.

        Args:
            server_url: Base Mermaid server URL, for example
                ``https://mermaid.ink``.
            theme: Mermaid theme passed to the rendering service.
        """
        self._server_url = server_url.rstrip("/")
        self._theme = theme

    def render(self, source: str, output_format: str) -> bytes:
        """Render Mermaid source through the configured web server.

        Args:
            source: Raw Mermaid source.
            output_format: Requested Mermaid output format.

        Returns:
            Rendered bytes returned by the server.

        Raises:
            MermaidRenderError: If the server cannot render the diagram.
        """
        encoded = encode_mermaid_payload(source, self._theme)
        url = f"{self._server_url}/{output_format}/{encoded}"
        _validate_http_url(url)
        request = Request(url, headers={"User-Agent": self._USER_AGENT})
        logger.info(
            "Rendering Mermaid through web server %s with theme %s",
            self._server_url,
            self._theme,
        )
        logger.debug("Mermaid encoded payload length: %d", len(encoded))
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310
                return cast("bytes", response.read())
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace").strip()
            reason = f"HTTP Error {exc.code}: {exc.reason}"
            raise MermaidRenderError(
                f"{reason}: {detail}" if detail else reason
            ) from exc
        except (OSError, URLError) as exc:
            raise MermaidRenderError(str(exc)) from exc


def _validate_http_url(url: str) -> None:
    """Validate that a renderer URL targets an HTTP(S) endpoint."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise MermaidRenderError(
            "Mermaid renderer URL must use http or https."
        )


__all__ = ["WebMermaidRenderer"]
