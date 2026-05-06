"""Internal data model for scribpy documentation objects.

Defines the core frozen dataclasses that flow through the pipeline:
    Project       — top-level documentation project state
    SourceFile    — a file discovered in the project
    Document      — a parsed Markdown document
    MarkdownAst   — parser output (tokens + backend tag)
    Heading       — a Markdown heading node
    Reference     — a Markdown link or cross-reference
    AssetRef      — an image, diagram, or static asset reference
    DocumentIndex — ordered index of files for assembly
    Diagnostic    — an error, warning, or info message
"""

from scribpy.model.diagnostic import Diagnostic, DiagnosticSeverity
from scribpy.model.document import Document
from scribpy.model.index import DocumentIndex, IndexMode
from scribpy.model.markdown import (
    AssetKind,
    AssetRef,
    Heading,
    MarkdownAst,
    Reference,
    ReferenceKind,
)
from scribpy.model.project import Project
from scribpy.model.protocols import (
    DiagramRenderer,
    FileSystem,
    HtmlRenderer,
    MarkdownParser,
    PdfRenderer,
)
from scribpy.model.results import BuildArtifact, BuildResult, LintResult, ParseResult
from scribpy.model.source import SourceFile

__all__ = [
    "AssetKind",
    "AssetRef",
    "BuildArtifact",
    "BuildResult",
    "DiagramRenderer",
    "Diagnostic",
    "DiagnosticSeverity",
    "Document",
    "DocumentIndex",
    "FileSystem",
    "Heading",
    "HtmlRenderer",
    "IndexMode",
    "LintResult",
    "MarkdownAst",
    "MarkdownParser",
    "PdfRenderer",
    "ParseResult",
    "Project",
    "Reference",
    "ReferenceKind",
    "SourceFile",
]
