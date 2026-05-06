"""Low-level reusable utilities for scribpy.

These helpers are small, stable, and domain-independent.
Sub-modules:
    utils.file_utils         — Markdown file discovery and I/O
    utils.markdown_generator — Random GFM document generator (testing / demo)
    utils.diagnostics        — Diagnostic formatting and aggregation

Planned sub-modules:
    utils.paths        — path normalization and resolution
    utils.strings      — slugify, text normalization
    utils.toml         — TOML reading helpers
    utils.yaml         — YAML reading helpers
    utils.hashing      — deterministic content hashes
    utils.io           — generic text file read/write
    utils.collections  — unique_preserve_order and similar helpers
"""

from scribpy.utils.diagnostics import (
    DIAGNOSTIC_SEVERITY_ORDER,
    format_diagnostic,
    format_diagnostics,
    group_diagnostics_by_path,
    has_errors,
    severity_rank,
    sort_diagnostics,
)
from scribpy.utils.file_utils import (
    is_md_file,
    list_md_files,
    read_md_file,
    write_md_file,
)
from scribpy.utils.markdown_generator import MarkdownConfig, generate_markdown

__all__ = [
    "DIAGNOSTIC_SEVERITY_ORDER",
    "MarkdownConfig",
    "format_diagnostic",
    "format_diagnostics",
    "generate_markdown",
    "group_diagnostics_by_path",
    "has_errors",
    "is_md_file",
    "list_md_files",
    "read_md_file",
    "severity_rank",
    "sort_diagnostics",
    "write_md_file",
]
