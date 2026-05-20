"""Mermaid web-service payload encoding."""

from __future__ import annotations

import base64
import json
import zlib


def encode_mermaid_payload(source: str, theme: str) -> str:
    """Encode Mermaid source using the mermaid.ink pako URL format.

    Args:
        source: Raw Mermaid source.
        theme: Mermaid theme passed to the rendering service.

    Returns:
        Pako-prefixed Mermaid web-service payload.
    """
    payload = json.dumps(
        {"code": source, "mermaid": {"theme": theme}},
        separators=(",", ":"),
    ).encode("utf-8")
    compressed = zlib.compress(payload)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
    return f"pako:{encoded}"


__all__ = ["encode_mermaid_payload"]
