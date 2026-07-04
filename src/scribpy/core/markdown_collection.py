"""Markdown collection domain object."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.core.markdown_document import MarkdownDocument
from scribpy.core.markdown_file import MarkdownFile

_MARKDOWN_SUFFIXES = frozenset({".md", ".markdown"})


@dataclass(frozen=True, slots=True)
class MarkdownCollection:
    """Represent an ordered collection of Markdown files.

    Attributes:
        root: Root directory used to discover Markdown files.
        files: Ordered Markdown files in the collection.
    """

    root: Path
    files: tuple[MarkdownFile, ...]

    @classmethod
    def from_tree(
        cls,
        root: str | Path,
        *,
        encoding: str = "utf-8",
    ) -> MarkdownCollection:
        """Load Markdown files recursively from a directory tree.

        Files are ordered by their path relative to ``root``. This is the v1
        collection strategy before ``scribpy.yml`` manifests are introduced.

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
        paths = _ordered_markdown_paths(collection_root)
        return cls(
            root=collection_root,
            files=tuple(
                MarkdownFile.from_path(path, encoding=encoding)
                for path in paths
            ),
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


def _ordered_markdown_paths(root: Path) -> tuple[Path, ...]:
    """Return Markdown files ordered by relative path.

    Args:
        root: Directory containing Markdown files and subdirectories.

    Returns:
        Markdown file paths sorted by relative path.
    """
    return tuple(
        sorted(
            (
                path
                for path in root.rglob("*")
                if path.is_file() and path.suffix.lower() in _MARKDOWN_SUFFIXES
            ),
            key=lambda path: path.relative_to(root).as_posix(),
        ),
    )
