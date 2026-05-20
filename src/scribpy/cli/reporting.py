"""Human-readable execution reports for CLI workflows."""

from __future__ import annotations

from typing import TextIO

from scribpy.cli.report_artifacts import print_artifact_summary
from scribpy.cli.report_status import has_blocking_lint, project_preparation_ok
from scribpy.cli.report_steps import print_steps
from scribpy.model import BuildResult, LintResult, ParseResult


def print_index_report(result: LintResult, stream: TextIO) -> None:
    """Print the high-level index-check execution report.

    Args:
        result: Index-check result to summarize.
        stream: Output stream receiving the report.
    """
    print_steps(
        (
            ("Resolve project configuration", project_preparation_ok(result)),
            ("Discover Markdown sources", project_preparation_ok(result)),
            ("Build document index", not result.failed),
        ),
        stream,
    )


def print_parse_report(result: ParseResult, stream: TextIO) -> None:
    """Print the high-level parse-check execution report.

    Args:
        result: Parse result to summarize.
        stream: Output stream receiving the report.
    """
    preparation_ok = project_preparation_ok(result)
    print_steps(
        (
            ("Resolve project configuration", preparation_ok),
            ("Discover Markdown sources", preparation_ok),
            ("Build document index", preparation_ok),
            ("Parse Markdown documents", not result.failed),
        ),
        stream,
    )
    if not result.failed:
        print(f"Parsed {len(result.documents)} document(s).", file=stream)


def print_lint_report(result: LintResult, stream: TextIO) -> None:
    """Print the high-level lint execution report.

    Args:
        result: Lint result to summarize.
        stream: Output stream receiving the report.
    """
    preparation_ok = project_preparation_ok(result)
    lint_ok = preparation_ok and not result.failed
    print_steps(
        (
            ("Resolve project configuration", preparation_ok),
            ("Parse project documents", preparation_ok),
            ("Run lint rules", lint_ok),
        ),
        stream,
    )


def print_build_report(
    result: BuildResult, target: str, stream: TextIO
) -> None:
    """Print the high-level build execution report.

    Args:
        result: Build result to summarize.
        target: User-facing build target label.
        stream: Output stream receiving the report.
    """
    preparation_ok = project_preparation_ok(result)
    lint_ok = preparation_ok and not has_blocking_lint(result)
    print_steps(
        (
            ("Resolve project configuration", preparation_ok),
            ("Parse project documents", preparation_ok),
            ("Run lint rules", lint_ok),
            (f"Build {target}", result.success),
        ),
        stream,
    )
    if result.success:
        print_artifact_summary(result.artifacts, stream)


__all__ = [
    "print_build_report",
    "print_index_report",
    "print_lint_report",
    "print_parse_report",
]
