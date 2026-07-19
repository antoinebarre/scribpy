"""PlantUML renderer backed by a PlantUML Server instance."""

from __future__ import annotations

import logging
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.core.plantuml.configuration import DEFAULT_PLANTUML_SERVER_URL
from scribpy.errors import PlantUmlRenderError

_log = logging.getLogger(__name__)

_HTTP_OK = 200
_REQUEST_TIMEOUT = 30
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"


class PlantUmlServerRenderer:
    """Render diagrams through a configurable PlantUML Server.

    Attributes:
        server_url: PlantUML Server base URL including its context path.
    """

    def __init__(
        self,
        server_url: str = DEFAULT_PLANTUML_SERVER_URL,
    ) -> None:
        """Initialize the renderer with a PlantUML Server URL.

        Args:
            server_url: Server base URL including its PlantUML context path.
        """
        self.server_url = server_url.rstrip("/")

    def render(self, diagram: str) -> bytes:
        """Render one PlantUML diagram as PNG.

        Args:
            diagram: PlantUML source without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            PlantUmlRenderError: If the request fails or is not successful.
        """
        encoded = _encode_hex(diagram)
        url = f"{self.server_url}/png/{encoded}"
        _log.debug("PlantUML Server render request: %s", url)
        request = Request(  # nosec B310  # noqa: S310
            url,
            headers={"User-Agent": _USER_AGENT},
            method="GET",
        )
        try:
            with urlopen(  # nosec B310  # noqa: S310
                request,
                timeout=_REQUEST_TIMEOUT,
            ) as response:
                if response.status != _HTTP_OK:
                    detail = (
                        f"PlantUML Server returned HTTP {response.status}."
                    )
                    raise PlantUmlRenderError(detail)
                data: bytes = response.read()
                _log.info("PlantUML Server render OK (%d bytes)", len(data))
                return data
        except URLError as exc:
            detail = f"PlantUML Server request failed: {exc.reason}"
            raise PlantUmlRenderError(detail) from exc


def _encode_hex(diagram: str) -> str:
    """Encode diagram source with PlantUML Server hexadecimal encoding.

    Args:
        diagram: PlantUML source text.

    Returns:
        UTF-8 hexadecimal source prefixed with the PlantUML ``~h`` marker.
    """
    return f"~h{diagram.encode('utf-8').hex()}"


__all__ = ["PlantUmlServerRenderer"]
