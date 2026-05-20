"""Validation rules for document indexes.

The validator compares the declared processing order with the scanner output:
it rejects unsafe paths and duplicates for every mode, then applies the
explicit-index-only checks for missing configured files and discovered files
left out of the configured order.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from scribpy.model import Diagnostic, DocumentIndex, SourceFile
from scribpy.project.index_diagnostics import (
    duplicate_entry,
    missing_explicit_file,
    uncovered_discovered_file,
    unsafe_entry,
    unsupported_index_mode,
)

SUPPORTED_INDEX_MODES = frozenset({"explicit", "filesystem"})


def validate_document_index(
    index: DocumentIndex,
    files: tuple[SourceFile, ...],
) -> tuple[Diagnostic, ...]:
    """Validate index entries against discovered source files.

    Args:
        index: Document index to validate.
        files: Markdown source files discovered by the project scanner.

    Returns:
        User-facing diagnostics for invalid, duplicate, missing, or uncovered
        index entries.
    """
    if index.mode not in SUPPORTED_INDEX_MODES:
        return (unsupported_index_mode(),)

    diagnostics: list[Diagnostic] = []
    discovered_paths = frozenset(
        source_file.relative_path for source_file in files
    )

    diagnostics.extend(_validate_entry_scope(index.paths))
    diagnostics.extend(_validate_duplicates(index.paths))

    if index.mode == "explicit":
        indexed_paths = set(index.paths)
        diagnostics.extend(
            _validate_missing_explicit_files(index.paths, discovered_paths)
        )
        diagnostics.extend(
            _validate_uncovered_discovered_files(indexed_paths, files)
        )

    return tuple(diagnostics)


def _validate_entry_scope(paths: tuple[Path, ...]) -> tuple[Diagnostic, ...]:
    """Return diagnostics for unsafe index entry paths."""
    return tuple(
        unsafe_entry(path) for path in paths if not is_safe_path(path)
    )


def _validate_duplicates(paths: tuple[Path, ...]) -> tuple[Diagnostic, ...]:
    """Return diagnostics for duplicated index entry paths."""
    counts = Counter(paths)
    return tuple(
        duplicate_entry(path) for path, count in counts.items() if count > 1
    )


def _validate_missing_explicit_files(
    paths: tuple[Path, ...],
    discovered_paths: frozenset[Path],
) -> tuple[Diagnostic, ...]:
    """Return diagnostics for explicit entries missing from scanned files."""
    return tuple(
        missing_explicit_file(path)
        for path in paths
        if is_safe_path(path) and path not in discovered_paths
    )


def _validate_uncovered_discovered_files(
    indexed_paths: set[Path],
    files: tuple[SourceFile, ...],
) -> tuple[Diagnostic, ...]:
    """Return warnings for discovered files omitted from explicit index."""
    return tuple(
        uncovered_discovered_file(source_file.relative_path)
        for source_file in files
        if source_file.relative_path not in indexed_paths
    )


def is_safe_path(path: Path) -> bool:
    """Return whether an index path stays inside the source tree.

    Args:
        path: Candidate index path.

    Returns:
        ``True`` when the path is relative and has no parent-directory segment.
    """
    return not path.is_absolute() and ".." not in path.parts


__all__ = ["SUPPORTED_INDEX_MODES", "is_safe_path", "validate_document_index"]
