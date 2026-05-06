"""Semantic extractors operating on a MarkdownAst.

Functions:
    extract_headings -- ATX headings with level, title, anchor and line.
    extract_links    -- Markdown inline links as Reference objects.
    extract_assets   -- Markdown inline images as AssetRef objects.

Anchor generation follows the GitHub-compatible convention so that links
within rendered documents are predictable across renderers.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

from scribpy.model.markdown import AssetRef, Heading, MarkdownAst, Reference

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_headings(ast: MarkdownAst) -> tuple[Heading, ...]:
    """Extract ATX headings from a parsed Markdown AST.

    Args:
        ast: Parser-neutral AST produced by ``parse_markdown``.

    Returns:
        Ordered tuple of ``Heading`` objects carrying level, title, anchor
        (GitHub-compatible) and one-based line number.
    """
    headings: list[Heading] = []
    tokens = ast.tokens
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.get("type") == "heading_open":
            level = _heading_level(token)
            line = _heading_line(token)
            title = ""
            if i + 1 < len(tokens) and tokens[i + 1].get("type") == "inline":
                title = str(tokens[i + 1].get("content", ""))
            anchor = _github_anchor(title)
            headings.append(Heading(level=level, title=title, anchor=anchor, line=line))
        i += 1
    return tuple(headings)


def extract_links(ast: MarkdownAst) -> tuple[Reference, ...]:
    """Extract inline Markdown links from a parsed AST.

    Only ``[text](target)`` links are extracted. Images are excluded —
    use :func:`extract_assets` for those.

    Args:
        ast: Parser-neutral AST produced by ``parse_markdown``.

    Returns:
        Ordered tuple of ``Reference`` objects. ``kind`` is ``"link"`` for
        plain URLs and ``"xref"`` for anchor-only targets. Local relative
        paths are resolved to a ``Path`` object.
    """
    refs: list[Reference] = []
    for token in ast.tokens:
        if token.get("type") != "inline":
            continue
        children = _get_children(token)
        line = _inline_line(token)
        i = 0
        while i < len(children):
            child = children[i]
            if child.get("type") == "link_open":
                raw_attrs = child.get("attrs")
                attrs = raw_attrs if isinstance(raw_attrs, Mapping) else {}
                href = str(attrs.get("href", ""))
                text = _collect_link_text(children, i + 1)
                refs.append(_build_reference(href, text, line))
            i += 1
    return tuple(refs)


def extract_assets(ast: MarkdownAst) -> tuple[AssetRef, ...]:
    """Extract inline Markdown image references from a parsed AST.

    Args:
        ast: Parser-neutral AST produced by ``parse_markdown``.

    Returns:
        Ordered tuple of ``AssetRef`` objects with ``kind="image"``.
        The ``target`` field preserves the raw ``src`` attribute; ``path``
        is set for local relative targets.
    """
    assets: list[AssetRef] = []
    for token in ast.tokens:
        if token.get("type") != "inline":
            continue
        children = _get_children(token)
        line = _inline_line(token)
        for child in children:
            if child.get("type") == "image":
                raw_attrs = child.get("attrs")
                attrs = raw_attrs if isinstance(raw_attrs, Mapping) else {}
                src = str(attrs.get("src", ""))
                alt = str(child.get("content", ""))
                path = _local_path(src)
                assets.append(
                    AssetRef(
                        kind="image",
                        target=src,
                        path=path,
                        title=alt or None,
                        line=line,
                    )
                )
    return tuple(assets)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _heading_level(token: Mapping[str, object]) -> int:
    tag = str(token.get("tag", "h1"))
    # tag is "h1" … "h6"
    try:
        return int(tag[1])
    except (IndexError, ValueError):
        return 1


def _heading_line(token: Mapping[str, object]) -> int | None:
    map_value = token.get("map")
    if isinstance(map_value, (list, tuple)) and map_value:
        try:
            return int(map_value[0]) + 1  # markdown-it-py is zero-based
        except (TypeError, ValueError):
            return None
    return None


def _inline_line(token: Mapping[str, object]) -> int | None:
    map_value = token.get("map")
    if isinstance(map_value, (list, tuple)) and map_value:
        try:
            return int(map_value[0]) + 1
        except (TypeError, ValueError):
            return None
    return None


def _github_anchor(title: str) -> str:
    """Generate a GitHub-compatible anchor slug from a heading title.

    Rules (https://docs.github.com/en/get-started/writing-on-github):
      1. lower-case the text;
      2. remove anything that is not a word character, space, or hyphen;
      3. replace spaces with hyphens.
    """
    lowered = title.lower()
    stripped = re.sub(r"[^\w\s-]", "", lowered)
    return re.sub(r"\s+", "-", stripped).strip("-")


def _get_children(token: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw = token.get("children")
    if not isinstance(raw, list):
        return []
    return [c for c in raw if isinstance(c, Mapping)]


def _collect_link_text(children: list[Mapping[str, object]], start: int) -> str:
    parts: list[str] = []
    for child in children[start:]:
        if child.get("type") == "link_close":
            break
        content = child.get("content")
        if content:
            parts.append(str(content))
    return "".join(parts)


def _build_reference(href: str, text: str, line: int | None) -> Reference:
    if href.startswith("#"):
        return Reference(kind="xref", target=href, text=text or None, line=line)
    path = _local_path(href)
    return Reference(kind="link", target=href, text=text or None, path=path, line=line)


def _local_path(target: str) -> Path | None:
    if not target:
        return None
    # External URLs and anchors are not local paths
    if target.startswith(("http://", "https://", "ftp://", "mailto:", "#")):
        return None
    return Path(target)


__all__ = ["extract_assets", "extract_headings", "extract_links"]
