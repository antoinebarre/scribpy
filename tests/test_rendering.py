"""Tests for readable public result rendering."""

from io import StringIO
from pathlib import Path

import scribpy
from scribpy.model import BuildResult, Diagnostic, LintResult, ParseResult


def test_print_result_keeps_successful_build_compact() -> None:
    stream = StringIO()

    scribpy.print_result(
        BuildResult(success=True, artifacts=(), diagnostics=()), file=stream
    )

    assert (
        stream.getvalue().strip()
        == "Build success: 0 artifact(s), 0 diagnostic(s)"
    )


def test_print_result_expands_diagnostics_with_location_and_hint() -> None:
    stream = StringIO()

    scribpy.print_result(
        BuildResult(
            success=False,
            artifacts=(),
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="LINT001",
                    message="Missing H1.",
                    path=Path("doc/index.md"),
                    line=1,
                    hint="Add one top-level heading.",
                ),
            ),
        ),
        file=stream,
    )

    rendered = stream.getvalue()
    assert "Build failed: 0 artifact(s), 1 diagnostic(s)" in rendered
    assert "ERROR LINT001 — doc/index.md:1 — Missing H1." in rendered
    assert "hint: Add one top-level heading." in rendered


def test_print_result_summarizes_parse_results() -> None:
    stream = StringIO()

    scribpy.print_result(
        ParseResult(documents=(), diagnostics=(), failed=False),
        file=stream,
    )

    assert (
        stream.getvalue().strip()
        == "Parse success: 0 document(s), 0 diagnostic(s)"
    )


def test_print_result_summarizes_lint_results() -> None:
    stream = StringIO()

    scribpy.print_result(
        LintResult(diagnostics=(), failed=False),
        file=stream,
    )

    assert stream.getvalue().strip() == "Check success: 0 diagnostic(s)"
