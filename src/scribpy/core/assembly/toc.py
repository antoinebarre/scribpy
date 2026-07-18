"""Table of contents generation for assembled Markdown documents."""

from __future__ import annotations

import re

from scribpy.core.assembly.slug import slugify_heading
from scribpy.core.markdown_patterns import _ATX_HEADING, _mask_fenced_blocks

_DEFAULT_TOC_DEPTH = 3


def generate_toc(content: str, max_depth: int = _DEFAULT_TOC_DEPTH) -> str:
    """Insert a table of contents after the first H1 in a Markdown document.

    Headings inside fenced code blocks are ignored.  The H1 itself is excluded
    from the TOC entries.  Entries deeper than ``max_depth`` levels below H1
    are also excluded.  If no headings below H1 exist within the depth limit
    the document is returned unchanged.  If no H1 is found the TOC is
    prepended to the document.

    Args:
        content: Assembled Markdown source text.
        max_depth: Maximum heading depth to include, relative to H1.  A value
            of 1 includes only H2; 2 includes H2 and H3; 3 (default) includes
            H2, H3, and H4.

    Returns:
        Markdown source with the TOC inserted, or the original content when
        no TOC entries can be produced.
    """
    headings = _extract_headings(content)
    entries = [h for h in headings if 1 < h[0] <= max_depth + 1]
    if not entries:
        return content
    toc_block = _render_toc(entries)
    return _insert_toc(content, toc_block)


def _extract_headings(content: str) -> list[tuple[int, str]]:
    """Return ATX headings not inside fenced code blocks.

    Args:
        content: Markdown source text.

    Returns:
        List of (level, title) pairs in document order.
    """
    masked = _mask_fenced_blocks(content)
    return [
        (len(m.group(1)), m.group(2).strip())
        for m in _ATX_HEADING.finditer(masked)
    ]


def _render_toc(entries: list[tuple[int, str]]) -> str:
    """Render TOC entries as an indented Markdown list.

    Indentation is relative to the minimum heading level present so the
    shallowest entries are always at the root of the list.

    Args:
        entries: List of (level, title) pairs, level >= 2.

    Returns:
        Markdown list string without leading or trailing blank lines.
    """
    min_level = min(level for level, _ in entries)
    lines: list[str] = []
    for level, title in entries:
        indent = "  " * (level - min_level)
        slug = slugify_heading(title)
        lines.append(f"{indent}- [{title}](#{slug})")
    return "\n".join(lines)


def _insert_toc(content: str, toc_block: str) -> str:
    """Insert the TOC block after the first H1 line.

    If no H1 is found the TOC is prepended to the document.

    Args:
        content: Assembled Markdown source text.
        toc_block: Rendered TOC Markdown string.

    Returns:
        Content with the TOC inserted.
    """
    h1_match = re.search(r"^#\s+.+$", content, re.MULTILINE)
    if h1_match is None:
        return toc_block + "\n\n" + content
    insert_pos = h1_match.end()
    before = content[:insert_pos]
    after = content[insert_pos:].lstrip("\n")
    return before + "\n\n" + toc_block + "\n\n" + after
