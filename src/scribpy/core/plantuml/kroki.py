"""PlantUML renderer backed by the kroki.io public web service."""

from __future__ import annotations

import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.core.diagram_encoding import encode_diagram
from scribpy.errors import PlantUmlRenderError

_log = logging.getLogger(__name__)

_KROKI_URL = "https://kroki.io/plantuml/png"
_HTTP_OK = 200
_REQUEST_TIMEOUT = 30
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"


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
        encoded = encode_diagram(diagram)
        url = f"{_KROKI_URL}/{encoded}"
        _log.debug("PlantUML render request: %s", url)
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
                    _log.error("PlantUML render failed: %s", msg)
                    raise PlantUmlRenderError(msg)
                data: bytes = response.read()
                _log.info("PlantUML render OK (%d bytes)", len(data))
                return data
        except URLError as exc:
            msg = f"Kroki request failed: {exc.reason}"
            _log.error("PlantUML render error: %s", exc.reason)
            raise PlantUmlRenderError(msg) from exc
