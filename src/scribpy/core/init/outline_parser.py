"""Outline Markdown parser and validator for scribpy scaffold generation."""

from __future__ import annotations

from pathlib import Path

from mkforge.headings import Heading, extract_headings
from mkforge.slugify import slugify_heading
from mkforge.verification import MarkdownSource

from scribpy.core.init.outline_node import OutlineNode
from scribpy.errors import OutlineValidationError

_MAX_ALLOWED_DEPTH = 6


def parse_outline(path: Path, *, max_depth: int = 4) -> list[OutlineNode]:
    """Parse and validate an outline Markdown file into a heading tree.

    The outline file must contain only ATX headings (``# Title``) and blank
    lines. The first heading must be H1. No heading level may be skipped (e.g.
    an H3 cannot appear directly under an H1). No two siblings at the same
    parent may produce the same filesystem slug. Heading depth is limited to
    *max_depth*.

    Args:
        path: Path to the outline Markdown file.
        max_depth: Maximum ATX heading level accepted (inclusive, 1-6).
            Headings deeper than this level raise an error.

    Returns:
        Ordered list of root-level ``OutlineNode`` objects (all H1 nodes).
        Each node's ``children`` list holds the next-level headings, and so on
        recursively.

    Raises:
        OutlineValidationError: If the outline contains non-heading content,
            skipped levels, headings exceeding *max_depth*, empty heading
            titles, or sibling slug collisions.
        ValueError: If *max_depth* is not between 1 and 6 inclusive.
    """
    if not 1 <= max_depth <= _MAX_ALLOWED_DEPTH:
        msg = f"max_depth must be between 1 and 6, got {max_depth}"
        raise ValueError(msg)

    text = path.read_text(encoding="utf-8")
    source = MarkdownSource.from_text(text)
    _check_non_heading_lines(source)
    headings = extract_headings(source)
    _validate_headings(headings, max_depth)
    return _build_tree(headings)


def _check_non_heading_lines(source: MarkdownSource) -> None:
    """Raise if the source contains non-blank, non-heading lines.

    An outline file is only allowed to contain ATX headings and blank lines.
    This check runs before heading extraction so that invalid content is
    reported with a precise line number rather than silently ignored.

    Args:
        source: Parsed Markdown source to inspect.

    Raises:
        OutlineValidationError: On the first non-blank, non-ATX-heading line.
    """
    for line in source.lines:
        text = line.text.rstrip()
        if not text:
            continue
        parts = text.split()
        marker = parts[0] if parts else ""
        is_atx_marker = (
            marker and not marker.strip("#") and text.startswith("#")
        )
        if not is_atx_marker:
            raise OutlineValidationError(
                line.number,
                f"outline must contain only ATX headings, got: {text!r}",
            )
        title = text[len(marker) :].strip()
        if not title:
            raise OutlineValidationError(
                line.number, "heading title must not be empty"
            )


def _validate_headings(
    headings: tuple[Heading, ...],
    max_depth: int,
) -> None:
    """Validate structural constraints on extracted headings.

    Checks performed in order:
    - At least one heading exists.
    - First heading is H1.
    - No heading exceeds *max_depth*.
    - No level is skipped relative to its predecessor.
    - No two siblings under the same parent share the same filesystem slug.

    Args:
        headings: Ordered headings from ``extract_headings``.
        max_depth: Maximum accepted heading level.

    Raises:
        OutlineValidationError: On any structural violation.
    """
    if not headings:
        raise OutlineValidationError(0, "outline file contains no headings")

    first = headings[0]
    if first.level != 1:
        raise OutlineValidationError(
            first.line,
            f"first heading must be H1, got H{first.level}",
        )

    prev_level = 0
    sibling_slugs: dict[tuple[int, ...], set[str]] = {}
    level_stack: list[int] = []

    for heading in headings:
        _check_depth(heading, max_depth)
        _check_no_level_skip(heading, prev_level)
        while level_stack and level_stack[-1] >= heading.level:
            level_stack.pop()
        parent_key = tuple(level_stack)
        level_stack.append(heading.level)
        _check_no_slug_collision(heading, sibling_slugs, parent_key)
        prev_level = heading.level


def _check_depth(heading: Heading, max_depth: int) -> None:
    """Raise if a heading exceeds the allowed depth.

    Args:
        heading: Heading to check.
        max_depth: Maximum accepted heading level.

    Raises:
        OutlineValidationError: When heading level exceeds *max_depth*.
    """
    if heading.level > max_depth:
        raise OutlineValidationError(
            heading.line,
            f"heading depth H{heading.level} exceeds max_depth={max_depth}",
        )


def _check_no_level_skip(heading: Heading, prev_level: int) -> None:
    """Raise if a heading skips a level relative to its predecessor.

    Args:
        heading: Current heading to check.
        prev_level: Level of the immediately preceding heading (0 at start).

    Raises:
        OutlineValidationError: When a level is skipped.
    """
    if prev_level > 0 and heading.level > prev_level + 1:
        raise OutlineValidationError(
            heading.line,
            f"heading level skipped: H{prev_level} -> H{heading.level}",
        )


def _check_no_slug_collision(
    heading: Heading,
    sibling_slugs: dict[tuple[int, ...], set[str]],
    parent_key: tuple[int, ...],
) -> None:
    """Raise if a heading's slug collides with a sibling under the same parent.

    Args:
        heading: Heading whose slug to check.
        sibling_slugs: Mutable mapping of parent-path key to seen slug sets.
        parent_key: Tuple identifying the parent path in the heading tree.

    Raises:
        OutlineValidationError: When the slug already exists for this parent.
    """
    slug = slugify_heading(heading.text)
    seen = sibling_slugs.setdefault(parent_key, set())
    if slug in seen:
        raise OutlineValidationError(
            heading.line,
            f"duplicate sibling slug {slug!r} (title: {heading.text!r})",
        )
    seen.add(slug)


def _build_tree(headings: tuple[Heading, ...]) -> list[OutlineNode]:
    """Build a tree of OutlineNode objects from a flat heading sequence.

    Args:
        headings: Ordered headings from ``extract_headings``, already
            validated.

    Returns:
        Ordered list of root H1 ``OutlineNode`` objects with nested children.
    """
    roots: list[OutlineNode] = []
    stack: list[OutlineNode] = []

    for heading in headings:
        node = OutlineNode(
            title=heading.text,
            level=heading.level,
            line_number=heading.line,
        )
        while stack and stack[-1].level >= heading.level:
            stack.pop()
        if not stack:
            roots.append(node)
        else:
            stack[-1].children.append(node)
        stack.append(node)

    return roots
