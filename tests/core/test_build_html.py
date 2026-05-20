"""Integration tests for the HTML build chain."""

from pathlib import Path

import pytest

from scribpy.config.types import HtmlBuilderConfig
from scribpy.core import build_project
from scribpy.core.build_options import HtmlBuildOverrides
from scribpy.core.build_project import build_html_with_overrides
from scribpy.core.build_html import build_html_project
from scribpy.model import BuildArtifact, Diagnostic


@pytest.fixture(autouse=True)
def _fake_mkdocs_build(monkeypatch: pytest.MonkeyPatch):
    """Keep integration tests focused on Scribpy orchestration."""

    def fake_run(project_root: Path, output_dir: Path):
        site_dir = project_root / output_dir / "site"
        site_dir.mkdir(parents=True, exist_ok=True)
        (site_dir / "index.html").write_text("<html></html>", encoding="utf-8")
        return BuildArtifact(site_dir, "html-site", "site"), ()

    monkeypatch.setattr("scribpy.core.build_html_site.run_mkdocs_build", fake_run)


def _write_config(root: Path, content: str) -> None:
    (root / "scribpy.toml").write_text(content, encoding="utf-8")


def _write_source(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class FakePlantUmlRenderer:
    """Offline renderer used by build-chain tests."""

    def render(self, source: str, output_format: str) -> bytes:
        """Return a tiny deterministic SVG."""
        return f"<svg>{source.strip()}</svg>".encode()


class FailingPlantUmlRenderer:
    """Renderer that simulates Java PlantUML failure."""

    def render(self, source: str, output_format: str) -> bytes:
        """Fail deterministically."""
        raise RuntimeError("bad uml")


def test_build_html_single_page_creates_index_html(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n\nWelcome.\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    index = tmp_path / "build/html/index.html"
    assert index.exists()
    content = index.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content
    assert "<h1" in content


def test_build_html_single_page_artifact_has_correct_target(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    doc_artifacts = [
        a for a in result.artifacts if a.artifact_type == "document"
    ]
    assert len(doc_artifacts) == 1
    assert doc_artifacts[0].target == "html"


def test_build_html_single_page_uses_project_title(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[project]\nname = "My Project"\n[paths]\nsource = "doc"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    content = (tmp_path / "build/html/index.html").read_text(encoding="utf-8")
    assert "My Project" in content


def test_build_html_single_page_copies_css(tmp_path: Path) -> None:
    css = tmp_path / "style.css"
    css.write_text("body { color: red; }", encoding="utf-8")
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html]\nmode = "single-page"\ncss_files = ["style.css"]\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    assert (tmp_path / "build/html/css/style.css").exists()
    html = (tmp_path / "build/html/index.html").read_text(encoding="utf-8")
    assert "css/style.css" in html
    assert (tmp_path / "build/html/js/toc.js").exists()


def test_build_html_single_page_flattens_links_and_assets(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[index]\nmode = "explicit"\nfiles = ["index.md", "guide/page.md"]\n',
    )
    _write_source(
        tmp_path, "doc/index.md", "# Home\n\n[Guide](guide/page.md#setup)\n"
    )
    _write_source(
        tmp_path,
        "doc/guide/page.md",
        "# Guide\n\n## Setup\n\n![diagram](../assets/diagram.png)\n",
    )
    asset = tmp_path / "doc/assets/diagram.png"
    asset.parent.mkdir(parents=True)
    asset.write_text("PNG", encoding="utf-8")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    html = (tmp_path / "build/html/index.html").read_text(encoding="utf-8")
    assert '<a href="#21-setup">Guide</a>' in html
    assert 'src="assets/assets/diagram.png"' in html
    assert (tmp_path / "build/html/assets/assets/diagram.png").exists()


def test_build_html_single_page_renders_plantuml_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment", lambda: ()
    )
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.JavaPlantUmlRenderer", FakePlantUmlRenderer
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(
        tmp_path,
        "doc/index.md",
        "# Home\n\n```plantuml\nAlice -> Bob\n```\n",
    )

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    assert any(a.artifact_type == "diagram" for a in result.artifacts)
    html = (tmp_path / "build/html/index.html").read_text(encoding="utf-8")
    assert 'src="assets/diagrams/plantuml-' in html


def test_build_html_single_page_stops_on_plantuml_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment", lambda: ()
    )
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.JavaPlantUmlRenderer", FailingPlantUmlRenderer
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is False
    assert any(d.code == "UML002" for d in result.diagnostics)


def test_build_html_single_page_missing_css_fails(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html]\ncss_files = ["ghost.css"]\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "CSS001" in codes


def test_build_html_site_creates_mkdocs_yml(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    mkdocs = tmp_path / "build/site/mkdocs.yml"
    assert mkdocs.exists()


def test_build_html_site_creates_docs_directory(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    assert (tmp_path / "build/site/docs/index.md").exists()


def test_build_html_site_renders_plantuml_locally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment", lambda: ()
    )
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.JavaPlantUmlRenderer", FakePlantUmlRenderer
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(
        tmp_path,
        "doc/guide/page.md",
        "# Page\n\n```plantuml\nA -> B\n```\n",
    )

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    page = (tmp_path / "build/site/docs/guide/page.md").read_text(encoding="utf-8")
    assert "../assets/diagrams/plantuml-" in page
    assert any(a.artifact_type == "diagram" for a in result.artifacts)


def test_build_html_site_stops_on_plantuml_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment", lambda: ()
    )
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.JavaPlantUmlRenderer", FailingPlantUmlRenderer
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is False
    assert any(d.code == "UML002" for d in result.diagnostics)


def test_build_html_java_plantuml_fails_early_without_java(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment",
        lambda: (Diagnostic("error", "UML004", "no java"),),
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is False
    assert any(d.code == "UML004" for d in result.diagnostics)


def test_build_html_web_plantuml_skips_java_preflight(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment",
        lambda: (_ for _ in ()).throw(AssertionError("should not be called")),
    )
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.WebPlantUmlRenderer", lambda _: FakePlantUmlRenderer()
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "web"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True


def test_build_html_single_page_renders_mermaid_web(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.mermaid.WebMermaidRenderer",
        lambda *args: FakePlantUmlRenderer(),
    )
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(
        tmp_path,
        "doc/index.md",
        "# Home\n\n```mermaid\nflowchart LR\nA-->B\n```\n",
    )

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is True
    assert any("mermaid-" in str(a.path) for a in result.artifacts)
    html = (tmp_path / "build/html/index.html").read_text(encoding="utf-8")
    assert 'src="assets/diagrams/mermaid-' in html


def test_build_html_site_renders_mermaid_web(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.mermaid.WebMermaidRenderer",
        lambda *args: FakePlantUmlRenderer(),
    )
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(
        tmp_path,
        "doc/guide/page.md",
        "# Page\n\n```mermaid\nflowchart LR\nA-->B\n```\n",
    )

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    page = (tmp_path / "build/site/docs/guide/page.md").read_text(encoding="utf-8")
    assert "../assets/diagrams/mermaid-" in page


def test_build_html_uses_injected_renderer_without_selecting_configured_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.validate_java_plantuml_environment", lambda: ()
    )
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_html_project(
        tmp_path,
        html_config=HtmlBuilderConfig(),
        filesystem=None,
        parser=None,
        registry=None,
        diagram_renderer=FakePlantUmlRenderer(),
    )

    assert result.success is True


def test_build_html_site_returns_rendered_site_artifact(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    assert any(
        artifact.artifact_type == "site" for artifact in result.artifacts
    )


def test_build_html_site_nav_order_matches_index(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[index]\nmode = "explicit"\nfiles = ["b.md", "a.md"]\n',
    )
    _write_source(tmp_path, "doc/a.md", "# A\n")
    _write_source(tmp_path, "doc/b.md", "# B\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert content.index("b.md") < content.index("a.md")


def test_build_html_site_uses_site_name_from_config(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[project]\nname = "My Project"\n[paths]\nsource = "doc"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert "My Project" in content


def test_build_html_site_uses_theme_from_config(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n[builders.html]\ntheme = "readthedocs"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert "theme: readthedocs" in content


def test_build_html_site_copies_css_and_declares_extra_css(
    tmp_path: Path,
) -> None:
    css = tmp_path / "custom.css"
    css.write_text("h1 { color: blue; }", encoding="utf-8")
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html]\ncss_files = ["custom.css"]\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is True
    assert (tmp_path / "build/site/docs/css/custom.css").exists()
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert "extra_css:" in content


def test_build_html_stops_when_project_preparation_fails(
    tmp_path: Path,
) -> None:
    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "CFG001" in codes


def test_build_html_project_blocks_when_preparation_fails(
    tmp_path: Path,
) -> None:
    result = build_html_project(
        tmp_path,
        html_config=HtmlBuilderConfig(),
        filesystem=None,
        parser=None,
        registry=None,
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "CFG001",
        "BLD002",
    ]


def test_build_html_stops_when_lint_fails(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## No H1\n")

    result = build_project(tmp_path, target="html", html_mode="single-page")

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "LINT001" in codes
    assert not (tmp_path / "build/html/index.html").exists()


def test_build_html_rejects_invalid_html_mode(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html", html_mode="pdf")

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "BLD001" in codes


def test_build_html_rejects_invalid_plantuml_renderer(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_html_with_overrides(
        tmp_path, HtmlBuildOverrides(plantuml_renderer="remote")
    )

    assert result.success is False
    assert any(d.code == "BLD001" for d in result.diagnostics)


def test_build_html_plantuml_override_replaces_project_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "scribpy.plugins.plantuml.WebPlantUmlRenderer", lambda _: FakePlantUmlRenderer()
    )
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n'
        '[builders.html.plantuml]\nrenderer = "java"\n',
    )
    _write_source(tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n")

    result = build_html_with_overrides(
        tmp_path,
        HtmlBuildOverrides(
            plantuml_renderer="web",
            plantuml_server_url="https://example.test/plantuml",
        ),
    )

    assert result.success is True


def test_build_html_target_alias_defaults_to_single_page(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html")

    assert result.success is True
    assert (tmp_path / "build/html/index.html").exists()


def test_build_html_site_target_alias(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    result = build_project(tmp_path, target="html-site")

    assert result.success is True
    assert (tmp_path / "build/site/mkdocs.yml").exists()


def test_build_html_single_page_write_failure_returns_error(
    tmp_path: Path,
) -> None:
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    class FailWriteFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.name == "index.html":
                raise OSError("disk full")
            super().write_text(path, content)

    result = build_project(
        tmp_path,
        target="html",
        html_mode="single-page",
        filesystem=FailWriteFS(),
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "BLD005" in codes


def test_build_html_single_page_transform_error_stops_build(
    tmp_path: Path,
) -> None:
    from scribpy.extensions import ExtensionRegistry
    from scribpy.model import Diagnostic
    from scribpy.transforms import TransformResult

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    def failing_transform(context):
        return TransformResult(
            documents=context.transformed_documents,
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="TRN001",
                    message="Transform failed.",
                ),
            ),
        )

    registry = ExtensionRegistry(html_transforms=(failing_transform,))
    result = build_project(
        tmp_path,
        target="html",
        html_mode="single-page",
        registry=registry,
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "TRN001" in codes


def test_build_html_site_transform_error_stops_build(tmp_path: Path) -> None:
    from scribpy.extensions import ExtensionRegistry
    from scribpy.model import Diagnostic
    from scribpy.transforms import TransformResult

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    def failing_transform(context):
        return TransformResult(
            documents=context.transformed_documents,
            diagnostics=(
                Diagnostic(
                    severity="error",
                    code="TRN002",
                    message="Transform failed.",
                ),
            ),
        )

    registry = ExtensionRegistry(html_transforms=(failing_transform,))
    result = build_project(
        tmp_path,
        target="html",
        html_mode="site",
        registry=registry,
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "TRN002" in codes


def test_build_html_site_write_failure_returns_error(tmp_path: Path) -> None:
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    class FailWriteFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.name == "mkdocs.yml":
                raise OSError("disk full")
            super().write_text(path, content)

    result = build_project(
        tmp_path,
        target="html",
        html_mode="site",
        filesystem=FailWriteFS(),
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "SITE001" in codes


def test_build_html_site_mkdocs_failure_returns_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    monkeypatch.setattr(
        "scribpy.core.build_html_site.run_mkdocs_build",
        lambda *_args: (
            None,
            (Diagnostic(severity="error", code="SITE003", message="failed"),),
        ),
    )

    result = build_project(tmp_path, target="html", html_mode="site")

    assert result.success is False
    assert "SITE003" in [diagnostic.code for diagnostic in result.diagnostics]


def test_build_html_single_page_asset_copy_error_returns_error(
    tmp_path: Path,
) -> None:
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir()
    img = doc_dir / "photo.png"
    img.write_bytes(b"PNG")
    _write_source(tmp_path, "doc/index.md", "# Home\n\n![photo](photo.png)\n")

    class FailAssetWriteFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.parent.name == "assets":
                raise OSError("disk full")
            super().write_text(path, content)

    result = build_project(
        tmp_path,
        target="html",
        html_mode="single-page",
        filesystem=FailAssetWriteFS(),
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "ASS002" in codes


def test_build_html_site_asset_copy_error_returns_error(
    tmp_path: Path,
) -> None:
    from scribpy.utils.file_utils import RealFileSystem

    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    doc_dir = tmp_path / "doc"
    doc_dir.mkdir()
    img = doc_dir / "photo.png"
    img.write_bytes(b"PNG")
    _write_source(tmp_path, "doc/index.md", "# Home\n\n![photo](photo.png)\n")

    class FailAssetWriteFS(RealFileSystem):
        written: list[str] = []

        def write_text(self, path: Path, content: str) -> None:
            if path.suffix == ".png":
                raise OSError("disk full")
            super().write_text(path, content)

    result = build_project(
        tmp_path,
        target="html",
        html_mode="site",
        filesystem=FailAssetWriteFS(),
    )

    assert result.success is False
    codes = [d.code for d in result.diagnostics]
    assert "ASS002" in codes
