"""Native lint rules for local assets."""

from __future__ import annotations

from scribpy.lint.context import LintContext
from scribpy.lint.resolution import (
    is_external_target,
    resolve_relative_path,
    split_local_target,
    stays_within_source_tree,
)
from scribpy.model import Diagnostic, Document


class MissingLocalAssetRule:
    """Validate that referenced local assets exist on disk."""

    code = "LINT004"

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics for missing local asset files.

        Args:
            context: Shared lint inputs for the current project.

        Returns:
            Diagnostics emitted by the asset rule.
        """
        diagnostics: list[Diagnostic] = []
        for document in context.documents:
            diagnostics.extend(self._lint_document(document, context))
        return tuple(diagnostics)

    def _lint_document(
        self,
        document: Document,
        context: LintContext,
    ) -> tuple[Diagnostic, ...]:
        diagnostics: list[Diagnostic] = []
        for asset in document.assets:
            if is_external_target(asset.target):
                continue
            raw_path, _anchor = split_local_target(asset.target)
            relative_path = resolve_relative_path(document, raw_path)
            asset_path = context.source_root / relative_path
            if stays_within_source_tree(relative_path) and asset_path.is_file():
                continue
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code=self.code,
                    message="Referenced local asset does not exist.",
                    path=document.relative_path,
                    line=asset.line,
                    hint=f"Check the asset path: {asset.target}",
                )
            )
        return tuple(diagnostics)


__all__ = ["MissingLocalAssetRule"]
