"""HTML builder section parsing for ``scribpy.toml``.

The ``builders.html`` table combines output-shape options, optional CSS, and
diagram renderer subconfiguration.  Keeping those concerns together makes the
boundary explicit: this module performs TOML shape checks and value coercion,
while the build services decide how the parsed options are executed.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from scribpy.config.html import parse_mermaid_config, parse_plantuml_config
from scribpy.config.parser_shared import (
    ConfigParseError,
    RawSection,
    nested_section,
    parse_optional_str,
)
from scribpy.config.types import HtmlBuilderConfig, HtmlMode

_KNOWN_HTML_MODES = frozenset[HtmlMode]({"single-page", "site"})


def parse_html_builder_config(raw: RawSection) -> HtmlBuilderConfig:
    """Parse the complete ``builders.html`` table.

    The returned object is already typed for downstream builders: paths are
    represented with ``Path``, the mode is constrained to the supported output
    modes, and renderer subsections are delegated to their own config parsers.

    Args:
        raw: Raw ``builders.html`` TOML section.

    Returns:
        Parsed HTML builder configuration.
    """
    mode = _parse_html_mode(raw)
    css_files = _parse_html_css_files(raw)
    site_name = parse_optional_str(raw, "site_name", "builders.html")
    theme = parse_optional_str(raw, "theme", "builders.html")
    output_dir_raw = parse_optional_str(raw, "output_dir", "builders.html")
    output_dir = Path(output_dir_raw) if output_dir_raw is not None else None
    plantuml = parse_plantuml_config(
        nested_section(raw, "plantuml", "builders.html"),
        parse_optional_str=parse_optional_str,
        error_type=ConfigParseError,
    )
    mermaid = parse_mermaid_config(
        nested_section(raw, "mermaid", "builders.html"),
        parse_optional_str=parse_optional_str,
    )
    return HtmlBuilderConfig(
        mode=mode,
        css_files=tuple(css_files),
        site_name=site_name,
        theme=theme,
        output_dir=output_dir,
        plantuml=plantuml,
        mermaid=mermaid,
    )


def _parse_html_mode(raw: RawSection) -> HtmlMode:
    """Parse the selected HTML output mode."""
    mode = raw.get("mode", "single-page")
    if not isinstance(mode, str) or mode not in _KNOWN_HTML_MODES:
        raise ConfigParseError(
            "Configuration value builders.html.mode must be 'single-page' or 'site'."
        )
    return mode


def _parse_html_css_files(raw: RawSection) -> list[Path]:
    """Parse stylesheet paths declared for HTML output.

    CSS files are project-relative user input at this stage.  Existence checks
    happen later in the asset-copying layer so config parsing can stay focused
    on shape and type validation.
    """
    css_raw = raw.get("css_files", ())
    if not isinstance(css_raw, Sequence) or isinstance(css_raw, str):
        raise ConfigParseError(
            "Configuration value builders.html.css_files must be a list."
        )
    css_files: list[Path] = []
    for item in css_raw:
        if not isinstance(item, str):
            raise ConfigParseError(
                "Every builders.html.css_files entry must be a string."
            )
        css_files.append(Path(item))
    return css_files


__all__ = ["parse_html_builder_config"]
