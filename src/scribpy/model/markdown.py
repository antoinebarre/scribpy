"""Markdown parser output and extracted semantic nodes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ReferenceKind = Literal["link", "image", "xref"]
AssetKind = Literal["image", "diagram", "static"]


@dataclass(frozen=True)
class MarkdownAst:
    """Parser-neutral Markdown syntax tree.

    Attributes:
        backend: Name of the parser backend that produced the tokens.
        tokens: Immutable sequence of parser tokens. Token payloads remain
            backend-specific so parser adapters can preserve their native data.
    """

    backend: str
    tokens: tuple[Mapping[str, object], ...]


@dataclass(frozen=True)
class Heading:
    """A heading extracted from a Markdown document.

    Attributes:
        level: Heading depth where ``1`` represents ``#`` and ``6`` represents
            ``######``.
        title: Visible heading text.
        anchor: Optional normalized anchor generated for this heading.
        line: Optional one-based line number where the heading starts.
    """

    level: int
    title: str
    anchor: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class Reference:
    """A Markdown link or cross-reference.

    Attributes:
        kind: Reference category detected in the document.
        target: Raw reference target, such as a URL, anchor, or relative link.
        text: Optional visible link text.
        path: Optional path to the referenced local file.
        line: Optional one-based line number where the reference appears.
    """

    kind: ReferenceKind
    target: str
    text: str | None = None
    path: Path | None = None
    line: int | None = None


@dataclass(frozen=True)
class AssetRef:
    """An image, diagram, or static asset referenced by a document.

    Attributes:
        kind: Asset category detected in the document.
        target: Raw asset target as written in Markdown.
        path: Optional path to the referenced local asset.
        title: Optional title or alt text associated with the asset.
        line: Optional one-based line number where the asset reference appears.
    """

    kind: AssetKind
    target: str
    path: Path | None = None
    title: str | None = None
    line: int | None = None


__all__ = [
    "AssetKind",
    "AssetRef",
    "Heading",
    "MarkdownAst",
    "Reference",
    "ReferenceKind",
]
