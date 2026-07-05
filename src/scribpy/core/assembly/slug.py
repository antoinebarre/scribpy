"""GitHub-style heading slug generation."""

from __future__ import annotations

import re

_INLINE_MARKERS = re.compile(r"[*_~`#]+")
_NON_SLUG_CHARS = re.compile(r"[^\w\s-]", flags=re.UNICODE)
_WHITESPACE = re.compile(r"\s+")


def slugify_heading(text: str) -> str:
    """Return a GitHub-style anchor slug from a Markdown heading title.

    The algorithm follows the GitHub Markdown anchor rules:
    strip inline markers, lowercase, remove non-word characters,
    and replace whitespace with hyphens.

    Args:
        text: Heading title text, possibly containing inline Markdown markers.

    Returns:
        URL-safe anchor slug.
    """
    text = _INLINE_MARKERS.sub("", text)
    text = text.lower()
    text = _NON_SLUG_CHARS.sub("", text)
    return _WHITESPACE.sub("-", text.strip())
