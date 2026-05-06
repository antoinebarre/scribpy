"""Utility functions for Markdown file discovery and I/O."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

_MD_SUFFIX = ".md"


class RealFileSystem:
    """Concrete ``FileSystem`` implementation backed by the OS filesystem."""

    def read_text(self, path: Path) -> str:
        """Return the UTF-8 text content of ``path``."""
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        """Write UTF-8 ``content`` to ``path``."""
        path.write_text(content, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists."""
        return path.exists()

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        """Yield paths below ``root`` matching ``pattern``."""
        return root.glob(pattern)


def is_md_file(path: Path) -> bool:
    """Returns True if path is an existing file with a .md extension."""
    return path.is_file() and path.suffix.lower() == _MD_SUFFIX


def list_md_files(path: Path, recursive: bool = True) -> list[Path]:
    """Lists all .md files under a directory.

    Args:
        path: Directory to search.
        recursive: If True, descend into sub-directories.

    Returns:
        Sorted list of Path objects pointing to .md files.

    Raises:
        NotADirectoryError: If path is not a directory.
    """
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {path}")
    pattern = f"**/*{_MD_SUFFIX}" if recursive else f"*{_MD_SUFFIX}"
    return sorted(path.glob(pattern))


def read_md_file(path: Path) -> str:
    """Reads and returns the raw content of a Markdown file.

    Args:
        path: Path to the .md file.

    Returns:
        File content as a UTF-8 string.

    Raises:
        FileNotFoundError: If path does not exist.
        ValueError: If path does not have a .md extension.
    """
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() != _MD_SUFFIX:
        raise ValueError(f"Expected a .md file, got: {path}")
    return path.read_text(encoding="utf-8")


def write_md_file(
    path: Path,
    content: str,
    create_parents: bool = False,
) -> None:
    """Writes content to a Markdown file.

    Args:
        path: Destination .md file path.
        content: Text to write.
        create_parents: If True, create missing parent directories.

    Raises:
        ValueError: If path does not have a .md extension.
        FileNotFoundError: If parent directory is missing and create_parents is False.
    """
    if path.suffix.lower() != _MD_SUFFIX:
        raise ValueError(f"Expected a .md file, got: {path}")
    if create_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.parent.exists():
        raise FileNotFoundError(f"Directory not found: {path.parent}")
    path.write_text(content, encoding="utf-8")
