"""Heading extraction and TOC block removal for HTML export."""

from __future__ import annotations

import re

from scribpy.core.assembly.slug import slugify_heading

_ATX_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FENCED_BLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
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


def _mask_fenced_blocks(content: str) -> str:
    """Replace fenced code block interiors with blank lines.

    Preserves line count so regex positions remain valid.

    Args:
        content: Markdown source text.

    Returns:
        Content with fenced block interiors replaced by newlines.
    """

    def _blank(match: re.Match[str]) -> str:
        """Return blank lines matching the fenced block line count.

        Args:
            match: Regex match object for a fenced code block.

        Returns:
            String of newlines equal to the matched block line count.
        """
        return "\n" * match.group(0).count("\n")

    return _FENCED_BLOCK.sub(_blank, content)
