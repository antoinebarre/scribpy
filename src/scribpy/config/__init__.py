"""Public exports for configuration loading and typed config objects."""

from scribpy.config.loader import (
    CONFIG_FILENAME,
    ConfigParseError,
    find_config,
    load_config,
    load_toml_config,
    parse_config,
    validate_config,
)
from scribpy.config.types import (
    Config,
    DocumentConfig,
    IndexConfig,
    NumberingConfig,
    NumberingStyle,
    PathConfig,
    ProjectConfig,
    TocConfig,
    TocStyle,
)

__all__ = [
    "CONFIG_FILENAME",
    "Config",
    "ConfigParseError",
    "DocumentConfig",
    "IndexConfig",
    "NumberingConfig",
    "NumberingStyle",
    "PathConfig",
    "ProjectConfig",
    "TocConfig",
    "TocStyle",
    "find_config",
    "load_config",
    "load_toml_config",
    "parse_config",
    "validate_config",
]
