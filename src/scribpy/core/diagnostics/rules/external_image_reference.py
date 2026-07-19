"""Diagnostic rule for external Markdown images."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.diagnostics.rules.image_targets import classify_image_target
from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_image import MarkdownImageReference

EXTERNAL_IMAGE_REFERENCE = "EXTERNAL_IMAGE_REFERENCE"


class ExternalImageReferenceRule:
    """Detect Markdown image references that target external resources.

    Examples:
        Valid Markdown when images are local and can be packaged::

            # Title

            ![Logo](assets/logo.png)

        Diagnostic Markdown when the image depends on a remote URL::

            # Title

            ![Remote logo](https://example.com/logo.png)
    """

    code = EXTERNAL_IMAGE_REFERENCE

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return external image diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Warning diagnostics for external image references.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            for reference in markdown_file.to_document().image_references
            if (
                diagnostic := _external_image_diagnostic(
                    context,
                    markdown_file,
                    reference,
                )
            )
            is not None
        )


def _external_image_diagnostic(
    context: CollectionDiagnosticContext,
    markdown_file: MarkdownFile,
    reference: MarkdownImageReference,
) -> CollectionDiagnostic | None:
    """Return an external image diagnostic when needed.

    Args:
        context: Collection diagnostic context.
        markdown_file: Markdown file containing the image reference.
        reference: Markdown image reference to inspect.

    Returns:
        Diagnostic when the image target is external, or None.
    """
    target = classify_image_target(context.root, markdown_file, reference)
    if not target.is_external:
        return None
    return CollectionDiagnostic(
        code=EXTERNAL_IMAGE_REFERENCE,
        severity=DiagnosticSeverity.WARNING,
        message=(
            "External image reference is not fetched by core diagnostics: "
            f"{reference.target!r}."
        ),
        path=markdown_file.path,
        line=reference.line,
    )
