"""Numeric formatting utilities for section-numbering styles."""

from __future__ import annotations


def format_number(value: int, style: str) -> str:
    """Format a counter value according to the numbering style.

    Args:
        value: Counter value to format.
        style: Numbering style: ``"alpha"``, ``"roman"``, or decimal.

    Returns:
        Formatted string representation of the value.
    """
    if style == "alpha":
        return _to_alpha(value)
    if style == "roman":
        return _to_roman(value)
    return str(value)


def _to_alpha(value: int) -> str:
    """Convert a positive integer to an uppercase alphabetic label.

    Args:
        value: Positive integer to convert.

    Returns:
        Alphabetic label (e.g. 1→A, 26→Z, 27→AA).
    """
    letters: list[str] = []
    while value:
        value, remainder = divmod(value - 1, 26)
        letters.append(chr(ord("A") + remainder))
    return "".join(reversed(letters))


def _to_roman(value: int) -> str:
    """Convert a positive integer to an uppercase Roman numeral.

    Args:
        value: Positive integer to convert.

    Returns:
        Roman numeral string (e.g. 4→IV, 9→IX).
    """
    numerals = (
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    )
    parts: list[str] = []
    for magnitude, numeral in numerals:
        count, value = divmod(value, magnitude)
        parts.append(numeral * count)
    return "".join(parts)


__all__ = ["format_number"]
