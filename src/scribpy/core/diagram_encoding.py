"""Diagram source encoding for URL-based rendering services.

This module provides the zlib + base64url encoding used by services such as
kroki.io.  It has no knowledge of any specific rendering service — it only
encodes the source text into a URL-safe string.
"""

from __future__ import annotations

import base64
import zlib


def encode_diagram(diagram: str) -> str:
    """Encode a diagram source as a URL-safe compressed string.

    Compresses the UTF-8 source with zlib (including the standard header and
    checksum) then encodes the result with URL-safe base64.  This encoding is
    accepted by kroki.io for all supported diagram formats via GET requests.

    Args:
        diagram: Raw diagram source text.

    Returns:
        URL-safe base64 string of the compressed diagram.
    """
    compressed = zlib.compress(diagram.encode("utf-8"), level=9)
    return base64.urlsafe_b64encode(compressed).decode("ascii")
