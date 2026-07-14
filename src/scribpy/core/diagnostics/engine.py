"""Collection diagnostic execution engine."""

from __future__ import annotations

import logging
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

_log = logging.getLogger(__name__)

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
    _log.debug("Running diagnostics on %d file(s) in '%s'", len(files), root)
    context = CollectionDiagnosticContext(root=root, files=files)
    diagnostics = tuple(
        diagnostic for rule in rules for diagnostic in rule.diagnose(context)
    )
    report = CollectionDiagnosticReport(diagnostics)
    _log.debug(
        "Diagnostics complete: %d finding(s), has_errors=%s",
        len(diagnostics),
        report.has_errors,
    )
    return report
