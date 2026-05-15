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

    from scribpy.core import load_markdown, get_headings

    doc = load_markdown("docs/index.md")
    for h in get_headings(doc):
        print(h.level, h.title)
"""

from scribpy._version import __version__

__all__ = ["__version__"]
