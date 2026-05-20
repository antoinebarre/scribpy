"""YAML and TOML adapters for frontmatter parsing."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from scribpy.model import Diagnostic
from scribpy.parser.frontmatter_diagnostics import (
    invalid_toml,
    invalid_yaml,
    yaml_not_mapping,
)


def yaml_adapter(
    raw: str,
    *,
    path: Path | None,
) -> tuple[dict[str, Any], tuple[Diagnostic, ...]]:
    """Parse YAML frontmatter into a plain mapping.

    Args:
        raw: Raw YAML block content without delimiters.
        path: Optional source path attached to diagnostics.

    Returns:
        Parsed mapping and diagnostics.
    """
    import yaml  # noqa: PLC0415

    try:
        data = yaml.safe_load(raw) or {}
        if not isinstance(data, dict):
            return {}, (yaml_not_mapping(path),)
        return dict(data), ()
    except yaml.YAMLError as exc:
        return {}, (invalid_yaml(exc, path, yaml_error_line(exc)),)


def toml_adapter(
    raw: str,
    *,
    path: Path | None,
) -> tuple[dict[str, Any], tuple[Diagnostic, ...]]:
    """Parse TOML frontmatter into a plain mapping.

    Args:
        raw: Raw TOML block content without delimiters.
        path: Optional source path attached to diagnostics.

    Returns:
        Parsed mapping and diagnostics.
    """
    import tomlkit  # noqa: PLC0415
    import tomlkit.exceptions  # noqa: PLC0415

    try:
        data = tomlkit.loads(raw)
        return dict(data), ()
    except tomlkit.exceptions.TOMLKitError as exc:
        return {}, (invalid_toml(exc, path),)


def yaml_error_line(exc: Any) -> int | None:
    """Return the source line for a YAML parser exception when available.

    Args:
        exc: YAML parser exception.

    Returns:
        One-based Markdown source line, or ``None`` when unavailable.
    """
    mark = getattr(exc, "problem_mark", None)
    if mark is None:
        return None
    return int(mark.line) + 2


__all__ = ["toml_adapter", "yaml_adapter", "yaml_error_line"]
