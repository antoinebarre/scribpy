"""Heading extraction and TOC block removal for HTML export."""

from __future__ import annotations

import re

from scribpy.core.assembly.slug import slugify_heading
from scribpy.core.markdown_patterns import _ATX_HEADING, _mask_fenced_blocks

_TOC_BLOCK = re.compile(
    r"\n\n"
    r"(?:[ \t]*- \[.+?\]\(#[^\)]*\)[ \t]*\n)+"
    r"(?:[ \t]{2,}- \[.+?\]\(#[^\)]*\)[ \t]*\n)*"
    r"\n?",
)


def extract_headings(
    content: str,
    toc_depth: int,
) -> list[tuple[int, str]]:
    """Return ATX headings eligible for the burger menu navigation.

    H1 is excluded; only headings at levels 2 through ``toc_depth + 1``
    are returned.  Headings inside fenced code blocks are ignored.

    Args:
        content: Assembled Markdown source text.
        toc_depth: Maximum depth relative to H1.  1 = H2 only,
            2 = H2+H3, 3 = H2+H3+H4, etc.

    Returns:
        List of (level, title) pairs in document order.
    """
    masked = _mask_fenced_blocks(content)
    max_level = toc_depth + 1
    return [
        (len(m.group(1)), m.group(2).strip())
        for m in _ATX_HEADING.finditer(masked)
        if 1 < len(m.group(1)) <= max_level
    ]


def strip_toc_block(content: str) -> str:
    """Remove the auto-generated TOC list block from Markdown content.

    The TOC block is a contiguous Markdown list of anchor links inserted
    by ``generate_toc()``.  When present it is removed so the HTML body
    does not duplicate the burger menu navigation.

    The original content is returned unchanged when no TOC block is found.

    Args:
        content: Assembled Markdown source text, possibly containing a TOC.

    Returns:
        Content with the TOC list block removed, or original if absent.
    """
    return _TOC_BLOCK.sub("\n\n", content, count=1)


def build_nav_entries(
    headings: list[tuple[int, str]],
) -> list[dict[str, str | int]]:
    """Convert heading pairs to navigation entry dicts for the burger menu.

    Args:
        headings: List of (level, title) pairs as returned by
            ``extract_headings()``.

    Returns:
        List of dicts with keys ``"level"``, ``"title"``, and ``"slug"``.
    """
    return [
        {"level": level, "title": title, "slug": slugify_heading(title)}
        for level, title in headings
    ]
