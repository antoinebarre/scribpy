"""scribpy.report — programmatic GFM report generator."""

from .assets import AssetRenderer, MatplotlibRenderer
from .errors import InvalidChildError, InvalidTableError, ReportDepthError
from .nodes import (
    BlockQuote,
    BulletList,
    Chapter,
    CodeBlock,
    FigureAsset,
    HorizontalRule,
    Image,
    ImageFile,
    LineBreak,
    Metadata,
    NumberedList,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
)

__all__ = [
    # Metadata
    "Metadata",
    # Containers
    "Report",
    "Chapter",
    "Section",
    # Block leaves
    "Paragraph",
    "CodeBlock",
    "Table",
    "BulletList",
    "NumberedList",
    "BlockQuote",
    "HorizontalRule",
    # Inline leaves
    "Text",
    "LineBreak",
    # Media
    "Image",
    "ImageFile",
    "FigureAsset",
    # Asset renderers
    "AssetRenderer",
    "MatplotlibRenderer",
    # Errors
    "ReportDepthError",
    "InvalidChildError",
    "InvalidTableError",
]
