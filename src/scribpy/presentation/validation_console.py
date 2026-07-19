"""Rich console presentation for project validation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.table import Table

from scribpy.core.diagnostics import DiagnosticSeverity
from scribpy.core.validation import ProjectDiagnostic, ProjectValidationReport

_SEVERITY_STYLE = {
    DiagnosticSeverity.ERROR: "bold red",
    DiagnosticSeverity.WARNING: "yellow",
    DiagnosticSeverity.INFO: "cyan",
}


def render_validation_report(
    report: ProjectValidationReport,
    *,
    console: Console | None = None,
) -> None:
    """Render a project validation report in a Rich console.

    Args:
        report: Structured project validation result.
        console: Optional destination console; the standard console is used
            when omitted.
    """
    destination = console or Console()
    destination.print(_summary(report))
    if report.diagnostics:
        destination.print(_diagnostic_table(report))
    status = "True" if report.is_valid else "False"
    style = "bold green" if report.is_valid else "bold red"
    destination.print(f"Project valid: [{style}]{status}[/{style}]")


def _summary(report: ProjectValidationReport) -> str:
    """Return the Rich-formatted validation summary.

    Args:
        report: Project validation result to summarize.

    Returns:
        Rich markup summary.
    """
    marker = (
        "[bold green]✓[/bold green]"
        if report.is_valid
        else "[bold red]✗[/bold red]"
    )
    return (
        f"{marker} [bold]Project validation[/bold] — "
        f"{report.manifest_count} manifest(s), "
        f"{report.markdown_count} Markdown file(s)"
    )


def _diagnostic_table(report: ProjectValidationReport) -> Table:
    """Build the diagnostic detail table.

    Args:
        report: Project validation result containing findings.

    Returns:
        Rich table containing one row per finding.
    """
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("Level", no_wrap=True)
    table.add_column("Code", no_wrap=True)
    table.add_column("Location")
    table.add_column("Message")
    for diagnostic in report.diagnostics:
        table.add_row(
            diagnostic.severity.value.upper(),
            diagnostic.code,
            _location(diagnostic, report.root),
            diagnostic.message,
            style=_SEVERITY_STYLE[diagnostic.severity],
        )
    return table


def _location(diagnostic: ProjectDiagnostic, root: Path) -> str:
    """Return a compact location for one diagnostic.

    Args:
        diagnostic: Finding whose source location is rendered.
        root: Project root used to shorten internal paths.

    Returns:
        Path with optional line and column.
    """
    if diagnostic.path is None:
        return "—"
    location = str(_display_path(diagnostic.path, root))
    if diagnostic.line is not None:
        location += f":{diagnostic.line}"
    if diagnostic.column is not None:
        location += f":{diagnostic.column}"
    return location


def _display_path(path: Path, root: Path) -> Path:
    """Return a project-relative path when possible.

    Args:
        path: Diagnostic source path.
        root: Project root used as the relative base.

    Returns:
        Relative internal path or the unchanged external path.
    """
    try:
        return path.relative_to(root)
    except ValueError:
        return path
