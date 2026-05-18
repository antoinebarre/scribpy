"""Tests for the simple top-level Scribpy Python API."""

from pathlib import Path

import scribpy


def _write_config(
    root: Path, content: str = '[paths]\nsource = "doc"\n'
) -> None:
    (root / "scribpy.toml").write_text(content, encoding="utf-8")


def _write_source(
    root: Path, relative_path: str, content: str = "# Home\n"
) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_top_level_api_exposes_main_workflows(tmp_path: Path) -> None:
    _write_config(tmp_path)
    _write_source(tmp_path, "doc/index.md")

    assert scribpy.check_index(str(tmp_path)).failed is False
    assert scribpy.check_parse(str(tmp_path)).failed is False
    assert scribpy.lint(str(tmp_path)).failed is False
    assert scribpy.build_markdown(str(tmp_path)).success is True
    assert scribpy.build_html(str(tmp_path)).success is True


def test_top_level_api_build_html_supports_site_mode(
    tmp_path: Path, monkeypatch
) -> None:
    _write_config(tmp_path)
    _write_source(tmp_path, "doc/index.md")

    def fake_run(project_root: Path, output_dir: Path):
        site_dir = project_root / output_dir / "site"
        site_dir.mkdir(parents=True, exist_ok=True)
        return scribpy.BuildArtifact(site_dir, "html-site", "site"), ()

    monkeypatch.setattr("scribpy.core.build_html.run_mkdocs_build", fake_run)

    result = scribpy.build_html(tmp_path, mode="site")

    assert result.success is True
    assert any(
        artifact.artifact_type == "site" for artifact in result.artifacts
    )


def test_top_level_api_builds_support_output_directory_overrides(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path)
    _write_source(tmp_path, "doc/index.md")

    markdown_result = scribpy.build_markdown(
        tmp_path, output_dir="ci/markdown"
    )
    html_result = scribpy.build_html(tmp_path, output_dir="ci/html")

    assert markdown_result.success is True
    assert (tmp_path / "ci/markdown/document.md").is_file()
    assert html_result.success is True
    assert (tmp_path / "ci/html/index.html").is_file()


def test_top_level_api_build_html_supports_plantuml_override(
    tmp_path: Path, monkeypatch
) -> None:
    _write_config(tmp_path)
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    class FakeRenderer:
        def render(self, source: str, output_format: str) -> bytes:
            return b"<svg/>"

    monkeypatch.setattr(
        "scribpy.core.build_html.WebPlantUmlRenderer", lambda _: FakeRenderer()
    )

    result = scribpy.build_html(
        tmp_path,
        plantuml_renderer="web",
        plantuml_server_url="https://example.test/plantuml",
    )

    assert result.success is True


def test_top_level_api_create_demo(tmp_path: Path) -> None:
    target = tmp_path / "demo"

    result = scribpy.create_demo(target)

    assert result.failed is False
    assert (target / "scribpy.toml").is_file()
