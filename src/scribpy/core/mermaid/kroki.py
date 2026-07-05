"""Mermaid renderer backed by the kroki.io public web service."""

from __future__ import annotations

import base64
import zlib
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.errors import MermaidRenderError

_KROKI_URL = "https://kroki.io/mermaid/png"
_REQUEST_TIMEOUT = 30
_HTTP_OK = 200
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"


class KrokiRenderer:
    """Render Mermaid diagrams via the kroki.io public web service.

    The diagram source is zlib-compressed and base64url-encoded, then sent
    as a GET request.  No external dependencies beyond the Python standard
    library are required.
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
        encoded = _encode_diagram(diagram)
        url = f"{_KROKI_URL}/{encoded}"
        request = Request(  # nosec B310  # noqa: S310
            url,
            headers={"User-Agent": _USER_AGENT},
            method="GET",
        )
        try:
            with urlopen(  # nosec B310  # noqa: S310
                request, timeout=_REQUEST_TIMEOUT
            ) as response:
                if response.status != _HTTP_OK:
                    msg = f"Kroki returned HTTP {response.status}."
                    raise MermaidRenderError(msg)
                data: bytes = response.read()
                return data
        except URLError as exc:
            msg = f"Kroki request failed: {exc.reason}"
            raise MermaidRenderError(msg) from exc


def _encode_diagram(diagram: str) -> str:
    """Encode a Mermaid diagram for use in a kroki.io URL path.

    The encoding follows the kroki.io specification: UTF-8 source compressed
    with zlib (including the standard header and checksum) then encoded with
    URL-safe base64.

    Args:
        diagram: Raw Mermaid source text.

    Returns:
        URL-safe base64 string of the compressed diagram.
    """
    compressed = zlib.compress(diagram.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")
