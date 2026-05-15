"""Indexing and parsing steps for the shared project pipeline."""

from __future__ import annotations

from dataclasses import replace

from scribpy.core.pipeline import PipelineResult
from scribpy.core.project_pipeline_state import ProjectPipelineState
from scribpy.parser.document import order_by_index, parse_documents
from scribpy.project import build_document_index
from scribpy.utils import has_errors


def build_index_step(
    state: ProjectPipelineState,
) -> PipelineResult[ProjectPipelineState]:
    """Build and validate the deterministic document index."""
    assert state.config is not None
    index, diagnostics = build_document_index(state.config, state.source_files)
    next_state = replace(state, index=index)
    if index is None or has_errors(diagnostics):
        return PipelineResult.fail(diagnostics, next_state)
    return PipelineResult.ok(next_state, diagnostics)


def parse_documents_step(
    state: ProjectPipelineState,
) -> PipelineResult[ProjectPipelineState]:
    """Order and parse source files into semantic documents."""
    assert state.index is not None
    ordered_files, order_diagnostics = order_by_index(state.index, state.source_files)
    parse_result = parse_documents(ordered_files, state.filesystem, state.parser)
    diagnostics = (*order_diagnostics, *parse_result.diagnostics)
    next_state = replace(
        state,
        ordered_files=tuple(ordered_files),
        documents=parse_result.documents,
    )
    if parse_result.failed:
        return PipelineResult.fail(diagnostics, next_state)
    return PipelineResult.ok(next_state, diagnostics)


__all__ = [
    "build_index_step",
    "parse_documents_step",
]
