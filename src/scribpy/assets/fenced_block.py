"""Shared utility for reading fenced code blocks line by line."""

from __future__ import annotations


def read_fenced_block(
    lines: list[str],
    start_index: int,
    close_marker: str,
) -> tuple[list[str], int | None]:
    """Collect lines inside a fenced block until the closing delimiter.

    Args:
        lines: All lines of the document (with or without line endings).
        start_index: Index of the first line *inside* the block (after the
            opening fence).
        close_marker: The stripped string that signals end-of-block (e.g.
            ``"```"``).

    Returns:
        A tuple ``(source_lines, close_index)`` where ``source_lines`` are
        the collected interior lines and ``close_index`` is the index of the
        closing-fence line, or ``None`` when no closing fence was found.
    """
    source_lines: list[str] = []
    index = start_index
    while index < len(lines) and lines[index].strip() != close_marker:
        source_lines.append(lines[index])
        index += 1
    return source_lines, index if index < len(lines) else None


__all__ = ["read_fenced_block"]
