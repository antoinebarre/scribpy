"""PDF-specific Markdown preparation helpers."""

from __future__ import annotations

import re
from dataclasses import replace

from scribpy.assets.targets import is_external
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.model import TransformedDocument
from scribpy.transforms import TransformOptions

_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def drop_internal_pdf_links(
    documents: tuple[TransformedDocument, ...],
) -> tuple[TransformedDocument, ...]:
    """Convert internal Markdown links to text for robust PDF rendering.

    Args:
        documents: Documents prepared for PDF output.

    Returns:
        Documents whose internal Markdown links are plain text.
    """
    return tuple(
        replace(
            document,
            content=_MARKDOWN_LINK_RE.sub(
                lambda match: _pdf_link_replacement(match), document.content
            ),
        )
        for document in documents
    )


def pdf_transform_options(state: ResolvedPipelineState) -> TransformOptions:
    """Return Markdown transform options adapted for PDF rendering.

    Args:
        state: Resolved project pipeline state.

    Returns:
        Transform options for PDF assembly.
    """
    return TransformOptions(
        document_title=state.config.document.title
        or state.config.project.name
        or "Document",
        toc_enabled=False,
        toc_max_level=state.config.document.toc.max_level,
        toc_style=state.config.document.toc.style,
        numbering_enabled=state.config.document.numbering.enabled,
        numbering_max_level=state.config.document.numbering.max_level,
        numbering_style=state.config.document.numbering.style,
    )


def _pdf_link_replacement(match: re.Match[str]) -> str:
    """Return a PDF-safe replacement for one Markdown link match."""
    label = match.group(1)
    target = match.group(2).strip()
    if is_external(target):
        return match.group(0)
    return label


__all__ = [
    "_MARKDOWN_LINK_RE",
    "_pdf_link_replacement",
    "drop_internal_pdf_links",
    "pdf_transform_options",
]
