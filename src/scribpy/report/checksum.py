"""File checksum utilities for report generation.

Provides a single ``file_checksum`` function that supports multiple
digest algorithms and returns a hex-encoded string.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Literal

Algorithm = Literal["md5", "sha1", "sha256", "sha512"]
_ALGORITHMS: tuple[Algorithm, ...] = ("md5", "sha1", "sha256", "sha512")


def file_checksum(path: str | Path, algorithm: Algorithm = "sha256") -> str:
    """Compute the checksum of a file.

    Args:
        path: Path to the file to hash.
        algorithm: Hash algorithm to use. One of ``md5``, ``sha1``,
            ``sha256`` (default), or ``sha512``.

    Returns:
        Lowercase hex-encoded digest string.

    Raises:
        ValueError: If ``algorithm`` is not supported.
        FileNotFoundError: If ``path`` does not exist.
    """
    if algorithm not in _ALGORITHMS:
        raise ValueError(
            f"Unsupported algorithm '{algorithm}'. Choose from {_ALGORITHMS}."
        )
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(f"File not found: {path}")
    h = hashlib.new(algorithm)
    with src.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
