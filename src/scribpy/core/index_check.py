"""Application service for project index validation."""

from __future__ import annotations

from pathlib import Path

from scribpy.config import CONFIG_FILENAME, find_config, load_config
from scribpy.logging import get_logger, prepare_logging
from scribpy.model import Diagnostic, LintResult
from scribpy.project import build_document_index, resolve_project_root, scan_project
from scribpy.utils import has_errors

logger = get_logger(__name__)


def run_index_check(root: Path | None = None) -> LintResult:
    """Check that a Scribpy project can produce a valid document index.

    Args:
        root: Project directory, path inside a project, path to ``scribpy.toml``,
            or ``None`` to use the current working directory.

    Returns:
        Lint-style result containing all user-facing diagnostics produced while
        locating configuration, loading configuration, scanning sources, and
        building the document index.
    """
    start = Path.cwd() if root is None else root
    logger.info("Starting index check from %s", start)
    config_path = _resolve_config_path(start)
    if config_path is None:
        logger.error("Could not resolve project configuration from %s", start)
        diagnostics: tuple[Diagnostic, ...] = (
            Diagnostic(
                severity="error",
                code="CFG001",
                message="Could not find scribpy.toml.",
                path=start,
                hint="Create scribpy.toml at the project root or pass its path.",
            ),
        )
        return LintResult(diagnostics=diagnostics, failed=True)

    config, config_diagnostics = load_config(config_path)
    if config is None or has_errors(config_diagnostics):
        return LintResult(
            diagnostics=config_diagnostics,
            failed=has_errors(config_diagnostics),
        )

    project_root = resolve_project_root(config_path)
    prepare_logging(project_root)
    source_files, scan_diagnostics = scan_project(project_root, config)
    if has_errors(scan_diagnostics):
        return LintResult(diagnostics=scan_diagnostics, failed=True)

    _index, index_diagnostics = build_document_index(config, source_files)
    diagnostics = (*config_diagnostics, *scan_diagnostics, *index_diagnostics)
    logger.info(
        "Completed index check: %d source file(s), %d diagnostic(s)",
        len(source_files),
        len(diagnostics),
    )
    return LintResult(diagnostics=diagnostics, failed=has_errors(diagnostics))


def _resolve_config_path(start: Path) -> Path | None:
    if start.name == CONFIG_FILENAME:
        return start if start.is_file() else None
    return find_config(start)


__all__ = ["run_index_check"]
