"""Functional pipeline for Markdown document assembly transforms."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

TransformFn = Callable[["AssembledDocument"], "AssembledDocument"]

_log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AssembledDocument:
    """Hold the in-progress state of a Markdown document being assembled.

    Attributes:
        content: Current Markdown source text.
        source_root: Collection root directory used for path resolution.
        output: Destination file path for the assembled document.
    """

    content: str
    source_root: Path
    output: Path

    def with_content(self, content: str) -> AssembledDocument:
        """Return a copy with replaced Markdown source text.

        Args:
            content: Replacement Markdown source text.

        Returns:
            Assembled document with updated content.
        """
        return AssembledDocument(
            content=content,
            source_root=self.source_root,
            output=self.output,
        )


def apply_transforms(
    doc: AssembledDocument,
    transforms: tuple[TransformFn, ...],
) -> AssembledDocument:
    """Apply a sequence of transform functions to an assembled document.

    Each transform receives the document produced by the previous one and
    returns a new document.  The pipeline is applied left-to-right.

    Args:
        doc: Initial assembled document.
        transforms: Ordered transform functions to apply.

    Returns:
        Final assembled document after all transforms have been applied.
    """
    for transform in transforms:
        _log.debug("Pipeline step: %s", transform.__name__)
        doc = transform(doc)
        _log.debug(
            "Pipeline step done: %s (%d chars)",
            transform.__name__,
            len(doc.content),
        )
    return doc
