"""Internal Markdown link rewriting for assembled documents."""

from __future__ import annotations

import re

from scribpy.core.assembly.slug import slugify_heading
from scribpy.core.markdown_file import MarkdownFile

_H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_INTERNAL_LINK_PATTERN = re.compile(
    r"(?<!!)\[(?P<label>[^\]]+)]\((?P<target>[^)#\n]+\.(?:md|markdown))\)",
    re.IGNORECASE,
)


def build_file_slug_map(
    files: tuple[MarkdownFile, ...],
) -> dict[str, str]:
    """Build a mapping from Markdown filename to its H1 anchor slug.

    Each file is mapped by its bare filename (e.g. ``"chapitre.md"``) to
    the GitHub-style slug of its first H1 heading title.  Files without
    an H1 are excluded from the map.

    Args:
        files: Ordered Markdown files in the collection.

    Returns:
        Mapping from filename to anchor slug.
    """
    result: dict[str, str] = {}
    for markdown_file in files:
        title = _extract_h1_title(markdown_file.content)
        if title is not None:
            result[markdown_file.name] = slugify_heading(title)
    return result


def rewrite_internal_links(
    content: str,
    file_slug_map: dict[str, str],
) -> str:
    """Rewrite internal Markdown file links to anchor references.

    Each ``[label](file.md)`` link whose target filename appears in
    *file_slug_map* is replaced by ``[label](#slug)``.  Links targeting
    files absent from the map are left unchanged.

    Args:
        content: Markdown source text to transform.
        file_slug_map: Mapping from filename to anchor slug.

    Returns:
        Markdown source text with internal links rewritten as anchors.
    """

    def _replace(match: re.Match[str]) -> str:
        target = match.group("target")
        filename = target.rsplit("/", 1)[-1]
        slug = file_slug_map.get(filename)
        if slug is None:
            return match.group(0)
        return f"[{match.group('label')}](#{slug})"

    return _INTERNAL_LINK_PATTERN.sub(_replace, content)


def _extract_h1_title(content: str) -> str | None:
    """Return the first H1 heading title found in Markdown content.

    Args:
        content: Markdown source text to scan.

    Returns:
        H1 title text without the leading ``# ``, or None if absent.
    """
    match = _H1_PATTERN.search(content)
    if match is None:
        return None
    return match.group(1).strip()
