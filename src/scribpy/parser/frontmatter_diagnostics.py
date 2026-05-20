"""Diagnostics emitted by Markdown frontmatter parsing."""

from __future__ import annotations

from pathlib import Path

from scribpy.model import Diagnostic


def unclosed_frontmatter(delimiter: str, path: Path | None) -> Diagnostic:
    """Return a diagnostic for an unclosed frontmatter block.

    Args:
        delimiter: Opening delimiter that must also close the block.
        path: Optional source path attached to diagnostics.

    Returns:
        Parser diagnostic for the unclosed block.
    """
    return Diagnostic(
        severity="error",
        code="PRS002",
        message=f"Frontmatter block opened with '{delimiter}' is not closed.",
        path=path,
        line=1,
        hint=(
            f"Close the frontmatter block with a line"
            f" containing only '{delimiter}'."
        ),
    )


def yaml_not_mapping(path: Path | None) -> Diagnostic:
    """Return a diagnostic for a non-mapping YAML frontmatter root.

    Args:
        path: Optional source path attached to diagnostics.

    Returns:
        Parser diagnostic for an invalid YAML root value.
    """
    return Diagnostic(
        severity="error",
        code="PRS002",
        message="YAML frontmatter must be a mapping, not a scalar or list.",
        path=path,
        line=1,
        hint="Use 'key: value' pairs at the top level of the YAML block.",
    )


def invalid_yaml(
    detail: object, path: Path | None, line: int | None
) -> Diagnostic:
    """Return a diagnostic for invalid YAML frontmatter syntax.

    Args:
        detail: YAML exception or error detail.
        path: Optional source path attached to diagnostics.
        line: One-based diagnostic line when available.

    Returns:
        Parser diagnostic for invalid YAML syntax.
    """
    return Diagnostic(
        severity="error",
        code="PRS002",
        message=f"Invalid YAML frontmatter: {detail}",
        path=path,
        line=line,
        hint="Fix the YAML syntax in the frontmatter block.",
    )


def invalid_toml(detail: object, path: Path | None) -> Diagnostic:
    """Return a diagnostic for invalid TOML frontmatter syntax.

    Args:
        detail: TOML parser exception or error detail.
        path: Optional source path attached to diagnostics.

    Returns:
        Parser diagnostic for invalid TOML syntax.
    """
    return Diagnostic(
        severity="error",
        code="PRS002",
        message=f"Invalid TOML frontmatter: {detail}",
        path=path,
        line=None,
        hint="Fix the TOML syntax in the frontmatter block.",
    )


__all__ = [
    "invalid_toml",
    "invalid_yaml",
    "unclosed_frontmatter",
    "yaml_not_mapping",
]
