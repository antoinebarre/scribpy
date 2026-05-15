"""Configuration and scan steps for the shared project pipeline."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from scribpy.config import CONFIG_FILENAME, find_config, load_config
from scribpy.core.pipeline import PipelineResult
from scribpy.core.project_pipeline_state import ProjectPipelineState
from scribpy.model import Diagnostic
from scribpy.project import resolve_project_root, scan_project
from scribpy.utils import has_errors


def resolve_config_step(
    state: ProjectPipelineState,
) -> PipelineResult[ProjectPipelineState]:
    """Resolve the project configuration path.

    Args:
        state: Initial project pipeline state.

    Returns:
        Updated state carrying the configuration path.
    """
    config_path = _resolve_config_path(state.start)
    if config_path is None:
        return PipelineResult.fail((_missing_config_diagnostic(state.start),), state)
    return PipelineResult.ok(replace(state, config_path=config_path))


def load_config_step(
    state: ProjectPipelineState,
) -> PipelineResult[ProjectPipelineState]:
    """Load and validate project configuration.

    Args:
        state: Project pipeline state with a resolved configuration path.

    Returns:
        Updated state carrying parsed configuration.
    """
    assert state.config_path is not None
    config, diagnostics = load_config(state.config_path)
    next_state = replace(state, config=config)
    if config is None or has_errors(diagnostics):
        return PipelineResult.fail(diagnostics, next_state)
    return PipelineResult.ok(next_state, diagnostics)


def scan_sources_step(
    state: ProjectPipelineState,
) -> PipelineResult[ProjectPipelineState]:
    """Discover source files from project configuration.

    Args:
        state: Project pipeline state with parsed configuration.

    Returns:
        Updated state carrying project root and discovered sources.
    """
    assert state.config_path is not None
    assert state.config is not None
    project_root = resolve_project_root(state.config_path)
    source_files, diagnostics = scan_project(project_root, state.config)
    next_state = replace(
        state,
        project_root=project_root,
        source_files=source_files,
    )
    if has_errors(diagnostics):
        return PipelineResult.fail(diagnostics, next_state)
    return PipelineResult.ok(next_state, diagnostics)


def _resolve_config_path(start: Path) -> Path | None:
    if start.name == CONFIG_FILENAME:
        return start if start.is_file() else None
    return find_config(start)


def _missing_config_diagnostic(start: Path) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="CFG001",
        message="Could not find scribpy.toml.",
        path=start,
        hint="Create scribpy.toml at the project root or pass its path.",
    )


__all__ = [
    "load_config_step",
    "resolve_config_step",
    "scan_sources_step",
]
