"""Minimal Markdown frontmatter parsing with YAML and TOML support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scribpy.model import Diagnostic

_YAML_DELIMITER = "---"
_TOML_DELIMITER = "+++"


@dataclass(frozen=True)
class FrontmatterResult:
    """Result of separating frontmatter from Markdown body.

    Attributes:
        frontmatter: Parsed key/value metadata. Supports YAML (``---``) and
            TOML (``+++``) blocks with native types (str, int, bool, list…).
        body: Markdown source after the frontmatter block, or the original
            source when no frontmatter block is present.
        body_start_line: One-based line number where ``body`` starts in the
            original source.
        diagnostics: Frontmatter diagnostics detected during parsing.
    """

    frontmatter: dict[str, Any]
    body: str
    body_start_line: int
    diagnostics: tuple[Diagnostic, ...]


def parse_frontmatter(source: str, path: Path | None = None) -> FrontmatterResult:
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
        return _parse_delimited_block(
            lines, delimiter=_YAML_DELIMITER, adapter=_yaml_adapter, path=path
        )
    if first == _TOML_DELIMITER:
        return _parse_delimited_block(
            lines, delimiter=_TOML_DELIMITER, adapter=_toml_adapter, path=path
        )

    return FrontmatterResult(
        frontmatter={}, body=source, body_start_line=1, diagnostics=()
    )


def _parse_delimited_block(
    lines: list[str],
    *,
    delimiter: str,
    adapter: Any,
    path: Path | None,
) -> FrontmatterResult:
    closing_index = _find_closing_delimiter(lines, delimiter)
    if closing_index is None:
        return FrontmatterResult(
            frontmatter={},
            body="",
            body_start_line=len(lines) + 1,
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="PRS002",
                    message=(
                        f"Frontmatter block opened with '{delimiter}' is not closed."
                    ),
                    path=path,
                    line=1,
                    hint=(
                        f"Close the frontmatter block with a line"
                        f" containing only '{delimiter}'."
                    ),
                ),
            ),
        )

    raw_block = "".join(lines[1:closing_index])
    frontmatter, diagnostics = adapter(raw_block, path=path)
    body_start_line = closing_index + 2
    return FrontmatterResult(
        frontmatter=frontmatter,
        body="".join(lines[closing_index + 1 :]),
        body_start_line=body_start_line,
        diagnostics=diagnostics,
    )


def _find_closing_delimiter(lines: list[str], delimiter: str) -> int | None:
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == delimiter:
            return index
    return None


def _yaml_adapter(
    raw: str,
    *,
    path: Path | None,
) -> tuple[dict[str, Any], tuple[Diagnostic, ...]]:
    import yaml  # noqa: PLC0415

    try:
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return {}, (
                Diagnostic(
                    severity="error",
                    code="PRS002",
                    message=(
                        "YAML frontmatter must be a mapping, not a scalar or list."
                    ),
                    path=path,
                    line=1,
                    hint=("Use 'key: value' pairs at the top level of the YAML block."),
                ),
            )
        return dict(data), ()
    except yaml.YAMLError as exc:
        line = _yaml_error_line(exc)
        return {}, (
            Diagnostic(
                severity="error",
                code="PRS002",
                message=f"Invalid YAML frontmatter: {exc}",
                path=path,
                line=line,
                hint="Fix the YAML syntax in the frontmatter block.",
            ),
        )


def _toml_adapter(
    raw: str,
    *,
    path: Path | None,
) -> tuple[dict[str, Any], tuple[Diagnostic, ...]]:
    import tomlkit  # noqa: PLC0415
    import tomlkit.exceptions  # noqa: PLC0415

    try:
        data = tomlkit.loads(raw)
        return dict(data), ()
    except tomlkit.exceptions.TOMLKitError as exc:
        return {}, (
            Diagnostic(
                severity="error",
                code="PRS002",
                message=f"Invalid TOML frontmatter: {exc}",
                path=path,
                line=None,
                hint="Fix the TOML syntax in the frontmatter block.",
            ),
        )


def _yaml_error_line(exc: Any) -> int | None:
    mark = getattr(exc, "problem_mark", None)
    if mark is None:
        return None
    return int(mark.line) + 2


__all__ = ["FrontmatterResult", "parse_frontmatter"]
