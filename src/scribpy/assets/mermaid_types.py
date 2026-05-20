"""Shared Mermaid rendering result and error types."""

from __future__ import annotations

from dataclasses import dataclass

from scribpy.model import BuildArtifact, Diagnostic


@dataclass(frozen=True)
class MermaidRenderResult:
    """Rendered Mermaid content plus generated assets and diagnostics.

    Attributes:
        content: Markdown content after Mermaid fences have been replaced.
        artifacts: Generated local SVG artifacts.
        diagnostics: Rendering or write diagnostics.
    """

    content: str
    artifacts: tuple[BuildArtifact, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


class MermaidRenderError(RuntimeError):
    """Raised when the Mermaid web renderer cannot render a diagram."""


__all__ = ["MermaidRenderError", "MermaidRenderResult"]
