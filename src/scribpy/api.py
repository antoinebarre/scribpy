"""Simple public Python API mirroring Scribpy's main CLI workflows."""

from __future__ import annotations

from pathlib import Path

from scribpy.config.types import HtmlMode
from scribpy.core import (
    DemoVariant,
    build_project,
    create_demo_project,
    lint_project,
    parse_project_documents,
    run_index_check,
)
from scribpy.model import BuildResult, LintResult, ParseResult

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
        variant: Demo variant to create.

    Returns:
        Lint-style result containing creation diagnostics.
    """
    return create_demo_project(Path(target), force=force, variant=variant)


def check_index(root: PathLike | None = None) -> LintResult:
    """Validate project discovery and index configuration.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Lint-style result containing index diagnostics.
    """
    return run_index_check(_path(root))


def check_parse(root: PathLike | None = None) -> ParseResult:
    """Parse indexed Markdown documents and return extracted semantics.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Parsed documents, diagnostics, and failure state.
    """
    return parse_project_documents(_path(root))


def lint(root: PathLike | None = None) -> LintResult:
    """Run Scribpy's lint chain on a documentation project.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Lint diagnostics and failure state.
    """
    return lint_project(_path(root))


def build_markdown(root: PathLike | None = None) -> BuildResult:
    """Build the assembled Markdown artifact.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.

    Returns:
        Build result for the Markdown target.
    """
    return build_project(_path(root), target="markdown")


def build_html(
    root: PathLike | None = None,
    *,
    mode: HtmlMode = "single-page",
) -> BuildResult:
    """Build HTML output in ``single-page`` or ``site`` mode.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        mode: HTML output mode.

    Returns:
        Build result for the requested HTML mode.
    """
    return build_project(_path(root), target="html", html_mode=mode)


def _path(value: PathLike | None) -> Path | None:
    return None if value is None else Path(value)


__all__ = [
    "PathLike",
    "build_html",
    "build_markdown",
    "check_index",
    "check_parse",
    "create_demo",
    "lint",
]
