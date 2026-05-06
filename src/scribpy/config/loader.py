"""Configuration loading and validation for ``scribpy.toml``."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from scribpy.config.types import Config, IndexConfig, PathConfig, ProjectConfig
from scribpy.model import Diagnostic, IndexMode
from scribpy.utils.toml import load_toml

CONFIG_FILENAME = "scribpy.toml"
_KNOWN_INDEX_MODES = frozenset[IndexMode]({"explicit", "filesystem", "hybrid"})

type RawSection = Mapping[str, object]


class ConfigParseError(ValueError):
    """Error raised when raw TOML data cannot be converted to typed config."""


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


def parse_config(raw: Mapping[str, object]) -> Config:
    """Parse raw TOML data into typed configuration objects.

    Args:
        raw: Raw TOML mapping loaded from ``scribpy.toml``.

    Returns:
        Parsed immutable configuration object.

    Raises:
        ConfigParseError: If a known configuration section or value has an
            invalid shape.
    """
    project = _parse_project_config(_section(raw, "project"))
    paths = _parse_path_config(_section(raw, "paths"))
    index = _parse_index_config(_section(raw, "index"))
    return Config(project=project, paths=paths, index=index)


def validate_config(config: Config) -> tuple[Diagnostic, ...]:
    """Validate semantic configuration constraints.

    Args:
        config: Parsed configuration object.

    Returns:
        Diagnostics describing invalid semantic values. An empty tuple means
        the configuration is valid for the current implementation phase.
    """
    diagnostics: list[Diagnostic] = []

    if not _is_safe_relative_path(config.paths.source):
        diagnostics.append(
            Diagnostic(
                severity="error",
                code="CFG004",
                message=(
                    "Configured source path must be relative and stay inside "
                    "the project."
                ),
                hint="Use a relative path such as 'doc' or 'docs'.",
            )
        )

    for file_path in config.index.files:
        if not _is_safe_relative_path(file_path):
            diagnostics.append(
                Diagnostic(
                    severity="error",
                    code="CFG004",
                    message=(
                        "Configured index file paths must be relative and stay "
                        "inside the project."
                    ),
                    path=file_path,
                    hint="Remove absolute paths and '..' segments from index.files.",
                )
            )

    return tuple(diagnostics)


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


def _section(raw: Mapping[str, object], name: str) -> RawSection:
    value = raw.get(name, {})
    if not isinstance(value, Mapping):
        raise ConfigParseError(f"Configuration section [{name}] must be a table.")
    return cast("RawSection", value)


def _parse_project_config(raw: RawSection) -> ProjectConfig:
    name = raw.get("name")
    if name is None:
        return ProjectConfig()
    if not isinstance(name, str):
        raise ConfigParseError("Configuration value project.name must be a string.")
    return ProjectConfig(name=name)


def _parse_path_config(raw: RawSection) -> PathConfig:
    source = raw.get("source", "doc")
    if not isinstance(source, str):
        raise ConfigParseError("Configuration value paths.source must be a string.")
    return PathConfig(source=Path(source))


def _parse_index_config(raw: RawSection) -> IndexConfig:
    mode = raw.get("mode", "filesystem")
    if not isinstance(mode, str):
        raise ConfigParseError("Configuration value index.mode must be a string.")
    if mode not in _KNOWN_INDEX_MODES:
        raise ConfigParseError(
            "Configuration value index.mode must be 'filesystem', 'explicit', "
            "or 'hybrid'."
        )

    files = raw.get("files", ())
    if not isinstance(files, Sequence) or isinstance(files, str):
        raise ConfigParseError("Configuration value index.files must be a list.")

    parsed_files: list[Path] = []
    for item in files:
        if not isinstance(item, str):
            raise ConfigParseError("Every index.files entry must be a string.")
        parsed_files.append(Path(item))

    return IndexConfig(mode=mode, files=tuple(parsed_files))


def _is_safe_relative_path(path: Path) -> bool:
    return not path.is_absolute() and ".." not in path.parts


__all__ = [
    "CONFIG_FILENAME",
    "ConfigParseError",
    "find_config",
    "load_config",
    "load_toml_config",
    "parse_config",
    "validate_config",
]
