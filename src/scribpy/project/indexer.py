"""Document index construction and validation."""

from __future__ import annotations

from scribpy.config import Config
from scribpy.model import Diagnostic, DocumentIndex, SourceFile
from scribpy.project.index_diagnostics import unsupported_config_mode
from scribpy.project.index_validation import (
    SUPPORTED_INDEX_MODES,
    validate_document_index,
)


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
    if config.index.mode not in SUPPORTED_INDEX_MODES:
        return None, (unsupported_config_mode(),)

    if config.index.mode == "filesystem":
        index = DocumentIndex(
            paths=tuple(source_file.relative_path for source_file in files),
            mode="filesystem",
        )
        return index, validate_document_index(index, files)

    index = DocumentIndex(paths=config.index.files, mode="explicit")
    return index, validate_document_index(index, files)


__all__ = ["build_document_index", "validate_document_index"]
