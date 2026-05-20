"""Shared frontmatter parser result types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scribpy.model import Diagnostic


@dataclass(frozen=True)
class FrontmatterResult:
    """Result of separating frontmatter from Markdown body.

    Attributes:
        frontmatter: Parsed key/value metadata. Supports YAML (``---``) and
            TOML (``+++``) blocks with native types.
        body: Markdown source after the frontmatter block, or the original
            source when no frontmatter block is present.
        body_start_line: One-based line number where ``body`` starts in the
            original source.
        diagnostics: Frontmatter diagnostics detected during parsing.
    """

    frontmatter: dict[str, Any]
    body: str
    body_start_line: int
    diagnostics: tuple[Diagnostic, ...]


__all__ = ["FrontmatterResult"]
