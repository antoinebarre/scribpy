"""Shared parsing primitives for config section parsers.

The config parser is split by user-facing TOML sections, but each section still
needs the same table guards and optional scalar handling.  Keeping those small
checks here gives the section modules one place to agree on error wording while
leaving each module responsible for its own domain values.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import cast

type RawSection = Mapping[str, object]


class ConfigParseError(ValueError):
    """Error raised when raw TOML data cannot be converted to typed config."""


def section(raw: Mapping[str, object], name: str) -> RawSection:
    """Return a top-level TOML table or raise a config shape error.

    Args:
        raw: Raw TOML root mapping.
        name: Top-level section name.

    Returns:
        The section as a raw mapping.
    """
    value = raw.get(name, {})
    if not isinstance(value, Mapping):
        raise ConfigParseError(
            f"Configuration section [{name}] must be a table."
        )
    return cast("RawSection", value)


def nested_section(raw: RawSection, name: str, parent: str) -> RawSection:
    """Return a nested TOML table with a parent-qualified error message.

    Args:
        raw: Raw parent section.
        name: Nested section name.
        parent: Parent section name used in diagnostics.

    Returns:
        The nested section as a raw mapping.
    """
    value = raw.get(name, {})
    if not isinstance(value, Mapping):
        raise ConfigParseError(
            f"Configuration section [{parent}.{name}] must be a table."
        )
    return cast("RawSection", value)


def parse_optional_str(raw: RawSection, key: str, section: str) -> str | None:
    """Parse an optional string value from a config section.

    Args:
        raw: Raw section containing the optional value.
        key: Value key to read.
        section: User-facing section name used in diagnostics.

    Returns:
        The string value, or ``None`` when absent.
    """
    value = raw.get(key)
    if value is not None and not isinstance(value, str):
        raise ConfigParseError(
            f"Configuration value {section}.{key} must be a string."
        )
    return value if isinstance(value, str) else None


__all__ = [
    "ConfigParseError",
    "RawSection",
    "nested_section",
    "parse_optional_str",
    "section",
]
