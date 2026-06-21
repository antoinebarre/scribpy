"""Mermaid web renderer — calls the mermaid.ink service.

Encodes the diagram source and sends it to mermaid.ink to retrieve
an SVG rendering.  Fails fast with a
:class:`~scribpy.errors.DiagramRenderError` on any network or
server error (REQ-025).
"""

from __future__ import annotations

import base64
from urllib.error import URLError
from urllib.request import Request, urlopen

from scribpy.errors import DiagramRenderError

_MERMAID_INK_URL = "https://mermaid.ink/svg/"


class MermaidWebRenderer:
    """Renders Mermaid diagrams via the mermaid.ink service.

    Attributes:
        server_url: Base URL of the mermaid.ink SVG endpoint.
    """

    def __init__(
        self,
        server_url: str = _MERMAID_INK_URL,
    ) -> None:
        """Initialise with a mermaid.ink server URL.

        Args:
            server_url: Base URL for SVG rendering endpoint.
        """
        self.server_url = server_url

    def render(self, source: str) -> str:
        """Render Mermaid source to SVG via mermaid.ink.

        Args:
            source: Raw Mermaid diagram source.

        Returns:
            SVG markup as a string.

        Raises:
            DiagramRenderError: On any network or server failure
                (REQ-025).
        """
        encoded = base64.urlsafe_b64encode(
            source.encode("utf-8"),
        ).decode("ascii")
        url = self.server_url + encoded
        request = Request(url)  # noqa: S310

        try:
            with urlopen(  # nosec B310  # noqa: S310
                request,
                timeout=30,
            ) as response:
                result: str = response.read().decode("utf-8")
                return result
        except (URLError, OSError) as exc:
            raise DiagramRenderError(
                block_name="mermaid-web",
                engine="mermaid",
                mode="web",
                reason=f"Mermaid.ink request failed: {exc}",
            ) from exc
