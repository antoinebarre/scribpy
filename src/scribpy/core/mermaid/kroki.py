"""Mermaid renderer backed by the kroki.io public web service."""

from __future__ import annotations

import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scribpy.errors import MermaidRenderError

_log = logging.getLogger(__name__)

_KROKI_URL = "https://kroki.io/mermaid/png"
_HTTP_OK = 200
_REQUEST_TIMEOUT = 30
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"


class KrokiRenderer:
    """Render Mermaid diagrams via the kroki.io public web service.

    The diagram source is sent as plain text in a POST request. No external
    dependencies beyond the Python standard library are required.
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
        _log.debug("Mermaid render request: %s", _KROKI_URL)
        request = Request(  # nosec B310  # noqa: S310
            _KROKI_URL,
            data=diagram.encode("utf-8"),
            headers={
                "Content-Type": "text/plain; charset=utf-8",
                "User-Agent": _USER_AGENT,
            },
            method="POST",
        )
        try:
            with urlopen(  # nosec B310  # noqa: S310
                request, timeout=_REQUEST_TIMEOUT
            ) as response:
                if response.status != _HTTP_OK:
                    msg = f"Kroki returned HTTP {response.status}."
                    _log.error("Mermaid render failed: %s", msg)
                    raise MermaidRenderError(msg)
                data: bytes = response.read()
                _log.info("Mermaid render OK (%d bytes)", len(data))
                return data
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            msg = f"Kroki returned HTTP {exc.code}: {detail or exc.reason}"
            _log.error("Mermaid render error: %s", msg)
            raise MermaidRenderError(msg) from exc
        except URLError as exc:
            msg = f"Kroki request failed: {exc.reason}"
            _log.error("Mermaid render error: %s", exc.reason)
            raise MermaidRenderError(msg) from exc
