"""Delimited frontmatter block parsing."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from scribpy.model import Diagnostic
from scribpy.parser.frontmatter_diagnostics import unclosed_frontmatter
from scribpy.parser.frontmatter_types import FrontmatterResult

type FrontmatterAdapter = Callable[
    [str],
    tuple[dict[str, Any], tuple[Diagnostic, ...]],
]


def parse_delimited_block(
    lines: list[str],
    *,
    delimiter: str,
    adapter: Callable[
        [str],
        tuple[dict[str, Any], tuple[Diagnostic, ...]],
    ],
    path: Path | None,
) -> FrontmatterResult:
    """Parse a frontmatter block enclosed by matching delimiters.

    Args:
        lines: Markdown source split into lines with line endings preserved.
        delimiter: Frontmatter delimiter that opens and closes the block.
        adapter: Parser for the raw block body.
        path: Optional source path attached to diagnostics.

    Returns:
        Parsed frontmatter result.
    """
    closing_index = _find_closing_delimiter(lines, delimiter)
    if closing_index is None:
        return FrontmatterResult(
            frontmatter={},
            body="",
            body_start_line=len(lines) + 1,
            diagnostics=(unclosed_frontmatter(delimiter, path),),
        )

    raw_block = "".join(lines[1:closing_index])
    frontmatter, diagnostics = adapter(raw_block)
    body_start_line = closing_index + 2
    return FrontmatterResult(
        frontmatter=frontmatter,
        body="".join(lines[closing_index + 1 :]),
        body_start_line=body_start_line,
        diagnostics=diagnostics,
    )


def _find_closing_delimiter(lines: list[str], delimiter: str) -> int | None:
    """Return the line index of a closing frontmatter delimiter."""
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == delimiter:
            return index
    return None


__all__ = ["parse_delimited_block"]
