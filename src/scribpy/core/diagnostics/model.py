"""Collection diagnostic data model."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from scribpy.core.markdown_file import MarkdownFile


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
