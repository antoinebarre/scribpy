"""Automatic section numbering for GFM reports."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class NumberingContext:
    """Tracks counters at each heading depth during traversal.

    Usage pattern:
        ctx.push()          # enter a new depth level (counter starts at 0)
        ctx.next()          # increment for current sibling
        prefix = ctx.prefix()
        ctx.pop()           # leave depth level
    """

    _counters: list[int] = field(default_factory=list)

    def push(self) -> None:
        """Descend one heading level, counter starts at 0."""
        self._counters.append(0)

    def pop(self) -> None:
        """Ascend one heading level."""
        self._counters.pop()

    def next(self) -> None:
        """Increment the counter at the current depth."""
        self._counters[-1] += 1

    def prefix(self) -> str:
        """Return the dotted numbering prefix for the current position.

        Returns:
            A string like ``'1.2.3.'`` reflecting all active counters.
        """
        return ".".join(str(c) for c in self._counters) + "."


def numbered_title(title: str, ctx: NumberingContext) -> str:
    """Return a title prefixed with its section number.

    Args:
        title: The raw heading title.
        ctx: The active NumberingContext.

    Returns:
        A string like ``'1.2. My Title'``.
    """
    return f"{ctx.prefix()} {title}"
