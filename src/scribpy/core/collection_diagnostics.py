"""Diagnostics for Markdown collections."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from scribpy.core.heading_normalizer import iter_markdown_headings
from scribpy.core.markdown_file import MarkdownFile

MAX_MARKDOWN_HEADING_LEVEL = 6
ROOT_FILE_HEADING_LEVEL = 2
HEADING_LEVEL_OVERFLOW = "HEADING_LEVEL_OVERFLOW"


class DiagnosticSeverity(StrEnum):
    """Classify diagnostic impact on publication workflows."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class CollectionDiagnostic:
    """Represent one collection quality finding.

    Attributes:
        code: Stable machine-readable diagnostic code.
        severity: Diagnostic severity.
        message: Human-readable explanation.
        path: Optional path related to the finding.
        line: Optional one-based source line related to the finding.
    """

    code: str
    severity: DiagnosticSeverity
    message: str
    path: Path | None = None
    line: int | None = None


@dataclass(frozen=True, slots=True)
class CollectionDiagnosticReport:
    """Represent diagnostics emitted for a Markdown collection.

    Attributes:
        diagnostics: Ordered diagnostics emitted by collection rules.
    """

    diagnostics: tuple[CollectionDiagnostic, ...] = ()

    @property
    def has_errors(self) -> bool:
        """Return whether the report contains blocking diagnostics.

        Returns:
            True when at least one diagnostic has error severity.
        """
        return any(
            diagnostic.severity == DiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )

    def by_severity(
        self,
        severity: DiagnosticSeverity,
    ) -> tuple[CollectionDiagnostic, ...]:
        """Return diagnostics matching a severity.

        Args:
            severity: Severity to filter by.

        Returns:
            Diagnostics with the requested severity.
        """
        return tuple(
            diagnostic
            for diagnostic in self.diagnostics
            if diagnostic.severity == severity
        )

    def summary(self) -> str:
        """Return a concise report summary.

        Returns:
            Human-readable report summary.
        """
        if not self.diagnostics:
            return "No collection diagnostics."
        return "\n".join(
            _diagnostic_summary(diagnostic) for diagnostic in self.diagnostics
        )


@dataclass(frozen=True, slots=True)
class CollectionDiagnosticContext:
    """Represent inputs shared by collection diagnostic rules.

    Attributes:
        root: Root directory used to discover Markdown files.
        files: Ordered Markdown files in the collection.
    """

    root: Path
    files: tuple[MarkdownFile, ...]


class CollectionDiagnosticRule(Protocol):
    """Protocol implemented by collection diagnostic strategies."""

    code: str

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return diagnostics emitted by this rule.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics emitted by this rule.
        """
        ...


class HeadingLevelOverflowRule:
    """Detect headings that would exceed Markdown level 6 after assembly."""

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


DEFAULT_COLLECTION_DIAGNOSTIC_RULES: tuple[CollectionDiagnosticRule, ...] = (
    HeadingLevelOverflowRule(),
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


def _diagnostic_summary(diagnostic: CollectionDiagnostic) -> str:
    """Return a concise text line for one diagnostic.

    Args:
        diagnostic: Diagnostic to summarize.

    Returns:
        Human-readable diagnostic summary line.
    """
    location = _diagnostic_location(diagnostic)
    return (
        f"{diagnostic.severity.value.upper()} {diagnostic.code}"
        f"{location}: {diagnostic.message}"
    )


def _diagnostic_location(diagnostic: CollectionDiagnostic) -> str:
    """Return a formatted diagnostic location.

    Args:
        diagnostic: Diagnostic containing optional path and line.

    Returns:
        Empty string or formatted path and line location.
    """
    if diagnostic.path is None:
        return ""
    if diagnostic.line is None:
        return f" {diagnostic.path}"
    return f" {diagnostic.path}:{diagnostic.line}"
