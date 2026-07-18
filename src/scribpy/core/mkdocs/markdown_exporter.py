"""Markdown file export with shared asset processing."""

from __future__ import annotations

import os
from pathlib import Path

from scribpy.core.diagram_blocks import render_diagram_blocks
from scribpy.core.image_collector import collect_images
from scribpy.core.manifest import BuildSettings
from scribpy.core.markdown_collection import MarkdownCollection


def export_markdown_files(
    collection: MarkdownCollection,
    docs_dir: Path,
    build: BuildSettings,
) -> None:
    """Export collection Markdown files and their local assets.

    Args:
        collection: Source Markdown collection.
        docs_dir: MkDocs source directory receiving files.
        build: Root manifest build settings for diagram rendering.

    Raises:
        OSError: If a Markdown file or asset cannot be written.
        ValueError: If a diagram backend is unknown.
        PlantUmlRenderError: If PlantUML rendering fails.
        MermaidRenderError: If Mermaid rendering fails.
        NotImplementedError: If a selected backend is unavailable.
    """
    assets_dir = docs_dir / "assets"
    generated_dir = assets_dir / "generated"
    collected: dict[str, Path] = {}
    for markdown_file in collection.files:
        relative_path = markdown_file.path.relative_to(collection.root)
        destination = docs_dir / relative_path
        asset_reference = _relative_reference(destination.parent, assets_dir)
        generated_reference = _relative_reference(
            destination.parent,
            generated_dir,
        )
        content = render_diagram_blocks(
            markdown_file.content,
            build,
            generated_dir,
            generated_reference,
        )
        content = collect_images(
            content,
            markdown_file.path.parent,
            assets_dir,
            asset_reference,
            collected,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding=markdown_file.encoding)


def _relative_reference(source_dir: Path, destination: Path) -> str:
    """Return a POSIX reference from one directory to another.

    Args:
        source_dir: Directory containing the referencing Markdown file.
        destination: Referenced asset directory.

    Returns:
        Relative POSIX path between the directories.
    """
    return Path(os.path.relpath(destination, source_dir)).as_posix()
