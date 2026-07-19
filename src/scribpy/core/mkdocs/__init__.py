"""MkDocs static project export."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.mkdocs.configuration import write_configuration
from scribpy.core.mkdocs.markdown_exporter import export_markdown_files
from scribpy.core.mkdocs.navigation import build_navigation
from scribpy.errors import ScaffoldCollisionError

_CONFIGURATION_NAME = "mkdocs.yml"


def mkdocs_export(source: Path, output: Path) -> None:
    """Export a Scribpy project as static MkDocs input files.

    Args:
        source: Scribpy project root containing the root manifest.
        output: Destination directory for ``mkdocs.yml`` and ``docs/``.

    Raises:
        ScaffoldCollisionError: If ``output/mkdocs.yml`` already exists.
        NotADirectoryError: If the source is not a directory.
        InvalidMarkdownError: If an exported source has no H1 heading.
        InvalidScribpyManifestError: If a project manifest is invalid.
        PlantUmlRenderError: If PlantUML rendering fails.
        MermaidRenderError: If Mermaid rendering fails.
        NotImplementedError: If a configured backend is unavailable.
        OSError: If a source or destination file cannot be accessed.
        UnicodeDecodeError: If a Markdown source is not valid UTF-8.
    """
    configuration_path = output / _CONFIGURATION_NAME
    if configuration_path.exists():
        raise ScaffoldCollisionError(str(configuration_path))

    collection = MarkdownCollection.from_tree(source)
    navigation = build_navigation(collection)
    output.mkdir(parents=True, exist_ok=True)
    export_markdown_files(
        collection,
        output / "docs",
        collection.manifest.build,
    )
    site_name = str(collection.manifest.project.get("title") or source.name)
    write_configuration(configuration_path, site_name, navigation)


__all__ = ["mkdocs_export"]
