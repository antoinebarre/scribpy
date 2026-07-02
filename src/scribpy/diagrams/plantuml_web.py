"""PlantUML web renderer — calls the public PlantUML server.

Encodes the diagram source and sends it to the PlantUML server to
retrieve an SVG rendering.  Fails fast with a
:class:`~scribpy.errors.DiagramRenderError` on any network or
server error (REQ-025).
"""

from __future__ import annotations

import zlib
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.errors import DiagramRenderError

_PLANTUML_SERVER = "http://www.plantuml.com/plantuml/svg/"

_PLANTUML_ALPHABET = (
    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"
)


def _encode_6bit(value: int) -> str:
    """Encode a 6-bit value to the PlantUML alphabet character.

    Args:
        value: Integer in range 0..63.

    Returns:
        Single character from the PlantUML encoding alphabet.
    """
    return _PLANTUML_ALPHABET[value & 0x3F]


def _encode_3bytes(b1: int, b2: int, b3: int) -> str:
    """Encode three bytes into four PlantUML-alphabet characters.

    Args:
        b1: First byte.
        b2: Second byte.
        b3: Third byte.

    Returns:
        Four encoded characters.
    """
    c1 = b1 >> 2
    c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
    c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
    c4 = b3 & 0x3F
    return (
        _encode_6bit(c1)
        + _encode_6bit(c2)
        + _encode_6bit(c3)
        + _encode_6bit(c4)
    )


def _plantuml_encode(text: str) -> str:
    """Encode PlantUML source for URL transmission.

    Uses deflate compression followed by the PlantUML custom
    base64-like encoding.

    Args:
        text: Raw PlantUML source code.

    Returns:
        Encoded string suitable for appending to the server URL.
    """
    data = zlib.compress(text.encode("utf-8"))[2:-4]
    encoded = []
    for i in range(0, len(data), 3):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0
        encoded.append(_encode_3bytes(b1, b2, b3))
    return "".join(encoded)


class PlantUmlWebRenderer:
    """Renders PlantUML diagrams via the public PlantUML server.

    Attributes:
        server_url: Base URL of the PlantUML server.
    """

    def __init__(
        self,
        server_url: str = _PLANTUML_SERVER,
    ) -> None:
        """Initialise with a PlantUML server URL.

        Args:
            server_url: Base URL for SVG rendering endpoint.
        """
        self.server_url = server_url

    def render(self, source: str) -> str:
        """Render PlantUML source to SVG via the web server.

        Args:
            source: Raw PlantUML diagram source.

        Returns:
            SVG markup as a string.

        Raises:
            DiagramRenderError: On any network or server failure
                (REQ-025).
        """
        encoded = _plantuml_encode(source)
        url = self.server_url + encoded
        request = Request(url)  # noqa: S310
        request.add_header("User-Agent", "scribpy/0.1")

        try:
            with urlopen(  # nosec B310  # noqa: S310
                request,
                timeout=30,
            ) as response:
                result: str = response.read().decode("utf-8")
                return result
        except (URLError, OSError) as exc:
            raise DiagramRenderError(
                block_name="plantuml-web",
                engine="plantuml",
                mode="web",
                reason=f"PlantUML server request failed: {exc}",
            ) from exc
