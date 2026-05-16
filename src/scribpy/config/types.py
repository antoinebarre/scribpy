"""Typed configuration objects for ``scribpy.toml``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scribpy.model import IndexMode

TocStyle = Literal["bullet", "numbered"]
NumberingStyle = Literal["decimal", "alpha", "roman"]


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
class TocConfig:
    """Table-of-contents configuration.

    Attributes:
        enabled: Whether to inject a generated table of contents.
        max_level: Deepest heading level included in the table of contents.
        style: Markdown list style used by the table of contents.
    """

    enabled: bool = True
    max_level: int = 6
    style: TocStyle = "bullet"


@dataclass(frozen=True)
class NumberingConfig:
    """Section-numbering configuration.

    Attributes:
        enabled: Whether to prefix headings with generated section numbers.
        max_level: Deepest heading level that receives generated numbering.
        style: Number style used for section prefixes.
    """

    enabled: bool = True
    max_level: int = 6
    style: NumberingStyle = "decimal"


@dataclass(frozen=True)
class DocumentConfig:
    """Document-level output configuration.

    Attributes:
        title: Optional global assembled-document title.
        toc: Generated table-of-contents settings.
        numbering: Section-numbering settings.
    """

    title: str | None = None
    toc: TocConfig = TocConfig()
    numbering: NumberingConfig = NumberingConfig()


@dataclass(frozen=True)
class Config:
    """Minimal project configuration required by the project context chain.

    Attributes:
        project: Project metadata.
        paths: Filesystem paths.
        index: Document index settings.
        document: Document output settings.
    """

    project: ProjectConfig = ProjectConfig()
    paths: PathConfig = PathConfig()
    index: IndexConfig = IndexConfig()
    document: DocumentConfig = DocumentConfig()


__all__ = [
    "Config",
    "DocumentConfig",
    "IndexConfig",
    "NumberingConfig",
    "NumberingStyle",
    "PathConfig",
    "ProjectConfig",
    "TocConfig",
    "TocStyle",
]
