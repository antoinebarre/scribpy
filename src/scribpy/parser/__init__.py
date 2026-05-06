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
