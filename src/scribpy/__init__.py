"""Scribpy public package interface."""

__version__ = "0.1.0"

from scribpy.core import (
    CollectionDiagnostic,
    CollectionDiagnosticReport,
    CollectionDiagnosticRule,
    DiagnosticSeverity,
    ExternalImageReferenceRule,
    FolderManifest,
    HeadingLevelOverflowRule,
    InternalMarkdownLinkRule,
    LocalImageMissingRule,
    MarkdownCollection,
    MarkdownDocument,
    MarkdownFile,
    MarkdownImageReference,
    RootManifest,
    SourceFirstHeadingH1Rule,
    SourceH1CountRule,
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
    "ExternalImageReferenceRule",
    "FolderManifest",
    "HeadingLevelOverflowRule",
    "InternalMarkdownLinkRule",
    "InvalidMarkdownError",
    "InvalidScribpyManifestError",
    "LocalImageMissingRule",
    "MarkdownCollection",
    "MarkdownDocument",
    "MarkdownFile",
    "MarkdownImageReference",
    "RootManifest",
    "ScribpyError",
    "ScribpyManifestWarning",
    "SourceFirstHeadingH1Rule",
    "SourceH1CountRule",
    "logging_context",
]
