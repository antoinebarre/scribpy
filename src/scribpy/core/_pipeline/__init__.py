"""Pipeline primitives for functional project preparation chains.

Re-exports the monad, state, and step functions that make up the shared
project parse pipeline.  This sub-package has no knowledge of specific build
targets or application services.

Public surface:
    PipelineResult              — result monad carrying value + diagnostics
    ProjectPipelineState        — frozen dataclass accumulating pipeline state
    run_project_parse_pipeline  — chains all setup steps into one call
"""

from scribpy.core.pipeline import PipelineResult
from scribpy.core.project_pipeline import run_project_parse_pipeline
from scribpy.core.project_pipeline_state import ProjectPipelineState

__all__ = [
    "PipelineResult",
    "ProjectPipelineState",
    "run_project_parse_pipeline",
]
