"""Readable console rendering for public Scribpy result objects."""

from __future__ import annotations

from typing import TextIO

from rich.console import Console
from rich.text import Text

from scribpy.model import BuildResult, LintResult, ParseResult
from scribpy.utils import sort_diagnostics

type PublicResult = BuildResult | LintResult | ParseResult


def print_result(result: PublicResult, *, file: TextIO | None = None) -> None:
    """Print a compact human-readable result summary.

    Successful results stay short. When diagnostics are present, each issue is
    expanded with its code, location, and remediation hint so interactive API
    use remains readable without hiding troubleshooting details.

    Args:
        result: Result returned by a public Scribpy workflow.
        file: Optional text stream. Defaults to standard output.

    Examples:
        >>> import scribpy
        >>> result = scribpy.build_html(".", mode="site")
        >>> scribpy.print_result(result)
    """
    console = Console(file=file, soft_wrap=True, highlight=False)
    console.print(_summary(result))
    for diagnostic in sort_diagnostics(result.diagnostics):
        location = ""
        if diagnostic.path is not None:
            location = diagnostic.path.as_posix()
            if diagnostic.line is not None:
                location += f":{diagnostic.line}"
            location += " — "
        console.print(
            Text.assemble(
                (
                    diagnostic.severity.upper(),
                    _severity_style(diagnostic.severity),
                ),
                f" {diagnostic.code} — {location}{diagnostic.message}",
            )
        )
        if diagnostic.hint:
            console.print(f"  hint: {diagnostic.hint}")


def _summary(result: PublicResult) -> Text:
    """Build the top-level result summary."""
    if isinstance(result, BuildResult):
        status = "success" if result.success else "failed"
        return Text(
            f"Build {status}: {len(result.artifacts)} artifact(s), "
            f"{len(result.diagnostics)} diagnostic(s)",
            style="green" if result.success else "red",
        )
    if isinstance(result, ParseResult):
        status = "failed" if result.failed else "success"
        return Text(
            f"Parse {status}: {len(result.documents)} document(s), "
            f"{len(result.diagnostics)} diagnostic(s)",
            style="red" if result.failed else "green",
        )
    status = "failed" if result.failed else "success"
    return Text(
        f"Check {status}: {len(result.diagnostics)} diagnostic(s)",
        style="red" if result.failed else "green",
    )


def _severity_style(severity: str) -> str:
    """Return the Rich style for one diagnostic severity."""
    return {"error": "bold red", "warning": "yellow", "info": "cyan"}[severity]


__all__ = ["PublicResult", "print_result"]
