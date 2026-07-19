"""Diagnostic rule for source H1 heading count."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.heading_normalizer import iter_markdown_headings
from scribpy.core.markdown_file import MarkdownFile

SOURCE_H1_COUNT_INVALID = "SOURCE_H1_COUNT_INVALID"


class SourceH1CountRule:
    """Detect Markdown source files without exactly one H1 heading.

    Examples:
        Valid Markdown because it has exactly one H1::

            # Title

            ## Section

        Invalid Markdown because it has no H1::

            ## Section

        Invalid Markdown because it has two H1 headings::

            # First title

            # Second title
    """

    code = SOURCE_H1_COUNT_INVALID

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return source H1 count diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics for files that do not contain exactly one H1 heading.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            if (diagnostic := _source_h1_count_diagnostic(markdown_file))
            is not None
        )


def _source_h1_count_diagnostic(
    markdown_file: MarkdownFile,
) -> CollectionDiagnostic | None:
    """Return a source H1 count diagnostic when the file is invalid.

    Args:
        markdown_file: Markdown file to inspect.

    Returns:
        Diagnostic when the file does not contain exactly one H1 heading, or
        None when the file is valid.
    """
    h1_headings = tuple(
        heading
        for heading in iter_markdown_headings(markdown_file.content)
        if heading.level == 1
    )
    if len(h1_headings) == 1:
        return None
    line = h1_headings[1].line if len(h1_headings) > 1 else None
    return CollectionDiagnostic(
        code=SOURCE_H1_COUNT_INVALID,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Markdown file must contain exactly one H1 heading; "
            f"found {len(h1_headings)}."
        ),
        path=markdown_file.path,
        line=line,
    )
