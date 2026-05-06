"""Diagnostic data carried by validation, lint, and build workflows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DiagnosticSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class Diagnostic:
    """A user-facing error, warning, or informational message.

    Diagnostics represent expected problems found while processing user input,
    such as invalid configuration, broken links, or lint rule violations. They
    are immutable so they can be safely passed across the processing pipeline.

    Attributes:
        severity: Importance level of the diagnostic. ``"error"`` indicates a
            blocking issue, ``"warning"`` indicates a non-blocking problem, and
            ``"info"`` provides contextual feedback.
        code: Stable machine-readable identifier for the diagnostic, such as
            ``"LINT001"``. Codes are intended for filtering, documentation, and
            tests.
        message: Human-readable explanation of the problem.
        path: Optional path to the file related to the diagnostic.
        line: Optional one-based line number in ``path`` where the issue was
            detected.
        hint: Optional remediation guidance that can be shown to the user.
    """

    severity: DiagnosticSeverity
    code: str
    message: str
    path: Path | None = None
    line: int | None = None
    hint: str | None = None


__all__ = ["Diagnostic", "DiagnosticSeverity"]
