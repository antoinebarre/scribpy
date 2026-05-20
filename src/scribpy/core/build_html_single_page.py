"""Single-page HTML build phases."""

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
    write_single_page_support_artifacts,
)
from scribpy.builders.markdown import merge_documents
from scribpy.config.types import HtmlBuilderConfig
from scribpy.core.build_html_shared import (
    custom_html_transforms,
    render_code_blocks,
    transform_options,
)
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.model import (
    BuildArtifact,
    BuildResult,
    Diagnostic,
    TransformedDocument,
)
from scribpy.model.protocols import CodeBlockPlugin
from scribpy.transforms import apply_transforms
from scribpy.utils import has_errors


def build_single_page(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
    plugins: tuple[CodeBlockPlugin, ...],
) -> BuildResult:
    """Orchestrate the three phases of a single-page HTML build.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        html_config: HTML builder configuration.
        registry: Extension registry for transforms and plugins.
        plugins: Diagram rendering plugins to apply.

    Returns:
        Build result with all produced artifacts and diagnostics.
    """
    abs_output = state.project_root / html_config.resolve_output_dir()
    source_root = (state.project_root / state.config.paths.source).resolve()

    rendered_docs, diagram_artifacts, diagnostics = _transform_phase(
        state, diagnostics, html_config, registry, plugins, abs_output
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    full_html, css_artifacts, diagnostics = _assemble_phase(
        state, diagnostics, html_config, rendered_docs, source_root, abs_output
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    support_artifacts, asset_artifacts, diagnostics = _write_phase(
        state, diagnostics, html_config, full_html, source_root, abs_output
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    return BuildResult(
        success=True,
        artifacts=(
            *support_artifacts,
            *css_artifacts,
            *asset_artifacts,
            *diagram_artifacts,
        ),
        diagnostics=diagnostics,
    )


def _transform_phase(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
    plugins: tuple[CodeBlockPlugin, ...],
    abs_output: Path,
) -> tuple[
    tuple[TransformedDocument, ...],
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Apply Markdown transforms then render fenced-code-block diagrams.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        html_config: HTML builder configuration.
        registry: Extension registry for transforms.
        plugins: Code-block plugins to apply.
        abs_output: Absolute output directory.

    Returns:
        Rendered documents, diagram artifacts, and accumulated diagnostics.
    """
    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=(
            *custom_html_transforms(registry),
            *registry.markdown_transforms,
        ),
        options=transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return (), (), diagnostics
    return render_code_blocks(
        transform_result.documents,
        diagnostics,
        plugins,
        abs_output / "assets",
        flattened=True,
        target="html",
    )


def _assemble_phase(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    rendered_docs: tuple[TransformedDocument, ...],
    source_root: Path,
    abs_output: Path,
) -> tuple[str, tuple[BuildArtifact, ...], tuple[Diagnostic, ...]]:
    """Rewrite asset links, merge documents, render to HTML, copy CSS.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        html_config: HTML builder configuration.
        rendered_docs: Documents after diagram rendering.
        source_root: Absolute source root directory.
        abs_output: Absolute output directory.

    Returns:
        Full HTML string, CSS artifacts, and accumulated diagnostics.
    """
    css_artifacts, css_diags, css_hrefs = copy_css_files_single_page(
        state.project_root, html_config.css_files, abs_output, state.filesystem
    )
    diagnostics = (*diagnostics, *css_diags)
    if has_errors(diagnostics):
        return "", css_artifacts, diagnostics

    rewritten = rewrite_asset_links_single_page(rendered_docs, source_root)
    assembled = merge_documents(rewritten)
    body_html = render_markdown_to_html(assembled.content)
    title = (
        state.config.document.title or state.config.project.name or "Document"
    )
    full_html = build_single_page_html(body_html, title, css_hrefs)
    return full_html, css_artifacts, diagnostics


def _write_phase(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    full_html: str,
    source_root: Path,
    abs_output: Path,
) -> tuple[
    tuple[BuildArtifact, ...],
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Write HTML + JS to disk then copy source assets.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        html_config: HTML builder configuration.
        full_html: Complete HTML document string.
        source_root: Absolute source root directory.
        abs_output: Absolute output directory.

    Returns:
        Support artifacts, asset artifacts, and accumulated diagnostics.
    """
    support_artifacts, support_diags = write_single_page_support_artifacts(
        state.project_root,
        full_html,
        html_config.resolve_output_dir(),
        state.filesystem,
    )
    diagnostics = (*diagnostics, *support_diags)
    if has_errors(diagnostics):
        return support_artifacts, (), diagnostics

    asset_paths = collect_asset_paths(state.documents, source_root)
    asset_artifacts, asset_diags = copy_assets(
        asset_paths, source_root, abs_output / "assets", state.filesystem
    )
    diagnostics = (*diagnostics, *asset_diags)
    return support_artifacts, asset_artifacts, diagnostics


__all__ = ["build_single_page"]
