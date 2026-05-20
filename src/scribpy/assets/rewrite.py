"""Rewrite local asset links for flattened single-page HTML output."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from scribpy.assets.targets import is_external
from scribpy.model import TransformedDocument


def rewrite_asset_links_single_page(
    documents: tuple[TransformedDocument, ...],
    source_root: Path,
) -> tuple[TransformedDocument, ...]:
    """Rewrite local image links for the flattened single-page output.

    Single-page HTML is written beside one shared ``assets/`` directory, while
    source Markdown image links are relative to each source document. This
    function rewrites only local image targets and leaves remote URLs intact.

    Args:
        documents: Target-ready documents that will be flattened into one page.
        source_root: Absolute source directory used to preserve asset subpaths.

    Returns:
        Documents whose local image links point into the shared asset directory.
    """
    return tuple(
        replace(
            document, content=_rewrite_document_links(document, source_root)
        )
        for document in documents
    )


def _rewrite_document_links(
    document: TransformedDocument, source_root: Path
) -> str:
    """Return one document's content with local asset links rewritten."""
    content = document.content
    for asset in document.source_document.assets:
        if asset.path is None or is_external(asset.target):
            continue
        rel = _single_page_asset_path(
            document.source_document.path.parent / asset.path, source_root
        )
        content = content.replace(
            f"]({asset.target})",
            f"](assets/{rel.as_posix()})",
        )
    return content


def _single_page_asset_path(asset_path: Path, source_root: Path) -> Path:
    """Return the single-page relative asset path for one source asset."""
    abs_path = asset_path.resolve()
    try:
        return abs_path.relative_to(source_root)
    except ValueError:
        return Path(abs_path.name)


__all__ = ["rewrite_asset_links_single_page"]
