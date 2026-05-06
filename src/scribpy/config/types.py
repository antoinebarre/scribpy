"""Typed configuration objects for ``scribpy.toml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model import IndexMode


@dataclass(frozen=True)
class ProjectConfig:
    """Project-level configuration.

    Attributes:
        name: Optional human-readable project name.
    """

    name: str | None = None


@dataclass(frozen=True)
class PathConfig:
    """Filesystem paths used by Scribpy.

    Attributes:
        source: Markdown source directory relative to the project root.
    """

    source: Path = Path("doc")


@dataclass(frozen=True)
class IndexConfig:
    """Document index configuration.

    Attributes:
        mode: Strategy used to build the document index.
        files: Explicit ordered Markdown file list when ``mode`` is
            ``"explicit"``.
    """

    mode: IndexMode = "filesystem"
    files: tuple[Path, ...] = ()


@dataclass(frozen=True)
class Config:
    """Minimal project configuration required by the project context chain.

    Attributes:
        project: Project metadata.
        paths: Filesystem paths.
        index: Document index settings.
    """

    project: ProjectConfig = ProjectConfig()
    paths: PathConfig = PathConfig()
    index: IndexConfig = IndexConfig()


__all__ = [
    "Config",
    "IndexConfig",
    "PathConfig",
    "ProjectConfig",
]
