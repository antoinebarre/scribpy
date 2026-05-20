"""PlantUML server URL encoding."""

from __future__ import annotations

import zlib


def encode_server_payload(source: str) -> str:
    """Encode PlantUML source using the server URL format.

    Args:
        source: Raw PlantUML source.

    Returns:
        PlantUML-compatible compressed URL payload.
    """
    compressed = zlib.compress(source.encode("utf-8"))[2:-4]
    return "".join(
        _encode6bit(byte >> 2)
        + _encode6bit(((byte & 0x3) << 4) | (next_byte >> 4))
        + _encode6bit(((next_byte & 0xF) << 2) | (last_byte >> 6))
        + _encode6bit(last_byte & 0x3F)
        for byte, next_byte, last_byte in _triples(compressed)
    )


def _triples(payload: bytes) -> tuple[tuple[int, int, int], ...]:
    """Pad compressed bytes into triples."""
    padded = payload + b"\0" * ((3 - len(payload) % 3) % 3)
    return tuple(
        (padded[index], padded[index + 1], padded[index + 2])
        for index in range(0, len(padded), 3)
    )


def _encode6bit(value: int) -> str:
    """Encode one six-bit PlantUML server symbol."""
    if value < 10:
        return chr(48 + value)
    value -= 10
    if value < 26:
        return chr(65 + value)
    value -= 26
    if value < 26:
        return chr(97 + value)
    value -= 26
    return "-" if value == 0 else "_"


__all__ = ["_encode6bit", "encode_server_payload"]
