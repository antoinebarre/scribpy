"""Markdown collection domain object."""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path

from scribpy.core.manifest import (
    FolderManifest,
    RootManifest,
    load_folder_manifest,
    load_root_manifest,
)
from scribpy.core.markdown_document import MarkdownDocument
from scribpy.core.markdown_file import MarkdownFile
from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})


@dataclass(frozen=True, slots=True)
class MarkdownCollection:
    """Represent an ordered collection of Markdown files.

    Attributes:
        root: Root directory used to discover Markdown files.
        files: Ordered Markdown files in the collection.
        manifest: Root manifest metadata and build settings.
    """

    root: Path
    files: tuple[MarkdownFile, ...]
    manifest: RootManifest = field(default_factory=RootManifest)

    @classmethod
    def from_tree(
        cls,
        root: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> MarkdownCollection:
        """Load Markdown files recursively from a directory tree.

        Files are ordered by local ``scribpy.yml`` manifests when present, or
        by alphabetical direct-child order when no manifest exists.

        Args:
            root: Directory containing Markdown files and subdirectories.
            encoding: Text encoding used to read each Markdown file.

        Returns:
            Markdown collection loaded from the directory tree.

        Raises:
            NotADirectoryError: If ``root`` is not a directory.
            OSError: If a Markdown file cannot be read.
            UnicodeDecodeError: If a Markdown file cannot be decoded.
        """
        collection_root = Path(root)
        if not collection_root.is_dir():
            raise NotADirectoryError(collection_root)
        root_manifest = load_root_manifest(collection_root)
        paths = _ordered_markdown_paths(collection_root, root_manifest)
        return cls(
            root=collection_root,
            files=tuple(
                MarkdownFile.from_path(path, encoding=encoding)
                for path in paths
            ),
            manifest=root_manifest,
        )

    def concatenate(self) -> MarkdownDocument:
        """Concatenate files into one in-memory Markdown document.

        Returns:
            Markdown document containing each file body in collection order.
        """
        chunks = tuple(
            content
            for markdown_file in self.files
            if (content := markdown_file.content.strip())
        )
        if not chunks:
            return MarkdownDocument("")
        return MarkdownDocument("\n\n".join(chunks) + "\n")


def _ordered_markdown_paths(
    root: Path,
    root_manifest: RootManifest,
) -> tuple[Path, ...]:
    """Return Markdown files ordered by manifest or direct-child names.

    Args:
        root: Directory containing Markdown files and subdirectories.
        root_manifest: Root manifest used for first-level ordering.

    Returns:
        Markdown file paths in collection order.
    """
    manifest = FolderManifest(
        path=root_manifest.path,
        order=root_manifest.order,
    )
    return _ordered_folder_paths(root, manifest)


def _ordered_folder_paths(
    folder: Path,
    manifest: FolderManifest,
) -> tuple[Path, ...]:
    """Return Markdown files ordered within one folder.

    Args:
        folder: Folder to scan.
        manifest: Manifest controlling the folder, if present.

    Returns:
        Markdown files from the folder and nested subfolders.
    """
    children = _direct_children(folder)
    if manifest.order:
        ordered_children = _manifest_children(folder, manifest, children)
        _warn_unlisted_children(folder, manifest, children)
    else:
        ordered_children = tuple(children[name] for name in sorted(children))
    return tuple(
        markdown_path
        for child in ordered_children
        for markdown_path in _paths_for_child(child)
    )


def _direct_children(folder: Path) -> dict[str, Path]:
    """Return direct child Markdown files and directories by name.

    Args:
        folder: Folder to inspect.

    Returns:
        Direct child paths keyed by filename.
    """
    children: dict[str, Path] = {}
    for child in folder.iterdir():
        if child.name == "scribpy.yml":
            continue
        if child.is_dir() or _is_markdown_file(child):
            children[child.name] = child
    return children


def _manifest_children(
    folder: Path,
    manifest: FolderManifest,
    children: dict[str, Path],
) -> tuple[Path, ...]:
    """Return children in manifest order.

    Args:
        folder: Folder controlled by the manifest.
        manifest: Local folder manifest.
        children: Available direct child paths.

    Returns:
        Child paths in manifest order.

    Raises:
        InvalidScribpyManifestError: If an ordered child does not exist.
    """
    ordered: list[Path] = []
    manifest_path = manifest.path or (folder / "scribpy.yml")
    for entry in manifest.order:
        child = children.get(entry)
        if child is None:
            raise InvalidScribpyManifestError(
                str(manifest_path),
                f"ordered child does not exist: {entry!r}",
            )
        ordered.append(child)
    return tuple(ordered)


def _warn_unlisted_children(
    folder: Path,
    manifest: FolderManifest,
    children: dict[str, Path],
) -> None:
    """Warn about children ignored by a local manifest.

    Args:
        folder: Folder controlled by the manifest.
        manifest: Local folder manifest.
        children: Available direct child paths.
    """
    listed = set(manifest.order)
    manifest_path = manifest.path or (folder / "scribpy.yml")
    for name in sorted(set(children) - listed):
        warnings.warn(
            f"Ignoring unlisted child {name!r} in {manifest_path}",
            ScribpyManifestWarning,
            stacklevel=2,
        )


def _paths_for_child(child: Path) -> tuple[Path, ...]:
    """Return Markdown paths represented by one child.

    Args:
        child: Direct child file or folder.

    Returns:
        Markdown file paths represented by the child.
    """
    if child.is_dir():
        return _ordered_folder_paths(child, load_folder_manifest(child))
    return (child,)


def _is_markdown_file(path: Path) -> bool:
    """Return whether a path is a supported Markdown file.

    Args:
        path: Candidate path.

    Returns:
        True when the path is a supported Markdown file.
    """
    return path.is_file() and path.suffix.lower() in _MARKDOWN_SUFFIXES
