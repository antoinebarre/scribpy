"""Convenience API for validating and reporting Scribpy projects."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from scribpy.core.validation import validate_project
from scribpy.presentation import render_validation_report


def valid_report(
    root: str | Path,
    *,
    console: Console | None = None,
) -> bool:
    """Validate a project, display its report, and return its validity.

    Args:
        root: Project directory containing Markdown and manifests.
        console: Optional Rich console receiving the report.

    Returns:
        True when the project contains no blocking validation finding.
    """
    report = validate_project(root)
    render_validation_report(report, console=console)
    return report.is_valid
