"""Built-in Markdown-oriented transforms.

This module re-exports the public transform functions from the three
sub-modules that implement them:

- :mod:`markdown_headings` — heading normalization, demotion, and numbering
- :mod:`markdown_toc`      — table-of-contents generation
- :mod:`markdown_links`    — cross-reference rewriting and link normalization
"""

from __future__ import annotations

from scribpy.transforms.markdown_headings import (
    apply_section_numbering,
    normalize_assembled_markdown_headings,
)
from scribpy.transforms.markdown_links import (
    resolve_cross_references,
    rewrite_links_for_target,
)
from scribpy.transforms.markdown_toc import generate_toc_transform

__all__ = [
    "apply_section_numbering",
    "generate_toc_transform",
    "normalize_assembled_markdown_headings",
    "resolve_cross_references",
    "rewrite_links_for_target",
]
