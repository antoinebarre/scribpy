"""Diagnostics emitted while validating document indexes."""

from __future__ import annotations

from pathlib import Path

from scribpy.model import Diagnostic


def unsupported_config_mode() -> Diagnostic:
    """Return the diagnostic for an unsupported configured index mode.

    Returns:
        Diagnostic for an unsupported configured index mode.
    """
    return Diagnostic(
        severity="error",
        code="IDX001",
        message="Configured index mode is not supported yet.",
        hint="Use index.mode = 'filesystem' or index.mode = 'explicit'.",
    )


def unsupported_index_mode() -> Diagnostic:
    """Return the diagnostic for an unsupported document index mode.

    Returns:
        Diagnostic for an unsupported document index mode.
    """
    return Diagnostic(
        severity="error",
        code="IDX001",
        message="Document index mode is not supported yet.",
        hint="Use an explicit or filesystem index.",
    )


def unsafe_entry(path: Path) -> Diagnostic:
    """Return the diagnostic for an unsafe index entry path.

    Args:
        path: Unsafe index entry path.

    Returns:
        Diagnostic for the unsafe entry.
    """
    return Diagnostic(
        severity="error",
        code="IDX004",
        message="Index entries must be relative and stay inside the source tree.",
        path=path,
        hint="Remove absolute paths and '..' segments from index.files.",
    )


def duplicate_entry(path: Path) -> Diagnostic:
    """Return the diagnostic for a duplicated index entry.

    Args:
        path: Duplicated index entry path.

    Returns:
        Diagnostic for the duplicate entry.
    """
    return Diagnostic(
        severity="error",
        code="IDX003",
        message="Index entry is duplicated.",
        path=path,
        hint="Keep each source file only once in index.files.",
    )


def missing_explicit_file(path: Path) -> Diagnostic:
    """Return the diagnostic for an explicit entry not discovered on disk.

    Args:
        path: Explicit index entry absent from discovered files.

    Returns:
        Diagnostic for the missing explicit file.
    """
    return Diagnostic(
        severity="error",
        code="IDX002",
        message="Explicit index entry was not found in discovered source files.",
        path=path,
        hint=(
            "Create the file under the source directory or remove it from "
            "index.files."
        ),
    )


def uncovered_discovered_file(path: Path) -> Diagnostic:
    """Return the warning for a discovered file absent from explicit index.

    Args:
        path: Discovered source file not present in the explicit index.

    Returns:
        Warning diagnostic for the uncovered file.
    """
    return Diagnostic(
        severity="warning",
        code="IDX005",
        message="Discovered source file is not listed in explicit index.",
        path=path,
        hint="Add the file to index.files if it should be part of the build.",
    )


__all__ = [
    "duplicate_entry",
    "missing_explicit_file",
    "uncovered_discovered_file",
    "unsafe_entry",
    "unsupported_config_mode",
    "unsupported_index_mode",
]
