"""PlantUML renderer backed by the official plantuml.com web server."""

from __future__ import annotations

import zlib
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.errors import PlantUmlRenderError

_PLANTUML_URL = "https://www.plantuml.com/plantuml/png"
_REQUEST_TIMEOUT = 30
_HTTP_OK = 200
_USER_AGENT = "Scribpy/0.1 (+https://github.com/example/scribpy)"

_PLANTUML_CHARS = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
)


class WebServerRenderer:
    """Render PlantUML diagrams via the official plantuml.com web server.

    Diagrams are encoded with the PlantUML text encoding (deflate + custom
    base64 alphabet) and sent as a GET request.  No external dependencies
    beyond the Python standard library are required.
    """

    def render(self, diagram: str) -> bytes:
        """Render a PlantUML diagram to PNG via plantuml.com.

        Args:
            diagram: PlantUML diagram source, without fenced code delimiters.

        Returns:
            PNG image bytes.

        Raises:
            PlantUmlRenderError: If the HTTP request fails or returns a
                non-200 status.
        """
        encoded = _encode_diagram(diagram)
        url = f"{_PLANTUML_URL}/{encoded}"
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
                    msg = f"PlantUML server returned HTTP {response.status}."
                    raise PlantUmlRenderError(msg)
                data: bytes = response.read()
                return data
        except URLError as exc:
            msg = f"PlantUML server request failed: {exc.reason}"
            raise PlantUmlRenderError(msg) from exc


def _encode_diagram(diagram: str) -> str:
    """Encode a PlantUML diagram for use in a plantuml.com URL path.

    The encoding follows the official PlantUML text encoding specification:
    UTF-8 source → zlib deflate (raw, wbits=-15) → 6-bit groups mapped to
    the PlantUML custom alphabet (digits, upper, lower, ``-``, ``_``).

    Args:
        diagram: Raw PlantUML source text.

    Returns:
        Encoded string suitable for appending to the plantuml.com PNG URL.
    """
    compressed = zlib.compress(diagram.encode("utf-8"), level=9)
    raw_deflate = compressed[2:-4]
    return _plantuml_b64encode(raw_deflate)


def _plantuml_b64encode(data: bytes) -> str:
    """Encode bytes using the PlantUML custom base64 alphabet.

    Processes bytes in groups of three, producing four 6-bit characters per
    group.  Trailing bytes are zero-padded and the result is trimmed to the
    number of significant characters.

    Args:
        data: Raw bytes to encode.

    Returns:
        PlantUML-encoded ASCII string.
    """
    _two_trailing = 2
    length = len(data)
    result = [
        _encode_triplet(data[i], data[i + 1], data[i + 2])
        for i in range(0, length - 2, 3)
    ]
    remainder = length % 3
    if remainder == 1:
        result.append(_encode_triplet(data[-1], 0, 0)[:2])
    elif remainder == _two_trailing:
        result.append(_encode_triplet(data[-2], data[-1], 0)[:3])
    return "".join(result)


def _encode_triplet(b1: int, b2: int, b3: int) -> str:
    """Map three bytes to four PlantUML alphabet characters.

    Args:
        b1: First byte value (0-255).
        b2: Second byte value (0-255).
        b3: Third byte value (0-255).

    Returns:
        Four-character string using the PlantUML custom base64 alphabet.
    """
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return (
        _PLANTUML_CHARS[c1]
        + _PLANTUML_CHARS[c2]
        + _PLANTUML_CHARS[c3]
        + _PLANTUML_CHARS[c4]
    )
