"""Internal Mermaid fenced-code-block plugin."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets.mermaid import WebMermaidRenderer, render_mermaid_documents
from scribpy.config.types import MermaidConfig
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument


class MermaidPlugin:
    """Render fenced ``mermaid`` Markdown blocks into SVG artifacts."""

    language = "mermaid"

    def __init__(
        self,
        config: MermaidConfig,
        renderer_override: WebMermaidRenderer | None = None,
    ) -> None:
        """Create the Mermaid block plugin.

        Args:
            config: Mermaid web rendering configuration.
            renderer_override: Optional injected renderer used by tests.
        """
        self._config = config
        self._renderer = renderer_override or WebMermaidRenderer(
            config.server_url,
            config.theme,
        )

    def has_blocks(self, content: str) -> bool:
        """Return whether Markdown content contains Mermaid fences.

        Args:
            content: Markdown source text to inspect.

        Returns:
            Whether the source contains Mermaid fences.
        """
        return "```mermaid" in content

    def preflight(self) -> tuple[Diagnostic, ...]:
        """Return Mermaid preflight diagnostics.

        Returns:
            No diagnostics. Mermaid is web-only and is checked during render.
        """
        return ()

    def render_documents(
        self,
        documents: tuple[TransformedDocument, ...],
        *,
        output_dir: Path,
        flattened: bool,
        target: str,
    ) -> tuple[
        tuple[TransformedDocument, ...],
        tuple[BuildArtifact, ...],
        tuple[Diagnostic, ...],
    ]:
        """Render Mermaid blocks across target-ready Markdown documents.

        Args:
            documents: Target-ready documents to inspect.
            output_dir: Root directory for generated plugin assets.
            flattened: Whether output documents will be merged into one page.
            target: Artifact target label.

        Returns:
            Rewritten documents, generated artifacts, and diagnostics.
        """
        return render_mermaid_documents(
            documents,
            renderer=self._renderer,
            diagrams_dir=output_dir / "diagrams",
            flattened=flattened,
            target=target,
        )


__all__ = ["MermaidPlugin"]
