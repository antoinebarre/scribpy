"""Concrete filesystem adapter used by Scribpy services."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


class RealFileSystem:
    """Concrete ``FileSystem`` implementation backed by the OS filesystem."""

    def read_text(self, path: Path) -> str:
        """Return the UTF-8 text content of a path.

        Args:
            path: File path to read.

        Returns:
            UTF-8 file contents.
        """
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        """Write UTF-8 content to a path.

        Args:
            path: File path to write.
            content: UTF-8 text content to persist.
        """
        path.write_text(content, encoding="utf-8")

    def exists(self, path: Path) -> bool:
        """Return whether a path exists.

        Args:
            path: Candidate filesystem path.

        Returns:
            Whether the path exists.
        """
        return path.exists()

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        """Yield matching paths below a root.

        Args:
            root: Directory to search below.
            pattern: Glob pattern relative to ``root``.

        Returns:
            Matching paths.
        """
        return root.glob(pattern)


__all__ = ["RealFileSystem"]
