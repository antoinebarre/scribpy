"""Document index construction and validation."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from scribpy.config import Config
from scribpy.model import Diagnostic, DocumentIndex, SourceFile

_SUPPORTED_INDEX_MODES = frozenset({"explicit", "filesystem"})


def build_document_index(
    config: Config,
    files: tuple[SourceFile, ...],
) -> tuple[DocumentIndex | None, tuple[Diagnostic, ...]]:
    """Build and validate a document index from configuration and scan output.

    Args:
        config: Parsed Scribpy configuration.
        files: Markdown source files discovered by the project scanner.

    Returns:
        A tuple containing the document index when it can be built, or ``None``
        when the configured mode is unsupported, plus validation diagnostics.
    """
    if config.index.mode not in _SUPPORTED_INDEX_MODES:
        return None, (
            Diagnostic(
                severity="error",
                code="IDX001",
                message="Configured index mode is not supported yet.",
                hint="Use index.mode = 'filesystem' or index.mode = 'explicit'.",
            ),
        )

    if config.index.mode == "filesystem":
        index = DocumentIndex(
            paths=tuple(source_file.relative_path for source_file in files),
            mode="filesystem",
        )
        return index, validate_document_index(index, files)

    index = DocumentIndex(paths=config.index.files, mode="explicit")
    return index, validate_document_index(index, files)


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
    if index.mode not in _SUPPORTED_INDEX_MODES:
        return (
            Diagnostic(
                severity="error",
                code="IDX001",
                message="Document index mode is not supported yet.",
                hint="Use an explicit or filesystem index.",
            ),
        )

    diagnostics: list[Diagnostic] = []
    discovered_paths = frozenset(source_file.relative_path for source_file in files)

    diagnostics.extend(_validate_entry_scope(index.paths))
    diagnostics.extend(_validate_duplicates(index.paths))

    if index.mode == "explicit":
        indexed_paths = set(index.paths)
        diagnostics.extend(
            _validate_missing_explicit_files(index.paths, discovered_paths)
        )
        diagnostics.extend(_validate_uncovered_discovered_files(indexed_paths, files))

    return tuple(diagnostics)


def _validate_entry_scope(paths: tuple[Path, ...]) -> tuple[Diagnostic, ...]:
    return tuple(
        Diagnostic(
            severity="error",
            code="IDX004",
            message="Index entries must be relative and stay inside the source tree.",
            path=path,
            hint="Remove absolute paths and '..' segments from index.files.",
        )
        for path in paths
        if not _is_safe_relative_path(path)
    )


def _validate_duplicates(paths: tuple[Path, ...]) -> tuple[Diagnostic, ...]:
    counts = Counter(paths)
    return tuple(
        Diagnostic(
            severity="error",
            code="IDX003",
            message="Index entry is duplicated.",
            path=path,
            hint="Keep each source file only once in index.files.",
        )
        for path, count in counts.items()
        if count > 1
    )


def _validate_missing_explicit_files(
    paths: tuple[Path, ...],
    discovered_paths: frozenset[Path],
) -> tuple[Diagnostic, ...]:
    return tuple(
        Diagnostic(
            severity="error",
            code="IDX002",
            message="Explicit index entry was not found in discovered source files.",
            path=path,
            hint=(
                "Create the file under the source directory or remove it from "
                "index.files."
            ),
        )
        for path in paths
        if _is_safe_relative_path(path) and path not in discovered_paths
    )


def _validate_uncovered_discovered_files(
    indexed_paths: set[Path],
    files: tuple[SourceFile, ...],
) -> tuple[Diagnostic, ...]:
    return tuple(
        Diagnostic(
            severity="warning",
            code="IDX005",
            message="Discovered source file is not listed in explicit index.",
            path=source_file.relative_path,
            hint="Add the file to index.files if it should be part of the build.",
        )
        for source_file in files
        if source_file.relative_path not in indexed_paths
    )


def _is_safe_relative_path(path: Path) -> bool:
    return not path.is_absolute() and ".." not in path.parts


__all__ = ["build_document_index", "validate_document_index"]
