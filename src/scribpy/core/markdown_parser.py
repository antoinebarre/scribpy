"""Markdown text to :class:`ParsedDocument` transformation.

Uses ``markdown-it-py`` for CommonMark-compliant parsing.  The parser
extracts headings, image references, and diagram code blocks from the
token stream in a single pass.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence

from markdown_it import MarkdownIt
from markdown_it.token import Token

from scribpy.core.document import (
    DiagramBlock,
    Heading,
    ImageRef,
    ParsedDocument,
)

_DIAGRAM_ENGINES = frozenset({"plantuml", "mermaid"})

_SLUG_STRIP_RE = re.compile(r"[^\w\s-]")
_SLUG_SPACE_RE = re.compile(r"[-\s]+")


def _slugify(text: str) -> str:
    """Convert heading text to a URL-friendly anchor slug.

    Args:
        text: Plain heading text.

    Returns:
        A lowercased, hyphen-separated slug with non-alphanumeric
        characters removed.
    """
    normalized = unicodedata.normalize("NFKD", text)
    stripped = _SLUG_STRIP_RE.sub("", normalized)
    return _SLUG_SPACE_RE.sub("-", stripped).strip("-").lower()


def _collect_inline_text(tokens: Sequence[Token]) -> str:
    """Extract plain text from a list of inline child tokens.

    Args:
        tokens: Child tokens of an ``inline`` token (from
            ``markdown-it-py``).

    Returns:
        Concatenated text content with markup stripped.
    """
    parts: list[str] = []
    for child in tokens:
        content: str = child.content or ""
        if content:
            parts.append(content)
    return "".join(parts)


def _extract_heading(tok: Token, next_tok: Token | None) -> Heading:
    """Build a Heading from a heading_open token and its inline sibling.

    Args:
        tok: The ``heading_open`` token.
        next_tok: The next token in the stream (expected to be
            ``inline``), or ``None``.

    Returns:
        A :class:`Heading` with level, text, and anchor.
    """
    level = int(tok.tag[1:])
    text = ""
    if next_tok is not None and next_tok.type == "inline":
        text = _collect_inline_text(next_tok.children or [])
    return Heading(level=level, text=text, anchor=_slugify(text))


def _extract_images(tok: Token) -> list[ImageRef]:
    """Extract image references from an inline token's children.

    Args:
        tok: An ``inline`` token whose children may contain images.

    Returns:
        List of :class:`ImageRef` found in this token.
    """
    refs: list[ImageRef] = []
    for child in tok.children or []:
        if child.type == "image":
            src = str(child.attrGet("src") or "")
            alt = child.content or ""
            title = str(child.attrGet("title") or "")
            refs.append(ImageRef(src=src, alt=alt, title=title))
    return refs


def _extract_diagram(tok: Token, index: int) -> DiagramBlock | None:
    """Try to extract a diagram block from a fence token.

    Args:
        tok: A ``fence`` token.
        index: The diagram index to assign if this is a diagram block.

    Returns:
        A :class:`DiagramBlock` if the fence language is a known
        diagram engine, otherwise ``None``.
    """
    info = (tok.info or "").strip().lower()
    if info not in _DIAGRAM_ENGINES:
        return None
    return DiagramBlock(engine=info, source=tok.content, index=index)


def parse(markdown_text: str) -> ParsedDocument:
    """Parse Markdown text into a structured document model.

    This function performs a single-pass extraction of headings, image
    references, and diagram code blocks from the token stream, then
    renders the full HTML body.

    Args:
        markdown_text: Raw Markdown source (UTF-8 string).

    Returns:
        A :class:`ParsedDocument` containing the rendered HTML and
        extracted metadata.
    """
    md = MarkdownIt("commonmark", {"html": True})
    tokens = md.parse(markdown_text)

    headings: list[Heading] = []
    images: list[ImageRef] = []
    diagrams: list[DiagramBlock] = []
    diagram_index = 0

    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            next_tok = tokens[i + 1] if i + 1 < len(tokens) else None
            headings.append(_extract_heading(tok, next_tok))
        elif tok.type == "inline":
            images.extend(_extract_images(tok))
        elif tok.type == "fence":
            block = _extract_diagram(tok, diagram_index)
            if block is not None:
                diagrams.append(block)
                diagram_index += 1

    html = md.render(markdown_text)

    return ParsedDocument(
        html=html,
        headings=tuple(headings),
        images=tuple(images),
        diagrams=tuple(diagrams),
    )
