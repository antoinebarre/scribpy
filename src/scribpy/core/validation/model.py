"""Project validation data model."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.core.diagnostics import DiagnosticSeverity


@dataclass(frozen=True, slots=True)
class ProjectDiagnostic:
    """Represent one project validation finding.

    Attributes:
        code: Stable machine-readable diagnostic code.
        severity: Impact of the finding on project validity.
        message: Human-readable explanation.
        path: Optional source path related to the finding.
        line: Optional one-based source line.
        column: Optional one-based source column.
        category: Diagnostic category supplied by its producer.
        target: Optional structured resource or contract target.
    """

    code: str
    severity: DiagnosticSeverity
    message: str
    path: Path | None = None
    line: int | None = None
    column: int | None = None
    category: str = "project-validation"
    target: str | None = None


@dataclass(frozen=True, slots=True)
class ProjectValidationReport:
    """Represent the complete validation result for one project.

    Attributes:
        root: Validated project root.
        diagnostics: Ordered findings emitted by all validation stages.
        markdown_count: Number of Markdown files verified by Mkforge.
        manifest_count: Number of manifests inspected by Scribpy.
    """

    root: Path
    diagnostics: tuple[ProjectDiagnostic, ...] = ()
    markdown_count: int = 0
    manifest_count: int = 0

    @property
    def is_valid(self) -> bool:
        """Return whether the project contains no blocking finding.

        Returns:
            True when no diagnostic has error severity.
        """
        return not self.has_errors

    @property
    def has_errors(self) -> bool:
        """Return whether the project contains a blocking finding.

        Returns:
            True when at least one diagnostic has error severity.
        """
        return any(
            item.severity == DiagnosticSeverity.ERROR
            for item in self.diagnostics
        )

    def by_severity(
        self,
        severity: DiagnosticSeverity,
    ) -> tuple[ProjectDiagnostic, ...]:
        """Return findings matching one severity.

        Args:
            severity: Severity selected by the caller.

        Returns:
            Diagnostics with the requested severity.
        """
        return tuple(
            item for item in self.diagnostics if item.severity == severity
        )
