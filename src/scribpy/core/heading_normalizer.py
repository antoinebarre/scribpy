"""Markdown heading normalization helpers."""

from __future__ import annotations

import re

from mkforge import MarkdownSource
from mkforge.verification.source_scan import lines_outside_fenced_code

_ATX_HEADING = re.compile(
    r"^(?P<marks>#{1,6})(?P<space>[ \t]+)(?P<title>.*?)(?P<newline>\r?\n)?$",
)
_MAX_HEADING_LEVEL = 6


def normalize_markdown_headings(content: str, base_level: int) -> str:
    """Shift Markdown ATX headings so source H1 starts at a target level.

    Args:
        content: Markdown source text to normalize.
        base_level: Heading level used for source H1 headings.

    Returns:
        Markdown source with normalized headings outside fenced code blocks.
    """
    outside_line_numbers = _outside_line_numbers(content)
    return "".join(
        _normalize_line(line, base_level)
        if line_number in outside_line_numbers
        else line
        for line_number, line in enumerate(
            content.splitlines(keepends=True), 1
        )
    )


def _outside_line_numbers(content: str) -> frozenset[int]:
    """Return line numbers outside fenced code blocks.

    Args:
        content: Markdown source text to scan.

    Returns:
        Line numbers that may contain real Markdown syntax.
    """
    source = MarkdownSource.from_text(content)
    return frozenset(line.number for line in lines_outside_fenced_code(source))


def _normalize_line(line: str, base_level: int) -> str:
    """Normalize one Markdown source line when it is an ATX heading.

    Args:
        line: Markdown source line.
        base_level: Heading level used for source H1 headings.

    Returns:
        Original line or normalized heading line.
    """
    match = _ATX_HEADING.match(line)
    if match is None:
        return line
    level = _target_heading_level(len(match.group("marks")), base_level)
    return (
        f"{'#' * level}"
        f"{match.group('space')}"
        f"{match.group('title')}"
        f"{match.group('newline') or ''}"
    )


def _target_heading_level(source_level: int, base_level: int) -> int:
    """Return the normalized heading level capped to Markdown limits.

    Args:
        source_level: Heading level found in the source document.
        base_level: Heading level used for source H1 headings.

    Returns:
        Heading level between 1 and 6.
    """
    return min(_MAX_HEADING_LEVEL, max(1, base_level) + source_level - 1)
