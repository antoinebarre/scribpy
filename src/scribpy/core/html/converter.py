"""Markdown-to-HTML conversion adapter."""

from __future__ import annotations

import markdown

_EXTENSIONS = ["tables", "fenced_code", "footnotes", "attr_list", "toc"]


def to_html(content: str) -> str:
    """Convert Markdown source text to an HTML fragment.

    Uses the ``python-markdown`` library with the ``tables``,
    ``fenced_code``, ``footnotes``, and ``attr_list`` extensions enabled.
    The ``toc`` extension is included so heading ``id`` attributes are
    generated and anchors in the burger menu resolve correctly.

    Args:
        content: Markdown source text (without the TOC block).

    Returns:
        HTML string for the document body (no ``<html>`` or ``<body>`` tags).
    """
    md = markdown.Markdown(extensions=_EXTENSIONS)
    return md.convert(content)
