"""Shared PlantUML rendering result and error types."""

from __future__ import annotations

from dataclasses import dataclass

from scribpy.model import BuildArtifact, Diagnostic


@dataclass(frozen=True)
class PlantUmlRenderResult:
    """Rendered PlantUML content plus generated assets and diagnostics.

    Attributes:
        content: Markdown content after PlantUML fences have been replaced.
        artifacts: Generated local SVG artifacts.
        diagnostics: Rendering or write diagnostics.
    """

    content: str
    artifacts: tuple[BuildArtifact, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


class PlantUmlRenderError(RuntimeError):
    """Raised when one PlantUML backend cannot render a diagram.

    Attributes:
        backend: Renderer backend that failed, either ``"java"`` or ``"web"``.
    """

    def __init__(self, backend: str, detail: str) -> None:
        """Create a typed PlantUML render error.

        Args:
            backend: Renderer backend that failed.
            detail: Backend-specific failure detail.
        """
        super().__init__(detail)
        self.backend = backend


__all__ = ["PlantUmlRenderError", "PlantUmlRenderResult"]
