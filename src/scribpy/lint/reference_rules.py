"""Native lint rule for local links and heading anchors."""

from __future__ import annotations

from pathlib import Path

from scribpy.lint.context import LintContext
from scribpy.lint.reference_diagnostics import (
    missing_anchor,
    missing_link_target,
)
from scribpy.lint.reference_targets import has_anchor, target_document
from scribpy.lint.resolution import is_external_target, split_local_target
from scribpy.model import Diagnostic, Document


class BrokenInternalLinkRule:
    """Validate local Markdown links and heading anchors."""

    code = "LINT003"

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics for unresolved local links or anchors.

        Args:
            context: Shared lint inputs for the current project.

        Returns:
            Diagnostics emitted by the internal-link rule.
        """
        documents = context.documents_by_path
        diagnostics: list[Diagnostic] = []
        for document in context.documents:
            diagnostics.extend(self._lint_document(document, documents))
        return tuple(diagnostics)

    def _lint_document(
        self,
        document: Document,
        documents: dict[Path, Document],
    ) -> tuple[Diagnostic, ...]:
        """Return diagnostics for one document's internal links."""
        diagnostics: list[Diagnostic] = []
        for reference in document.links:
            if is_external_target(reference.target):
                continue

            raw_path, anchor = split_local_target(reference.target)
            target = target_document(document, raw_path, documents)
            if target is None:
                diagnostics.append(
                    missing_link_target(
                        document, reference.target, reference.line
                    )
                )
            elif anchor is not None and not has_anchor(target, anchor):
                diagnostics.append(
                    missing_anchor(document, anchor, reference.line)
                )
        return tuple(diagnostics)


__all__ = ["BrokenInternalLinkRule"]
