"""Materialize one Mermaid source block as an image asset."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from scribpy.assets.mermaid_diagnostics import (
    render_failure_diagnostic,
    write_failure_diagnostic,
)
from scribpy.assets.mermaid_types import MermaidRenderError
from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import DiagramRenderer

logger = get_logger(__name__)


@dataclass(frozen=True)
class RenderedMermaidBlock:
    """Result of rendering one Mermaid block to disk.

    Attributes:
        filename: Deterministic SVG filename for generated Markdown links.
        artifacts: Generated artifact when rendering and writing succeed.
        diagnostics: Error diagnostics when rendering or writing fails.
    """

    filename: str
    artifacts: tuple[BuildArtifact, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


def render_block_asset(
    source: str,
    *,
    renderer: DiagramRenderer,
    output_dir: Path,
    target: str,
    source_label: str | None,
    image_format: str = "svg",
) -> RenderedMermaidBlock:
    """Render one Mermaid source block and write its image asset.

    Args:
        source: Raw Mermaid source inside one fenced block.
        renderer: Renderer object exposing ``render(source, format)``.
        output_dir: Destination directory for generated image files.
        target: Artifact target label.
        source_label: Optional source document label used in logs.
        image_format: Requested output image format.

    Returns:
        Rendered block result with filename, artifacts, and diagnostics.
    """
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    filename = f"mermaid-{digest}.{image_format}"
    artifact_path = output_dir / filename
    label = source_label or "<unknown document>"
    logger.info(
        "Rendering Mermaid block %s from %s to %s",
        digest,
        label,
        artifact_path,
    )
    try:
        image = renderer.render(source, _renderer_format(image_format))
    except MermaidRenderError as exc:
        logger.error(
            "Mermaid block %s from %s failed to render: %s",
            digest,
            label,
            exc,
        )
        return RenderedMermaidBlock(
            filename, diagnostics=(render_failure_diagnostic(str(exc)),)
        )
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(image)
    except Exception as exc:
        logger.error(
            "Mermaid block %s from %s failed to write: %s",
            digest,
            label,
            exc,
        )
        return RenderedMermaidBlock(
            filename,
            diagnostics=(write_failure_diagnostic(exc, artifact_path),),
        )
    logger.info("Rendered Mermaid block %s from %s", digest, label)
    return RenderedMermaidBlock(
        filename, artifacts=(BuildArtifact(artifact_path, target, "diagram"),)
    )


def _renderer_format(image_format: str) -> str:
    """Return the Mermaid service path for an artifact extension."""
    if image_format == "png":
        return "img"
    return image_format


__all__ = ["RenderedMermaidBlock", "render_block_asset"]
