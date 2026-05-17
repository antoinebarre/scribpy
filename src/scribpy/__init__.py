"""scribpy — Docs-as-Code toolkit and document compiler.

Package layout
--------------
scribpy.cli
    Command-line interface (scribpy init / lint / build / …).
scribpy.core
    Public Python API facade for scripting and automation.
scribpy.config
    scribpy.toml loading, parsing, and validation.
scribpy.project
    Project scanning and document index management.
scribpy.model
    Frozen dataclasses: Project, Document, Heading, Reference, …
scribpy.parser
    Markdown parsing layer (MarkdownParser protocol + adapters).
scribpy.lint
    Documentation quality engine (lint rules + diagnostics).
scribpy.transforms
    Document transformation pipeline (TOC, includes, numbering, …).
scribpy.builders
    Output generation: Markdown, HTML, PDF.
scribpy.themes
    HTML / PDF templates and CSS theme management.
scribpy.assets
    Image, diagram, and static file handling.
scribpy.extensions
    Plugin registry for custom rules, transforms, and builders.
scribpy.utils
    Low-level path, string, I/O, and hashing helpers.

Quick start
-----------
::

    import scribpy

    scribpy.check_index(".")
    scribpy.lint(".")
    scribpy.build_html(".", mode="site")
"""

from scribpy._version import __version__
from scribpy.api import (
    build_html,
    build_markdown,
    check_index,
    check_parse,
    create_demo,
    lint,
)
from scribpy.logging import logging_context
from scribpy.model import BuildArtifact, BuildResult, LintResult, ParseResult

__all__ = [
    "BuildArtifact",
    "BuildResult",
    "LintResult",
    "ParseResult",
    "__version__",
    "build_html",
    "build_markdown",
    "check_index",
    "check_parse",
    "create_demo",
    "lint",
    "logging_context",
]
