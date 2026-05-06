"""Application service for project Markdown parsing (FC-03 chain)."""

from __future__ import annotations

from pathlib import Path

from scribpy.config import CONFIG_FILENAME, find_config, load_config
from scribpy.model import Diagnostic, ParseResult
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.parser.document import order_by_index, parse_documents
from scribpy.project import build_document_index, resolve_project_root, scan_project
from scribpy.utils import has_errors
from scribpy.utils.file_utils import RealFileSystem


def parse_project_documents(
    root: Path | None = None,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
) -> ParseResult:
    """Load a project, build its document index, and parse all Markdown files.

    This function is the FC-03 application entry point. It:
      1. Locates and loads ``scribpy.toml``.
      2. Scans the source directory for Markdown files.
      3. Builds and validates the document index.
      4. Reorders the discovered files to match the index order.
      5. Parses every source file into a typed ``Document``.

    Configuration, scanning, and index errors are surfaced as ``Diagnostic``
    objects inside the returned ``ParseResult``. A ``ParseResult.failed``
    flag of ``True`` means at least one blocking error prevented full parsing.

    Args:
        root: Project directory, any path inside a project, or a direct path
            to ``scribpy.toml``. Defaults to the current working directory.
        filesystem: Injected ``FileSystem`` service. Defaults to the real
            OS filesystem when ``None``.
        parser: Optional external ``MarkdownParser`` injected into the parse
            chain. Defaults to the bundled ``markdown-it-py`` adapter.

    Returns:
        A ``ParseResult`` containing parsed documents and all diagnostics
        produced during configuration loading, scanning, indexing, and parsing.
    """
    fs = filesystem if filesystem is not None else RealFileSystem()
    start = Path.cwd() if root is None else root

    config_path = _resolve_config_path(start)
    if config_path is None:
        return _failed(
            Diagnostic(
                severity="error",
                code="CFG001",
                message="Could not find scribpy.toml.",
                path=start,
                hint="Create scribpy.toml at the project root or pass its path.",
            )
        )

    config, config_diagnostics = load_config(config_path)
    if config is None or has_errors(config_diagnostics):
        return ParseResult(
            documents=(),
            diagnostics=config_diagnostics,
            failed=True,
        )

    project_root = resolve_project_root(config_path)
    source_files, scan_diagnostics = scan_project(project_root, config)
    if has_errors(scan_diagnostics):
        return ParseResult(
            documents=(),
            diagnostics=(*config_diagnostics, *scan_diagnostics),
            failed=True,
        )

    index, index_diagnostics = build_document_index(config, source_files)
    pre_parse_diagnostics = (*config_diagnostics, *scan_diagnostics, *index_diagnostics)
    if index is None or has_errors(index_diagnostics):
        return ParseResult(
            documents=(),
            diagnostics=pre_parse_diagnostics,
            failed=True,
        )

    ordered_files, order_diagnostics = order_by_index(index, source_files)
    all_pre = (*pre_parse_diagnostics, *order_diagnostics)

    parse_result = parse_documents(ordered_files, fs, parser)
    return ParseResult(
        documents=parse_result.documents,
        diagnostics=(*all_pre, *parse_result.diagnostics),
        failed=has_errors(all_pre) or parse_result.failed,
    )


def _resolve_config_path(start: Path) -> Path | None:
    if start.name == CONFIG_FILENAME:
        return start if start.is_file() else None
    return find_config(start)


def _failed(diagnostic: Diagnostic) -> ParseResult:
    return ParseResult(documents=(), diagnostics=(diagnostic,), failed=True)


__all__ = ["parse_project_documents"]
