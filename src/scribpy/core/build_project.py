"""Application service for build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.builders import merge_documents, write_markdown_artifact
from scribpy.core.project_pipeline import (
    ProjectPipelineState,
    run_project_parse_pipeline,
)
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.model import BuildResult, Diagnostic
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.transforms import apply_transforms
from scribpy.utils import has_errors


def build_project(
    root: Path | None = None,
    *,
    target: str = "markdown",
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
    registry: ExtensionRegistry | None = None,
) -> BuildResult:
    """Build a Scribpy project for one target.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        target: Requested build target. Phase 5 supports ``"markdown"`` only.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.
        registry: Optional lint rule registry override.

    Returns:
        Build artifacts plus diagnostics produced by the chain.
    """
    if target != "markdown":
        return BuildResult(
            success=False,
            artifacts=(),
            diagnostics=(_unsupported_target_diagnostic(target),),
        )

    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked_build(diagnostics)

    active_registry = registry if registry is not None else ExtensionRegistry.native()
    diagnostics = _lint_state(state, diagnostics, active_registry)
    if has_errors(diagnostics):
        return _blocked_build(diagnostics)

    return _write_markdown_build(state, diagnostics, active_registry)


def _prepare_build_state(
    root: Path | None,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
) -> tuple[ProjectPipelineState | None, tuple[Diagnostic, ...]]:
    prepared = run_project_parse_pipeline(root, filesystem, parser)
    if prepared.failed or prepared.value is None or has_errors(prepared.diagnostics):
        return None, prepared.diagnostics
    return prepared.value, prepared.diagnostics


def _lint_state(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> tuple[Diagnostic, ...]:
    assert state.project_root is not None
    assert state.config is not None
    assert state.index is not None
    context = LintContext(
        source_root=(state.project_root / state.config.paths.source).resolve(),
        documents=state.documents,
        document_index=state.index,
    )
    lint_result = run_lint_rules(context, registry.lint_rules)
    return (*diagnostics, *lint_result.diagnostics)


def _write_markdown_build(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> BuildResult:
    assert state.project_root is not None
    assert state.config is not None
    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=registry.markdown_transforms,
        document_title=state.config.project.name or "Document",
    )
    transformed_diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(transformed_diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=transformed_diagnostics
        )
    assembled = merge_documents(transform_result.documents)
    artifact, write_diagnostics = write_markdown_artifact(
        state.project_root,
        assembled,
        state.filesystem,
    )
    final_diagnostics = (*transformed_diagnostics, *write_diagnostics)
    if artifact is None or has_errors(final_diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=final_diagnostics)
    return BuildResult(
        success=True, artifacts=(artifact,), diagnostics=final_diagnostics
    )


def _unsupported_target_diagnostic(target: str) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="BLD001",
        message=f"Unsupported build target: {target}",
        hint="Use target='markdown' until additional builders are implemented.",
    )


def _blocked_build(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    return BuildResult(
        success=False,
        artifacts=(),
        diagnostics=(*diagnostics, _blocked_build_diagnostic()),
    )


def _blocked_build_diagnostic() -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="BLD002",
        message="Build stopped because blocking diagnostics were reported upstream.",
        hint="Resolve project, parse, or lint errors before building.",
    )


__all__ = ["build_project"]
