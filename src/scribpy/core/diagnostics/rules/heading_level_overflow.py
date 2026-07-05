"""Diagnostic rule for assembled heading level overflow."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.heading_normalizer import iter_markdown_headings
from scribpy.core.markdown_file import MarkdownFile

MAX_MARKDOWN_HEADING_LEVEL = 6
ROOT_FILE_HEADING_LEVEL = 2
HEADING_LEVEL_OVERFLOW = "HEADING_LEVEL_OVERFLOW"


class HeadingLevelOverflowRule:
    """Detect headings that would exceed Markdown level 6 after assembly.

    Examples:
        Valid Markdown at root level because H5 becomes H6 after assembly::

            # Title

            ##### Deep section

        Invalid Markdown at root level because H6 would become H7::

            # Title

            ###### Too deep
    """

    code = HEADING_LEVEL_OVERFLOW

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return heading overflow diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics for headings that cannot be represented after
            collection assembly.
        """
        diagnostics: list[CollectionDiagnostic] = []
        for markdown_file in context.files:
            diagnostics.extend(
                _file_heading_overflow_diagnostics(context.root, markdown_file)
            )
        return tuple(diagnostics)


def _file_heading_overflow_diagnostics(
    root: Path,
    markdown_file: MarkdownFile,
) -> tuple[CollectionDiagnostic, ...]:
    """Return heading overflow diagnostics for one Markdown file.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file to inspect.

    Returns:
        Heading overflow diagnostics for the file.
    """
    base_level = ROOT_FILE_HEADING_LEVEL + len(
        _relative_folder_parts(root, markdown_file.path)
    )
    return tuple(
        _heading_overflow_diagnostic(
            markdown_file, heading.title, heading.line
        )
        for heading in iter_markdown_headings(markdown_file.content)
        if base_level + heading.level - 1 > MAX_MARKDOWN_HEADING_LEVEL
    )


def _heading_overflow_diagnostic(
    markdown_file: MarkdownFile,
    title: str,
    line: int,
) -> CollectionDiagnostic:
    """Return one heading overflow diagnostic.

    Args:
        markdown_file: Markdown file containing the heading.
        title: Heading title text.
        line: One-based source line number.

    Returns:
        Heading overflow diagnostic.
    """
    return CollectionDiagnostic(
        code=HEADING_LEVEL_OVERFLOW,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Heading would exceed Markdown level 6 after collection assembly: "
            f"{title!r}."
        ),
        path=markdown_file.path,
        line=line,
    )


def _relative_folder_parts(root: Path, path: Path) -> tuple[str, ...]:
    """Return relative parent folder names for one Markdown file.

    Args:
        root: Collection root directory.
        path: Markdown file path.

    Returns:
        Relative parent folder names, or an empty tuple for external files.
    """
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        return ()
    return relative_path.parent.parts
