"""Scribpy public package interface."""

__version__ = "0.1.0"

from scribpy.core import (
    CollectionDiagnostic,
    CollectionDiagnosticReport,
    CollectionDiagnosticRule,
    DiagnosticSeverity,
    FolderManifest,
    MarkdownCollection,
    MarkdownDocument,
    MarkdownFile,
    MarkdownImageReference,
    RootManifest,
)
from scribpy.errors import (
    InvalidMarkdownError,
    InvalidScribpyManifestError,
    ScribpyError,
    ScribpyManifestWarning,
)
from scribpy.log import logging_context

__all__ = [
    "CollectionDiagnostic",
    "CollectionDiagnosticReport",
    "CollectionDiagnosticRule",
    "DiagnosticSeverity",
    "FolderManifest",
    "InvalidMarkdownError",
    "InvalidScribpyManifestError",
    "MarkdownCollection",
    "MarkdownDocument",
    "MarkdownFile",
    "MarkdownImageReference",
    "RootManifest",
    "ScribpyError",
    "ScribpyManifestWarning",
    "logging_context",
]
