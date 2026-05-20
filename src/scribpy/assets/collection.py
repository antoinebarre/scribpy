"""Collect local asset paths referenced by parsed documents."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets.targets import is_external
from scribpy.model import Document


def collect_asset_paths(
    documents: tuple[Document, ...],
    source_root: Path,
) -> tuple[Path, ...]:
    """Collect unique absolute asset paths referenced across all documents.

    Args:
        documents: Parsed source documents.
        source_root: Absolute root from which relative asset paths are
            resolved.

    Returns:
        Unique absolute asset paths in deterministic order.
    """
    seen: set[Path] = set()
    ordered: list[Path] = []
    for document in documents:
        for candidate in _local_asset_candidates(document):
            abs_path = (document.path.parent / candidate).resolve()
            if abs_path not in seen:
                seen.add(abs_path)
                ordered.append(abs_path)
    return tuple(ordered)


def _local_asset_candidates(document: Document) -> tuple[Path, ...]:
    """Return local asset path candidates from one document."""
    candidates: list[Path] = []
    for asset in document.assets:
        if asset.path is not None:
            candidate = asset.path
        else:
            if is_external(asset.target):
                continue
            candidate = Path(asset.target)
        if not is_external(str(candidate)):
            candidates.append(candidate)
    return tuple(candidates)


__all__ = ["collect_asset_paths"]
