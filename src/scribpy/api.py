"""Simple public Python API mirroring Scribpy's main CLI workflows."""

from __future__ import annotations

from pathlib import Path

from scribpy.config.types import HtmlMode, PlantUmlRendererMode
from scribpy.core import (
    DemoVariant,
    build_project,
    create_demo_project,
    lint_project,
    parse_project_documents,
    run_index_check,
)
from scribpy.core.build_options import HtmlBuildOverrides, PdfBuildOverrides
from scribpy.core.build_project import (
    build_html_with_overrides,
    build_pdf_with_overrides,
)
from scribpy.model import BuildResult, LintResult, ParseResult
from scribpy.model.protocols import PdfRenderer

type PathLike = str | Path


def create_demo(
    target: PathLike = "scribpy-demo",
    *,
    force: bool = False,
    variant: DemoVariant = "valid",
) -> LintResult:
    """Create a tutorial project, like ``scribpy demo create``.

    Args:
        target: Directory where the demo project should be created.
        force: Overwrite demo-managed files when they already exist.
        variant: Demo variant to create. Accepted values are ``"valid"`` and
            ``"invalid"``.

    Returns:
        Lint-style result containing creation diagnostics.

    Examples:
        >>> create_demo("demo")
        >>> create_demo("broken-demo", variant="invalid", force=True)
    """
    return create_demo_project(Path(target), force=force, variant=variant)


def check_index(root: PathLike | None = None) -> LintResult:
    """Validate project discovery and index configuration.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Lint-style result containing index diagnostics.

    Examples:
        >>> check_index(".")
    """
    return run_index_check(_path(root))


def check_parse(root: PathLike | None = None) -> ParseResult:
    """Parse indexed Markdown documents and return extracted semantics.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Parsed documents, diagnostics, and failure state.

    Examples:
        >>> result = check_parse(".")
        >>> len(result.documents)
    """
    return parse_project_documents(_path(root))


def lint(root: PathLike | None = None) -> LintResult:
    """Run Scribpy's lint chain on a documentation project.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Lint diagnostics and failure state.

    Examples:
        >>> lint(".")
    """
    return lint_project(_path(root))


def build_markdown(
    root: PathLike | None = None,
    *,
    output_dir: PathLike | None = None,
) -> BuildResult:
    """Build the assembled Markdown artifact.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        output_dir: Optional directory that receives ``document.md``. Relative
            paths are resolved from the project root; absolute paths are kept.

    Returns:
        Build result for the Markdown target.

    Examples:
        >>> build_markdown(".")
        >>> build_markdown(".", output_dir="/tmp/scribpy-md")
    """
    return build_project(
        _path(root),
        target="markdown",
        output_dir=_path(output_dir),
    )


def build_html(
    root: PathLike | None = None,
    *,
    mode: HtmlMode = "single-page",
    output_dir: PathLike | None = None,
    extra_css: list[PathLike] | None = None,
    plantuml_renderer: PlantUmlRendererMode | None = None,
    plantuml_server_url: str | None = None,
) -> BuildResult:
    """Build HTML output in ``single-page`` or ``site`` mode.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        mode: HTML output mode. Accepted values are ``"single-page"`` and
            ``"site"``.
        output_dir: Optional HTML output directory override. Relative paths are
            resolved from the project root; absolute paths are kept.
        extra_css: Additional CSS file paths (relative to the project root) to
            append after the project-configured stylesheets.
        plantuml_renderer: Optional PlantUML backend override.
        plantuml_server_url: Optional PlantUML server URL override for web mode.

    Returns:
        Build result for the requested HTML mode.

    Examples:
        >>> build_html(".", mode="single-page")
        >>> build_html(".", mode="site", output_dir="build/ci-site")
        >>> build_html(".", extra_css=["theme/custom.css"])
        >>> build_html(".", plantuml_renderer="web")
    """
    extra = tuple(Path(p) for p in extra_css) if extra_css else ()
    return build_html_with_overrides(
        _path(root),
        HtmlBuildOverrides(
            mode=mode,
            output_dir=_path(output_dir),
            extra_css=extra,
            plantuml_renderer=plantuml_renderer,
            plantuml_server_url=plantuml_server_url,
        ),
    )


def build_pdf(
    root: PathLike | None = None,
    *,
    output_dir: PathLike | None = None,
    extra_css: list[PathLike] | None = None,
    pdf_renderer: PdfRenderer | None = None,
) -> BuildResult:
    """Build PDF output using an injectable renderer.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        output_dir: Optional PDF output directory override. Relative paths are
            resolved from the project root; absolute paths are kept.
        extra_css: Additional PDF CSS file paths appended after configured CSS.
        pdf_renderer: Optional renderer implementing ``PdfRenderer``. When
            omitted, Scribpy uses the optional ``MarkdownPdfRenderer`` adapter.

    Returns:
        Build result for the PDF target.

    Examples:
        >>> build_pdf(".")
        >>> build_pdf(".", extra_css=["theme/pdf.css"])
    """
    extra = tuple(Path(p) for p in extra_css) if extra_css else ()
    return build_pdf_with_overrides(
        _path(root),
        PdfBuildOverrides(output_dir=_path(output_dir), extra_css=extra),
        pdf_renderer=pdf_renderer,
    )


def _path(value: PathLike | None) -> Path | None:
    """Convert an optional public path value into ``Path``."""
    return None if value is None else Path(value)


__all__ = [
    "PathLike",
    "build_html",
    "build_markdown",
    "build_pdf",
    "check_index",
    "check_parse",
    "create_demo",
    "lint",
]
