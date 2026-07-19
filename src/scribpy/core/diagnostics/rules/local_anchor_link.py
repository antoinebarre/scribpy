"""Diagnostic rule for local anchor links."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.core.diagnostics.model import (
    CollectionDiagnostic,
    CollectionDiagnosticContext,
    DiagnosticSeverity,
)
from scribpy.core.diagnostics.rules.markdown_link_targets import (
    MarkdownLinkReference,
    extract_markdown_links,
)
from scribpy.core.markdown_file import MarkdownFile

LOCAL_ANCHOR_LINK = "LOCAL_ANCHOR_LINK"


class LocalAnchorLinkRule:
    """Detect any link containing an anchor fragment.

    Anchor fragments such as ``#section`` are forbidden in collection source
    files whether they appear alone (``#section``) or appended to a file path
    (``other_file.md#section``).  After assembly all source files are merged
    into one document; anchor ids in the assembled output must be managed by
    the assembly pipeline, not written by hand in source files.

    Examples:
        Invalid anchor-only link::

            [See Section](#section)

        Invalid cross-file link with anchor::

            [See Section](other_file.md#section)
    """

    code = LOCAL_ANCHOR_LINK

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return anchor link diagnostics for every link containing ``#``.

        Args:
            context: Collection diagnostic context.

        Returns:
            Error diagnostics for every link whose target contains ``#``.
        """
        return tuple(
            _anchor_link_diagnostic(markdown_file, link)
            for markdown_file in context.files
            for link in extract_markdown_links(markdown_file.content)
            if "#" in link.target
        )


def _anchor_link_diagnostic(
    markdown_file: MarkdownFile,
    reference: MarkdownLinkReference,
) -> CollectionDiagnostic:
    """Return one local anchor link diagnostic.

    Args:
        markdown_file: Markdown file containing the anchor link.
        reference: Markdown link reference to report.

    Returns:
        Error diagnostic for the anchor-only link.
    """
    return CollectionDiagnostic(
        code=LOCAL_ANCHOR_LINK,
        severity=DiagnosticSeverity.ERROR,
        message=(
            "Anchor fragments are forbidden in collection source files; "
            "anchors in the assembled document are managed by the assembly "
            f"pipeline: {reference.target!r}."
        ),
        path=markdown_file.path,
        line=reference.line,
    )
