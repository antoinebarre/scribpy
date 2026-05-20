"""Table-of-contents generation transform."""

from __future__ import annotations

import re
from dataclasses import replace

from scribpy.model import Heading
from scribpy.transforms.markdown_headings import extract_transformed_headings
from scribpy.transforms.types import TransformContext, TransformResult


def generate_toc_transform(context: TransformContext) -> TransformResult:
    """Insert a generated table of contents into the first document.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with one generated TOC placed after the first H1 when headings
        beyond level 1 exist.
    """
    if not context.options.toc_enabled:
        return TransformResult(documents=context.transformed_documents)

    headings = extract_transformed_headings(context.transformed_documents)
    toc_items = [
        heading
        for heading in headings
        if 2 <= heading.level <= context.options.toc_max_level
    ]
    if not context.transformed_documents or not toc_items:
        return TransformResult(documents=context.transformed_documents)

    toc = _render_toc(toc_items, context.options.toc_style)
    first, *rest = context.transformed_documents
    updated_first = replace(first, content=_insert_toc(first.content, toc))
    return TransformResult(documents=(updated_first, *rest))


def _render_toc(headings: list[Heading], style: str) -> str:
    """Render a Markdown table-of-contents block.

    Args:
        headings: Headings to include in the TOC.
        style: List marker style: ``"numbered"`` or ``"-"`` (bullet).

    Returns:
        Markdown TOC block as a string.
    """
    marker = "1." if style == "numbered" else "-"
    lines = ["## Table of Contents"]
    for heading in headings:
        indent = "  " * (heading.level - 2)
        lines.append(f"{indent}{marker} [{heading.title}](#{heading.anchor})")
    return "\n".join(lines)


def _insert_toc(content: str, toc: str) -> str:
    """Insert a TOC block after the first H1 in content.

    Args:
        content: Markdown content string.
        toc: Rendered TOC block to insert.

    Returns:
        Content with the TOC inserted after the first H1, or prepended when
        no H1 is found.
    """
    first_h1 = re.search(r"^#\s+.+$", content, flags=re.MULTILINE)
    if first_h1 is None:
        return f"{toc}\n\n{content}" if content else f"{toc}\n"
    insert_at = first_h1.end()
    remainder = content[insert_at:].lstrip("\n")
    suffix = f"\n\n{remainder}" if remainder else "\n"
    return f"{content[:insert_at]}\n\n{toc}{suffix}"


__all__ = ["generate_toc_transform"]
