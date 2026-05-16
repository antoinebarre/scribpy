"""Execution helpers for ordered document transform pipelines."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.model import Diagnostic, Document, TransformedDocument
from scribpy.transforms.markdown import (
    apply_section_numbering,
    generate_toc_transform,
    normalize_assembled_markdown_headings,
    resolve_cross_references,
    rewrite_links_for_target,
)
from scribpy.transforms.types import (
    BuildTarget,
    Transform,
    TransformContext,
    TransformResult,
)


def apply_transforms(
    documents: tuple[Document, ...],
    *,
    target: BuildTarget,
    transforms: Iterable[Transform],
    document_title: str | None = None,
) -> TransformResult:
    """Apply ordered transforms and return target-ready documents.

    Args:
        documents: Parsed source documents in deterministic order.
        target: Build target currently being prepared.
        transforms: Ordered transformation functions.
        document_title: Optional global title for assembled target outputs.

    Returns:
        Final transformed documents plus accumulated diagnostics.
    """
    transformed = tuple(
        TransformedDocument.from_document(document) for document in documents
    )
    diagnostics: list[Diagnostic] = []
    for transform in transforms:
        result = transform(
            TransformContext(
                target=target,
                documents=documents,
                transformed_documents=transformed,
                document_title=document_title,
            )
        )
        transformed = result.documents
        diagnostics.extend(result.diagnostics)
    return TransformResult(documents=transformed, diagnostics=tuple(diagnostics))


def native_markdown_transforms() -> tuple[Transform, ...]:
    """Return built-in transforms for assembled Markdown output.

    Returns:
        Ordered built-in Markdown transforms.
    """
    return (
        normalize_assembled_markdown_headings,
        apply_section_numbering,
        resolve_cross_references,
        generate_toc_transform,
    )


def native_html_transforms() -> tuple[Transform, ...]:
    """Return built-in transforms for HTML-oriented output.

    Returns:
        Ordered built-in HTML transforms.
    """
    return (
        apply_section_numbering,
        rewrite_links_for_target,
        generate_toc_transform,
    )


__all__ = ["apply_transforms", "native_html_transforms", "native_markdown_transforms"]
