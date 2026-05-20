"""Application service for HTML build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.config.types import HtmlBuilderConfig
from scribpy.core.build_html_shared import (
    code_block_plugins,
    preflight_code_block_plugins,
)
from scribpy.core.build_html_single_page import build_single_page
from scribpy.core.build_html_site import build_site
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.lint import LintContext, run_lint_rules
from scribpy.logging import get_logger
from scribpy.model import BuildResult, Diagnostic
from scribpy.model.protocols import DiagramRenderer, FileSystem, MarkdownParser
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

    active_registry = (
        registry if registry is not None else ExtensionRegistry.native()
    )
    resolved = state.require_resolved()
    diagnostics = _lint(resolved, diagnostics, active_registry)
    if has_errors(diagnostics):
        return _blocked(diagnostics)

    plugins = code_block_plugins(
        active_registry, html_config, diagram_renderer
    )
    diagnostics = (
        *diagnostics,
        *preflight_code_block_plugins(resolved, plugins),
    )
    if has_errors(diagnostics):
        return BuildResult(
            success=False, artifacts=(), diagnostics=diagnostics
        )

    if html_config.mode == "single-page":
        logger.info("Starting single-page HTML build")
        return build_single_page(
            resolved, diagnostics, html_config, active_registry, plugins
        )
    logger.info("Starting site HTML build")
    return build_site(
        resolved, diagnostics, html_config, active_registry, plugins
    )


def _lint(
    state: ResolvedPipelineState,
    diagnostics: tuple[Diagnostic, ...],
    registry: ExtensionRegistry,
) -> tuple[Diagnostic, ...]:
    """Run all registered lint rules and append their diagnostics.

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


def _blocked(diagnostics: tuple[Diagnostic, ...]) -> BuildResult:
    """Wrap upstream diagnostics in a terminal blocked-build result.

    Args:
        diagnostics: Diagnostics to include in the result.

    Returns:
        A failed build result with a blocking diagnostic appended.
    """
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
