"""Source file data discovered from a Scribpy project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceFile:
    """A Markdown source file discovered in a project.

    Attributes:
        path: Absolute or project-resolved path to the source file.
        relative_path: Path of the source file relative to the project root or
            configured source directory.
    """

    path: Path
    relative_path: Path


__all__ = ["SourceFile"]
