"""Tests for HTML builder configuration loading."""

from pathlib import Path

import pytest

from scribpy.config.loader import ConfigParseError, parse_config
from scribpy.config.types import HtmlBuilderConfig


def test_html_config_defaults() -> None:
    config = parse_config({})
    assert config.html.mode == "single-page"
    assert config.html.css_files == ()
    assert config.html.site_name is None
    assert config.html.output_dir is None


def test_html_config_single_page_mode() -> None:
    config = parse_config({"builders": {"html": {"mode": "single-page"}}})
    assert config.html.mode == "single-page"


def test_html_config_site_mode() -> None:
    config = parse_config({"builders": {"html": {"mode": "site"}}})
    assert config.html.mode == "site"


def test_html_config_invalid_mode_raises() -> None:
    with pytest.raises(ConfigParseError, match="builders.html.mode"):
        parse_config({"builders": {"html": {"mode": "pdf"}}})


def test_html_config_css_files() -> None:
    config = parse_config(
        {"builders": {"html": {"css_files": ["assets/style.css", "custom.css"]}}}
    )
    assert config.html.css_files == (Path("assets/style.css"), Path("custom.css"))


def test_html_config_css_files_not_a_list_raises() -> None:
    with pytest.raises(ConfigParseError, match="css_files"):
        parse_config({"builders": {"html": {"css_files": "style.css"}}})


def test_html_config_css_files_non_string_entry_raises() -> None:
    with pytest.raises(ConfigParseError, match="css_files"):
        parse_config({"builders": {"html": {"css_files": [42]}}})


def test_html_config_site_name() -> None:
    config = parse_config(
        {"builders": {"html": {"site_name": "My Docs"}}}
    )
    assert config.html.site_name == "My Docs"


def test_html_config_site_name_non_string_raises() -> None:
    with pytest.raises(ConfigParseError, match="site_name"):
        parse_config({"builders": {"html": {"site_name": 42}}})


def test_html_config_output_dir() -> None:
    config = parse_config(
        {"builders": {"html": {"output_dir": "out/html"}}}
    )
    assert config.html.output_dir == Path("out/html")


def test_html_config_output_dir_non_string_raises() -> None:
    with pytest.raises(ConfigParseError, match="output_dir"):
        parse_config({"builders": {"html": {"output_dir": 123}}})


def test_html_builder_config_resolve_output_dir_single_page() -> None:
    cfg = HtmlBuilderConfig(mode="single-page")
    assert cfg.resolve_output_dir() == Path("build/html")


def test_html_builder_config_resolve_output_dir_site() -> None:
    cfg = HtmlBuilderConfig(mode="site")
    assert cfg.resolve_output_dir() == Path("build/site")


def test_html_builder_config_resolve_output_dir_override() -> None:
    cfg = HtmlBuilderConfig(mode="single-page", output_dir=Path("custom/out"))
    assert cfg.resolve_output_dir() == Path("custom/out")


def test_builders_section_not_a_table_raises() -> None:
    with pytest.raises(ConfigParseError, match="\\[builders\\]"):
        parse_config({"builders": "not-a-table"})


def test_builders_html_section_not_a_table_raises() -> None:
    with pytest.raises(ConfigParseError, match="\\[builders.html\\]"):
        parse_config({"builders": {"html": "not-a-table"}})
