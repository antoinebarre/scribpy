"""Collection diagnostic execution engine."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.core.diagnostics.model import (
    CollectionDiagnosticContext,
    CollectionDiagnosticReport,
    CollectionDiagnosticRule,
)
from scribpy.core.diagnostics.rules import (
    ExternalImageReferenceRule,
    HeadingLevelOverflowRule,
    ImageOutsideRootRule,
    InternalMarkdownLinkRule,
    LocalAnchorLinkRule,
    LocalImageMissingRule,
    SourceFirstHeadingH1Rule,
    SourceH1CountRule,
)
from scribpy.core.markdown_file import MarkdownFile

DEFAULT_COLLECTION_DIAGNOSTIC_RULES: tuple[CollectionDiagnosticRule, ...] = (
    SourceFirstHeadingH1Rule(),
    SourceH1CountRule(),
    HeadingLevelOverflowRule(),
    LocalImageMissingRule(),
    ImageOutsideRootRule(),
    ExternalImageReferenceRule(),
    InternalMarkdownLinkRule(),
    LocalAnchorLinkRule(),
)


def diagnose_collection(
    root: Path,
    files: tuple[MarkdownFile, ...],
    rules: Iterable[CollectionDiagnosticRule] = (
        DEFAULT_COLLECTION_DIAGNOSTIC_RULES
    ),
) -> CollectionDiagnosticReport:
    """Run collection diagnostic rules.

    Args:
        root: Collection root directory.
        files: Ordered Markdown files in the collection.
        rules: Diagnostic rules to execute.

    Returns:
        Diagnostic report emitted by all rules.
    """
    context = CollectionDiagnosticContext(root=root, files=files)
    diagnostics = tuple(
        diagnostic for rule in rules for diagnostic in rule.diagnose(context)
    )
    return CollectionDiagnosticReport(diagnostics)
