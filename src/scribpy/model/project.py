"""Top-level Scribpy project data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scribpy.model.index import DocumentIndex
from scribpy.model.source import SourceFile


@dataclass(frozen=True)
class Project:
    """Top-level project state shared across processing chains.

    Attributes:
        root: Project root directory.
        config: Parsed project configuration. This is typed as a mapping until
            the dedicated configuration dataclasses are implemented.
        source_files: Source files discovered for the project.
        index: Optional document index when one has already been built.
    """

    root: Path
    config: Mapping[str, Any]
    source_files: tuple[SourceFile, ...]
    index: DocumentIndex | None = None


__all__ = ["Project"]
