"""Rewrite Mermaid fenced blocks inside Markdown.

This module owns the Markdown-level pass: detect Mermaid fences, keep ordinary
content untouched, delegate SVG materialization, and replace each completed
block with a deterministic image link.
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath

from scribpy.assets.fenced_block import read_fenced_block
from scribpy.assets.mermaid_block_assets import render_block_asset
from scribpy.assets.mermaid_diagnostics import unclosed_block_diagnostic
from scribpy.assets.mermaid_types import MermaidRenderResult
from scribpy.model import BuildArtifact
from scribpy.model.protocols import DiagramRenderer

_MERMAID_OPEN = "```mermaid"
_MERMAID_CLOSE = "```"
_DIAGRAMS_DIR = PurePosixPath("assets/diagrams")


def render_mermaid_blocks(
    content: str,
    *,
    renderer: DiagramRenderer,
    output_dir: Path,
    href_prefix: PurePosixPath = _DIAGRAMS_DIR,
    target: str = "html",
    source_label: str | None = None,
) -> MermaidRenderResult:
    """Render fenced Mermaid blocks to local SVG image references.

    Args:
        content: Markdown content that may contain fenced ``mermaid`` blocks.
        renderer: Mermaid web renderer adapter.
        output_dir: Absolute destination directory for generated SVG files.
        href_prefix: Relative output path used in generated Markdown links.
        target: Artifact target label.
        source_label: Optional source document label used in logs.

    Returns:
        Rewritten content plus generated artifacts and diagnostics.
    """
    rewritten: list[str] = []
    artifacts: list[BuildArtifact] = []
    lines = content.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() != _MERMAID_OPEN:
            rewritten.append(line)
            index += 1
            continue

        source_lines, close_index = read_fenced_block(
            lines, index + 1, _MERMAID_CLOSE
        )
        if close_index is None:
            return MermaidRenderResult(
                content=content,
                diagnostics=(unclosed_block_diagnostic(),),
            )

        result = render_block_asset(
            "".join(source_lines),
            renderer=renderer,
            output_dir=output_dir,
            target=target,
            source_label=source_label,
        )
        if result.diagnostics:
            return MermaidRenderResult(
                content=content, diagnostics=result.diagnostics
            )
        artifacts.extend(result.artifacts)
        rewritten.append(
            f"![Mermaid diagram]({href_prefix / result.filename})\n"
        )
        index = close_index + 1
    return MermaidRenderResult(
        content="".join(rewritten), artifacts=tuple(artifacts)
    )


__all__ = ["_DIAGRAMS_DIR", "render_mermaid_blocks"]
