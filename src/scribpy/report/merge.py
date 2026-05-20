"""Markdown document merge utilities.

Provides ``merge_markdown`` to concatenate several GFM strings into one
coherent document, with optional heading-level adjustment per section.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MergeSection:
    """One source document to include in a merged report.

    Attributes:
        content: The GFM string to merge.
        heading_offset: Number of ``#`` levels to add to every heading in
            this section (0 = keep as-is, 1 = demote H1→H2, etc.).
    """

    content: str
    heading_offset: int = 0


def merge_markdown(
    *sections: MergeSection, separator: str = "\n\n---\n\n"
) -> str:
    """Merge several GFM documents into a single string.

    Each section's headings are shifted by ``heading_offset`` levels.
    The sections are joined with ``separator`` (default: horizontal rule).
    The first section's frontmatter (if any) is preserved; frontmatter
    from subsequent sections is stripped.

    Args:
        *sections: Source sections to merge, in order.
        separator: String inserted between sections.

    Returns:
        A single merged GFM string.
    """
    parts: list[str] = []
    for i, section in enumerate(sections):
        text = (
            _strip_frontmatter(section.content) if i > 0 else section.content
        )
        text = _shift_headings(text, section.heading_offset)
        parts.append(text.strip())
    return separator.join(parts)


def _shift_headings(text: str, offset: int) -> str:
    """Add ``offset`` ``#`` characters to every ATX heading line.

    Args:
        text: GFM source text.
        offset: Number of heading levels to add (0 = no change).

    Returns:
        Text with adjusted heading levels (capped at H6).
    """
    if offset == 0:
        return text

    def _replace(m: re.Match[str]) -> str:
        """Replace a heading match with the offset-adjusted heading."""
        hashes = m.group(1)
        new_level = min(len(hashes) + offset, 6)
        return "#" * new_level + m.group(2)

    return re.sub(r"^(#{1,6})([ \t].*)$", _replace, text, flags=re.MULTILINE)


def _strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block from ``text``.

    Args:
        text: GFM source text that may start with ``---`` frontmatter.

    Returns:
        Text with the frontmatter block removed, or the original text
        if no frontmatter block is present.
    """
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        return text
    # Find the closing ---
    rest = stripped[3:]
    end = re.search(r"^\s*---\s*$", rest, flags=re.MULTILINE)
    if end is None:
        return text
    return rest[end.end() :].lstrip()
