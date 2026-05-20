"""Semantic validation for parsed Scribpy configuration."""

from __future__ import annotations

from pathlib import Path

from scribpy.config.types import Config
from scribpy.model import Diagnostic


def validate_config(config: Config) -> tuple[Diagnostic, ...]:
    """Validate semantic configuration constraints.

    Args:
        config: Parsed configuration object.

    Returns:
        Diagnostics describing invalid semantic values. An empty tuple means
        the configuration is valid for the current implementation phase.
    """
    diagnostics: list[Diagnostic] = []

    if not _is_safe_relative_path(config.paths.source):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="CFG004",
                message=(
                    "Configured source path must be relative and stay inside "
                    "the project."
                ),
                hint="Use a relative path such as 'doc' or 'docs'.",
            )
        )

    for file_path in config.index.files:
        if not _is_safe_relative_path(file_path):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="CFG004",
                    message=(
                        "Configured index file paths must be relative and stay "
                        "inside the project."
                    ),
                    path=file_path,
                    hint="Remove absolute paths and '..' segments from index.files.",
                )
            )

    return tuple(diagnostics)


def _is_safe_relative_path(path: Path) -> bool:
    """Return whether safe relative path."""
    return not path.is_absolute() and ".." not in path.parts


__all__ = ["validate_config"]
