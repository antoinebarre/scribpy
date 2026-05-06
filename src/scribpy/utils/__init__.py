"""Low-level reusable utilities for scribpy.

These helpers are small, stable, and domain-independent.
Sub-modules:
    utils.file_utils         — Markdown file discovery and I/O
    utils.markdown_generator — Random GFM document generator (testing / demo)

Planned sub-modules:
    utils.paths        — path normalization and resolution
    utils.strings      — slugify, text normalization
    utils.toml         — TOML reading helpers
    utils.yaml         — YAML reading helpers
    utils.hashing      — deterministic content hashes
    utils.io           — generic text file read/write
    utils.diagnostics  — Diagnostic formatting and aggregation
    utils.collections  — unique_preserve_order and similar helpers
"""

from scribpy.utils.file_utils import (
    is_md_file,
    list_md_files,
    read_md_file,
    write_md_file,
)
from scribpy.utils.markdown_generator import MarkdownConfig, generate_markdown

__all__ = [
    "MarkdownConfig",
    "generate_markdown",
    "is_md_file",
    "list_md_files",
    "read_md_file",
    "write_md_file",
]
