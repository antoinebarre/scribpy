"""Typed configuration objects for ``scribpy.toml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model import IndexMode


@dataclass(frozen=True)
class ProjectConfig:
    """Project-level configuration."""

    name: str | None = None


@dataclass(frozen=True)
class PathConfig:
    """Filesystem paths used by Scribpy."""

    source: Path = Path("doc")


@dataclass(frozen=True)
class IndexConfig:
    """Document index configuration."""

    mode: IndexMode = "filesystem"
    files: tuple[Path, ...] = ()


@dataclass(frozen=True)
class Config:
    """Minimal project configuration required by the project context chain."""

    project: ProjectConfig = ProjectConfig()
    paths: PathConfig = PathConfig()
    index: IndexConfig = IndexConfig()


__all__ = [
    "Config",
    "IndexConfig",
    "PathConfig",
    "ProjectConfig",
]
