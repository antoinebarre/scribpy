"""MkDocs site HTML build phases."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.assets import collect_asset_paths, copy_assets
from scribpy.builders.html_site import (
    run_mkdocs_build,
    write_site_artifacts_with_css,
)
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


@dataclass(frozen=True)
class _SiteBuildContext:
    """Intermediate products produced during the site build phase."""

    state: ResolvedPipelineState
    html_config: HtmlBuilderConfig
    rendered_documents: tuple[TransformedDocument, ...]
    diagram_artifacts: tuple[BuildArtifact, ...]
    site_name: str
    docs_dir: Path


def build_site(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
    plugins: tuple[CodeBlockPlugin, ...],
) -> BuildResult:
    """Transform documents and render diagrams for a MkDocs site build.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        html_config: HTML builder configuration.
        registry: Extension registry for transforms and plugins.
        plugins: Diagram rendering plugins to apply.

    Returns:
        Build result with all produced artifacts and diagnostics.
    """
    transform_result = apply_transforms(
        state.documents,
        target="html",
        transforms=custom_html_transforms(registry),
        options=transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    docs_dir = state.project_root / html_config.resolve_output_dir() / "docs"
    rendered_documents, diagram_artifacts, diagnostics = render_code_blocks(
        transform_result.documents,
        diagnostics,
        plugins,
        docs_dir / "assets",
        flattened=False,
        target="html-site",
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    ctx = _SiteBuildContext(
        state=state,
        html_config=html_config,
        rendered_documents=rendered_documents,
        diagram_artifacts=diagram_artifacts,
        site_name=html_config.site_name
        or state.config.project.name
        or "Documentation",
        docs_dir=docs_dir,
    )
    return _materialize_site(ctx, diagnostics)


def _materialize_site(
    ctx: _SiteBuildContext,
    diagnostics: tuple[Diagnostic, ...],
) -> BuildResult:
    """Write site files, copy assets, then invoke MkDocs.

    Args:
        ctx: Site build context with all intermediate products.
        diagnostics: Diagnostics already collected upstream.

    Returns:
        Final build result with all site artifacts and diagnostics.
    """
    artifacts, site_diags = write_site_artifacts_with_css(
        ctx.state.project_root,
        ctx.rendered_documents,
        ctx.site_name,
        ctx.html_config.resolve_output_dir(),
        ctx.html_config.css_files,
        ctx.state.filesystem,
        theme=ctx.html_config.theme,
    )
    diagnostics = (*diagnostics, *site_diags)
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    source_root = (
        ctx.state.project_root / ctx.state.config.paths.source
    ).resolve()
    asset_paths = collect_asset_paths(ctx.state.documents, source_root)
    asset_artifacts, asset_diags = copy_assets(
        asset_paths, source_root, ctx.docs_dir, ctx.state.filesystem
    )
    diagnostics = (*diagnostics, *asset_diags)
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    rendered_site, mkdocs_diags = run_mkdocs_build(
        ctx.state.project_root,
        ctx.html_config.resolve_output_dir(),
    )
    diagnostics = (*diagnostics, *mkdocs_diags)
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )
    assert rendered_site is not None

    return BuildResult(
        success=True,
        artifacts=(
            *artifacts,
            *asset_artifacts,
            *ctx.diagram_artifacts,
            rendered_site,
        ),
        diagnostics=diagnostics,
    )


__all__ = ["build_site"]
