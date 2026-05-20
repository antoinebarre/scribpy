"""Table of contents generation for GFM reports."""

from __future__ import annotations

import re
from collections.abc import Sequence


def _slugify(title: str) -> str:
    """Convert a heading title to a GitHub-compatible anchor slug.

    Args:
        title: The raw heading text.

    Returns:
        A lowercase, hyphenated slug suitable for GFM anchors.
    """
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug.strip())
    return slug


def _toc_line(title: str, depth: int) -> str:
    """Format a single TOC entry.

    Args:
        title: The heading title.
        depth: Nesting depth (1 = chapter level).

    Returns:
        An indented GFM list item with an anchor link.
    """
    anchor = _slugify(title)
    indent = "  " * (depth - 1)
    return f"{indent}- [{title}](#{anchor})"


def generate_toc(report: object) -> str:
    """Return a GFM TOC string for the given Report.

    Args:
        report: A Report instance to generate the TOC for.

    Returns:
        A newline-separated string of GFM list items, or an empty
        string if the report has no chapters.
    """
    from .nodes import Chapter, Report

    assert isinstance(report, Report)
    lines: list[str] = []

    for chapter in report.children:
        assert isinstance(chapter, Chapter)
        lines.append(_toc_line(chapter.title, 1))
        _collect_section_toc(chapter.children, depth=2, lines=lines)

    return "\n".join(lines)


def _collect_section_toc(
    children: Sequence[object],
    depth: int,
    lines: list[str],
) -> None:
    """Recursively append TOC lines for Section nodes.

    Args:
        children: Child nodes of a Chapter or Section.
        depth: Current TOC indentation depth.
        lines: Accumulator list to append TOC entries into.
    """
    from .nodes import Section

    for child in children:
        if isinstance(child, Section):
            lines.append(_toc_line(child.title, depth))
            _collect_section_toc(child.children, depth + 1, lines)
