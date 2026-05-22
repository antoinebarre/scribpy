"""Application service for PDF build chains."""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

from scribpy.assets import (
    collect_asset_paths,
    copy_assets,
    rewrite_asset_links_single_page,
)
from scribpy.assets.targets import is_external
from scribpy.builders.markdown import merge_documents
from scribpy.builders.pdf import (
    DEFAULT_PDF_CSS,
    PDF_OUTPUT_FILE,
    MarkdownPdfRenderer,
    PdfDocument,
    PdfOptions,
)
from scribpy.config.types import PdfBuilderConfig
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.logging import get_logger
from scribpy.model import BuildResult, Diagnostic, TransformedDocument
from scribpy.model.protocols import FileSystem, MarkdownParser, PdfRenderer
from scribpy.transforms import TransformOptions, apply_transforms
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
    diagnostics = _lint(resolved, diagnostics, active_registry)
    if has_errors(diagnostics):
        return _blocked(diagnostics)

    pdf_document, diagnostics = _prepare_pdf_document(
        resolved, diagnostics, pdf_config, active_registry
    )
    if pdf_document is None or has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    abs_output = _absolute_output_dir(
        resolved.project_root, pdf_config.resolve_output_dir()
    )
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

    renderer = pdf_renderer or MarkdownPdfRenderer()
    logger.info("Starting PDF build")
    render_result = renderer.render(pdf_document, abs_output / PDF_OUTPUT_FILE)
    diagnostics = (*diagnostics, *render_result.diagnostics)
    if not render_result.success or render_result.artifact is None:
        return BuildResult(
            success=False, artifacts=assets, diagnostics=diagnostics
        )
    return BuildResult(
        success=True,
        artifacts=(render_result.artifact, *assets),
        diagnostics=diagnostics,
    )


def _prepare_pdf_document(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    pdf_config: PdfBuilderConfig,
    registry: ExtensionRegistry,
) -> tuple[PdfDocument | None, tuple[Diagnostic, ...]]:
    """Transform documents and prepare the renderer-neutral PDF payload."""
    source_root = (state.project_root / state.config.paths.source).resolve()
    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=registry.markdown_transforms,
        options=_pdf_transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return None, diagnostics

    css_files, css_diagnostics = _resolve_css_files(
        state.project_root, pdf_config.css_files
    )
    diagnostics = (*diagnostics, *css_diagnostics)
    if has_errors(diagnostics):
        return None, diagnostics

    rewritten = rewrite_asset_links_single_page(
        transform_result.documents, source_root
    )
    assembled = merge_documents(_drop_internal_pdf_links(rewritten))
    return (
        PdfDocument(
            markdown=assembled.content,
            root=_absolute_output_dir(
                state.project_root, pdf_config.resolve_output_dir()
            ).resolve(),
            css_files=css_files,
            default_css=DEFAULT_PDF_CSS,
            options=PdfOptions(
                paper_size=pdf_config.paper_size,
                toc_level=pdf_config.toc_level,
            ),
        ),
        diagnostics,
    )


def _resolve_css_files(
    project_root: Path, css_files: tuple[Path, ...]
) -> tuple[tuple[Path, ...], tuple[Diagnostic, ...]]:
    """Resolve and validate configured PDF CSS paths."""
    resolved: list[Path] = []
    diagnostics: list[Diagnostic] = []
    for css_file in css_files:
        abs_path = (
            css_file if css_file.is_absolute() else project_root / css_file
        )
        if not abs_path.is_file():
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="PDF003",
                    message="PDF CSS file does not exist.",
                    path=abs_path,
                    hint="Update builders.pdf.css or pass an existing --css path.",
                )
            )
            continue
        resolved.append(abs_path)
    return tuple(resolved), tuple(diagnostics)


_MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")


def _drop_internal_pdf_links(
    documents: tuple[TransformedDocument, ...],
) -> tuple[TransformedDocument, ...]:
    """Convert internal Markdown links to text for robust PDF rendering."""
    return tuple(
        replace(
            document,
            content=_MARKDOWN_LINK_RE.sub(
                lambda match: _pdf_link_replacement(match), document.content
            ),
        )
        for document in documents
    )


def _pdf_link_replacement(match: re.Match[str]) -> str:
    """Return a PDF-safe replacement for one Markdown link match."""
    label = match.group(1)
    target = match.group(2).strip()
    if is_external(target):
        return match.group(0)
    return label


def _pdf_transform_options(state: ResolvedPipelineState) -> TransformOptions:
    """Return Markdown transform options adapted for PDF rendering.

    ``markdown-pdf`` already exposes native PDF bookmarks through ``toc_level``.
    Keeping Scribpy's generated Markdown TOC would add anchor links that
    PyMuPDF cannot always resolve as PDF destinations.
    """
    return TransformOptions(
        document_title=state.config.document.title
        or state.config.project.name
        or "Document",
        toc_enabled=False,
        toc_max_level=state.config.document.toc.max_level,
        toc_style=state.config.document.toc.style,
        numbering_enabled=state.config.document.numbering.enabled,
        numbering_max_level=state.config.document.numbering.max_level,
        numbering_style=state.config.document.numbering.style,
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
