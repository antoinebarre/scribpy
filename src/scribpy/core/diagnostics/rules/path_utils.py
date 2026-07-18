"""Path containment helpers shared by diagnostic rules."""

from __future__ import annotations

from pathlib import Path


def _is_inside_root(root: Path, path: Path) -> bool:
    """Return whether a path resolves inside the collection root.

    Args:
        root: Collection root directory.
        path: Candidate resolved or unresolved path.

    Returns:
        True when the path is inside the collection root.
    """
    return path.resolve(strict=False).is_relative_to(root.resolve())
