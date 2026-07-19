"""Diagnostic rule for internal Markdown file links."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.diagnostics.rules.markdown_link_targets import (
    MarkdownLinkReference,
    classify_markdown_link_target,
    extract_markdown_links,
)
from scribpy.core.diagnostics.rules.path_utils import _is_inside_root
from scribpy.core.markdown_file import MarkdownFile

INTERNAL_MARKDOWN_LINK_MISSING = "INTERNAL_MARKDOWN_LINK_MISSING"
INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT = "INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT"
INTERNAL_MARKDOWN_LINK_RULE = "INTERNAL_MARKDOWN_LINK_RULE"


class InternalMarkdownLinkRule:
    """Detect invalid links to internal Markdown files.

    Examples:
        Valid Markdown when the target exists under the collection root::

            # Title

            [Guide](guide/page.md)

        Valid Markdown when an anchor-only link stays in the current page::

            # Title

            [Section](#section)

        Invalid Markdown when the target Markdown file does not exist::

            # Title

            [Missing](guide/missing.md)

        Invalid Markdown when the target escapes the collection root::

            # Title

            [Outside](../../outside.md)
    """

    code = INTERNAL_MARKDOWN_LINK_RULE

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return internal Markdown link diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics for missing Markdown files and links outside root.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            for link in extract_markdown_links(markdown_file.content)
            if (
                diagnostic := _internal_markdown_link_diagnostic(
                    context.root,
                    markdown_file,
                    link,
                )
            )
            is not None
        )


def _internal_markdown_link_diagnostic(
    root: Path,
    markdown_file: MarkdownFile,
    reference: MarkdownLinkReference,
) -> CollectionDiagnostic | None:
    """Return an internal Markdown link diagnostic when needed.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the link reference.
        reference: Markdown link reference to inspect.

    Returns:
        Diagnostic when the link is invalid, or None.
    """
    target = classify_markdown_link_target(root, markdown_file, reference)
    if not target.is_markdown or target.resolved_path is None:
        return None
    if not _is_inside_root(root, target.resolved_path):
        return _outside_root_diagnostic(markdown_file, reference)
    if not target.resolved_path.is_file():
        return _missing_markdown_diagnostic(markdown_file, reference)
    return None


def _missing_markdown_diagnostic(
    markdown_file: MarkdownFile,
    reference: MarkdownLinkReference,
) -> CollectionDiagnostic:
    """Return one missing Markdown file diagnostic.

    Args:
        markdown_file: Markdown file containing the link reference.
        reference: Markdown link reference to report.

    Returns:
        Missing Markdown file diagnostic.
    """
    return CollectionDiagnostic(
        code=INTERNAL_MARKDOWN_LINK_MISSING,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Internal Markdown link target does not exist: "
            f"{reference.target!r}."
        ),
        path=markdown_file.path,
        line=reference.line,
    )


def _outside_root_diagnostic(
    markdown_file: MarkdownFile,
    reference: MarkdownLinkReference,
) -> CollectionDiagnostic:
    """Return one outside-root Markdown link diagnostic.

    Args:
        markdown_file: Markdown file containing the link reference.
        reference: Markdown link reference to report.

    Returns:
        Outside-root Markdown link diagnostic.
    """
    return CollectionDiagnostic(
        code=INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Internal Markdown link target must stay inside collection root: "
            f"{reference.target!r}."
        ),
        path=markdown_file.path,
        line=reference.line,
    )
