"""Manifest-driven MkDocs navigation construction."""

from __future__ import annotations

import re
from pathlib import Path

from scribpy.core.manifest import (
    FolderManifest,
    RootManifest,
    load_folder_manifest,
)
from scribpy.core.markdown_collection import MarkdownCollection
from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.mkdocs.configuration import Navigation
from scribpy.errors import InvalidMarkdownError

_H1 = re.compile(r"^#\s+(?P<title>.+?)\s*$")
_FENCE = re.compile(r"^(?P<marker>`{3,}|~{3,})")


def build_navigation(collection: MarkdownCollection) -> Navigation:
    """Build ordered hierarchical navigation for a collection.

    Args:
        collection: Manifest-ordered Markdown collection.

    Returns:
        MkDocs navigation mapping list.

    Raises:
        InvalidMarkdownError: If an exported source has no H1 heading.
    """
    files_by_relative_path = {
        markdown_file.path.relative_to(collection.root): markdown_file
        for markdown_file in collection.files
    }
    return _folder_navigation(
        collection.root,
        Path(),
        collection.manifest,
        files_by_relative_path,
    )


def _folder_navigation(
    root: Path,
    relative_folder: Path,
    manifest: RootManifest | FolderManifest,
    files: dict[Path, MarkdownFile],
) -> Navigation:
    """Build navigation entries for one source folder.

    Args:
        root: Collection root directory.
        relative_folder: Folder relative to the collection root.
        manifest: Manifest carrying the folder order.
        files: Relative source path to Markdown file mapping.

    Returns:
        Navigation entries for direct children containing exported files.
    """
    direct_names = _direct_child_names(relative_folder, files)
    manifest_order = getattr(manifest, "order", ())
    names = _ordered_names(direct_names, manifest_order)
    entries: Navigation = []
    for name in names:
        child = relative_folder / name
        markdown_file = files.get(child)
        if markdown_file is not None:
            entries.append({_first_h1(markdown_file): child.as_posix()})
            continue
        folder_manifest = load_folder_manifest(root / child)
        children = _folder_navigation(
            root,
            child,
            folder_manifest,
            files,
        )
        if children:
            title = folder_manifest.title or name.capitalize()
            entries.append({title: children})
    return entries


def _direct_child_names(
    relative_folder: Path,
    files: dict[Path, MarkdownFile],
) -> set[str]:
    """Return direct child names leading to exported Markdown files.

    Args:
        relative_folder: Folder relative to the collection root.
        files: Relative source path to Markdown file mapping.

    Returns:
        Direct Markdown file or directory names.
    """
    names: set[str] = set()
    depth = len(relative_folder.parts)
    for relative_path in files:
        if relative_path.parts[:depth] != relative_folder.parts:
            continue
        names.add(relative_path.parts[depth])
    return names


def _ordered_names(
    direct_names: set[str],
    manifest_order: tuple[str, ...],
) -> tuple[str, ...]:
    """Order relevant direct names from a local manifest.

    Args:
        direct_names: Names that lead to exported Markdown files.
        manifest_order: Direct-child order declared by the manifest.

    Returns:
        Ordered relevant names.
    """
    if not manifest_order:
        return tuple(sorted(direct_names))
    normalized = (entry.strip().rstrip("/") for entry in manifest_order)
    return tuple(name for name in normalized if name in direct_names)


def _first_h1(markdown_file: MarkdownFile) -> str:
    """Extract the first H1 outside fenced code blocks.

    Args:
        markdown_file: Source Markdown file.

    Returns:
        First H1 text.

    Raises:
        InvalidMarkdownError: If the source contains no H1.
    """
    closing_marker: str | None = None
    for line in markdown_file.content.splitlines():
        fence = _FENCE.match(line)
        if fence is not None:
            marker = fence.group("marker")
            if closing_marker is None:
                closing_marker = marker[0]
            elif marker[0] == closing_marker:
                closing_marker = None
            continue
        if closing_marker is None and (heading := _H1.match(line)):
            return heading.group("title").strip().rstrip("#").rstrip()
    detail = f"Missing H1 heading: {markdown_file.path}"
    raise InvalidMarkdownError(detail)
