"""Image reference resolution and existence verification.

Checks that every image referenced in a :class:`ParsedDocument` exists
on the filesystem.  Missing images are collected as warnings without
interrupting the processing of valid images (REQ-004, REQ-018).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from scribpy.core.document import ImageRef, ParsedDocument

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageWarning:
    """A warning about a missing image reference.

    Attributes:
        src: The image source path that could not be resolved.
        message: Human-readable description of the problem.
    """

    src: str
    message: str


@dataclass(frozen=True)
class ResolvedImages:
    """Result of image resolution for a document.

    Attributes:
        valid: Image references whose source files exist.
        warnings: Warnings for images that could not be found.
    """

    valid: tuple[ImageRef, ...]
    warnings: tuple[ImageWarning, ...]


def resolve_images(
    document: ParsedDocument,
    base_dir: Path,
) -> ResolvedImages:
    """Verify existence of all image references in a document.

    Each image ``src`` is resolved relative to *base_dir*.  Missing
    images produce a warning but do not interrupt processing of
    remaining images (REQ-018).

    Args:
        document: The parsed document containing image references.
        base_dir: Directory against which relative image paths are
            resolved.

    Returns:
        A :class:`ResolvedImages` with valid refs and warnings.
    """
    valid: list[ImageRef] = []
    warnings: list[ImageWarning] = []

    for img in document.images:
        resolved_path = base_dir / img.src
        if resolved_path.is_file():
            valid.append(img)
            _log.debug("Image found: %s", resolved_path)
        else:
            warning = ImageWarning(
                src=img.src,
                message=f"Image not found: {resolved_path}",
            )
            warnings.append(warning)
            _log.warning("Image not found: %s", resolved_path)

    return ResolvedImages(
        valid=tuple(valid),
        warnings=tuple(warnings),
    )
