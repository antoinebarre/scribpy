"""Application services — one public function per project workflow.

Each service orchestrates the shared parse pipeline and one or more
domain-specific steps (lint, transform, build, demo creation).  Services
are the canonical entry-points for the CLI and the public Python API.

Public surface:
    build_project           — dispatch build for any supported target
    build_html_project      — HTML-specific build (single-page or site)
    lint_project            — load, parse, and lint a project
    parse_project_documents — load, index, and parse a project
    run_index_check         — validate project index without full parse
    create_demo_project     — scaffold a demo project on disk
    DemoVariant             — literal type for demo variants
"""

from scribpy.core.build_html import build_html_project
from scribpy.core.build_project import build_project
from scribpy.core.demo import DemoVariant, create_demo_project
from scribpy.core.index_check import run_index_check
from scribpy.core.lint_project import lint_project
from scribpy.core.parse_check import parse_project_documents

__all__ = [
    "DemoVariant",
    "build_html_project",
    "build_project",
    "create_demo_project",
    "lint_project",
    "parse_project_documents",
    "run_index_check",
]
