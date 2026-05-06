"""Public exports for project scanning and document index management."""

from scribpy.project.indexer import build_document_index, validate_document_index
from scribpy.project.scanner import resolve_project_root, scan_project

__all__ = [
    "build_document_index",
    "resolve_project_root",
    "scan_project",
    "validate_document_index",
]
