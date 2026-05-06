"""Markdown parsing via markdown-it-py, isolated behind the MarkdownParser protocol."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from scribpy.model import MarkdownAst
from scribpy.model.protocols import MarkdownParser

_BACKEND = "markdown-it-py"

_SUPPORTED_BLOCK_TYPES = frozenset(
    {
        "heading_open",
        "heading_close",
        "inline",
        "paragraph_open",
        "paragraph_close",
        "fence",
        "bullet_list_open",
        "bullet_list_close",
        "ordered_list_open",
        "ordered_list_close",
        "list_item_open",
        "list_item_close",
        "html_block",
        "hr",
        "blockquote_open",
        "blockquote_close",
        "code_block",
    }
)


def parse_markdown(body: str, parser: MarkdownParser | None = None) -> MarkdownAst:
    """Parse Markdown source into a ``MarkdownAst``.

    Uses the bundled ``markdown-it-py`` adapter when no ``parser`` is injected.

    Args:
        body: Markdown source text (without frontmatter).
        parser: Optional external parser conforming to ``MarkdownParser``. When
            provided the adapter is bypassed entirely.

    Returns:
        A parser-neutral ``MarkdownAst`` whose tokens are plain mappings.
    """
    if parser is not None:
        return parser.parse(body)
    return _markdown_adapter(body)


def _markdown_adapter(body: str) -> MarkdownAst:
    from markdown_it import MarkdownIt  # noqa: PLC0415

    md = MarkdownIt()
    raw_tokens = md.parse(body)
    tokens = tuple(_convert_token(t) for t in raw_tokens)
    return MarkdownAst(backend=_BACKEND, tokens=tokens)


def _convert_token(token: Any) -> Mapping[str, object]:
    result: dict[str, object] = {
        "type": token.type,
        "tag": token.tag,
        "level": token.level,
        "content": token.content,
        "map": list(token.map) if token.map else None,
        "attrs": dict(token.attrs) if token.attrs else {},
    }
    if token.children:
        result["children"] = [_convert_child(c) for c in token.children]
    return result


def _convert_child(token: Any) -> Mapping[str, object]:
    return {
        "type": token.type,
        "tag": token.tag,
        "content": token.content,
        "attrs": dict(token.attrs) if token.attrs else {},
    }


__all__ = ["parse_markdown"]
