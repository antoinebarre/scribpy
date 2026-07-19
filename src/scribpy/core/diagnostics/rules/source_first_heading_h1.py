"""Diagnostic rule for source first heading level."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.heading_normalizer import (
    MarkdownHeading,
    iter_markdown_headings,
)
from scribpy.core.markdown_file import MarkdownFile

SOURCE_FIRST_HEADING_NOT_H1 = "SOURCE_FIRST_HEADING_NOT_H1"


class SourceFirstHeadingH1Rule:
    """Detect Markdown source files whose first heading is not H1.

    Examples:
        Valid Markdown because the first heading is H1::

            # Title

            ## Section

        Invalid Markdown because the first heading is H2::

            ## Section

            # Title
    """

    code = SOURCE_FIRST_HEADING_NOT_H1

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return first-heading diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics for files whose first heading is not H1.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            if (diagnostic := _source_first_heading_diagnostic(markdown_file))
            is not None
        )


def _source_first_heading_diagnostic(
    markdown_file: MarkdownFile,
) -> CollectionDiagnostic | None:
    """Return a first-heading diagnostic when the file is invalid.

    Args:
        markdown_file: Markdown file to inspect.

    Returns:
        Diagnostic when the first heading exists and is not H1, or None.
    """
    headings = iter_markdown_headings(markdown_file.content)
    if not headings or headings[0].level == 1:
        return None
    return _first_heading_not_h1_diagnostic(markdown_file, headings[0])


def _first_heading_not_h1_diagnostic(
    markdown_file: MarkdownFile,
    heading: MarkdownHeading,
) -> CollectionDiagnostic:
    """Return one first-heading diagnostic.

    Args:
        markdown_file: Markdown file containing the heading.
        heading: First source heading.

    Returns:
        First-heading diagnostic.
    """
    return CollectionDiagnostic(
        code=SOURCE_FIRST_HEADING_NOT_H1,
        severity=DiagnosticSeverity.ERROR,
        message=f"First Markdown heading must be H1; found H{heading.level}.",
        path=markdown_file.path,
        line=heading.line,
    )
