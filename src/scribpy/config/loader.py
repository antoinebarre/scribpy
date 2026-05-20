"""Configuration loading and validation for ``scribpy.toml``."""

from __future__ import annotations

import tomllib
from pathlib import Path

from scribpy.config.parser import ConfigParseError, parse_config
from scribpy.config.types import Config
from scribpy.config.validation import validate_config
from scribpy.model import Diagnostic
from scribpy.utils.toml import load_toml

CONFIG_FILENAME = "scribpy.toml"


def find_config(start: Path) -> Path | None:
    """Find ``scribpy.toml`` by walking upward from a starting path.

    Args:
        start: Directory or file path from which the lookup starts.

    Returns:
        Path to the first discovered configuration file, or ``None`` when no
        configuration file exists in ``start`` or any parent directory.
    """
    current = start if start.is_dir() else start.parent
    for candidate_root in (current, *current.parents):
        candidate = candidate_root / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
    return None


def load_toml_config(path: Path) -> dict[str, object]:
    """Load raw TOML configuration from a file.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        Raw TOML data as a string-keyed dictionary.

    Raises:
        OSError: If the file cannot be read.
        tomllib.TOMLDecodeError: If the file content is not valid TOML.
    """
    return load_toml(path)


def load_config(path: Path) -> tuple[Config | None, tuple[Diagnostic, ...]]:
    """Load and validate configuration from a file or project path.

    Args:
        path: Path to ``scribpy.toml`` or to a directory inside a Scribpy
            project.

    Returns:
        A tuple containing the parsed configuration when loading succeeds, or
        ``None`` otherwise, plus diagnostics for expected user-facing failures.
    """
    config_path = path if path.name == CONFIG_FILENAME else find_config(path)
    if config_path is None or not config_path.is_file():
        return None, (
            Diagnostic(
                severity="error",
                code="CFG001",
                message="Could not find scribpy.toml.",
                path=path,
                hint="Create scribpy.toml at the project root or pass its path.",
            ),
        )

    try:
        raw = load_toml_config(config_path)
    except tomllib.TOMLDecodeError as error:
        return None, (
            Diagnostic(
                severity="error",
                code="CFG002",
                message=f"Invalid TOML: {error}",
                path=config_path,
            ),
        )
    except OSError as error:
        return None, (
            Diagnostic(
                severity="error",
                code="CFG001",
                message=f"Could not read scribpy.toml: {error}",
                path=config_path,
            ),
        )

    try:
        config = parse_config(raw)
    except ConfigParseError as error:
        return None, (
            Diagnostic(
                severity="error",
                code="CFG003",
                message=str(error),
                path=config_path,
            ),
        )

    return config, validate_config(config)


__all__ = [
    "CONFIG_FILENAME",
    "ConfigParseError",
    "find_config",
    "load_config",
    "load_toml_config",
    "parse_config",
    "validate_config",
]
