"""Target document and anchor resolution for internal links."""

from __future__ import annotations

from pathlib import Path

from scribpy.lint.resolution import (
    resolve_relative_path,
    stays_within_source_tree,
)
from scribpy.model import Document


def target_document(
    document: Document,
    raw_path: str,
    documents: dict[Path, Document],
) -> Document | None:
    """Return the document targeted by one local Markdown link.

    Args:
        document: Source document that owns the link.
        raw_path: Local path component from the link target.
        documents: Documents indexed by source-relative path.

    Returns:
        Target document, or ``None`` when the target is missing or unsafe.
    """
    if raw_path == "":
        return document
    relative_path = resolve_relative_path(document, raw_path)
    if not stays_within_source_tree(relative_path):
        return None
    return documents.get(relative_path)


def has_anchor(document: Document, anchor: str) -> bool:
    """Return whether a target document exposes one heading anchor.

    Args:
        document: Target document.
        anchor: Anchor without the leading ``#``.

    Returns:
        ``True`` when one parsed heading has the requested anchor.
    """
    return any(heading.anchor == anchor for heading in document.headings)


__all__ = ["has_anchor", "target_document"]
