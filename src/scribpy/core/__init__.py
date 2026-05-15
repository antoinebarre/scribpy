"""Public Python API facade for Scribpy."""

from scribpy.builders import merge_documents
from scribpy.core.build_project import build_project
from scribpy.core.demo import DemoVariant, create_demo_project
from scribpy.core.index_check import run_index_check
from scribpy.core.lint_project import lint_project
from scribpy.core.parse_check import parse_project_documents

check_index = run_index_check

__all__ = [
    "DemoVariant",
    "build_project",
    "check_index",
    "create_demo_project",
    "lint_project",
    "merge_documents",
    "parse_project_documents",
    "run_index_check",
]
