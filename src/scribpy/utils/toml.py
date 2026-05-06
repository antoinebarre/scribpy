"""TOML loading helpers."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast


def load_toml(path: Path) -> dict[str, object]:
    """Load a TOML file into a string-keyed dictionary.

    Args:
        path: Path to the TOML file.

    Returns:
        Parsed TOML document.

    Raises:
        OSError: If the file cannot be read.
        tomllib.TOMLDecodeError: If the file content is not valid TOML.
    """
    with path.open("rb") as stream:
        return cast("dict[str, object]", tomllib.load(stream))


__all__ = ["load_toml"]
