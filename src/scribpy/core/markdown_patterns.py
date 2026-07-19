"""Shared patterns and classifications for Markdown processing."""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_ATX_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
_FENCED_BLOCK = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
ROOT_FILE_HEADING_LEVEL: int = 2


def _mask_fenced_blocks(content: str) -> str:
    """Replace fenced code blocks with blank lines.

    Args:
        content: Markdown source text.

    Returns:
        Content with fenced blocks replaced while preserving line count.
    """

    def _blank(match: re.Match[str]) -> str:
        """Return blank lines matching a fenced block's line count.

        Args:
            match: Fenced block regular-expression match.

        Returns:
            Newlines matching the fenced block line count.
        """
        return "\n" * match.group(0).count("\n")

    return _FENCED_BLOCK.sub(_blank, content)


def _is_external_target(target: str) -> bool:
    """Return whether a Markdown target points outside local files.

    Args:
        target: Raw Markdown target.

    Returns:
        True when the target has an external scheme or network location.
    """
    parsed = urlsplit(target)
    return bool(parsed.netloc or (parsed.scheme and parsed.scheme != "file"))
