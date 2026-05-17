"""Human-readable execution reports for CLI workflows."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TextIO

from scribpy.model import BuildArtifact, BuildResult, LintResult, ParseResult


def print_index_report(result: LintResult, stream: TextIO) -> None:
    """Print the high-level index-check execution report.

    Args:
        result: Index-check result to summarize.
        stream: Output stream receiving the report.
    """
    _print_steps(
        (
            ("Resolve project configuration", _project_preparation_ok(result)),
            ("Discover Markdown sources", _project_preparation_ok(result)),
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
    preparation_ok = _project_preparation_ok(result)
    _print_steps(
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
    preparation_ok = _project_preparation_ok(result)
    lint_ok = preparation_ok and not result.failed
    _print_steps(
        (
            ("Resolve project configuration", preparation_ok),
            ("Parse project documents", preparation_ok),
            ("Run lint rules", lint_ok),
        ),
        stream,
    )


def print_build_report(result: BuildResult, target: str, stream: TextIO) -> None:
    """Print the high-level build execution report.

    Args:
        result: Build result to summarize.
        target: User-facing build target label.
        stream: Output stream receiving the report.
    """
    preparation_ok = _project_preparation_ok(result)
    lint_ok = preparation_ok and not _has_blocking_lint(result)
    _print_steps(
        (
            ("Resolve project configuration", preparation_ok),
            ("Parse project documents", preparation_ok),
            ("Run lint rules", lint_ok),
            (f"Build {target}", result.success),
        ),
        stream,
    )
    if result.success:
        _print_artifact_summary(result.artifacts, stream)


def _print_steps(steps: Sequence[tuple[str, bool]], stream: TextIO) -> None:
    for label, succeeded in steps:
        mark = "✔" if succeeded else "✘"
        status = "done" if succeeded else "failed"
        print(f"{mark} {label} — {status}", file=stream)


def _print_artifact_summary(
    artifacts: Sequence[BuildArtifact],
    stream: TextIO,
) -> None:
    if not artifacts:
        return
    primary = _primary_artifact(artifacts)
    print("", file=stream)
    print(f"Primary artifact: {primary.path}", file=stream)
    if len(artifacts) > 1:
        print(f"Additional artifacts: {len(artifacts) - 1}", file=stream)


def _primary_artifact(artifacts: Sequence[BuildArtifact]) -> BuildArtifact:
    preferred_types = ("document", "site", "page")
    for artifact_type in preferred_types:
        for artifact in artifacts:
            if artifact.artifact_type == artifact_type:
                return artifact
    return artifacts[0]


def _project_preparation_ok(result: BuildResult | LintResult | ParseResult) -> bool:
    return not any(
        diagnostic.severity == "error"
        and diagnostic.code.startswith(("CFG", "PRJ", "IDX", "PRS"))
        for diagnostic in result.diagnostics
    )


def _has_blocking_lint(result: BuildResult) -> bool:
    return any(
        diagnostic.severity == "error" and diagnostic.code.startswith("LINT")
        for diagnostic in result.diagnostics
    )


__all__ = [
    "print_build_report",
    "print_index_report",
    "print_lint_report",
    "print_parse_report",
]
