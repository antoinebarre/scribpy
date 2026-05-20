"""Cross-reference and link-rewriting transforms."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

from scribpy.lint.resolution import resolve_relative_path
from scribpy.model import Document, TransformedDocument
from scribpy.transforms.markdown_headings import extract_transformed_headings
from scribpy.transforms.types import TransformContext, TransformResult

_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


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

    lookup = _anchor_lookup(context.documents, context.transformed_documents)
    transformed = tuple(
        replace(document, content=_rewrite_links(document, lookup))
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
        replace(
            document,
            content=_rewrite_markdown_links_to_html(document.content),
        )
        for document in context.transformed_documents
    )
    return TransformResult(documents=transformed)


def _anchor_lookup(
    documents: tuple[Document, ...],
    transformed_documents: tuple[TransformedDocument, ...],
) -> dict[tuple[Path, str | None], str | None]:
    """Build a mapping from (relative_path, original_anchor) to new anchor.

    Args:
        documents: Original parsed documents.
        transformed_documents: Documents after earlier transforms.

    Returns:
        Lookup dict keyed by ``(relative_path, original_anchor)`` mapping to
        the post-transform anchor, or ``None`` when no anchor exists.
    """
    lookup: dict[tuple[Path, str | None], str | None] = {}
    for source, transformed in zip(
        documents, transformed_documents, strict=True
    ):
        transformed_headings = extract_transformed_headings((transformed,))
        source_aligned = (
            transformed_headings[-len(source.headings) :]
            if source.headings
            else ()
        )
        lookup[(source.relative_path, None)] = (
            source_aligned[0].anchor if source_aligned else None
        )
        for original, updated in zip(
            source.headings, source_aligned, strict=False
        ):
            lookup[(source.relative_path, original.anchor)] = updated.anchor
    return lookup


def _rewrite_links(
    document: TransformedDocument,
    anchor_lookup: dict[tuple[Path, str | None], str | None],
) -> str:
    """Rewrite internal Markdown links using the pre-built anchor lookup.

    Args:
        document: Transformed document whose links to rewrite.
        anchor_lookup: Mapping from (path, anchor) to new anchor string.

    Returns:
        Document content with rewritten internal links.
    """

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
        target_path = resolve_relative_path(
            document.source_document, parts.path
        )
        anchor = anchor_lookup.get((target_path, parts.fragment or None))
        if anchor is None:
            return match.group(0)
        return f"[{text}](#{anchor})"

    return _LINK_RE.sub(replace_link, document.content)


def _rewrite_markdown_links_to_html(content: str) -> str:
    """Rewrite ``*.md`` links to ``*.html`` for HTML-target output.

    Args:
        content: Markdown content string.

    Returns:
        Content with ``.md`` links converted to ``.html`` equivalents.
    """

    def replace_link(match: re.Match[str]) -> str:
        """Rewrite one Markdown document link to its HTML equivalent.

        Args:
            match: Regex match containing link text and target.

        Returns:
            Rewritten HTML-oriented link or the original match text.
        """
        text, target = match.groups()
        parts = urlsplit(target)
        if (
            parts.scheme
            or target.startswith("//")
            or not parts.path.endswith(".md")
        ):
            return match.group(0)
        path = f"{parts.path[:-3]}.html"
        suffix = f"#{parts.fragment}" if parts.fragment else ""
        return f"[{text}]({path}{suffix})"

    return _LINK_RE.sub(replace_link, content)


__all__ = ["resolve_cross_references", "rewrite_links_for_target"]
