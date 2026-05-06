"""Minimal Markdown frontmatter parsing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model import Diagnostic


@dataclass(frozen=True)
class FrontmatterResult:
    """Result of separating frontmatter from Markdown body.

    Attributes:
        frontmatter: Parsed key/value metadata. The MVP parser only supports
            simple ``key: value`` pairs.
        body: Markdown source after the frontmatter block, or the original
            source when no frontmatter block is present.
        body_start_line: One-based line number where ``body`` starts in the
            original source.
        diagnostics: Frontmatter diagnostics detected during parsing.
    """

    frontmatter: dict[str, str]
    body: str
    body_start_line: int
    diagnostics: tuple[Diagnostic, ...]


def parse_frontmatter(source: str, path: Path | None = None) -> FrontmatterResult:
    """Parse a minimal frontmatter block at the beginning of a Markdown source.

    The MVP parser intentionally supports only a leading block delimited by
    ``---`` and simple ``key: value`` metadata lines. Documents without a
    leading frontmatter block are valid and return an empty metadata mapping.

    Args:
        source: Raw Markdown source text.
        path: Optional path attached to produced diagnostics.

    Returns:
        Parsed frontmatter, body text, body start line and diagnostics.
    """
    lines = source.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return FrontmatterResult(
            frontmatter={},
            body=source,
            body_start_line=1,
            diagnostics=(),
        )

    closing_index = _find_closing_delimiter(lines)
    if closing_index is None:
        return FrontmatterResult(
            frontmatter={},
            body="",
            body_start_line=len(lines) + 1,
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="PRS002",
                    message="Frontmatter block is not closed.",
                    path=path,
                    line=1,
                    hint=(
                        "Close the frontmatter block with a line containing only '---'."
                    ),
                ),
            ),
        )

    frontmatter, diagnostics = _parse_frontmatter_lines(
        lines[1:closing_index],
        path=path,
    )
    body_start_line = closing_index + 2
    return FrontmatterResult(
        frontmatter=frontmatter,
        body="".join(lines[closing_index + 1 :]),
        body_start_line=body_start_line,
        diagnostics=diagnostics,
    )


def _find_closing_delimiter(lines: list[str]) -> int | None:
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return index
    return None


def _parse_frontmatter_lines(
    lines: list[str],
    *,
    path: Path | None,
) -> tuple[dict[str, str], tuple[Diagnostic, ...]]:
    frontmatter: dict[str, str] = {}
    diagnostics: list[Diagnostic] = []

    for offset, line in enumerate(lines, start=2):
        stripped = line.strip()
        if not stripped:
            continue
        if ":" not in stripped:
            diagnostics.append(_invalid_frontmatter_line(path, offset))
            continue
        key, value = stripped.split(":", maxsplit=1)
        key = key.strip()
        if not key:
            diagnostics.append(_invalid_frontmatter_line(path, offset))
            continue
        frontmatter[key] = value.strip()

    return frontmatter, tuple(diagnostics)


def _invalid_frontmatter_line(path: Path | None, line: int) -> Diagnostic:
    return Diagnostic(
        severity="error",
        code="PRS002",
        message="Invalid frontmatter line.",
        path=path,
        line=line,
        hint="Use simple 'key: value' frontmatter entries.",
    )


__all__ = ["FrontmatterResult", "parse_frontmatter"]
