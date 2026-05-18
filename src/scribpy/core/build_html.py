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
    write_single_page_support_artifacts,
)
from scribpy.builders.html_site import (
    run_mkdocs_build,
    write_site_artifacts_with_css,
)
from scribpy.builders.markdown import merge_documents
from scribpy.config.types import HtmlBuilderConfig
from scribpy.core.project_pipeline import ProjectPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, BuildResult, Diagnostic, TransformedDocument
from scribpy.model.protocols import (
    CodeBlockPlugin,
    DiagramRenderer,
    FileSystem,
    MarkdownParser,
)
from scribpy.plugins import PlantUmlPlugin
from scribpy.transforms import Transform, TransformOptions, apply_transforms
from scribpy.transforms.pipeline import native_html_transforms
from scribpy.utils import has_errors

logger = get_logger(__name__)


def build_html_project(
    root: Path | None,
    *,
    html_config: HtmlBuilderConfig,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
    registry: ExtensionRegistry | None,
    diagram_renderer: DiagramRenderer | None = None,
) -> BuildResult:
    """Build HTML output for one mode.

    Args:
        root: Project root path or ``None`` for cwd.
        html_config: HTML builder configuration including mode and CSS.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.
        registry: Optional extension registry override.
        diagram_renderer: Optional local diagram renderer override.

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
    code_block_plugins = _code_block_plugins(
        active_registry,
        html_config,
        diagram_renderer,
    )
    diagnostics = (
        *diagnostics,
        *_preflight_code_block_plugins(state, code_block_plugins),
    )
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    if html_config.mode == "single-page":
        logger.info("Starting single-page HTML build")
        return _build_single_page(
            state, diagnostics, html_config, active_registry, code_block_plugins
        )
    logger.info("Starting site HTML build")
    return _build_site(
        state, diagnostics, html_config, active_registry, code_block_plugins
    )


def _lint(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> tuple[Diagnostic, ...]:
    """Lint ."""
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
    code_block_plugins: tuple[CodeBlockPlugin, ...],
) -> BuildResult:
    """Build single page."""
    assert state.project_root is not None
    assert state.config is not None

    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=(
            *_custom_html_transforms(registry),
            *registry.markdown_transforms,
        ),
        options=_transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    abs_output = state.project_root / html_config.resolve_output_dir()
    rendered_documents, diagram_artifacts, diagnostics = _render_code_blocks(
        transform_result.documents,
        diagnostics,
        code_block_plugins,
        abs_output / "assets",
        flattened=True,
        target="html",
    )
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)
    css_artifacts, css_diags, css_hrefs = copy_css_files_single_page(
        state.project_root, html_config.css_files, abs_output, state.filesystem
    )
    diagnostics = (*diagnostics, *css_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    source_root = (state.project_root / state.config.paths.source).resolve()
    rewritten_documents = rewrite_asset_links_single_page(
        rendered_documents,
        source_root,
    )
    assembled = merge_documents(rewritten_documents)
    body_html = render_markdown_to_html(assembled.content)
    title = state.config.document.title or state.config.project.name or "Document"
    full_html = build_single_page_html(body_html, title, css_hrefs)

    support_artifacts, support_diags = write_single_page_support_artifacts(
        state.project_root,
        full_html,
        html_config.resolve_output_dir(),
        state.filesystem,
    )
    diagnostics = (*diagnostics, *support_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    asset_paths = collect_asset_paths(state.documents, source_root)
    assets_dir = abs_output / "assets"
    asset_artifacts, asset_diags = copy_assets(
        asset_paths, source_root, assets_dir, state.filesystem
    )
    diagnostics = (*diagnostics, *asset_diags)
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    result = BuildResult(
        success=True,
        artifacts=(
            *support_artifacts,
            *css_artifacts,
            *asset_artifacts,
            *diagram_artifacts,
        ),
        diagnostics=diagnostics,
    )
    logger.info("Built single-page HTML with %d artifact(s)", len(result.artifacts))
    return result


def _build_site(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    registry: ExtensionRegistry,
    code_block_plugins: tuple[CodeBlockPlugin, ...],
) -> BuildResult:
    """Build site."""
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

    docs_dir = state.project_root / html_config.resolve_output_dir() / "docs"
    rendered_documents, diagram_artifacts, diagnostics = _render_code_blocks(
        transform_result.documents,
        diagnostics,
        code_block_plugins,
        docs_dir / "assets",
        flattened=False,
        target="html-site",
    )
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)

    site_name = html_config.site_name or state.config.project.name or "Documentation"
    return _materialize_site(
        state,
        diagnostics,
        html_config,
        rendered_documents,
        diagram_artifacts,
        site_name,
        docs_dir,
    )


def _materialize_site(
    state: ProjectPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    html_config: HtmlBuilderConfig,
    rendered_documents: tuple[TransformedDocument, ...],
    diagram_artifacts: tuple[BuildArtifact, ...],
    site_name: str,
    docs_dir: Path,
) -> BuildResult:
    """Write site files, copy assets, then invoke MkDocs.

    Args:
        state: Prepared project state.
        diagnostics: Diagnostics already collected by the site build.
        html_config: HTML builder configuration.
        rendered_documents: Documents after PlantUML rendering.
        diagram_artifacts: Generated PlantUML SVG artifacts.
        site_name: Final site title.
        docs_dir: Absolute MkDocs docs directory.

    Returns:
        Final site build result.
    """
    assert state.project_root is not None
    assert state.config is not None
    artifacts, site_diags = write_site_artifacts_with_css(
        state.project_root,
        rendered_documents,
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
    if has_errors(diagnostics):
        return BuildResult(success=False, artifacts=(), diagnostics=diagnostics)
    assert rendered_site is not None

    result = BuildResult(
        success=True,
        artifacts=(*artifacts, *asset_artifacts, *diagram_artifacts, rendered_site),
        diagnostics=diagnostics,
    )
    logger.info("Built site HTML with %d artifact(s)", len(result.artifacts))
    return result


def _transform_options(state: ProjectPipelineState) -> TransformOptions:
    """Handle transform options."""
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


def _render_code_blocks(
    documents: tuple[TransformedDocument, ...],
    diagnostics: tuple[Diagnostic, ...],
    plugins: tuple[CodeBlockPlugin, ...],
    output_dir: Path,
    *,
    flattened: bool,
    target: str,
) -> tuple[
    tuple[TransformedDocument, ...],
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Render fenced-code-block plugins and append diagnostics.

    Args:
        documents: Target-ready documents to inspect.
        diagnostics: Diagnostics already collected by the build.
        plugins: Ordered code-block plugins to apply.
        output_dir: Destination root for plugin-generated assets.
        flattened: Whether output documents will be merged into one page.
        target: Artifact target label.

    Returns:
        Rewritten documents, generated artifacts, and accumulated diagnostics.
    """
    rendered_documents = documents
    artifacts: list[BuildArtifact] = []
    for plugin in plugins:
        rendered_documents, plugin_artifacts, plugin_diags = plugin.render_documents(
            rendered_documents,
            output_dir=output_dir,
            flattened=flattened,
            target=target,
        )
        artifacts.extend(plugin_artifacts)
        diagnostics = (*diagnostics, *plugin_diags)
        if has_errors(diagnostics):
            break
    return rendered_documents, tuple(artifacts), diagnostics


def _preflight_code_block_plugins(
    state: ProjectPipelineState,
    plugins: tuple[CodeBlockPlugin, ...],
) -> tuple[Diagnostic, ...]:
    """Run early plugin validation only for plugins present in source Markdown."""
    diagnostics: list[Diagnostic] = []
    for plugin in plugins:
        if any(plugin.has_blocks(document.source) for document in state.documents):
            diagnostics.extend(plugin.preflight())
    return tuple(diagnostics)


def _code_block_plugins(
    registry: ExtensionRegistry,
    html_config: HtmlBuilderConfig,
    override: DiagramRenderer | None,
) -> tuple[CodeBlockPlugin, ...]:
    """Return built-in and registry-provided code-block plugins."""
    return (
        PlantUmlPlugin(html_config.plantuml, override),
        *registry.code_block_plugins,
    )


def _custom_html_transforms(
    registry: ExtensionRegistry,
) -> tuple[Transform, ...]:
    """Return custom html transforms."""
    native = native_html_transforms()
    return tuple(
        transform for transform in registry.html_transforms if transform not in native
    )


def _blocked(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    """Create a blocked ."""
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
