"""Markdown parsing layer for scribpy.

Responsibilities:
    - Parse Markdown source into a MarkdownAst (parse_markdown)
    - Extract YAML/TOML frontmatter (parse_frontmatter)
    - Read and parse a SourceFile into a Document (parse_document_file)
    - Parse all project source files in bulk (parse_documents)

The MarkdownParser protocol is injected; concrete adapters
(e.g. markdown-it-py) live in scribpy.parser.adapters.

Extraction helpers:
    extract_headings(ast) -> tuple[Heading, ...]
    extract_links(ast)    -> tuple[Reference, ...]
    extract_assets(ast)   -> tuple[AssetRef, ...]
"""

from __future__ import annotations

from scribpy.parser.document import order_by_index, parse_document_file, parse_documents
from scribpy.parser.extractors import extract_assets, extract_headings, extract_links
from scribpy.parser.frontmatter import FrontmatterResult, parse_frontmatter
from scribpy.parser.markdown import parse_markdown

__all__ = [
    "FrontmatterResult",
    "extract_assets",
    "extract_headings",
    "extract_links",
    "order_by_index",
    "parse_document_file",
    "parse_documents",
    "parse_frontmatter",
    "parse_markdown",
]
