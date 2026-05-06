"""TOML loading helpers."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import cast


def load_toml(path: Path) -> dict[str, object]:
    """Load a TOML file into a string-keyed dictionary."""

    with path.open("rb") as stream:
        return cast("dict[str, object]", tomllib.load(stream))


__all__ = ["load_toml"]
