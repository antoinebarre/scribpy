"""Tests for scribpy.utils.diagnostics."""

from pathlib import Path

from scribpy.model import Diagnostic
from scribpy.utils import (
    format_diagnostic,
    format_diagnostics,
    group_diagnostics_by_path,
    has_errors,
    severity_rank,
    sort_diagnostics,
)


def test_severity_rank_orders_errors_before_warnings_before_info() -> None:
    assert severity_rank("error") < severity_rank("warning")
    assert severity_rank("warning") < severity_rank("info")


def test_has_errors_returns_true_when_any_diagnostic_is_error() -> None:
    diagnostics = (
        Diagnostic(severity="info", code="INFO001", message="Checked"),
        Diagnostic(severity="error", code="LINT001", message="Missing H1"),
    )

    assert has_errors(diagnostics) is True


def test_has_errors_returns_false_without_errors() -> None:
    diagnostics = (
        Diagnostic(severity="info", code="INFO001", message="Checked"),
        Diagnostic(severity="warning", code="LINT007", message="Trailing space"),
    )

    assert has_errors(diagnostics) is False


def test_format_diagnostic_handles_path_line_and_hint() -> None:
    diagnostic = Diagnostic(
        severity="warning",
        code="LINT007",
        message="Trailing whitespace",
        path=Path("docs/index.md"),
        line=12,
        hint="Remove the trailing spaces.",
    )

    assert (
        format_diagnostic(diagnostic)
        == "docs/index.md:12: warning LINT007: Trailing whitespace\n"
        "  hint: Remove the trailing spaces."
    )


def test_format_diagnostic_handles_path_without_line() -> None:
    diagnostic = Diagnostic(
        severity="error",
        code="CFG001",
        message="Missing config section",
        path=Path("scribpy.toml"),
    )

    assert format_diagnostic(diagnostic) == (
        "scribpy.toml: error CFG001: Missing config section"
    )


def test_format_diagnostic_handles_global_diagnostic() -> None:
    diagnostic = Diagnostic(
        severity="info",
        code="RUN001",
        message="No Markdown files found",
    )

    assert format_diagnostic(diagnostic) == "info RUN001: No Markdown files found"


def test_sort_diagnostics_is_deterministic_by_path_line_severity_code_message() -> None:
    global_error = Diagnostic(
        severity="error",
        code="CFG001",
        message="Invalid configuration",
    )
    later_error = Diagnostic(
        severity="error",
        code="LINT003",
        message="Broken link",
        path=Path("docs/index.md"),
        line=8,
    )
    earlier_warning = Diagnostic(
        severity="warning",
        code="LINT007",
        message="Trailing whitespace",
        path=Path("docs/index.md"),
        line=2,
    )
    same_line_error = Diagnostic(
        severity="error",
        code="LINT001",
        message="Missing H1",
        path=Path("docs/index.md"),
        line=2,
    )

    assert sort_diagnostics(
        (later_error, earlier_warning, global_error, same_line_error)
    ) == (global_error, same_line_error, earlier_warning, later_error)


def test_format_diagnostics_sorts_by_default() -> None:
    diagnostics = (
        Diagnostic(
            severity="warning",
            code="LINT007",
            message="Trailing whitespace",
            path=Path("docs/b.md"),
        ),
        Diagnostic(
            severity="error",
            code="LINT001",
            message="Missing H1",
            path=Path("docs/a.md"),
        ),
    )

    assert format_diagnostics(diagnostics) == (
        "docs/a.md: error LINT001: Missing H1\n"
        "docs/b.md: warning LINT007: Trailing whitespace"
    )


def test_format_diagnostics_can_preserve_input_order() -> None:
    diagnostics = (
        Diagnostic(severity="warning", code="W001", message="Second"),
        Diagnostic(severity="error", code="E001", message="First"),
    )

    assert format_diagnostics(diagnostics, sort=False) == (
        "warning W001: Second\nerror E001: First"
    )


def test_group_diagnostics_by_path_returns_sorted_groups() -> None:
    global_diagnostic = Diagnostic(
        severity="info",
        code="RUN001",
        message="Started",
    )
    first_path_diagnostic = Diagnostic(
        severity="error",
        code="LINT001",
        message="Missing H1",
        path=Path("docs/a.md"),
    )
    second_path_diagnostic = Diagnostic(
        severity="warning",
        code="LINT007",
        message="Trailing whitespace",
        path=Path("docs/b.md"),
    )

    grouped = group_diagnostics_by_path(
        (second_path_diagnostic, global_diagnostic, first_path_diagnostic)
    )

    assert tuple(grouped) == (None, Path("docs/a.md"), Path("docs/b.md"))
    assert grouped[None] == (global_diagnostic,)
    assert grouped[Path("docs/a.md")] == (first_path_diagnostic,)
    assert grouped[Path("docs/b.md")] == (second_path_diagnostic,)
