"""Utilities shared by image diagnostic rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_image import MarkdownImageReference
from scribpy.core.markdown_patterns import _is_external_target


@dataclass(frozen=True, slots=True)
class ImageTarget:
    """Represent a classified Markdown image target.

    Attributes:
        reference: Markdown image reference found in source text.
        resolved_path: Local filesystem path when the target is local.
        is_external: Whether the target is external to the documentation tree.
    """

    reference: MarkdownImageReference
    resolved_path: Path | None
    is_external: bool


def classify_image_target(
    root: Path,
    markdown_file: MarkdownFile,
    reference: MarkdownImageReference,
) -> ImageTarget:
    """Classify and resolve a Markdown image target.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the image reference.
        reference: Markdown image reference to classify.

    Returns:
        Classified image target.
    """
    if _is_external_target(reference.target):
        return ImageTarget(
            reference=reference,
            resolved_path=None,
            is_external=True,
        )
    return ImageTarget(
        reference=reference,
        resolved_path=_local_image_path(root, markdown_file, reference.target),
        is_external=False,
    )


def _local_image_path(
    root: Path,
    markdown_file: MarkdownFile,
    target: str,
) -> Path:
    """Resolve a local Markdown image target.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the image reference.
        target: Raw Markdown image target.

    Returns:
        Local filesystem path represented by the target.
    """
    parsed = urlsplit(target)
    target_path = Path(unquote(parsed.path))
    if target_path.is_absolute():
        return root / target_path.relative_to("/")
    return markdown_file.path.parent / target_path
