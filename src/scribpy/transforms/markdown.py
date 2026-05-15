"""Built-in Markdown-oriented transforms."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

from scribpy.lint.resolution import resolve_relative_path
from scribpy.model import Document, Heading, TransformedDocument
from scribpy.transforms.types import TransformContext, TransformResult

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def apply_section_numbering(context: TransformContext) -> TransformResult:
    """Prefix headings with deterministic section numbers.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with numbered Markdown headings.
    """
    counters = [0] * 6
    transformed: list[TransformedDocument] = []
    for document in context.transformed_documents:
        content = _HEADING_RE.sub(
            lambda match: _number_heading(match, counters), document.content
        )
        transformed.append(replace(document, content=content))
    return TransformResult(documents=tuple(transformed))


def generate_toc_transform(context: TransformContext) -> TransformResult:
    """Insert a generated table of contents into the first document.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with one generated TOC placed after the first H1 when headings
        beyond level 1 exist.
    """
    headings = _extract_transformed_headings(context.transformed_documents)
    toc_items = [heading for heading in headings if heading.level >= 2]
    if not context.transformed_documents or not toc_items:
        return TransformResult(documents=context.transformed_documents)

    toc = _render_toc(toc_items)
    first, *rest = context.transformed_documents
    updated_first = replace(first, content=_insert_toc(first.content, toc))
    return TransformResult(documents=(updated_first, *rest))


def resolve_cross_references(context: TransformContext) -> TransformResult:
    """Rewrite Markdown cross-document links for assembled Markdown output.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with local file links rewritten to assembled-document anchors
        when the target is Markdown.
    """
    if context.target != "markdown":
        return TransformResult(documents=context.transformed_documents)

    anchor_lookup = _anchor_lookup(context.documents, context.transformed_documents)
    transformed = tuple(
        replace(
            document,
            content=_rewrite_links(document, anchor_lookup),
        )
        for document in context.transformed_documents
    )
    return TransformResult(documents=transformed)


def rewrite_links_for_target(context: TransformContext) -> TransformResult:
    """Normalize target-specific Markdown links.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with links normalized for the current target.
    """
    if context.target != "html":
        return TransformResult(documents=context.transformed_documents)

    transformed = tuple(
        replace(document, content=_rewrite_markdown_links_to_html(document.content))
        for document in context.transformed_documents
    )
    return TransformResult(documents=transformed)


def _number_heading(match: re.Match[str], counters: list[int]) -> str:
    marks, title = match.groups()
    level = len(marks)
    counters[level - 1] += 1
    for index in range(level, len(counters)):
        counters[index] = 0
    prefix = ".".join(str(value) for value in counters[:level] if value)
    return f"{marks} {prefix} {title}"


def _extract_transformed_headings(
    documents: tuple[TransformedDocument, ...],
) -> tuple[Heading, ...]:
    headings: list[Heading] = []
    for document in documents:
        for match in _HEADING_RE.finditer(document.content):
            marks, title = match.groups()
            headings.append(
                Heading(level=len(marks), title=title, anchor=_anchor(title))
            )
    return tuple(headings)


def _render_toc(headings: list[Heading]) -> str:
    lines = ["## Table of Contents"]
    for heading in headings:
        indent = "  " * (heading.level - 2)
        lines.append(f"{indent}- [{heading.title}](#{heading.anchor})")
    return "\n".join(lines)


def _insert_toc(content: str, toc: str) -> str:
    first_h1 = re.search(r"^#\s+.+$", content, flags=re.MULTILINE)
    if first_h1 is None:
        return f"{toc}\n\n{content}" if content else f"{toc}\n"
    insert_at = first_h1.end()
    remainder = content[insert_at:].lstrip("\n")
    suffix = f"\n\n{remainder}" if remainder else "\n"
    return f"{content[:insert_at]}\n\n{toc}{suffix}"


def _anchor_lookup(
    documents: tuple[Document, ...],
    transformed_documents: tuple[TransformedDocument, ...],
) -> dict[tuple[Path, str | None], str | None]:
    lookup: dict[tuple[Path, str | None], str | None] = {}
    for source, transformed in zip(documents, transformed_documents, strict=True):
        transformed_headings = _extract_transformed_headings((transformed,))
        lookup[(source.relative_path, None)] = (
            transformed_headings[0].anchor if transformed_headings else None
        )
        for original, updated in zip(
            source.headings, transformed_headings, strict=False
        ):
            lookup[(source.relative_path, original.anchor)] = updated.anchor
    return lookup


def _rewrite_links(
    document: TransformedDocument,
    anchor_lookup: dict[tuple[Path, str | None], str | None],
) -> str:
    def replace_link(match: re.Match[str]) -> str:
        """Rewrite one local Markdown link when a target anchor is known.

        Args:
            match: Regex match containing link text and target.

        Returns:
            Rewritten Markdown link or the original match text.
        """
        text, target = match.groups()
        parts = urlsplit(target)
        if parts.scheme or target.startswith("//") or parts.path == "":
            return match.group(0)
        source_document = document.source_document
        target_path = resolve_relative_path(source_document, parts.path)
        anchor = anchor_lookup.get((target_path, parts.fragment or None))
        if anchor is None:
            return match.group(0)
        return f"[{text}](#{anchor})"

    return _LINK_RE.sub(replace_link, document.content)


def _rewrite_markdown_links_to_html(content: str) -> str:
    def replace_link(match: re.Match[str]) -> str:
        """Rewrite one Markdown document link to its HTML equivalent.

        Args:
            match: Regex match containing link text and target.

        Returns:
            Rewritten HTML-oriented link or the original match text.
        """
        text, target = match.groups()
        parts = urlsplit(target)
        if parts.scheme or target.startswith("//") or not parts.path.endswith(".md"):
            return match.group(0)
        path = f"{parts.path[:-3]}.html"
        suffix = f"#{parts.fragment}" if parts.fragment else ""
        return f"[{text}]({path}{suffix})"

    return _LINK_RE.sub(replace_link, content)


def _anchor(title: str) -> str:
    lowered = title.lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered)
    return re.sub(r"\s+", "-", stripped).strip("-")


__all__ = [
    "apply_section_numbering",
    "generate_toc_transform",
    "resolve_cross_references",
    "rewrite_links_for_target",
]
