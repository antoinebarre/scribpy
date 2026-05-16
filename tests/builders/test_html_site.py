"""Tests for the MkDocs site scaffold builder."""

from pathlib import Path

from scribpy.builders.html_site import (
    build_mkdocs_yaml,
    run_mkdocs_build,
    write_site_artifacts,
    write_site_artifacts_with_css,
)
from scribpy.model import Document, MarkdownAst, TransformedDocument
from scribpy.utils.file_utils import RealFileSystem


def _document(path: str, title: str | None = None) -> Document:
    return Document(
        path=Path("/project/doc") / path,
        relative_path=Path(path),
        source="",
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=title,
        headings=(),
        links=(),
        assets=(),
    )


def _transformed(
    path: str, content: str = "# Page\n", title: str | None = None
) -> TransformedDocument:
    return TransformedDocument(
        relative_path=Path(path),
        content=content,
        source_document=_document(path, title=title),
    )


def test_build_mkdocs_yaml_minimal() -> None:
    yaml = build_mkdocs_yaml("My Site", [], [])
    assert "site_name: My Site" in yaml


def test_build_mkdocs_yaml_with_nav() -> None:
    yaml = build_mkdocs_yaml("Site", [{"Home": "index.md"}], [])
    assert "nav:" in yaml
    assert "Home" in yaml
    assert "index.md" in yaml


def test_build_mkdocs_yaml_with_extra_css() -> None:
    yaml = build_mkdocs_yaml("Site", [], ["css/style.css"])
    assert "extra_css:" in yaml
    assert "css/style.css" in yaml


def test_build_mkdocs_yaml_special_chars_quoted() -> None:
    yaml = build_mkdocs_yaml("Site: Docs", [], [])
    assert "'Site: Docs'" in yaml


def test_write_site_artifacts_creates_mkdocs_yml(tmp_path: Path) -> None:
    docs = (_transformed("index.md", "# Home\n", title="Home"),)
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "My Site", Path("build/site"), RealFileSystem()
    )

    assert diagnostics == ()
    mkdocs_path = tmp_path / "build/site/mkdocs.yml"
    assert mkdocs_path.exists()
    content = mkdocs_path.read_text(encoding="utf-8")
    assert "site_name: My Site" in content


def test_write_site_artifacts_creates_docs_pages(tmp_path: Path) -> None:
    docs = (
        _transformed("a.md", "# A\n"),
        _transformed("b.md", "# B\n"),
    )
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), RealFileSystem()
    )

    assert diagnostics == ()
    assert (tmp_path / "build/site/docs/a.md").exists()
    assert (tmp_path / "build/site/docs/b.md").exists()


def test_write_site_artifacts_nav_order_matches_documents(
    tmp_path: Path,
) -> None:
    docs = (
        _transformed("first.md", "# First\n", title="First"),
        _transformed("second.md", "# Second\n", title="Second"),
    )
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), RealFileSystem()
    )

    assert diagnostics == ()
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert content.index("first.md") < content.index("second.md")


def test_write_site_artifacts_page_title_fallback(tmp_path: Path) -> None:
    docs = (_transformed("my-page.md", "# Content\n", title=None),)
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), RealFileSystem()
    )

    assert diagnostics == ()
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert "My Page" in content


def test_write_site_artifacts_returns_mkdocs_and_page_artifacts(
    tmp_path: Path,
) -> None:
    docs = (_transformed("index.md", "# Home\n"),)
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), RealFileSystem()
    )

    assert diagnostics == ()
    targets = {a.target for a in artifacts}
    types = {a.artifact_type for a in artifacts}
    assert "html-site" in targets
    assert "mkdocs-config" in types
    assert "page" in types


def test_write_site_artifacts_with_css_copies_stylesheet(
    tmp_path: Path,
) -> None:
    css_file = tmp_path / "style.css"
    css_file.write_text("body { color: red; }", encoding="utf-8")

    docs = (_transformed("index.md", "# Home\n"),)
    artifacts, diagnostics = write_site_artifacts_with_css(
        tmp_path,
        docs,
        "S",
        Path("build/site"),
        (Path("style.css"),),
        RealFileSystem(),
    )

    assert diagnostics == ()
    dest = tmp_path / "build/site/docs/css/style.css"
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == "body { color: red; }"


def test_write_site_artifacts_with_css_declares_extra_css(
    tmp_path: Path,
) -> None:
    css_file = tmp_path / "custom.css"
    css_file.write_text("h1 { color: blue; }", encoding="utf-8")

    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts_with_css(
        tmp_path,
        docs,
        "S",
        Path("build/site"),
        (Path("custom.css"),),
        RealFileSystem(),
    )

    assert diagnostics == ()
    content = (tmp_path / "build/site/mkdocs.yml").read_text(encoding="utf-8")
    assert "extra_css:" in content
    assert "custom.css" in content


def test_write_site_artifacts_with_css_missing_file_reports_css001(
    tmp_path: Path,
) -> None:
    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts_with_css(
        tmp_path,
        docs,
        "S",
        Path("build/site"),
        (Path("missing.css"),),
        RealFileSystem(),
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CSS001"


def test_write_site_artifacts_write_failure_reports_site001(
    tmp_path: Path,
) -> None:
    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.name == "mkdocs.yml":
                raise OSError("disk full")
            super().write_text(path, content)

    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), FailFS()
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "SITE001"


def test_write_site_artifacts_page_write_failure_reports_site002(
    tmp_path: Path,
) -> None:
    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.suffix == ".md":
                raise OSError("disk full")
            super().write_text(path, content)

    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts(
        tmp_path, docs, "S", Path("build/site"), FailFS()
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "SITE002"


def test_write_site_artifacts_with_css_page_failure_stops_early(
    tmp_path: Path,
) -> None:
    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.suffix == ".md":
                raise OSError("disk full")
            super().write_text(path, content)

    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts_with_css(
        tmp_path, docs, "S", Path("build/site"), (), FailFS()
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "SITE002"


def test_copy_css_files_write_failure_reports_css002(tmp_path: Path) -> None:
    css_file = tmp_path / "style.css"
    css_file.write_text("body {}", encoding="utf-8")

    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            if path.suffix == ".css":
                raise OSError("disk full")
            super().write_text(path, content)

    docs = (_transformed("index.md"),)
    artifacts, diagnostics = write_site_artifacts_with_css(
        tmp_path,
        docs,
        "S",
        Path("build/site"),
        (Path("style.css"),),
        FailFS(),
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CSS002"


def test_run_mkdocs_build_returns_site_artifact(
    tmp_path: Path, monkeypatch
) -> None:
    class Completed:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("scribpy.builders.html_site.subprocess.run", lambda *a, **k: Completed())

    artifact, diagnostics = run_mkdocs_build(tmp_path, Path("build/site"))

    assert diagnostics == ()
    assert artifact is not None
    assert artifact.path == tmp_path / "build/site/site"
    assert artifact.artifact_type == "site"


def test_run_mkdocs_build_reports_failure(tmp_path: Path, monkeypatch) -> None:
    class Completed:
        returncode = 1
        stdout = ""
        stderr = "No module named mkdocs"

    monkeypatch.setattr("scribpy.builders.html_site.subprocess.run", lambda *a, **k: Completed())

    artifact, diagnostics = run_mkdocs_build(tmp_path, Path("build/site"))

    assert artifact is None
    assert diagnostics[0].code == "SITE003"


def test_run_mkdocs_build_reports_execution_error(
    tmp_path: Path, monkeypatch
) -> None:
    def fail(*args, **kwargs):
        raise OSError("missing executable")

    monkeypatch.setattr("scribpy.builders.html_site.subprocess.run", fail)

    artifact, diagnostics = run_mkdocs_build(tmp_path, Path("build/site"))

    assert artifact is None
    assert diagnostics[0].code == "SITE003"
    assert "Cannot execute MkDocs" in diagnostics[0].message
