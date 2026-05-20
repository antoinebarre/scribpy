"""Minimal Markdown frontmatter parsing with YAML and TOML support."""

from __future__ import annotations

from pathlib import Path

from scribpy.parser.frontmatter_adapters import (
    toml_adapter,
    yaml_adapter,
    yaml_error_line,
)
from scribpy.parser.frontmatter_blocks import parse_delimited_block
from scribpy.parser.frontmatter_types import FrontmatterResult

_YAML_DELIMITER = "---"
_TOML_DELIMITER = "+++"

_yaml_error_line = yaml_error_line


def parse_frontmatter(
    source: str, path: Path | None = None
) -> FrontmatterResult:
    """Separate and parse a frontmatter block at the start of a Markdown source.

    Supports YAML blocks delimited by ``---`` and TOML blocks delimited by
    ``+++``. Documents without a leading frontmatter block are valid and return
    an empty metadata mapping.

    Args:
        source: Raw Markdown source text.
        path: Optional path attached to produced diagnostics.

    Returns:
        Parsed frontmatter, body text, body start line and diagnostics.
    """
    lines = source.splitlines(keepends=True)
    if not lines:
        return FrontmatterResult(
            frontmatter={}, body=source, body_start_line=1, diagnostics=()
        )

    first = lines[0].strip()
    if first == _YAML_DELIMITER:
        return parse_delimited_block(
            lines,
            delimiter=_YAML_DELIMITER,
            adapter=lambda raw: yaml_adapter(raw, path=path),
            path=path,
        )
    if first == _TOML_DELIMITER:
        return parse_delimited_block(
            lines,
            delimiter=_TOML_DELIMITER,
            adapter=lambda raw: toml_adapter(raw, path=path),
            path=path,
        )

    return FrontmatterResult(
        frontmatter={}, body=source, body_start_line=1, diagnostics=()
    )


__all__ = ["FrontmatterResult", "_yaml_error_line", "parse_frontmatter"]
