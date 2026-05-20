"""Helpers for classifying asset reference targets."""

from __future__ import annotations


def is_external(path: str) -> bool:
    """Return whether an asset target points outside the local project.

    Args:
        path: Asset target or path-like string.

    Returns:
        ``True`` when the target is remote or otherwise external.
    """
    return path.startswith(("http://", "https://", "//", "mailto:"))


__all__ = ["is_external"]
