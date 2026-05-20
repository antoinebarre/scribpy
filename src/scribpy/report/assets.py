"""Report asset rendering and image-copy public facade."""

from __future__ import annotations

from scribpy.report.asset_protocols import AssetRenderer, SavableFigure
from scribpy.report.image_files import copy_image_file
from scribpy.report.matplotlib import MatplotlibRenderer

_SavableFigure = SavableFigure

__all__ = [
    "AssetRenderer",
    "MatplotlibRenderer",
    "_SavableFigure",
    "copy_image_file",
]
