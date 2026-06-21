"""Tests for scribpy.config — frozen configuration dataclasses."""

from pathlib import Path

import pytest

from scribpy.config import (
    CssConfig,
    DiagramConfig,
    OutputFormat,
    RenderMode,
    ScribpyConfig,
    TocConfig,
)


class TestRenderMode:
    """Tests for the RenderMode enum."""

    def test_web_value(self) -> None:
        """Requirement: RenderMode.WEB has string value 'web'."""
        assert RenderMode.WEB.value == "web"

    def test_offline_value(self) -> None:
        """Requirement: RenderMode.OFFLINE has string value 'offline'."""
        assert RenderMode.OFFLINE.value == "offline"

    def test_members_count(self) -> None:
        """Requirement: RenderMode has exactly two members."""
        assert len(RenderMode) == 2


class TestOutputFormat:
    """Tests for the OutputFormat enum."""

    def test_html_value(self) -> None:
        """Requirement: OutputFormat.HTML has string value 'html'."""
        assert OutputFormat.HTML.value == "html"

    def test_pdf_value(self) -> None:
        """Requirement: OutputFormat.PDF has string value 'pdf'."""
        assert OutputFormat.PDF.value == "pdf"

    def test_members_count(self) -> None:
        """Requirement: OutputFormat has exactly two members."""
        assert len(OutputFormat) == 2


class TestCssConfig:
    """Tests for the CssConfig dataclass."""

    def test_default_path_is_none(self) -> None:
        """Requirement: CssConfig defaults to no custom CSS."""
        cfg = CssConfig()
        assert cfg.path is None

    def test_custom_path(self) -> None:
        """Requirement: CssConfig accepts a user-supplied path."""
        cfg = CssConfig(path=Path("style.css"))
        assert cfg.path == Path("style.css")

    def test_frozen(self) -> None:
        """Requirement: CssConfig is immutable."""
        cfg = CssConfig()
        with pytest.raises(AttributeError):
            cfg.path = Path("x.css")  # type: ignore[misc]


class TestTocConfig:
    """Tests for the TocConfig dataclass."""

    def test_default_disabled(self) -> None:
        """Requirement: TOC is disabled by default."""
        cfg = TocConfig()
        assert cfg.enabled is False

    def test_enabled(self) -> None:
        """Requirement: TOC can be explicitly enabled."""
        cfg = TocConfig(enabled=True)
        assert cfg.enabled is True

    def test_frozen(self) -> None:
        """Requirement: TocConfig is immutable."""
        cfg = TocConfig()
        with pytest.raises(AttributeError):
            cfg.enabled = True  # type: ignore[misc]


class TestDiagramConfig:
    """Tests for the DiagramConfig dataclass."""

    def test_default_render_mode_is_offline(self) -> None:
        """Requirement: default diagram mode is offline (REQ-024)."""
        cfg = DiagramConfig()
        assert cfg.render_mode is RenderMode.OFFLINE

    def test_default_plantuml_jar_is_none(self) -> None:
        """Requirement: no default PlantUML JAR path."""
        cfg = DiagramConfig()
        assert cfg.plantuml_jar is None

    def test_custom_values(self) -> None:
        """Requirement: DiagramConfig accepts custom values."""
        jar = Path("/opt/plantuml.jar")
        cfg = DiagramConfig(
            render_mode=RenderMode.WEB,
            plantuml_jar=jar,
        )
        assert cfg.render_mode is RenderMode.WEB
        assert cfg.plantuml_jar == jar

    def test_frozen(self) -> None:
        """Requirement: DiagramConfig is immutable."""
        cfg = DiagramConfig()
        with pytest.raises(AttributeError):
            cfg.render_mode = RenderMode.WEB  # type: ignore[misc]


class TestScribpyConfig:
    """Tests for the top-level ScribpyConfig."""

    def test_defaults(self) -> None:
        """Requirement: ScribpyConfig provides sensible defaults."""
        cfg = ScribpyConfig()
        assert cfg.source == Path(".")
        assert cfg.output_dir == Path("work/build")
        assert cfg.output_format is OutputFormat.HTML
        assert isinstance(cfg.css, CssConfig)
        assert isinstance(cfg.toc, TocConfig)
        assert isinstance(cfg.diagrams, DiagramConfig)

    def test_custom_source_and_output(self) -> None:
        """Requirement: source and output_dir are configurable."""
        cfg = ScribpyConfig(
            source=Path("docs/readme.md"),
            output_dir=Path("dist"),
        )
        assert cfg.source == Path("docs/readme.md")
        assert cfg.output_dir == Path("dist")

    def test_frozen(self) -> None:
        """Requirement: ScribpyConfig is immutable."""
        cfg = ScribpyConfig()
        with pytest.raises(AttributeError):
            cfg.source = Path("/tmp")  # type: ignore[misc]

    def test_nested_configs_are_independent(self) -> None:
        """Requirement: two ScribpyConfig instances share no state."""
        cfg_a = ScribpyConfig()
        cfg_b = ScribpyConfig(
            output_format=OutputFormat.PDF,
            toc=TocConfig(enabled=True),
        )
        assert cfg_a.output_format is OutputFormat.HTML
        assert cfg_b.output_format is OutputFormat.PDF
        assert cfg_a.toc.enabled is False
        assert cfg_b.toc.enabled is True
