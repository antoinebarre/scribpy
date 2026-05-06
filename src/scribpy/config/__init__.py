"""Configuration loading and validation for scribpy.toml.

Responsibilities:
    - Locate scribpy.toml (find_config)
    - Load raw TOML data (load_toml_config)
    - Parse raw dict into typed Config objects (parse_config)
    - Validate semantic consistency (validate_config)
    - Combined load + validate entry point (load_config)

The Config dataclass and sub-configs (ProjectConfig, PathConfig,
DocumentConfig, MarkdownConfig, LintConfig, IndexConfig,
TransformConfig, BuilderConfig, AssetConfig, ExtensionConfig)
are defined in scribpy.config.types.
"""
