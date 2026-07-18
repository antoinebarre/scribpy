"""Core domain objects for Scribpy."""

from scribpy.core.assembly import (
    AssembledDocument,
    TransformFn,
    apply_transforms,
    build_file_slug_map,
    collect_images,
    concatenate,
    rewrite_internal_links,
    slugify_heading,
)
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
from scribpy.core.html import html_export
from scribpy.core.init import (
    OutlineNode,
    init_from_outline,
    init_skeleton,
    parse_outline,
)
from scribpy.core.manifest import FolderManifest, RootManifest
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.markdown_document import MarkdownDocument
from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_image import MarkdownImageReference
from scribpy.core.validation import (
    ProjectDiagnostic,
    ProjectValidationReport,
    validate_project,
)

__all__ = [
    "AssembledDocument",
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
    "OutlineNode",
    "ProjectDiagnostic",
    "ProjectValidationReport",
    "RootManifest",
    "SourceFirstHeadingH1Rule",
    "SourceH1CountRule",
    "TransformFn",
    "apply_transforms",
    "build_file_slug_map",
    "collect_images",
    "concatenate",
    "html_export",
    "init_from_outline",
    "init_skeleton",
    "parse_outline",
    "rewrite_internal_links",
    "slugify_heading",
    "validate_project",
]
