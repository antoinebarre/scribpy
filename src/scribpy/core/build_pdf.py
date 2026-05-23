"""Application service for PDF build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets import (
    collect_asset_paths,
    copy_assets,
)
from scribpy.builders.pdf import (
    PDF_OUTPUT_FILE,
    MarkdownPdfRenderer,
    PdfDocument,
)
from scribpy.builders.pdf_assets import rasterize_svg_artifacts_for_pdf
from scribpy.config.types import PdfBuilderConfig
from scribpy.core.build_html_shared import (
    code_block_plugins,
    preflight_code_block_plugins,
)
from scribpy.core.pdf_document import prepare_pdf_document
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.logging import get_logger
from scribpy.model import (
    BuildArtifact,
    BuildResult,
    Diagnostic,
)
from scribpy.model.protocols import (
    FileSystem,
    MarkdownParser,
    PdfRenderer,
)
from scribpy.utils import has_errors

logger = get_logger(__name__)


def build_pdf_project(
    root: Path | None,
    *,
    pdf_config: PdfBuilderConfig,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
    registry: ExtensionRegistry | None,
    pdf_renderer: PdfRenderer | None = None,
) -> BuildResult:
    """Build PDF output using an injected renderer.

    Args:
        root: Project root path or ``None`` for cwd.
        pdf_config: PDF builder configuration including CSS and output path.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.
        registry: Optional extension registry override.
        pdf_renderer: Optional renderer injected by the Python API.

    Returns:
        Build result with artifacts and diagnostics.
    """
    from scribpy.core.build_project import _prepare_build_state

    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked(diagnostics)

    active_registry = (
        registry if registry is not None else ExtensionRegistry.native()
    )
    resolved = state.require_resolved()
    return _build_pdf_from_resolved_state(
        resolved,
        diagnostics,
        pdf_config,
        active_registry,
        pdf_renderer,
    )


def _build_pdf_from_resolved_state(
    resolved: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    pdf_config: PdfBuilderConfig,
    registry: ExtensionRegistry,
    pdf_renderer: PdfRenderer | None,
) -> BuildResult:
    """Build PDF from an already resolved project state."""
    diagnostics = _lint(resolved, diagnostics, registry)
    if has_errors(diagnostics):
        return _blocked(diagnostics)

    abs_output = _absolute_output_dir(
        resolved.project_root, pdf_config.resolve_output_dir()
    )
    plugins = code_block_plugins(registry, resolved.config.html, None)
    diagnostics = (
        *diagnostics,
        *preflight_code_block_plugins(resolved, plugins),
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    pdf_document, diagram_artifacts, diagnostics = prepare_pdf_document(
        resolved, diagnostics, pdf_config, registry, plugins, abs_output
    )
    if pdf_document is None or has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=diagram_artifacts, diagnostics=diagnostics
        )

    return _copy_rasterize_and_render_pdf(
        resolved,
        abs_output,
        pdf_document,
        diagram_artifacts,
        diagnostics,
        pdf_renderer,
    )


def _copy_rasterize_and_render_pdf(
    resolved: ResolvedPipelineState,
    abs_output: Path,
    pdf_document: PdfDocument,
    diagram_artifacts: tuple[BuildArtifact, ...],
    diagnostics: tuple[Diagnostic, ...],
    pdf_renderer: PdfRenderer | None,
) -> BuildResult:
    """Copy assets, rasterize SVGs, and invoke the final PDF renderer."""
    source_root = (
        resolved.project_root / resolved.config.paths.source
    ).resolve()
    assets, asset_diagnostics = copy_assets(
        collect_asset_paths(resolved.documents, source_root),
        source_root,
        abs_output / "assets",
        resolved.filesystem,
    )
    diagnostics = (*diagnostics, *asset_diagnostics)
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=assets, diagnostics=diagnostics
        )

    pdf_document, raster_artifacts, raster_diagnostics = (
        rasterize_svg_artifacts_for_pdf(
            pdf_document, (*assets, *diagram_artifacts)
        )
    )
    diagnostics = (*diagnostics, *raster_diagnostics)
    if has_errors(diagnostics):
        return BuildResult(
            success=False,
            artifacts=(*assets, *diagram_artifacts, *raster_artifacts),
            diagnostics=diagnostics,
        )

    renderer = pdf_renderer or MarkdownPdfRenderer()
    logger.info("Starting PDF build")
    render_result = renderer.render(pdf_document, abs_output / PDF_OUTPUT_FILE)
    diagnostics = (*diagnostics, *render_result.diagnostics)
    if not render_result.success or render_result.artifact is None:
        return BuildResult(
            success=False,
            artifacts=(*assets, *diagram_artifacts, *raster_artifacts),
            diagnostics=diagnostics,
        )
    return BuildResult(
        success=True,
        artifacts=(
            render_result.artifact,
            *assets,
            *diagram_artifacts,
            *raster_artifacts,
        ),
        diagnostics=diagnostics,
    )


def _lint(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> tuple[Diagnostic, ...]:
    """Run registered lint rules and append diagnostics."""
    context = LintContext(
        source_root=(state.project_root / state.config.paths.source).resolve(),
        documents=state.documents,
        document_index=state.index,
    )
    lint_result = run_lint_rules(context, registry.lint_rules)
    return (*diagnostics, *lint_result.diagnostics)


def _blocked(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    """Create a blocked PDF build result."""
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


def _absolute_output_dir(project_root: Path, output_dir: Path) -> Path:
    """Resolve an output directory from the project root when needed."""
    return (
        output_dir if output_dir.is_absolute() else project_root / output_dir
    )


__all__ = ["build_pdf_project"]
