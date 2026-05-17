"""Application service for HTML build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets import (
    collect_asset_paths,
    copy_assets,
    copy_css_files_single_page,
    rewrite_asset_links_single_page,
)
from scribpy.builders.html_single_page import (
    build_single_page_html,
    render_markdown_to_html,
    write_single_page_artifact,
)
from scribpy.builders.html_site import run_mkdocs_build, write_site_artifacts_with_css
from scribpy.builders.markdown import merge_documents
from scribpy.config.types import HtmlBuilderConfig
from scribpy.core.project_pipeline import ProjectPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.model import BuildResult, Diagnostic
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.transforms import Transform, TransformOptions, apply_transforms
from scribpy.transforms.pipeline import native_html_transforms
from scribpy.utils import has_errors


def build_html_project(
    root: Path | None,
    *,
    html_config: HtmlBuilderConfig,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
    registry: ExtensionRegistry | None,
) -> BuildResult:
    """Build HTML output for one mode.

    Args:
        root: Project root path or ``None`` for cwd.
        html_config: HTML builder configuration including mode and CSS.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.
        registry: Optional extension registry override.

    Returns:
        Build result with artifacts and diagnostics.
    """
    from scribpy.core.build_project import _prepare_build_state

    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked(diagnostics)

    active_registry = registry if registry is not None else ExtensionRegistry.native()
    diagnostics = _lint(state, diagnostics, active_registry)
    if has_errors(diagnostics):
        return _blocked(diagnostics)

    if html_config.mode == "single-page":
        return _build_single_page(state, diagnostics, html_config, active_registry)
    return _build_site(state, diagnostics, html_config, active_registry)


def _lint(
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


def _build_single_page(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
) -> BuildResult:
    assert state.project_root is not None
    assert state.config is not None

    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=(*_custom_html_transforms(registry), *registry.markdown_transforms),
        options=_transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    abs_output = state.project_root / html_config.resolve_output_dir()
    css_artifacts, css_diags, css_hrefs = copy_css_files_single_page(
        state.project_root, html_config.css_files, abs_output, state.filesystem
    )
    diagnostics = (*diagnostics, *css_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    source_root = (state.project_root / state.config.paths.source).resolve()
    rewritten_documents = rewrite_asset_links_single_page(
        transform_result.documents,
        source_root,
    )
    assembled = merge_documents(rewritten_documents)
    body_html = render_markdown_to_html(assembled.content)
    title = state.config.document.title or state.config.project.name or "Document"
    full_html = build_single_page_html(body_html, title, css_hrefs)

    artifact, write_diags = write_single_page_artifact(
        state.project_root,
        full_html,
        html_config.resolve_output_dir(),
        state.filesystem,
    )
    diagnostics = (*diagnostics, *write_diags)
    if artifact is None or has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    asset_paths = collect_asset_paths(state.documents, source_root)
    assets_dir = abs_output / "assets"
    asset_artifacts, asset_diags = copy_assets(
        asset_paths, source_root, assets_dir, state.filesystem
    )
    diagnostics = (*diagnostics, *asset_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    return BuildResult(
        success=True,
        artifacts=(artifact, *css_artifacts, *asset_artifacts),
        diagnostics=diagnostics,
    )


def _build_site(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
) -> BuildResult:
    assert state.project_root is not None
    assert state.config is not None

    transform_result = apply_transforms(
        state.documents,
        target="html",
        transforms=_custom_html_transforms(registry),
        options=_transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    site_name = html_config.site_name or state.config.project.name or "Documentation"
    artifacts, site_diags = write_site_artifacts_with_css(
        state.project_root,
        transform_result.documents,
        site_name,
        html_config.resolve_output_dir(),
        html_config.css_files,
        state.filesystem,
        theme=html_config.theme,
    )
    diagnostics = (*diagnostics, *site_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    source_root = (state.project_root / state.config.paths.source).resolve()
    asset_paths = collect_asset_paths(state.documents, source_root)
    docs_dir = state.project_root / html_config.resolve_output_dir() / "docs"
    asset_artifacts, asset_diags = copy_assets(
        asset_paths, source_root, docs_dir, state.filesystem
    )
    diagnostics = (*diagnostics, *asset_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    rendered_site, mkdocs_diags = run_mkdocs_build(
        state.project_root,
        html_config.resolve_output_dir(),
    )
    diagnostics = (*diagnostics, *mkdocs_diags)
    if rendered_site is None or has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    return BuildResult(
        success=True,
        artifacts=(*artifacts, *asset_artifacts, rendered_site),
        diagnostics=diagnostics,
    )


def _transform_options(state: ProjectPipelineState) -> TransformOptions:
    assert state.config is not None
    return TransformOptions(
        document_title=state.config.document.title
        or state.config.project.name
        or "Document",
        toc_enabled=state.config.document.toc.enabled,
        toc_max_level=state.config.document.toc.max_level,
        toc_style=state.config.document.toc.style,
        numbering_enabled=state.config.document.numbering.enabled,
        numbering_max_level=state.config.document.numbering.max_level,
        numbering_style=state.config.document.numbering.style,
    )


def _custom_html_transforms(registry: ExtensionRegistry) -> tuple[Transform, ...]:
    native = native_html_transforms()
    return tuple(
        transform for transform in registry.html_transforms if transform not in native
    )


def _blocked(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    return BuildResult(
        success=False,
        artifacts=(),
        diagnostics=(
            *diagnostics,
            Diagnostic(
                severity="error",
                code="BLD002",
                message=(
                    "Build stopped because blocking diagnostics were reported upstream."
                ),
                hint="Resolve project, parse, or lint errors before building.",
            ),
        ),
    )


__all__ = ["build_html_project"]
