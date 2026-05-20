"""Diagnostics emitted by internal-link linting."""

from __future__ import annotations

from scribpy.model import Diagnostic, Document


def missing_link_target(
    document: Document,
    target: str,
    line: int | None,
) -> Diagnostic:
    """Create a diagnostic for an unresolved local link target.

    Args:
        document: Document that owns the broken link.
        target: Raw link target from the source Markdown.
        line: Source line for the link when available.

    Returns:
        Internal-link diagnostic for the missing target path.
    """
    return Diagnostic(
        severity="error",
        code="LINT003",
        message="Internal link target does not exist.",
        path=document.relative_path,
        line=line,
        hint=f"Check the target path: {target}",
    )


def missing_anchor(
    document: Document, anchor: str, line: int | None
) -> Diagnostic:
    """Create a diagnostic for an unresolved local link anchor.

    Args:
        document: Document that owns the broken link.
        anchor: Missing heading anchor without the leading ``#``.
        line: Source line for the link when available.

    Returns:
        Internal-link diagnostic for the missing anchor.
    """
    return Diagnostic(
        severity="error",
        code="LINT003",
        message="Internal link anchor does not exist.",
        path=document.relative_path,
        line=line,
        hint=f"Check the target anchor: #{anchor}",
    )


__all__ = ["missing_anchor", "missing_link_target"]
