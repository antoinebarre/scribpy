"""Diagnostic formatting and aggregation helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from scribpy.model import Diagnostic, DiagnosticSeverity

DIAGNOSTIC_SEVERITY_ORDER: Mapping[DiagnosticSeverity, int] = {
    "error": 0,
    "warning": 1,
    "info": 2,
}


def severity_rank(severity: DiagnosticSeverity) -> int:
    """Return the deterministic sort rank for a diagnostic severity.

    Args:
        severity: Diagnostic severity to rank.

    Returns:
        Integer sort rank.
    """
    return DIAGNOSTIC_SEVERITY_ORDER[severity]


def has_errors(diagnostics: Iterable[Diagnostic]) -> bool:
    """Return whether any diagnostic has ``"error"`` severity.

    Args:
        diagnostics: Diagnostics to inspect.

    Returns:
        Whether at least one diagnostic is an error.
    """
    return any(diagnostic.severity == "error" for diagnostic in diagnostics)


def sort_diagnostics(diagnostics: Iterable[Diagnostic]) -> tuple[Diagnostic, ...]:
    """Return diagnostics sorted by stable display fields.

    Args:
        diagnostics: Diagnostics to sort.

    Returns:
        Diagnostics sorted by path, line, severity, code, and message.
    """
    return tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def group_diagnostics_by_path(
    diagnostics: Iterable[Diagnostic],
) -> Mapping[Path | None, tuple[Diagnostic, ...]]:
    """Return diagnostics grouped by path with sorted entries per group.

    Args:
        diagnostics: Diagnostics to group.

    Returns:
        Mapping from related path to sorted diagnostics.
    """
    grouped: dict[Path | None, list[Diagnostic]] = {}
    for diagnostic in sort_diagnostics(diagnostics):
        grouped.setdefault(diagnostic.path, []).append(diagnostic)

    return {
        path: tuple(path_diagnostics)
        for path, path_diagnostics in sorted(grouped.items(), key=_path_group_key)
    }


def format_diagnostic(diagnostic: Diagnostic) -> str:
    """Format one diagnostic for deterministic CLI output.

    Args:
        diagnostic: Diagnostic to render.

    Returns:
        Human-readable diagnostic text.
    """
    prefix = _format_location(diagnostic)
    body = f"{diagnostic.severity} {diagnostic.code}: {diagnostic.message}"
    first_line = f"{prefix}: {body}" if prefix else body

    if diagnostic.hint is None:
        return first_line

    return f"{first_line}\n  hint: {diagnostic.hint}"


def format_diagnostics(
    diagnostics: Sequence[Diagnostic],
    *,
    sort: bool = True,
) -> str:
    """Format diagnostics as a deterministic CLI report.

    Args:
        diagnostics: Diagnostics to render.
        sort: Whether to sort diagnostics before formatting.

    Returns:
        Newline-separated diagnostic report.
    """
    items = sort_diagnostics(diagnostics) if sort else tuple(diagnostics)
    return "\n".join(format_diagnostic(diagnostic) for diagnostic in items)


def _diagnostic_sort_key(diagnostic: Diagnostic) -> tuple[str, int, int, str, str]:
    path_key = "" if diagnostic.path is None else diagnostic.path.as_posix()
    line_key = -1 if diagnostic.line is None else diagnostic.line
    return (
        path_key,
        line_key,
        severity_rank(diagnostic.severity),
        diagnostic.code,
        diagnostic.message,
    )


def _path_group_key(item: tuple[Path | None, object]) -> tuple[str, str]:
    path = item[0]
    if path is None:
        return ("", "")
    return ("1", path.as_posix())


def _format_location(diagnostic: Diagnostic) -> str:
    if diagnostic.path is None:
        return ""

    path = diagnostic.path.as_posix()
    if diagnostic.line is None:
        return path

    return f"{path}:{diagnostic.line}"


__all__ = [
    "DIAGNOSTIC_SEVERITY_ORDER",
    "format_diagnostic",
    "format_diagnostics",
    "group_diagnostics_by_path",
    "has_errors",
    "severity_rank",
    "sort_diagnostics",
]
