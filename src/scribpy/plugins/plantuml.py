"""Internal PlantUML fenced-code-block plugin."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets.plantuml import (
    JavaPlantUmlRenderer,
    WebPlantUmlRenderer,
    render_plantuml_documents,
    validate_java_plantuml_environment,
)
from scribpy.config.types import PlantUmlConfig
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import DiagramRenderer


class PlantUmlPlugin:
    """Render fenced ``plantuml`` Markdown blocks into SVG artifacts."""

    language = "plantuml"

    def __init__(
        self,
        config: PlantUmlConfig,
        renderer_override: DiagramRenderer | None = None,
    ) -> None:
        """Create the PlantUML block plugin.

        Args:
            config: PlantUML backend configuration.
            renderer_override: Optional injected renderer used by tests or callers.
        """
        self._config = config
        self._renderer = renderer_override or self._select_renderer(config)

    def has_blocks(self, content: str) -> bool:
        """Return whether Markdown content contains PlantUML fences.

        Args:
            content: Markdown source text to inspect.

        Returns:
            Whether the source contains PlantUML fences.
        """
        return "```plantuml" in content

    def preflight(self) -> tuple[Diagnostic, ...]:
        """Validate the Java backend only when it was explicitly requested.

        Returns:
            Diagnostics raised by Java runtime validation.
        """
        if self._config.renderer != "java":
            return ()
        return validate_java_plantuml_environment()

    def render_documents(
        self,
        documents: tuple[TransformedDocument, ...],
        *,
        output_dir: Path,
        flattened: bool,
        target: str,
        image_format: str = "svg",
    ) -> tuple[
        tuple[TransformedDocument, ...],
        tuple[BuildArtifact, ...],
        tuple[Diagnostic, ...],
    ]:
        """Render PlantUML blocks across target-ready Markdown documents.

        Args:
            documents: Target-ready documents to inspect.
            output_dir: Root directory for generated plugin assets.
            flattened: Whether output documents will be merged into one page.
            target: Artifact target label.
            image_format: Requested image format for generated diagrams.

        Returns:
            Rewritten documents, generated artifacts, and diagnostics.
        """
        return render_plantuml_documents(
            documents,
            renderer=self._renderer,
            diagrams_dir=output_dir / "diagrams",
            flattened=flattened,
            target=target,
            image_format=image_format,
        )

    @staticmethod
    def _select_renderer(config: PlantUmlConfig) -> DiagramRenderer:
        """Return the configured PlantUML renderer implementation."""
        if config.renderer == "web":
            return WebPlantUmlRenderer(config.server_url)
        return JavaPlantUmlRenderer()


__all__ = ["PlantUmlPlugin"]
