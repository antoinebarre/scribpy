"""Status predicates shared by CLI reports."""

from __future__ import annotations

from scribpy.model import BuildResult, LintResult, ParseResult


def project_preparation_ok(
    result: BuildResult | LintResult | ParseResult,
) -> bool:
    """Return whether project preparation completed without blocking errors.

    Args:
        result: Workflow result carrying diagnostics.

    Returns:
        True when configuration, project indexing, and parsing diagnostics do
        not contain blocking errors.
    """
    return not any(
        diagnostic.severity == "error"
        and diagnostic.code.startswith(("CFG", "PRJ", "IDX", "PRS"))
        for diagnostic in result.diagnostics
    )


def has_blocking_lint(result: BuildResult) -> bool:
    """Return whether build diagnostics include blocking lint errors.

    Args:
        result: Build result carrying diagnostics.

    Returns:
        True when at least one error diagnostic belongs to linting.
    """
    return any(
        diagnostic.severity == "error" and diagnostic.code.startswith("LINT")
        for diagnostic in result.diagnostics
    )


__all__ = ["has_blocking_lint", "project_preparation_ok"]
