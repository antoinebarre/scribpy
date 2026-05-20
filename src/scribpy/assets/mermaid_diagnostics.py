"""User-facing Mermaid diagnostics."""

from __future__ import annotations

from pathlib import Path

from scribpy.model import Diagnostic


def render_failure_diagnostic(detail: str) -> Diagnostic:
    """Return a Mermaid web-renderer failure diagnostic.

    Args:
        detail: Renderer failure detail.

    Returns:
        Diagnostic for a Mermaid rendering failure.
    """
    return Diagnostic(
        severity="error",
        code="MRM002",
        message=f"Mermaid web rendering failed: {detail}",
        hint=(
            "Check builders.html.mermaid.server_url, Mermaid syntax, "
            "and network access to the configured rendering service."
        ),
    )


def write_failure_diagnostic(exc: Exception, path: Path) -> Diagnostic:
    """Return a diagnostic for a failed SVG asset write.

    Args:
        exc: Raised write exception.
        path: Destination path that could not be written.

    Returns:
        Diagnostic for the failed write.
    """
    return Diagnostic(
        severity="error",
        code="MRM003",
        message=f"Cannot write Mermaid SVG asset: {exc}",
        path=path,
        hint="Check that the build directory is writable.",
    )


def unclosed_block_diagnostic() -> Diagnostic:
    """Return a diagnostic for an unclosed Mermaid fence.

    Returns:
        Diagnostic for an unclosed fenced code block.
    """
    return Diagnostic(
        severity="error",
        code="MRM001",
        message="Unclosed Mermaid fenced block.",
        hint="Close the block with a line containing only ```.",
    )


__all__ = [
    "render_failure_diagnostic",
    "unclosed_block_diagnostic",
    "write_failure_diagnostic",
]
