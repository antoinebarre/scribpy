"""Application service for build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.builders import merge_documents, write_markdown_artifact
from scribpy.config.types import HtmlMode
from scribpy.core.build_options import HtmlBuildOverrides, PdfBuildOverrides
from scribpy.core.project_pipeline import (
    ProjectPipelineState,
    run_project_parse_pipeline,
)
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.logging import get_logger
from scribpy.model import BuildResult, Diagnostic
from scribpy.model.protocols import FileSystem, MarkdownParser, PdfRenderer
from scribpy.transforms import TransformOptions, apply_transforms
from scribpy.utils import has_errors

_HTML_TARGETS = frozenset({"html", "html-single-page", "html-site"})
_PDF_TARGETS = frozenset({"pdf"})
logger = get_logger(__name__)


def build_project(
    root: Path | None = None,
    *,
    target: str = "markdown",
    html_mode: str | None = None,
    output_dir: Path | None = None,
    extra_css: tuple[Path, ...] = (),
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
    registry: ExtensionRegistry | None = None,
) -> BuildResult:
    """Build a Scribpy project for one target.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        target: Requested build target: ``"markdown"``, ``"html"``,
            ``"html-single-page"``, ``"html-site"``, or ``"pdf"``.
        html_mode: HTML output mode override — ``"single-page"`` or ``"site"``.
            When set, takes precedence over the project configuration.
        output_dir: Optional build output directory override. Relative paths are
            resolved from the project root; absolute paths are preserved. For
            HTML builds this overrides ``[builders.html].output_dir``.
        extra_css: Additional CSS files to append to the HTML or PDF build.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.
        registry: Optional lint rule registry override.

    Returns:
        Build artifacts plus diagnostics produced by the chain.
    """
    if target in _HTML_TARGETS:
        return _dispatch_html_build(
            root,
            target,
            HtmlBuildOverrides(
                mode=html_mode,
                output_dir=output_dir,
                extra_css=extra_css,
            ),
            filesystem,
            parser,
            registry,
        )

    if target in _PDF_TARGETS:
        return _dispatch_pdf_build(
            root,
            PdfBuildOverrides(output_dir=output_dir, extra_css=extra_css),
            filesystem,
            parser,
            registry,
            None,
        )

    if target != "markdown":
        logger.error("Unsupported build target: %s", target)
        return BuildResult(
            success=False,
            artifacts=(),
            diagnostics=(_unsupported_target_diagnostic(target),),
        )

    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked_build(diagnostics)

    active_registry = (
        registry if registry is not None else ExtensionRegistry.native()
    )
    resolved = state.require_resolved()
    diagnostics = _lint_state(resolved, diagnostics, active_registry)
    if has_errors(diagnostics):
        return _blocked_build(diagnostics)

    return _write_markdown_build(
        resolved, diagnostics, active_registry, output_dir
    )


def _dispatch_html_build(
    root: Path | None,
    target: str,
    overrides: HtmlBuildOverrides,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
    registry: ExtensionRegistry | None,
) -> BuildResult:
    """Dispatch html build."""
    from scribpy.config.types import HtmlBuilderConfig, PlantUmlConfig
    from scribpy.core.build_html import build_html_project

    # Resolve the effective mode from the target string or explicit override.
    mode_diagnostic = _html_mode_diagnostic(overrides.mode)
    if mode_diagnostic is not None:
        return BuildResult(
            success=False, artifacts=(), diagnostics=(mode_diagnostic,)
        )
    effective_mode = _effective_html_mode(target, overrides.mode)

    # Load config to pick up html section defaults, then override the mode.
    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked_build(diagnostics)

    resolved_for_config = state.require_resolved()
    base_html_config = resolved_for_config.config.html
    plantuml_renderer = overrides.plantuml_renderer
    if plantuml_renderer is not None and plantuml_renderer not in (
        "java",
        "web",
    ):
        return BuildResult(
            success=False,
            artifacts=(),
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="BLD001",
                    message=f"Unsupported PlantUML renderer: {plantuml_renderer}",
                    hint="Use plantuml_renderer='java' or 'web'.",
                ),
            ),
        )
    effective_plantuml = PlantUmlConfig(
        renderer=plantuml_renderer or base_html_config.plantuml.renderer,  # type: ignore[arg-type]
        server_url=overrides.plantuml_server_url
        or base_html_config.plantuml.server_url,
    )
    html_config = HtmlBuilderConfig(
        mode=effective_mode,
        css_files=(*base_html_config.css_files, *overrides.extra_css),
        site_name=base_html_config.site_name,
        theme=base_html_config.theme,
        output_dir=overrides.output_dir
        if overrides.output_dir is not None
        else base_html_config.output_dir,
        plantuml=effective_plantuml,
        mermaid=base_html_config.mermaid,
    )

    return build_html_project(
        root,
        html_config=html_config,
        filesystem=filesystem,
        parser=parser,
        registry=registry,
    )


def build_html_with_overrides(
    root: Path | None,
    overrides: HtmlBuildOverrides,
    *,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
    registry: ExtensionRegistry | None = None,
) -> BuildResult:
    """Build HTML output using grouped per-run overrides.

    Args:
        root: Project root or path inside the project.
        overrides: Grouped HTML overrides for one build.
        filesystem: Optional filesystem override.
        parser: Optional parser override.
        registry: Optional extension registry override.

    Returns:
        HTML build result.
    """
    return _dispatch_html_build(
        root,
        "html",
        overrides,
        filesystem,
        parser,
        registry,
    )


def _dispatch_pdf_build(
    root: Path | None,
    overrides: PdfBuildOverrides,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
    registry: ExtensionRegistry | None,
    pdf_renderer: PdfRenderer | None,
) -> BuildResult:
    """Dispatch PDF build."""
    from scribpy.config.types import PdfBuilderConfig
    from scribpy.core.build_pdf import build_pdf_project

    state, diagnostics = _prepare_build_state(root, filesystem, parser)
    if state is None:
        return _blocked_build(diagnostics)

    resolved = state.require_resolved()
    base_pdf_config = resolved.config.pdf
    pdf_config = PdfBuilderConfig(
        css_files=(*base_pdf_config.css_files, *overrides.extra_css),
        output_dir=overrides.output_dir
        if overrides.output_dir is not None
        else base_pdf_config.output_dir,
        paper_size=base_pdf_config.paper_size,
        toc_level=base_pdf_config.toc_level,
    )
    return build_pdf_project(
        root,
        pdf_config=pdf_config,
        filesystem=filesystem,
        parser=parser,
        registry=registry,
        pdf_renderer=pdf_renderer,
    )


def build_pdf_with_overrides(
    root: Path | None,
    overrides: PdfBuildOverrides,
    *,
    pdf_renderer: PdfRenderer | None = None,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
    registry: ExtensionRegistry | None = None,
) -> BuildResult:
    """Build PDF output using grouped per-run overrides.

    Args:
        root: Project root or path inside the project.
        overrides: Grouped PDF overrides for one build.
        pdf_renderer: Optional injected renderer. When omitted, Scribpy uses
            the built-in ``MarkdownPdfRenderer`` adapter.
        filesystem: Optional filesystem override.
        parser: Optional parser override.
        registry: Optional extension registry override.

    Returns:
        PDF build result.
    """
    return _dispatch_pdf_build(
        root,
        overrides,
        filesystem,
        parser,
        registry,
        pdf_renderer,
    )


def _prepare_build_state(
    root: Path | None,
    filesystem: FileSystem | None,
    parser: MarkdownParser | None,
) -> tuple[ProjectPipelineState | None, tuple[Diagnostic, ...]]:
    """Handle prepare build state."""
    prepared = run_project_parse_pipeline(root, filesystem, parser)
    if (
        prepared.failed
        or prepared.value is None
        or has_errors(prepared.diagnostics)
    ):
        return None, prepared.diagnostics
    return prepared.value, prepared.diagnostics


def _lint_state(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> tuple[Diagnostic, ...]:
    """Run registered lint rules and append their diagnostics.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        registry: Extension registry providing lint rules.

    Returns:
        Accumulated diagnostics including any lint findings.
    """
    context = LintContext(
        source_root=(state.project_root / state.config.paths.source).resolve(),
        documents=state.documents,
        document_index=state.index,
    )
    lint_result = run_lint_rules(context, registry.lint_rules)
    return (*diagnostics, *lint_result.diagnostics)


def _write_markdown_build(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
    output_dir: Path | None,
) -> BuildResult:
    """Apply Markdown transforms and write the merged artifact to disk.

    Args:
        state: Fully resolved pipeline state.
        diagnostics: Diagnostics already collected upstream.
        registry: Extension registry providing Markdown transforms.
        output_dir: Optional output directory override.

    Returns:
        Build result with the Markdown artifact and all diagnostics.
    """
    transform_result = apply_transforms(
        state.documents,
        target="markdown",
        transforms=registry.markdown_transforms,
        options=TransformOptions(
            document_title=state.config.document.title
            or state.config.project.name
            or "Document",
            toc_enabled=state.config.document.toc.enabled,
            toc_max_level=state.config.document.toc.max_level,
            toc_style=state.config.document.toc.style,
            numbering_enabled=state.config.document.numbering.enabled,
            numbering_max_level=state.config.document.numbering.max_level,
            numbering_style=state.config.document.numbering.style,
        ),
    )
    transformed_diagnostics = (*diagnostics, *transform_result.diagnostics)
    if has_errors(transformed_diagnostics):
        logger.error(
            "Markdown transform failed with %d diagnostic(s)",
            len(transformed_diagnostics),
        )
        return BuildResult(
            success=False, artifacts=(), diagnostics=transformed_diagnostics
        )
    assembled = merge_documents(transform_result.documents)
    artifact, write_diagnostics = write_markdown_artifact(
        state.project_root,
        assembled,
        state.filesystem,
        output_dir=output_dir
        if output_dir is not None
        else Path("build/markdown"),
    )
    final_diagnostics = (*transformed_diagnostics, *write_diagnostics)
    if artifact is None or has_errors(final_diagnostics):
        logger.error(
            "Markdown build failed with %d diagnostic(s)",
            len(final_diagnostics),
        )
        return BuildResult(
            success=False, artifacts=(), diagnostics=final_diagnostics
        )
    logger.info("Built Markdown artifact: %s", artifact.path)
    return BuildResult(
        success=True, artifacts=(artifact,), diagnostics=final_diagnostics
    )


def _unsupported_target_diagnostic(target: str) -> Diagnostic:
    """Handle unsupported target diagnostic."""
    return Diagnostic(
        severity="error",
        code="BLD001",
        message=f"Unsupported build target: {target}",
        hint="Use target='markdown', 'html', or 'pdf'.",
    )


def _blocked_build(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    """Create a blocked build."""
    return BuildResult(
        success=False,
        artifacts=(),
        diagnostics=(*diagnostics, _blocked_build_diagnostic()),
    )


def _blocked_build_diagnostic() -> Diagnostic:
    """Create a blocked build diagnostic."""
    return Diagnostic(
        severity="error",
        code="BLD002",
        message=(
            "Build stopped because blocking diagnostics were reported upstream."
        ),
        hint="Resolve project, parse, or lint errors before building.",
    )


__all__ = [
    "build_html_with_overrides",
    "build_pdf_with_overrides",
    "build_project",
]


def _html_mode_diagnostic(mode: str | None) -> Diagnostic | None:
    """Return an unsupported-mode diagnostic when needed."""
    if mode is None or mode in ("single-page", "site"):
        return None
    return Diagnostic(
        severity="error",
        code="BLD001",
        message=f"Unsupported HTML mode: {mode}",
        hint="Use html_mode='single-page' or 'site'.",
    )


def _effective_html_mode(target: str, mode: str | None) -> HtmlMode:
    """Return the effective HTML mode for one build."""
    if mode is not None:
        return mode  # type: ignore[return-value]
    return "site" if target == "html-site" else "single-page"
