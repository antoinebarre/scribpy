"""Core domain objects for Scribpy."""

from scribpy.core.diagnostics import (
    CollectionDiagnostic,
    CollectionDiagnosticReport,
    CollectionDiagnosticRule,
    DiagnosticSeverity,
    ExternalImageReferenceRule,
    HeadingLevelOverflowRule,
    InternalMarkdownLinkRule,
    LocalImageMissingRule,
    SourceFirstHeadingH1Rule,
    SourceH1CountRule,
)
from scribpy.core.manifest import FolderManifest, RootManifest
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.markdown_document import MarkdownDocument
from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_image import MarkdownImageReference

__all__ = [
    "CollectionDiagnostic",
    "CollectionDiagnosticReport",
    "CollectionDiagnosticRule",
    "DiagnosticSeverity",
    "ExternalImageReferenceRule",
    "FolderManifest",
    "HeadingLevelOverflowRule",
    "InternalMarkdownLinkRule",
    "LocalImageMissingRule",
    "MarkdownCollection",
    "MarkdownDocument",
    "MarkdownFile",
    "MarkdownImageReference",
    "RootManifest",
    "SourceFirstHeadingH1Rule",
    "SourceH1CountRule",
]
