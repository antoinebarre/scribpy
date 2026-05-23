"""Materialize one PlantUML source block as an image asset."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from scribpy.assets.plantuml_diagnostics import (
    java_render_failure_diagnostic,
    render_failure_diagnostic,
)
from scribpy.assets.plantuml_types import PlantUmlRenderError
from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import DiagramRenderer

logger = get_logger(__name__)


@dataclass(frozen=True)
class RenderedPlantUmlBlock:
    """Result of rendering one PlantUML block to disk.

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
    renderer: DiagramRenderer,
    output_dir: Path,
    target: str,
    image_format: str = "svg",
) -> RenderedPlantUmlBlock:
    """Render one PlantUML source block and write its image asset.

    Args:
        source: Raw PlantUML source inside one fenced block.
        renderer: Diagram renderer backend.
        output_dir: Destination directory for generated image files.
        target: Artifact target label.
        image_format: Requested output image format.

    Returns:
        Rendered block result with filename, artifacts, and diagnostics.
    """
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
    filename = f"plantuml-{digest}.{image_format}"
    artifact_path = output_dir / filename
    logger.info("Rendering PlantUML block %s to %s", digest, artifact_path)
    try:
        image = renderer.render(source, image_format)
    except PlantUmlRenderError as exc:
        logger.error("PlantUML block %s failed to render: %s", digest, exc)
        return RenderedPlantUmlBlock(
            filename, diagnostics=(render_failure_diagnostic(exc),)
        )
    except (OSError, RuntimeError, UnicodeDecodeError) as exc:
        logger.error("PlantUML block %s failed to render: %s", digest, exc)
        return RenderedPlantUmlBlock(
            filename, diagnostics=(java_render_failure_diagnostic(str(exc)),)
        )
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_bytes(image)
    except Exception as exc:
        logger.error("PlantUML block %s failed to write: %s", digest, exc)
        return RenderedPlantUmlBlock(
            filename,
            diagnostics=(_write_failure_diagnostic(exc, artifact_path),),
        )
    logger.info("Rendered PlantUML block %s", digest)
    return RenderedPlantUmlBlock(
        filename, artifacts=(BuildArtifact(artifact_path, target, "diagram"),)
    )


def _write_failure_diagnostic(exc: Exception, path: Path) -> Diagnostic:
    """Return a diagnostic for a failed image asset write."""
    return Diagnostic(
        severity="error",
        code="UML003",
        message=f"Cannot write PlantUML image asset: {exc}",
        path=path,
        hint="Check that the build directory is writable.",
    )


__all__ = ["RenderedPlantUmlBlock", "render_block_asset"]
