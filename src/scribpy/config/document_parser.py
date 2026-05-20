"""Document presentation parsing for ``scribpy.toml``.

This module owns the ``document`` table and its nested ``toc`` and
``numbering`` sections.  These options shape the assembled Markdown/HTML output
but do not participate in project discovery, so they stay separate from the
core project and index parser.
"""

from __future__ import annotations

from scribpy.config.parser_shared import (
    ConfigParseError,
    RawSection,
    nested_section,
)
from scribpy.config.types import (
    DocumentConfig,
    NumberingConfig,
    NumberingStyle,
    TocConfig,
    TocStyle,
)

_KNOWN_TOC_STYLES = frozenset[TocStyle]({"bullet", "numbered"})
_KNOWN_NUMBERING_STYLES = frozenset[NumberingStyle](
    {"decimal", "alpha", "roman"}
)


def parse_document_config(raw: RawSection) -> DocumentConfig:
    """Parse assembled-document presentation options.

    The title is the only direct scalar on the section today. Nested
    subsections are parsed through dedicated helpers so TOC and numbering rules
    can evolve independently without expanding the top-level parser again.

    Args:
        raw: Raw ``document`` TOML section.

    Returns:
        Parsed document configuration.
    """
    title = raw.get("title")
    if title is not None and not isinstance(title, str):
        raise ConfigParseError(
            "Configuration value document.title must be a string."
        )
    toc = _parse_toc_config(nested_section(raw, "toc", "document"))
    numbering = _parse_numbering_config(
        nested_section(raw, "numbering", "document")
    )
    return DocumentConfig(title=title, toc=toc, numbering=numbering)


def _parse_toc_config(raw: RawSection) -> TocConfig:
    """Parse table-of-contents settings.

    These settings describe generated navigation in the assembled document;
    they intentionally do not inspect source documents or headings here.
    """
    enabled = _parse_bool(raw, "enabled", "document.toc", True)
    max_level = _parse_heading_level(raw, "max_level", "document.toc", 6)
    style = raw.get("style", "bullet")
    if not isinstance(style, str) or style not in _KNOWN_TOC_STYLES:
        raise ConfigParseError(
            "Configuration value document.toc.style must be 'bullet' or 'numbered'."
        )
    return TocConfig(enabled=enabled, max_level=max_level, style=style)


def _parse_numbering_config(raw: RawSection) -> NumberingConfig:
    """Parse section-numbering settings.

    Numbering style and maximum depth are validated as config shape. The
    transform layer later applies those settings to actual Markdown headings.
    """
    enabled = _parse_bool(raw, "enabled", "document.numbering", True)
    max_level = _parse_heading_level(raw, "max_level", "document.numbering", 6)
    style = raw.get("style", "decimal")
    if not isinstance(style, str) or style not in _KNOWN_NUMBERING_STYLES:
        raise ConfigParseError(
            "Configuration value document.numbering.style must be "
            "'decimal', 'alpha', or 'roman'."
        )
    return NumberingConfig(enabled=enabled, max_level=max_level, style=style)


def _parse_bool(
    raw: RawSection, key: str, section: str, default: bool
) -> bool:
    """Parse a boolean scalar from a known document subsection."""
    value = raw.get(key, default)
    if not isinstance(value, bool):
        raise ConfigParseError(
            f"Configuration value {section}.{key} must be a boolean."
        )
    return value


def _parse_heading_level(
    raw: RawSection, key: str, section: str, default: int
) -> int:
    """Parse a Markdown heading level constrained to ``1..6``."""
    value = raw.get(key, default)
    if (
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 1 <= value <= 6
    ):
        raise ConfigParseError(
            f"Configuration value {section}.{key} must be an integer from 1 to 6."
        )
    return value


__all__ = ["parse_document_config"]
