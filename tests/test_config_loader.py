"""Tests for scribpy.config_loader — three-level config cascade."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scribpy.config import (
    CssConfig,
    DiagramConfig,
    OutputFormat,
    RenderMode,
    ScribpyConfig,
    TocConfig,
)
from scribpy.config_loader import (
    _build_config,
    _config_to_dict,
    _merge,
    _parse_css,
    _parse_diagrams,
    _parse_toc,
    _read_local_config,
    _read_pyproject_section,
    _read_toml,
    load_config,
)


class TestReadToml:
    """Tests for _read_toml."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        """Requirement: absent file returns an empty dict."""
        result = _read_toml(tmp_path / "nope.toml")
        assert result == {}

    def test_reads_valid_toml(self, tmp_path: Path) -> None:
        """Requirement: valid TOML is parsed into a dict."""
        f = tmp_path / "test.toml"
        f.write_text('[section]\nkey = "value"\n', encoding="utf-8")
        result = _read_toml(f)
        assert result == {"section": {"key": "value"}}


class TestReadPyprojectSection:
    """Tests for _read_pyproject_section."""

    def test_missing_pyproject(self, tmp_path: Path) -> None:
        """Requirement: absent pyproject.toml returns empty dict."""
        assert _read_pyproject_section(tmp_path) == {}

    def test_pyproject_without_tool_scribpy(self, tmp_path: Path) -> None:
        """Requirement: pyproject without [tool.scribpy] returns empty."""
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "foo"\n',
            encoding="utf-8",
        )
        assert _read_pyproject_section(tmp_path) == {}

    def test_pyproject_with_tool_scribpy(self, tmp_path: Path) -> None:
        """Requirement: [tool.scribpy] section is extracted."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.scribpy]\noutput_format = "pdf"\n',
            encoding="utf-8",
        )
        result = _read_pyproject_section(tmp_path)
        assert result == {"output_format": "pdf"}


class TestReadLocalConfig:
    """Tests for _read_local_config."""

    def test_missing_scribpy_toml(self, tmp_path: Path) -> None:
        """Requirement: absent scribpy.toml returns empty dict."""
        assert _read_local_config(tmp_path) == {}

    def test_reads_scribpy_toml(self, tmp_path: Path) -> None:
        """Requirement: scribpy.toml is parsed correctly."""
        (tmp_path / "scribpy.toml").write_text(
            'source = "docs"\n',
            encoding="utf-8",
        )
        result = _read_local_config(tmp_path)
        assert result == {"source": "docs"}


class TestMerge:
    """Tests for the _merge helper."""

    def test_flat_override(self) -> None:
        """Requirement: overlay values replace base values."""
        base: dict[str, Any] = {"a": 1, "b": 2}
        overlay: dict[str, Any] = {"b": 99, "c": 3}
        result = _merge(base, overlay)
        assert result == {"a": 1, "b": 99, "c": 3}

    def test_nested_merge(self) -> None:
        """Requirement: nested dicts are merged recursively."""
        base: dict[str, Any] = {"x": {"a": 1, "b": 2}}
        overlay: dict[str, Any] = {"x": {"b": 99}}
        result = _merge(base, overlay)
        assert result == {"x": {"a": 1, "b": 99}}

    def test_overlay_replaces_non_dict(self) -> None:
        """Requirement: non-dict overlay replaces base entirely."""
        base: dict[str, Any] = {"x": {"a": 1}}
        overlay: dict[str, Any] = {"x": "flat"}
        result = _merge(base, overlay)
        assert result == {"x": "flat"}

    def test_empty_overlay(self) -> None:
        """Requirement: empty overlay leaves base unchanged."""
        base: dict[str, Any] = {"a": 1}
        result = _merge(base, {})
        assert result == {"a": 1}


class TestParseCss:
    """Tests for _parse_css."""

    def test_empty_returns_default(self) -> None:
        """Requirement: empty dict gives default CssConfig."""
        assert _parse_css({}) == CssConfig()

    def test_path_parsed(self) -> None:
        """Requirement: path string is converted to Path."""
        result = _parse_css({"path": "style.css"})
        assert result.path == Path("style.css")

    def test_none_path(self) -> None:
        """Requirement: explicit None path is preserved."""
        result = _parse_css({"path": None})
        assert result.path is None


class TestParseToc:
    """Tests for _parse_toc."""

    def test_empty_returns_default(self) -> None:
        """Requirement: empty dict gives disabled TOC."""
        assert _parse_toc({}) == TocConfig(enabled=False)

    def test_enabled_true(self) -> None:
        """Requirement: enabled=true is parsed."""
        assert _parse_toc({"enabled": True}) == TocConfig(enabled=True)


class TestParseDiagrams:
    """Tests for _parse_diagrams."""

    def test_empty_returns_default(self) -> None:
        """Requirement: empty dict gives offline mode, no jar."""
        result = _parse_diagrams({})
        assert result.render_mode is RenderMode.OFFLINE
        assert result.plantuml_jar is None

    def test_web_mode(self) -> None:
        """Requirement: render_mode='web' is parsed."""
        result = _parse_diagrams({"render_mode": "web"})
        assert result.render_mode is RenderMode.WEB

    def test_plantuml_jar(self) -> None:
        """Requirement: plantuml_jar string is converted to Path."""
        result = _parse_diagrams({"plantuml_jar": "/opt/p.jar"})
        assert result.plantuml_jar == Path("/opt/p.jar")


class TestBuildConfig:
    """Tests for _build_config."""

    def test_empty_gives_defaults(self) -> None:
        """Requirement: empty mapping produces default ScribpyConfig."""
        cfg = _build_config({})
        assert cfg == ScribpyConfig()

    def test_all_fields(self) -> None:
        """Requirement: all fields are parsed from a full mapping."""
        raw: dict[str, Any] = {
            "source": "docs/index.md",
            "output_dir": "dist",
            "output_format": "pdf",
            "css": {"path": "theme.css"},
            "toc": {"enabled": True},
            "diagrams": {
                "render_mode": "web",
                "plantuml_jar": "/jar",
            },
        }
        cfg = _build_config(raw)
        assert cfg.source == Path("docs/index.md")
        assert cfg.output_dir == Path("dist")
        assert cfg.output_format is OutputFormat.PDF
        assert cfg.css.path == Path("theme.css")
        assert cfg.toc.enabled is True
        assert cfg.diagrams.render_mode is RenderMode.WEB
        assert cfg.diagrams.plantuml_jar == Path("/jar")


class TestConfigToDict:
    """Tests for _config_to_dict."""

    def test_roundtrip(self) -> None:
        """Requirement: config -> dict -> config is identity."""
        original = ScribpyConfig(
            source=Path("src"),
            output_dir=Path("out"),
            output_format=OutputFormat.PDF,
            css=CssConfig(path=Path("s.css")),
            toc=TocConfig(enabled=True),
            diagrams=DiagramConfig(
                render_mode=RenderMode.WEB,
                plantuml_jar=Path("/jar"),
            ),
        )
        rebuilt = _build_config(_config_to_dict(original))
        assert rebuilt == original

    def test_none_paths(self) -> None:
        """Requirement: None paths serialize correctly."""
        cfg = ScribpyConfig()
        d = _config_to_dict(cfg)
        assert d["css"]["path"] is None
        assert d["diagrams"]["plantuml_jar"] is None


class TestLoadConfig:
    """Tests for the load_config cascade."""

    def test_no_files_gives_defaults(self, tmp_path: Path) -> None:
        """Requirement: no config files produces defaults."""
        cfg = load_config(root=tmp_path)
        assert cfg == ScribpyConfig()

    def test_pyproject_only(self, tmp_path: Path) -> None:
        """Requirement: [tool.scribpy] in pyproject is loaded."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.scribpy]\noutput_format = "pdf"\n',
            encoding="utf-8",
        )
        cfg = load_config(root=tmp_path)
        assert cfg.output_format is OutputFormat.PDF

    def test_local_overrides_pyproject(self, tmp_path: Path) -> None:
        """Requirement: scribpy.toml overrides pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.scribpy]\noutput_format = "pdf"\nsource = "from_pyp"\n',
            encoding="utf-8",
        )
        (tmp_path / "scribpy.toml").write_text(
            'output_format = "html"\n',
            encoding="utf-8",
        )
        cfg = load_config(root=tmp_path)
        assert cfg.output_format is OutputFormat.HTML
        assert cfg.source == Path("from_pyp")

    def test_api_overrides_all(self, tmp_path: Path) -> None:
        """Requirement: API overrides take highest priority."""
        (tmp_path / "scribpy.toml").write_text(
            'output_format = "pdf"\nsource = "from_local"\n',
            encoding="utf-8",
        )
        api = ScribpyConfig(
            source=Path("from_api"),
            output_format=OutputFormat.HTML,
        )
        cfg = load_config(root=tmp_path, overrides=api)
        assert cfg.source == Path("from_api")
        assert cfg.output_format is OutputFormat.HTML

    def test_nested_cascade(self, tmp_path: Path) -> None:
        """Requirement: nested sections merge across layers."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.scribpy.diagrams]\n"
            'render_mode = "web"\n'
            'plantuml_jar = "/from_pyp"\n',
            encoding="utf-8",
        )
        (tmp_path / "scribpy.toml").write_text(
            '[diagrams]\nplantuml_jar = "/from_local"\n',
            encoding="utf-8",
        )
        cfg = load_config(root=tmp_path)
        assert cfg.diagrams.render_mode is RenderMode.WEB
        assert cfg.diagrams.plantuml_jar == Path("/from_local")

    def test_default_root_is_cwd(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: root defaults to cwd when not specified."""
        (tmp_path / "scribpy.toml").write_text(
            'source = "from_cwd"\n',
            encoding="utf-8",
        )
        monkeypatch.chdir(tmp_path)
        cfg = load_config()
        assert cfg.source == Path("from_cwd")
