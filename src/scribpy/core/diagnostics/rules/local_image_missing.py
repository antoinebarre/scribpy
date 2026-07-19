"""Diagnostic rule for missing local Markdown images."""

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

LOCAL_IMAGE_MISSING = "LOCAL_IMAGE_MISSING"


class LocalImageMissingRule:
    """Detect local Markdown image references whose files do not exist.

    Examples:
        Valid Markdown when ``assets/logo.png`` exists next to the document::

            # Title

            ![Logo](assets/logo.png)

        Invalid Markdown when ``assets/missing.png`` does not exist::

            # Title

            ![Missing](assets/missing.png)
    """

    code = LOCAL_IMAGE_MISSING

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return missing local image diagnostics.

        Args:
            context: Collection diagnostic context.

        Returns:
            Diagnostics for local image references whose file is missing.
        """
        return tuple(
            diagnostic
            for markdown_file in context.files
            for reference in markdown_file.to_document().image_references
            if (
                diagnostic := _missing_local_image_diagnostic(
                    context,
                    markdown_file,
                    reference,
                )
            )
            is not None
        )


def _missing_local_image_diagnostic(
    context: CollectionDiagnosticContext,
    markdown_file: MarkdownFile,
    reference: MarkdownImageReference,
) -> CollectionDiagnostic | None:
    """Return a missing local image diagnostic when needed.

    Args:
        context: Collection diagnostic context.
        markdown_file: Markdown file containing the image reference.
        reference: Markdown image reference to inspect.

    Returns:
        Diagnostic when the local image file is missing, or None.
    """
    if reference.target.strip() == "":
        return _local_image_missing_diagnostic(markdown_file, reference)
    target = classify_image_target(context.root, markdown_file, reference)
    if target.is_external or target.resolved_path is None:
        return None
    if target.resolved_path.exists():
        return None
    return _local_image_missing_diagnostic(markdown_file, reference)


def _local_image_missing_diagnostic(
    markdown_file: MarkdownFile,
    reference: MarkdownImageReference,
) -> CollectionDiagnostic:
    """Return one missing local image diagnostic.

    Args:
        markdown_file: Markdown file containing the image reference.
        reference: Markdown image reference to report.

    Returns:
        Missing local image diagnostic.
    """
    return CollectionDiagnostic(
        code=LOCAL_IMAGE_MISSING,
        severity=DiagnosticSeverity.ERROR,
        message=f"Local image file does not exist: {reference.target!r}.",
        path=markdown_file.path,
        line=reference.line,
    )
