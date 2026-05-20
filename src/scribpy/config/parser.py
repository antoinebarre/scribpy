"""Typed parsing for core ``scribpy.toml`` sections.

This module translates raw TOML tables into immutable config objects for the
project, source paths, document index, and assembled-document options.  HTML
builder parsing lives in its own module because it has renderer-specific nested
tables and output-mode rules that change independently from the core project
shape.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from scribpy.config.document_parser import parse_document_config
from scribpy.config.html_builder_parser import parse_html_builder_config
from scribpy.config.parser_shared import (
    ConfigParseError,
    RawSection,
    nested_section,
    section,
)
from scribpy.config.types import (
    Config,
    IndexConfig,
    PathConfig,
    ProjectConfig,
)
from scribpy.model import IndexMode

_KNOWN_INDEX_MODES = frozenset[IndexMode]({"explicit", "filesystem", "hybrid"})


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
    project = _parse_project_config(section(raw, "project"))
    paths = _parse_path_config(section(raw, "paths"))
    index = _parse_index_config(section(raw, "index"))
    document = parse_document_config(section(raw, "document"))
    builders_raw = section(raw, "builders")
    html = parse_html_builder_config(
        nested_section(builders_raw, "html", "builders")
    )
    return Config(
        project=project, paths=paths, index=index, document=document, html=html
    )


def _parse_project_config(raw: RawSection) -> ProjectConfig:
    """Parse project metadata.

    The section is optional, so an absent name simply keeps the default project
    config.  Shape errors are raised here while semantic validation remains in
    the validation module.
    """
    name = raw.get("name")
    if name is None:
        return ProjectConfig()
    if not isinstance(name, str):
        raise ConfigParseError(
            "Configuration value project.name must be a string."
        )
    return ProjectConfig(name=name)


def _parse_path_config(raw: RawSection) -> PathConfig:
    """Parse source path settings.

    The path is intentionally converted but not normalized here; validation
    later checks whether it is safe relative to the project root.
    """
    source = raw.get("source", "doc")
    if not isinstance(source, str):
        raise ConfigParseError(
            "Configuration value paths.source must be a string."
        )
    return PathConfig(source=Path(source))


def _parse_index_config(raw: RawSection) -> IndexConfig:
    """Parse document-index mode and explicit file entries.

    Hybrid mode is accepted at parse time so downstream validation and index
    checks can report user-facing diagnostics with the original config context.
    """
    mode = raw.get("mode", "filesystem")
    if not isinstance(mode, str):
        raise ConfigParseError(
            "Configuration value index.mode must be a string."
        )
    if mode not in _KNOWN_INDEX_MODES:
        raise ConfigParseError(
            "Configuration value index.mode must be 'filesystem', 'explicit', "
            "or 'hybrid'."
        )

    files = raw.get("files", ())
    if not isinstance(files, Sequence) or isinstance(files, str):
        raise ConfigParseError(
            "Configuration value index.files must be a list."
        )

    parsed_files: list[Path] = []
    for item in files:
        if not isinstance(item, str):
            raise ConfigParseError("Every index.files entry must be a string.")
        parsed_files.append(Path(item))

    return IndexConfig(mode=mode, files=tuple(parsed_files))


__all__ = ["ConfigParseError", "RawSection", "parse_config"]
