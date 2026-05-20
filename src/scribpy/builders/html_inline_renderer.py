"""Markdown-to-HTML inline and block rendering utilities."""

from __future__ import annotations

import re

_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def render_markdown_to_html(content: str) -> str:
    """Convert Markdown content to HTML using lightweight built-in rendering.

    Args:
        content: Markdown text to render.

    Returns:
        HTML string without surrounding ``<html>`` scaffolding.
    """
    html_lines: list[str] = []
    code_lines: list[str] = []
    code_lang = ""
    in_code_block = False

    for line in content.split("\n"):
        if line.startswith("```"):
            in_code_block, code_lines, code_lang = _handle_fence(
                line, in_code_block, code_lines, code_lang, html_lines
            )
            continue
        if in_code_block:
            code_lines.append(line)
            continue
        html_lines.append(_render_block_line(line))

    return "\n".join(html_lines)


def _handle_fence(
    line: str,
    in_code_block: bool,
    code_lines: list[str],
    code_lang: str,
    html_lines: list[str],
) -> tuple[bool, list[str], str]:
    """Toggle code fence state and emit a block when closing.

    Args:
        line: Current line starting with backtick fence.
        in_code_block: Whether we are currently inside a code block.
        code_lines: Lines accumulated inside the current code block.
        code_lang: Language tag of the current code block.
        html_lines: Accumulated HTML output lines (mutated in place).

    Returns:
        Updated ``(in_code_block, code_lines, code_lang)`` triple.
    """
    if in_code_block:
        escaped = "\n".join(escape_html(ln) for ln in code_lines)
        lang_attr = f' class="language-{code_lang}"' if code_lang else ""
        html_lines.append(f"<pre><code{lang_attr}>{escaped}</code></pre>")
        return False, [], ""
    return True, [], line[3:].strip()


def _render_block_line(line: str) -> str:
    """Convert one non-code Markdown line to its HTML equivalent.

    Args:
        line: A single Markdown line outside any code fence.

    Returns:
        HTML representation of the line.
    """
    heading_match = _HEADING_RE.match(line)
    if heading_match:
        marks, title = heading_match.groups()
        level = len(marks)
        return (
            f'<h{level} id="{_anchor(title)}">{inline_html(title)}</h{level}>'
        )
    if line.startswith("---") and line.strip("-") == "":
        return "<hr>"
    stripped = line.strip()
    return f"<p>{inline_html(stripped)}</p>" if stripped else ""


def _anchor(title: str) -> str:
    """Convert a heading title to a URL-safe anchor slug."""
    lowered = title.lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered)
    return re.sub(r"\s+", "-", stripped).strip("-")


def escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Raw string to escape.

    Returns:
        String with ``&``, ``<``, ``>``, and ``"`` replaced by HTML entities.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def inline_html(text: str) -> str:
    """Render inline Markdown (links, images, bold, italic, code) to HTML.

    Args:
        text: Markdown inline text to convert.

    Returns:
        HTML string with inline elements replaced by their HTML equivalents.
    """
    text = _IMAGE_RE.sub(
        lambda m: f'<img src="{m.group(2)}" alt="{escape_html(m.group(1))}">',
        text,
    )
    text = _LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', text
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(
        r"`(.+?)`", lambda m: f"<code>{escape_html(m.group(1))}</code>", text
    )
    return text


__all__ = [
    "escape_html",
    "inline_html",
    "render_markdown_to_html",
]
