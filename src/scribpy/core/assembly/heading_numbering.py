"""Heading numbering adapter for MkForge."""

from __future__ import annotations

import mkforge


def number_markdown_headings(content: str) -> str:
    """Apply MkForge heading numbering to assembled Markdown content.

    Args:
        content: Assembled Markdown source text.

    Returns:
        Markdown source returned by MkForge.

    Raises:
        TypeError: If MkForge rejects the Markdown source type.
        ValueError: If MkForge rejects its numbering configuration.
    """
    return mkforge.renumber_markdown_headings(content, start_level=2)
