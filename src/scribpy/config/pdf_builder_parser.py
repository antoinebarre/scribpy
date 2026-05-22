"""PDF builder section parsing for ``scribpy.toml``."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from scribpy.config.parser_shared import (
    ConfigParseError,
    RawSection,
    parse_optional_str,
)
from scribpy.config.types import PdfBuilderConfig


def parse_pdf_builder_config(raw: RawSection) -> PdfBuilderConfig:
    """Parse the ``builders.pdf`` table.

    Args:
        raw: Raw ``builders.pdf`` TOML section.

    Returns:
        Parsed PDF builder configuration.
    """
    css_files = _parse_pdf_css_files(raw)
    output_dir_raw = parse_optional_str(raw, "output_dir", "builders.pdf")
    paper_size = raw.get("paper_size", "A4")
    toc_level = raw.get("toc_level", 3)

    if not isinstance(paper_size, str):
        raise ConfigParseError(
            "Configuration value builders.pdf.paper_size must be a string."
        )
    if not isinstance(toc_level, int):
        raise ConfigParseError(
            "Configuration value builders.pdf.toc_level must be an integer."
        )
    if toc_level < 0 or toc_level > 6:
        raise ConfigParseError(
            "Configuration value builders.pdf.toc_level must be between 0 and 6."
        )

    return PdfBuilderConfig(
        css_files=tuple(css_files),
        output_dir=Path(output_dir_raw)
        if output_dir_raw is not None
        else None,
        paper_size=paper_size,
        toc_level=toc_level,
    )


def _parse_pdf_css_files(raw: RawSection) -> list[Path]:
    """Parse PDF stylesheet paths declared as ``css``."""
    css_raw = raw.get("css", ())
    if not isinstance(css_raw, Sequence) or isinstance(css_raw, str):
        raise ConfigParseError(
            "Configuration value builders.pdf.css must be a list."
        )
    css_files: list[Path] = []
    for item in css_raw:
        if not isinstance(item, str):
            raise ConfigParseError(
                "Every builders.pdf.css entry must be a string."
            )
        css_files.append(Path(item))
    return css_files


__all__ = ["parse_pdf_builder_config"]
