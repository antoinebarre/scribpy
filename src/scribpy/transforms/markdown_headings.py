"""Heading normalization, demotion, and section-numbering transforms."""

from __future__ import annotations

import re
from dataclasses import replace

from scribpy.model import Heading, TransformedDocument
from scribpy.transforms.number_formatting import format_number
from scribpy.transforms.types import TransformContext, TransformResult

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)


def normalize_assembled_markdown_headings(
    context: TransformContext,
) -> TransformResult:
    """Prepare one assembled Markdown hierarchy with a single global H1.

    Args:
        context: Current transform inputs.

    Returns:
        Documents whose source headings are demoted by one level, with the
        configured global H1 prepended to the first Markdown document.
    """
    if context.target != "markdown" or not context.transformed_documents:
        return TransformResult(documents=context.transformed_documents)

    normalized = tuple(
        replace(document, content=_demote_headings(document.content))
        for document in context.transformed_documents
    )
    title = context.options.document_title or "Document"
    first, *rest = normalized
    updated_first = replace(
        first, content=f"# {title}\n\n{first.content.lstrip()}"
    )
    return TransformResult(documents=(updated_first, *rest))


def apply_section_numbering(context: TransformContext) -> TransformResult:
    """Prefix headings with deterministic section numbers.

    Args:
        context: Current transform inputs.

    Returns:
        Documents with numbered Markdown headings.
    """
    if not context.options.numbering_enabled:
        return TransformResult(documents=context.transformed_documents)

    counters = [0] * 6
    transformed: list[TransformedDocument] = []
    for document in context.transformed_documents:
        content = _HEADING_RE.sub(
            lambda match: _number_heading(match, counters, context),
            document.content,
        )
        transformed.append(replace(document, content=content))
    return TransformResult(documents=tuple(transformed))


def extract_transformed_headings(
    documents: tuple[TransformedDocument, ...],
) -> tuple[Heading, ...]:
    """Extract headings from transformed document content.

    Args:
        documents: Transformed documents to scan.

    Returns:
        All headings found in document order.
    """
    headings: list[Heading] = []
    for document in documents:
        for match in _HEADING_RE.finditer(document.content):
            marks, title = match.groups()
            headings.append(
                Heading(level=len(marks), title=title, anchor=_anchor(title))
            )
    return tuple(headings)


def _number_heading(
    match: re.Match[str], counters: list[int], context: TransformContext
) -> str:
    """Apply a section number prefix to one heading match.

    Args:
        match: Heading regex match with marks and title groups.
        counters: Mutable per-level counter state.
        context: Current transform inputs for target and numbering options.

    Returns:
        Numbered heading string.
    """
    marks, title = match.groups()
    level = len(marks)
    if context.target == "markdown" and level == 1:
        for index in range(len(counters)):
            counters[index] = 0
        return match.group(0)
    if level > context.options.numbering_max_level:
        return match.group(0)
    counters[level - 1] += 1
    for index in range(level, len(counters)):
        counters[index] = 0
    prefix = ".".join(
        format_number(value, context.options.numbering_style)
        for value in counters[:level]
        if value
    )
    return f"{marks} {prefix} {title}"


def _demote_headings(content: str) -> str:
    """Demote all Markdown headings in content by one level.

    Args:
        content: Markdown source string.

    Returns:
        Content with each heading promoted by one ``#`` (capped at level 6).
    """

    def replace_heading(match: re.Match[str]) -> str:
        """Demote one Markdown heading by a single level.

        Args:
            match: Heading match containing marks and title.

        Returns:
            Markdown heading with one additional marker, capped at level six.
        """
        marks, title = match.groups()
        return f"{'#' * min(len(marks) + 1, 6)} {title}"

    return _HEADING_RE.sub(replace_heading, content)


def _anchor(title: str) -> str:
    """Convert a heading title to a URL-safe anchor slug.

    Args:
        title: Raw heading text.

    Returns:
        Lowercase hyphenated anchor string.
    """
    lowered = title.lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered)
    return re.sub(r"\s+", "-", stripped).strip("-")


__all__ = [
    "apply_section_numbering",
    "extract_transformed_headings",
    "normalize_assembled_markdown_headings",
]
