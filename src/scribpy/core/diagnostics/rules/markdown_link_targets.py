"""Utilities shared by Markdown link diagnostic rules."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import SplitResult, unquote, urlsplit

from mkforge import MarkdownSource
from mkforge.verification.source_scan import lines_outside_fenced_code

from scribpy.core.markdown_file import MarkdownFile
from scribpy.core.markdown_patterns import _MARKDOWN_SUFFIXES

_MARKDOWN_LINK = re.compile(
    r"(?<!!)\[(?P<label>[^\]]+)]\((?P<body>[^)\n]*)\)",
)


@dataclass(frozen=True, slots=True)
class MarkdownLinkReference:
    """Represent one Markdown link reference found in source text.

    Attributes:
        label: Link label text between square brackets.
        target: Link target path or URL.
        title: Optional link title.
        line: One-based line number in the source text.
        column: One-based column number in the source text.
    """

    label: str
    target: str
    title: str | None
    line: int
    column: int


@dataclass(frozen=True, slots=True)
class MarkdownLinkTarget:
    """Represent a classified Markdown link target.

    Attributes:
        reference: Markdown link reference found in source text.
        resolved_path: Local filesystem path when the target is local.
        is_external: Whether the target is external to the documentation tree.
        is_anchor_only: Whether the target points to the same page anchor.
        is_markdown: Whether the target names a Markdown file.
    """

    reference: MarkdownLinkReference
    resolved_path: Path | None
    is_external: bool
    is_anchor_only: bool
    is_markdown: bool


def extract_markdown_links(content: str) -> tuple[MarkdownLinkReference, ...]:
    """Extract inline Markdown links outside fenced code blocks.

    Args:
        content: Markdown source text to scan.

    Returns:
        Markdown links found outside fenced code blocks.
    """
    source = MarkdownSource.from_text(content)
    links: list[MarkdownLinkReference] = []
    for line in lines_outside_fenced_code(source):
        links.extend(_line_links(line.text, line.number))
    return tuple(links)


def classify_markdown_link_target(
    root: Path,
    markdown_file: MarkdownFile,
    reference: MarkdownLinkReference,
) -> MarkdownLinkTarget:
    """Classify and resolve a Markdown link target.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the link reference.
        reference: Markdown link reference to classify.

    Returns:
        Classified Markdown link target.
    """
    parsed = urlsplit(reference.target)
    if reference.target.startswith("#"):
        return _target(reference, None, is_anchor_only=True)
    if _is_external(parsed):
        return _target(reference, None, is_external=True)
    path = Path(unquote(parsed.path))
    if path.suffix.lower() not in _MARKDOWN_SUFFIXES:
        return _target(reference, None)
    return _target(
        reference,
        _local_markdown_path(root, markdown_file, path),
        is_markdown=True,
    )


def _line_links(
    line: str, line_number: int
) -> tuple[MarkdownLinkReference, ...]:
    """Return Markdown links found in one line.

    Args:
        line: Markdown source line.
        line_number: One-based source line number.

    Returns:
        Markdown link references found in the line.
    """
    return tuple(
        _link_reference(match, line_number)
        for match in _MARKDOWN_LINK.finditer(line)
    )


def _link_reference(
    match: re.Match[str],
    line_number: int,
) -> MarkdownLinkReference:
    """Return a Markdown link reference from a regex match.

    Args:
        match: Regex match containing link label and body.
        line_number: One-based source line number.

    Returns:
        Markdown link reference.
    """
    target, title = _split_link_body(match.group("body"))
    return MarkdownLinkReference(
        label=match.group("label"),
        target=target,
        title=title,
        line=line_number,
        column=match.start() + 1,
    )


def _split_link_body(body: str) -> tuple[str, str | None]:
    """Split a Markdown link body into target and optional title.

    Args:
        body: Text between Markdown link parentheses.

    Returns:
        Link target and optional link title.
    """
    try:
        parts = tuple(shlex.split(body.strip()))
    except ValueError:
        parts = tuple(body.strip().split())
    if not parts:
        return "", None
    return parts[0], " ".join(parts[1:]) or None


def _is_external(parsed_target: SplitResult) -> bool:
    """Return whether a parsed target points outside local files.

    Args:
        parsed_target: Parsed URL target.

    Returns:
        True when the target has an external URL scheme or network location.
    """
    return bool(
        parsed_target.netloc
        or (parsed_target.scheme and parsed_target.scheme != "file")
    )


def _local_markdown_path(
    root: Path,
    markdown_file: MarkdownFile,
    path: Path,
) -> Path:
    """Resolve a local Markdown link path.

    Args:
        root: Collection root directory.
        markdown_file: Markdown file containing the link reference.
        path: Parsed local target path.

    Returns:
        Local filesystem path represented by the target.
    """
    if path.is_absolute():
        return root / path.relative_to("/")
    return markdown_file.path.parent / path


def _target(
    reference: MarkdownLinkReference,
    resolved_path: Path | None,
    *,
    is_external: bool = False,
    is_anchor_only: bool = False,
    is_markdown: bool = False,
) -> MarkdownLinkTarget:
    """Create a classified Markdown link target.

    Args:
        reference: Markdown link reference found in source text.
        resolved_path: Local filesystem path when available.
        is_external: Whether the target is external.
        is_anchor_only: Whether the target is an anchor-only reference.
        is_markdown: Whether the target names a Markdown file.

    Returns:
        Classified Markdown link target.
    """
    return MarkdownLinkTarget(
        reference=reference,
        resolved_path=resolved_path,
        is_external=is_external,
        is_anchor_only=is_anchor_only,
        is_markdown=is_markdown,
    )
