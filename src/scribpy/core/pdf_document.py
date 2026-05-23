"""Prepare renderer-neutral PDF documents."""

from __future__ import annotations

from pathlib import Path

from scribpy.assets import rewrite_asset_links_single_page
from scribpy.builders.markdown import merge_documents
from scribpy.builders.pdf import DEFAULT_PDF_CSS, PdfDocument, PdfOptions
from scribpy.builders.pdf_markdown import (
    drop_internal_pdf_links,
    pdf_transform_options,
)
from scribpy.config.types import PdfBuilderConfig
from scribpy.core.build_html_shared import render_code_blocks
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.model import BuildArtifact, Diagnostic
from scribpy.model.protocols import CodeBlockPlugin
from scribpy.transforms import apply_transforms
from scribpy.utils import has_errors


def prepare_pdf_document(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    pdf_config: PdfBuilderConfig,
    registry: ExtensionRegistry,
    plugins: tuple[CodeBlockPlugin, ...],
    abs_output: Path,
) -> tuple[
    PdfDocument | None,
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Transform documents and prepare the renderer-neutral PDF payload.

    Args:
        state: Fully resolved project pipeline state.
        diagnostics: Diagnostics already collected by the build.
        pdf_config: PDF builder configuration.
        registry: Extension registry providing Markdown transforms.
        plugins: Code-block plugins used to render diagrams.
        abs_output: Absolute PDF output directory.

    Returns:
        Prepared PDF document, generated diagram artifacts, and diagnostics.
    """
    source_root = (state.project_root / state.config.paths.source).resolve()
    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=registry.markdown_transforms,
        options=pdf_transform_options(state),
    )
    diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(diagnostics):
        return None, (), diagnostics

    css_files, css_diagnostics = resolve_pdf_css_files(
        state.project_root, pdf_config.css_files
    )
    diagnostics = (*diagnostics, *css_diagnostics)
    if has_errors(diagnostics):
        return None, (), diagnostics

    rendered_documents, diagram_artifacts, diagnostics = render_code_blocks(
        transform_result.documents,
        diagnostics,
        plugins,
        abs_output / "assets",
        flattened=True,
        target="pdf",
    )
    if has_errors(diagnostics):
        return None, diagram_artifacts, diagnostics

    rewritten = rewrite_asset_links_single_page(
        rendered_documents, source_root
    )
    assembled = merge_documents(drop_internal_pdf_links(rewritten))
    return (
        PdfDocument(
            markdown=assembled.content,
            root=abs_output.resolve(),
            css_files=css_files,
            default_css=DEFAULT_PDF_CSS,
            options=PdfOptions(
                paper_size=pdf_config.paper_size,
                toc_level=pdf_config.toc_level,
            ),
        ),
        diagram_artifacts,
        diagnostics,
    )


def resolve_pdf_css_files(
    project_root: Path, css_files: tuple[Path, ...]
) -> tuple[tuple[Path, ...], tuple[Diagnostic, ...]]:
    """Resolve and validate configured PDF CSS paths.

    Args:
        project_root: Root used to resolve relative CSS paths.
        css_files: CSS paths from config or API/CLI overrides.

    Returns:
        Resolved CSS paths and diagnostics for missing files.
    """
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


__all__ = ["prepare_pdf_document", "resolve_pdf_css_files"]
