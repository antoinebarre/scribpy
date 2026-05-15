"""Application service for documentation linting (FC-04 chain)."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.project_pipeline import (
    ProjectPipelineState,
    run_project_parse_pipeline,
)
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.model import LintResult
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.utils import has_errors


def lint_project(
    root: Path | None = None,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
    registry: ExtensionRegistry | None = None,
) -> LintResult:
    """Load, parse, and lint a Scribpy documentation project."""
    prepared = run_project_parse_pipeline(root, filesystem, parser)
    if prepared.failed or prepared.value is None or has_errors(prepared.diagnostics):
        return LintResult(diagnostics=prepared.diagnostics, failed=True)

    context = _build_lint_context(prepared.value)
    active_registry = registry if registry is not None else ExtensionRegistry.native()
    lint_result = run_lint_rules(context, active_registry.lint_rules)
    diagnostics = (*prepared.diagnostics, *lint_result.diagnostics)
    return LintResult(diagnostics=diagnostics, failed=has_errors(diagnostics))


def _build_lint_context(state: ProjectPipelineState) -> LintContext:
    assert state.project_root is not None
    assert state.config is not None
    assert state.index is not None
    return LintContext(
        source_root=(state.project_root / state.config.paths.source).resolve(),
        documents=state.documents,
        document_index=state.index,
    )


__all__ = ["lint_project"]
