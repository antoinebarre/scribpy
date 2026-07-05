"""Collection diagnostic rule registry imports."""

from scribpy.core.diagnostics.rules.external_image_reference import (
    EXTERNAL_IMAGE_REFERENCE,
    ExternalImageReferenceRule,
)
from scribpy.core.diagnostics.rules.heading_level_overflow import (
    HEADING_LEVEL_OVERFLOW,
    HeadingLevelOverflowRule,
)
from scribpy.core.diagnostics.rules.image_outside_root import (
    IMAGE_OUTSIDE_ROOT,
    ImageOutsideRootRule,
)
from scribpy.core.diagnostics.rules.internal_markdown_link import (
    INTERNAL_MARKDOWN_LINK_MISSING,
    INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT,
    INTERNAL_MARKDOWN_LINK_RULE,
    InternalMarkdownLinkRule,
)
from scribpy.core.diagnostics.rules.local_anchor_link import (
    LOCAL_ANCHOR_LINK,
    LocalAnchorLinkRule,
)
from scribpy.core.diagnostics.rules.local_image_missing import (
    LOCAL_IMAGE_MISSING,
    LocalImageMissingRule,
)
from scribpy.core.diagnostics.rules.source_first_heading_h1 import (
    SOURCE_FIRST_HEADING_NOT_H1,
    SourceFirstHeadingH1Rule,
)
from scribpy.core.diagnostics.rules.source_h1_count import (
    SOURCE_H1_COUNT_INVALID,
    SourceH1CountRule,
)

__all__ = [
    "EXTERNAL_IMAGE_REFERENCE",
    "HEADING_LEVEL_OVERFLOW",
    "IMAGE_OUTSIDE_ROOT",
    "INTERNAL_MARKDOWN_LINK_MISSING",
    "INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT",
    "INTERNAL_MARKDOWN_LINK_RULE",
    "LOCAL_ANCHOR_LINK",
    "LOCAL_IMAGE_MISSING",
    "SOURCE_FIRST_HEADING_NOT_H1",
    "SOURCE_H1_COUNT_INVALID",
    "ExternalImageReferenceRule",
    "HeadingLevelOverflowRule",
    "ImageOutsideRootRule",
    "InternalMarkdownLinkRule",
    "LocalAnchorLinkRule",
    "LocalImageMissingRule",
    "SourceFirstHeadingH1Rule",
    "SourceH1CountRule",
]
