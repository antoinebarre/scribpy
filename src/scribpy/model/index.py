"""Document index data used to assemble documents deterministically."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

IndexMode = Literal["explicit", "filesystem", "hybrid"]


@dataclass(frozen=True)
class DocumentIndex:
    """Ordered list of source files used for assembly.

    Attributes:
        paths: Ordered source paths. The order is significant and determines
            how documents are linted, transformed, and assembled.
        mode: Strategy that produced the index.
    """

    paths: tuple[Path, ...]
    mode: IndexMode


__all__ = ["DocumentIndex", "IndexMode"]
