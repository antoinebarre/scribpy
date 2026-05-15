"""Native lint rules for local links and assets."""

from __future__ import annotations

from pathlib import Path

from scribpy.lint.context import LintContext
from scribpy.lint.resolution import (
    is_external_target,
    resolve_relative_path,
    split_local_target,
    stays_within_source_tree,
)
from scribpy.model import Diagnostic, Document


class BrokenInternalLinkRule:
    """Validate local Markdown links and heading anchors."""

    code = "LINT003"

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics for unresolved local links or anchors."""
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
        diagnostics: list[Diagnostic] = []
        for reference in document.links:
            if is_external_target(reference.target):
                continue

            raw_path, anchor = split_local_target(reference.target)
            target_document = self._target_document(document, raw_path, documents)
            if target_document is None:
                diagnostics.append(
                    _missing_link_target(document, reference.target, reference.line)
                )
            elif anchor is not None and not _has_anchor(target_document, anchor):
                diagnostics.append(_missing_anchor(document, anchor, reference.line))
        return tuple(diagnostics)

    def _target_document(
        self,
        document: Document,
        raw_path: str,
        documents: dict[Path, Document],
    ) -> Document | None:
        if raw_path == "":
            return document
        relative_path = resolve_relative_path(document, raw_path)
        if not stays_within_source_tree(relative_path):
            return None
        return documents.get(relative_path)


def _missing_link_target(
    document: Document,
    target: str,
    line: int | None,
) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="LINT003",
        message="Internal link target does not exist.",
        path=document.relative_path,
        line=line,
        hint=f"Check the target path: {target}",
    )


def _missing_anchor(document: Document, anchor: str, line: int | None) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="LINT003",
        message="Internal link anchor does not exist.",
        path=document.relative_path,
        line=line,
        hint=f"Check the target anchor: #{anchor}",
    )


def _has_anchor(document: Document, anchor: str) -> bool:
    return any(heading.anchor == anchor for heading in document.headings)


__all__ = ["BrokenInternalLinkRule"]
