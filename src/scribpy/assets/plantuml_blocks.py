"""Rewrite PlantUML fenced blocks inside Markdown.

This module stays focused on Markdown structure: find ``plantuml`` fences,
preserve all non-diagram lines, delegate SVG materialization, and replace each
closed block with a deterministic image reference.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from scribpy.assets.fenced_block import read_fenced_block
from scribpy.assets.plantuml_block_assets import render_block_asset
from scribpy.assets.plantuml_types import PlantUmlRenderResult
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import DiagramRenderer

_PLANTUML_OPEN = "```plantuml"
_PLANTUML_CLOSE = "```"
_DIAGRAMS_DIR = PurePosixPath("assets/diagrams")


def render_plantuml_blocks(
    content: str,
    *,
    renderer: DiagramRenderer,
    output_dir: Path,
    href_prefix: PurePosixPath = _DIAGRAMS_DIR,
    target: str = "html",
    image_format: str = "svg",
) -> PlantUmlRenderResult:
    """Render fenced PlantUML blocks to local image references.

    Args:
        content: Markdown content that may contain fenced ``plantuml`` blocks.
        renderer: Local diagram renderer adapter.
        output_dir: Absolute destination directory for generated image files.
        href_prefix: Relative output path used in generated Markdown links.
        target: Artifact target label.
        image_format: Requested output image format.

    Returns:
        Rewritten content plus generated artifacts and diagnostics.
    """
    rewritten: list[str] = []
    artifacts: list[BuildArtifact] = []
    lines = content.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() != _PLANTUML_OPEN:
            rewritten.append(line)
            index += 1
            continue

        source_lines, close_index = read_fenced_block(
            lines, index + 1, _PLANTUML_CLOSE
        )
        if close_index is None:
            return PlantUmlRenderResult(
                content=content,
                diagnostics=(_unclosed_block_diagnostic(),),
            )

        source = "".join(source_lines)
        result = render_block_asset(
            source, renderer, output_dir, target, image_format
        )
        if result.diagnostics:
            return PlantUmlRenderResult(
                content=content, diagnostics=result.diagnostics
            )
        artifacts.extend(result.artifacts)
        rewritten.append(
            f"![PlantUML diagram]({href_prefix / result.filename})\n"
        )
        index = close_index + 1
    return PlantUmlRenderResult(
        content="".join(rewritten),
        artifacts=tuple(artifacts),
    )


def _unclosed_block_diagnostic() -> Diagnostic:
    """Return a diagnostic for an unclosed PlantUML fence."""
    return Diagnostic(
        severity="error",
        code="UML001",
        message="Unclosed PlantUML fenced block.",
        hint="Close the block with a line containing only ```.",
    )


__all__ = ["_DIAGRAMS_DIR", "render_plantuml_blocks"]
