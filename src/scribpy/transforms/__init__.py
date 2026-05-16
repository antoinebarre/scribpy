"""Document transformation pipeline for target-ready outputs."""

from scribpy.transforms.markdown import (
    apply_section_numbering,
    generate_toc_transform,
    normalize_assembled_markdown_headings,
    resolve_cross_references,
    rewrite_links_for_target,
)
from scribpy.transforms.pipeline import (
    apply_transforms,
    native_html_transforms,
    native_markdown_transforms,
)
from scribpy.transforms.types import (
    BuildTarget,
    Transform,
    TransformContext,
    TransformResult,
)

__all__ = [
    "BuildTarget",
    "Transform",
    "TransformContext",
    "TransformResult",
    "apply_section_numbering",
    "apply_transforms",
    "generate_toc_transform",
    "normalize_assembled_markdown_headings",
    "native_html_transforms",
    "native_markdown_transforms",
    "resolve_cross_references",
    "rewrite_links_for_target",
]
