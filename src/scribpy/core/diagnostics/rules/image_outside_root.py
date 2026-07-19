"""Diagnostic rule for local image references outside the collection root."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.diagnostics.rules.image_targets import classify_image_target
from scribpy.core.diagnostics.rules.path_utils import _is_inside_root
from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_image import MarkdownImageReference

IMAGE_OUTSIDE_ROOT = "IMAGE_OUTSIDE_ROOT"


class ImageOutsideRootRule:
    """Detect local image references that resolve outside the collection root.

    A local image path such as ``../../outside/logo.png`` may exist on disk
    yet escape the collection tree, making it impossible to package or publish
    the collection as a self-contained unit.

    Examples:
        Valid Markdown when the image is inside the collection root::

            # Title

            ![Logo](assets/logo.png)

        Invalid Markdown when the image escapes the root::

            # Title

            ![Logo](../../outside/logo.png)
    """

    code = IMAGE_OUTSIDE_ROOT

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return outside-root image diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Error diagnostics for local images that escape the collection root.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            for reference in markdown_file.to_document().image_references
            if (
                diagnostic := _image_outside_root_diagnostic(
                    context.root,
                    markdown_file,
                    reference,
                )
            )
            is not None
        )


def _image_outside_root_diagnostic(
    root: Path,
    markdown_file: MarkdownFile,
    reference: MarkdownImageReference,
) -> CollectionDiagnostic | None:
    """Return an outside-root image diagnostic when needed.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the image reference.
        reference: Markdown image reference to inspect.

    Returns:
        Diagnostic when the image escapes the collection root, or None.
    """
    if reference.target.strip() == "":
        return None
    target = classify_image_target(root, markdown_file, reference)
    if target.is_external or target.resolved_path is None:
        return None
    if _is_inside_root(root, target.resolved_path):
        return None
    return CollectionDiagnostic(
        code=IMAGE_OUTSIDE_ROOT,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Local image must stay inside the collection root: "
            f"{reference.target!r}."
        ),
        path=markdown_file.path,
        line=reference.line,
    )
