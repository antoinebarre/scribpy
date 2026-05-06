"""Parsed Markdown document data."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scribpy.model.markdown import AssetRef, Heading, MarkdownAst, Reference


@dataclass(frozen=True)
class Document:
    """A parsed Markdown document and its extracted semantic data.

    Attributes:
        path: Absolute or project-resolved path to the source document.
        relative_path: Path of the document relative to the project root or
            configured source directory.
        source: Raw Markdown source text.
        frontmatter: Parsed frontmatter values.
        ast: Parser-neutral Markdown syntax tree.
        title: Optional document title, usually extracted from frontmatter or
            the first H1 heading.
        headings: Headings extracted from the document.
        links: Links and cross-references extracted from the document.
        assets: Asset references extracted from the document.
    """

    path: Path
    relative_path: Path
    source: str
    frontmatter: Mapping[str, Any]
    ast: MarkdownAst
    title: str | None
    headings: tuple[Heading, ...]
    links: tuple[Reference, ...]
    assets: tuple[AssetRef, ...]


__all__ = ["Document"]
