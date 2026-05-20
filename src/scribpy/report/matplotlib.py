"""Matplotlib-backed report asset renderer."""

from __future__ import annotations

from pathlib import Path

from scribpy.report.asset_protocols import SavableFigure


class MatplotlibRenderer:
    """Render a ``matplotlib`` Figure to a PNG file.

    Attributes:
        figure: Any object exposing a ``savefig`` method.
        dpi: Image resolution in dots per inch.
    """

    def __init__(self, figure: SavableFigure, *, dpi: int = 150) -> None:
        """Initialise with a savable figure.

        Args:
            figure: An object implementing ``savefig``.
            dpi: Image resolution in dots per inch.
        """
        self._figure = figure
        self._dpi = dpi

    def render(self, output_path: str) -> str:
        """Save the figure as a PNG file.

        Args:
            output_path: Destination file path, usually ending with ``.png``.

        Returns:
            The ``output_path`` string for embedding in Markdown.
        """
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._figure.savefig(str(dest), dpi=self._dpi, bbox_inches="tight")
        return output_path


__all__ = ["MatplotlibRenderer"]
