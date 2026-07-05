"""Markdown collection domain object."""

from __future__ import annotations

import warnings
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from scribpy.core.diagnostics import (
    CollectionDiagnosticReport,
    CollectionDiagnosticRule,
    diagnose_collection,
)
from scribpy.core.heading_normalizer import normalize_markdown_headings
from scribpy.core.manifest import (
    FolderManifest,
    RootManifest,
    load_folder_manifest,
    load_root_manifest,
)
from scribpy.core.markdown_document import MarkdownDocument
from scribpy.core.markdown_file import MarkdownFile
from scribpy.errors import (
    InvalidMarkdownError,
    InvalidScribpyManifestError,
    ScribpyManifestWarning,
)

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})
_ROOT_FILE_HEADING_LEVEL = 2


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
        """Concatenate files into one normalized Markdown document.

        Returns:
            Markdown document containing one H1, folder headings, and each file
            body in collection order.

        Raises:
            InvalidMarkdownError: If collection diagnostics contain blocking
                errors.
        """
        if not self.files:
            return MarkdownDocument("")
        report = self.diagnose()
        if report.has_errors:
            raise InvalidMarkdownError(report.summary())
        chunks = [f"# {_document_title(self.root, self.manifest)}"]
        previous_folder_parts: tuple[str, ...] = ()
        for markdown_file in self.files:
            folder_parts = _relative_folder_parts(
                self.root, markdown_file.path
            )
            chunks.extend(
                _folder_heading_chunks(
                    self.root,
                    previous_folder_parts,
                    folder_parts,
                ),
            )
            previous_folder_parts = folder_parts
            content = markdown_file.content.strip()
            if content:
                chunks.append(
                    normalize_markdown_headings(
                        content,
                        _ROOT_FILE_HEADING_LEVEL + len(folder_parts),
                    ),
                )
        return MarkdownDocument("\n\n".join(chunks) + "\n")

    def diagnose(
        self,
        rules: Iterable[CollectionDiagnosticRule] | None = None,
    ) -> CollectionDiagnosticReport:
        """Run diagnostics on the Markdown collection.

        Args:
            rules: Optional diagnostic rules. When omitted, Scribpy default
                collection rules are used.

        Returns:
            Collection diagnostic report.
        """
        if rules is None:
            return diagnose_collection(self.root, self.files)
        return diagnose_collection(self.root, self.files, rules)


def _document_title(root: Path, manifest: RootManifest) -> str:
    """Return the title used for the assembled document H1.

    Args:
        root: Collection root directory.
        manifest: Root manifest containing optional project metadata.

    Returns:
        Document title.
    """
    title = manifest.project.get("title")
    if title is None or title == "":
        return root.name
    return str(title)


def _relative_folder_parts(root: Path, path: Path) -> tuple[str, ...]:
    """Return relative parent folder names for one Markdown file.

    Args:
        root: Collection root directory.
        path: Markdown file path.

    Returns:
        Relative parent folder names, or an empty tuple for root files.
    """
    try:
        relative_path = path.relative_to(root)
    except ValueError:
        return ()
    return relative_path.parent.parts


def _folder_heading_chunks(
    root: Path,
    previous_folder_parts: tuple[str, ...],
    current_folder_parts: tuple[str, ...],
) -> list[str]:
    """Return folder headings needed before the current file.

    Args:
        root: Collection root directory.
        previous_folder_parts: Folder parts used by the previous file.
        current_folder_parts: Folder parts used by the current file.

    Returns:
        Folder heading chunks to insert before the current file.
    """
    common_size = _common_prefix_size(
        previous_folder_parts, current_folder_parts
    )
    return [
        _folder_heading(root, current_folder_parts[: index + 1], index)
        for index in range(common_size, len(current_folder_parts))
    ]


def _common_prefix_size(
    left_parts: tuple[str, ...],
    right_parts: tuple[str, ...],
) -> int:
    """Return the shared prefix length between two folder paths.

    Args:
        left_parts: First folder path parts.
        right_parts: Second folder path parts.

    Returns:
        Number of shared leading parts.
    """
    size = 0
    for left, right in zip(left_parts, right_parts, strict=False):
        if left != right:
            return size
        size += 1
    return size


def _folder_heading(
    root: Path, folder_parts: tuple[str, ...], index: int
) -> str:
    """Return one Markdown folder heading.

    Args:
        root: Collection root directory.
        folder_parts: Relative folder path parts for this heading.
        index: Zero-based folder depth.

    Returns:
        Markdown heading for the folder.
    """
    level = min(6, _ROOT_FILE_HEADING_LEVEL + index)
    folder_path = root.joinpath(*folder_parts)
    return f"{'#' * level} {_folder_title(folder_path)}"


def _folder_title(folder: Path) -> str:
    """Return a folder display title from manifest or folder name.

    Args:
        folder: Folder represented in the assembled document.

    Returns:
        Folder title.
    """
    return load_folder_manifest(folder).title or folder.name


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
