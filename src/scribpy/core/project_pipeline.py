"""Reusable project preparation pipeline shared by functional chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.core.pipeline import PipelineResult
from scribpy.core.project_pipeline_document_steps import (
    build_index_step,
    parse_documents_step,
)
from scribpy.core.project_pipeline_setup_steps import (
    load_config_step,
    resolve_config_step,
    scan_sources_step,
)
from scribpy.core.project_pipeline_state import ProjectPipelineState
from scribpy.model.protocols import FileSystem, MarkdownParser
from scribpy.utils.file_utils import RealFileSystem


def run_project_parse_pipeline(
    root: Path | None = None,
    filesystem: FileSystem | None = None,
    parser: MarkdownParser | None = None,
) -> PipelineResult[ProjectPipelineState]:
    """Run the shared project pipeline through document parsing.

    Args:
        root: Project root, child path, config path, or ``None`` for cwd.
        filesystem: Optional filesystem service override.
        parser: Optional Markdown parser override.

    Returns:
        Project preparation state plus accumulated diagnostics.
    """
    initial = ProjectPipelineState(
        start=Path.cwd() if root is None else root,
        filesystem=filesystem if filesystem is not None else RealFileSystem(),
        parser=parser,
    )
    return (
        PipelineResult.ok(initial)
        .bind(resolve_config_step)
        .bind(load_config_step)
        .bind(scan_sources_step)
        .bind(build_index_step)
        .bind(parse_documents_step)
    )


__all__ = [
    "ProjectPipelineState",
    "run_project_parse_pipeline",
]
