"""Application service for project Markdown parsing (FC-03 chain)."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.project_pipeline import run_project_parse_pipeline
from scribpy.model import ParseResult
from scribpy.model.protocols import FileSystem, MarkdownParser


def parse_project_documents(
    root: Path | None = None,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
) -> ParseResult:
    """Load a project, build its document index, and parse all Markdown files."""
    result = run_project_parse_pipeline(root, filesystem, parser)
    documents = () if result.value is None else result.value.documents
    return ParseResult(
        documents=documents,
        diagnostics=result.diagnostics,
        failed=result.failed,
    )


__all__ = ["parse_project_documents"]
