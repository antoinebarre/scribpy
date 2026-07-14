"""Outline document tree node for scribpy scaffold generation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OutlineNode:
    """One heading node in a parsed outline document tree.

    Represents a single ATX heading extracted from an outline Markdown file.
    Children are headings directly nested under this node (next depth level).

    Attributes:
        title: Raw heading text without the leading ``#`` markers.
        level: ATX heading level (1 = H1, 2 = H2, … 6 = H6).
        line_number: 1-based source line where this heading appeared.
        children: Ordered direct child nodes (one level deeper).
    """

    title: str
    level: int
    line_number: int
    children: list[OutlineNode] = field(default_factory=list)
