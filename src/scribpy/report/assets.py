"""Asset renderer protocol, built-in implementations, and image file helpers.

Two kinds of media nodes exist:

- ``FigureAsset`` — produced programmatically by an ``AssetRenderer``
  (e.g. a matplotlib chart).  The renderer writes the file itself.
- ``ImageFile`` — a user-supplied image file that must be *copied* into
  the report output directory so the Markdown document is self-contained.

The ``collect_and_copy_images`` helper handles the copy step during
``save_report``.
"""

from __future__ import annotations

import shutil
from pathlib import Path
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


class _SavableFigure(Protocol):
    """Structural protocol for objects that expose ``savefig``."""

    def savefig(self, fname: str, *, dpi: int, bbox_inches: str) -> None:
        """Save the figure to a file.

        Args:
            fname: Output file path.
            dpi: Resolution in dots per inch.
            bbox_inches: Bounding-box mode (e.g. ``"tight"``).
        """
        ...


class MatplotlibRenderer:
    """Render a ``matplotlib`` Figure to a PNG file.

    Attributes:
        figure: Any object exposing a ``savefig`` method (e.g.
            ``matplotlib.figure.Figure``).
        dpi: Image resolution in dots per inch (default 150).
    """

    def __init__(self, figure: _SavableFigure, *, dpi: int = 150) -> None:
        """Initialise with a savable figure.

        Args:
            figure: An object implementing ``savefig`` (typically a
                ``matplotlib.figure.Figure``).
            dpi: Image resolution in dots per inch.
        """
        self._figure = figure
        self._dpi = dpi

    def render(self, output_path: str) -> str:
        """Save the figure as a PNG file.

        Args:
            output_path: Destination file path (should end with ``.png``).

        Returns:
            The ``output_path`` string, for embedding in Markdown.
        """
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        self._figure.savefig(str(dest), dpi=self._dpi, bbox_inches="tight")
        return output_path


def copy_image_file(source_path: str, assets_dir: Path) -> str:
    """Copy a user-supplied image into the report assets directory.

    The file is copied to ``assets_dir / <filename>``.  If a file with
    the same name already exists it is overwritten.

    Args:
        source_path: Path to the original image file.
        assets_dir: Destination directory (created if it does not exist).

    Returns:
        A POSIX-style relative path string suitable for GFM embedding
        (e.g. ``"assets/photo.png"``).

    Raises:
        FileNotFoundError: If ``source_path`` does not exist.
    """
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(f"ImageFile source not found: {source_path}")
    assets_dir.mkdir(parents=True, exist_ok=True)
    dest = assets_dir / src.name
    shutil.copy2(src, dest)
    return (Path("assets") / src.name).as_posix()
