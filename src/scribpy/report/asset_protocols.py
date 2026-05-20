"""Protocols for report media renderers."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class AssetRenderer(Protocol):
    """Protocol for objects that can render a figure to a file.

    Implementors must produce a file at the given path and return the
    relative path string to embed in Markdown.
    """

    def render(self, output_path: str) -> str:
        """Render the figure and save it to ``output_path``.

        Args:
            output_path: Absolute or relative destination file path.

        Returns:
            The path string to embed in a GFM ``![alt](path)`` link.
            This is typically ``output_path`` itself or a relative variant.
        """
        ...


class SavableFigure(Protocol):
    """Structural protocol for objects that expose ``savefig``."""

    def savefig(self, fname: str, *, dpi: int, bbox_inches: str) -> None:
        """Save the figure to a file.

        Args:
            fname: Output file path.
            dpi: Resolution in dots per inch.
            bbox_inches: Bounding-box mode such as ``"tight"``.
        """
        ...


__all__ = ["AssetRenderer", "SavableFigure"]
