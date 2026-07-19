"""Internal Markdown link rewriting for assembled documents."""

from __future__ import annotations

import re

import mkforge

from scribpy.core.assembly.slug import slugify_heading
from scribpy.core.markdown_file import MarkdownFile

_H1_PATTERN = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
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


def build_numbered_file_slug_map(
    files: tuple[MarkdownFile, ...],
    content: str,
) -> dict[str, str]:
    """Build filename anchors from MkForge-numbered assembled Markdown.

    Args:
        files: Ordered Markdown files in the collection.
        content: MkForge-numbered assembled Markdown source.

    Returns:
        Mapping from filename to anchor slug for final numbered headings.
    """
    target_titles = _file_target_titles(files)
    numbered_titles = _numbered_heading_titles(content)
    result: dict[str, str] = {}
    search_start = 0
    for filename, target_title in target_titles:
        match_index = _matching_heading_index(
            numbered_titles,
            target_title,
            search_start,
        )
        if match_index is None:
            continue
        result[filename] = slugify_heading(numbered_titles[match_index])
        search_start = match_index + 1
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


def _file_target_titles(
    files: tuple[MarkdownFile, ...],
) -> tuple[tuple[str, str], ...]:
    """Return source filenames with unnumbered source H1 titles.

    Args:
        files: Ordered Markdown files in the collection.

    Returns:
        Filename and title pairs for files with an H1.
    """
    result: list[tuple[str, str]] = []
    for markdown_file in files:
        title = _extract_h1_title(markdown_file.content)
        if title is None:
            continue
        result.append(
            (
                markdown_file.name,
                mkforge.strip_heading_numbering_text(title),
            )
        )
    return tuple(result)


def _numbered_heading_titles(content: str) -> tuple[str, ...]:
    """Return heading titles from assembled numbered Markdown.

    Args:
        content: Assembled Markdown source.

    Returns:
        Heading titles without leading Markdown markers.
    """
    return tuple(
        match.group(1).strip() for match in _HEADING_PATTERN.finditer(content)
    )


def _matching_heading_index(
    numbered_titles: tuple[str, ...],
    target_title: str,
    search_start: int,
) -> int | None:
    """Return the next numbered heading matching an unnumbered source title.

    Args:
        numbered_titles: Final heading titles in assembled order.
        target_title: Source H1 title with source numbering removed by MkForge.
        search_start: First heading index to inspect.

    Returns:
        Matching heading index, or None when the title is absent.
    """
    for index in range(search_start, len(numbered_titles)):
        title = numbered_titles[index]
        if mkforge.strip_heading_numbering_text(title) == target_title:
            return index
    return None


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
