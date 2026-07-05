"""Markdown collection assembly pipeline."""

from scribpy.core.assembly.concatenate import concatenate
from scribpy.core.assembly.image_collector import collect_images
from scribpy.core.assembly.link_rewriter import (
    build_file_slug_map,
    rewrite_internal_links,
)
from scribpy.core.assembly.pipeline import (
    AssembledDocument,
    TransformFn,
    apply_transforms,
)
from scribpy.core.assembly.slug import slugify_heading

__all__ = [
    "AssembledDocument",
    "TransformFn",
    "apply_transforms",
    "build_file_slug_map",
    "collect_images",
    "concatenate",
    "rewrite_internal_links",
    "slugify_heading",
]
