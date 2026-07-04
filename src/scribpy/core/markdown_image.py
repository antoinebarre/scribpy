"""Markdown image reference domain object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarkdownImageReference:
    """Represent one image reference written in Markdown.

    Attributes:
        alt_text: Alternative text between Markdown image brackets.
        target: Raw image target path or URL from the Markdown source.
        title: Optional Markdown image title.
        line: One-based line number where the reference starts.
        column: One-based column number where the reference starts.
    """

    alt_text: str
    target: str
    title: str | None = None
    line: int | None = None
    column: int | None = None
