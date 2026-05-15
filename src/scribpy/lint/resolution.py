"""Resolution helpers shared by native lint rules."""

from __future__ import annotations

import posixpath
from pathlib import Path
from urllib.parse import urlsplit

from scribpy.model import Document


def is_external_target(target: str) -> bool:
    """Return whether a target uses a non-local URI scheme.

    Args:
        target: Raw Markdown link or asset target.

    Returns:
        Whether the target is external to the source tree.
    """
    parts = urlsplit(target)
    return bool(parts.scheme) or target.startswith("//")


def split_local_target(target: str) -> tuple[str, str | None]:
    """Split a local target into path and optional anchor fragment.

    Args:
        target: Raw local Markdown target.

    Returns:
        Pair containing the path part and optional anchor fragment.
    """
    parts = urlsplit(target)
    anchor = parts.fragment or None
    return parts.path, anchor


def resolve_relative_path(document: Document, target_path: str) -> Path:
    """Resolve a local target path against a document's relative directory.

    Args:
        document: Document containing the target.
        target_path: Raw local path from the Markdown source.

    Returns:
        Normalized source-relative target path.
    """
    base = document.relative_path.parent.as_posix()
    normalized = posixpath.normpath(posixpath.join(base, target_path))
    return Path(normalized)


def stays_within_source_tree(path: Path) -> bool:
    """Return whether a normalized path stays in the source tree.

    Args:
        path: Normalized candidate path.

    Returns:
        Whether the path is relative and does not escape with ``..``.
    """
    return not path.is_absolute() and ".." not in path.parts


__all__ = [
    "is_external_target",
    "resolve_relative_path",
    "split_local_target",
    "stays_within_source_tree",
]
