"""Tests for demo project creation."""

from pathlib import Path

import pytest

from scribpy.core import (
    build_project,
    create_demo_project,
    lint_project,
    parse_project_documents,
    run_index_check,
)


def test_create_demo_project_writes_tutorial_files(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"

    result = create_demo_project(target)

    assert result.failed is False
    assert result.diagnostics == ()
    assert (target / "scribpy.toml").is_file()
    assert (target / "doc/index.md").is_file()
    assert (target / "doc/guide/getting-started/overview.md").is_file()
    assert (target / "doc/guide/workflows/review.md").is_file()
    assert (target / "doc/architecture/pipeline.md").is_file()
    assert (target / "doc/reference/diagnostics.md").is_file()
    assert (target / "doc/tutorials/build-markdown.md").is_file()
    assert (target / "doc/appendix/changelog.md").is_file()
    assert (target / "doc/assets/architecture.svg").is_file()
    assert (target / "doc/assets/setup.svg").is_file()
    assert (target / "theme/demo.css").is_file()
    assert (target / "theme/pdf.css").is_file()
    assert (target / "README.md").is_file()
    assert len(tuple((target / "doc").rglob("*.md"))) == 33


def test_created_demo_project_passes_index_check(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = run_index_check(target)

    assert result.failed is False
    assert result.diagnostics == ()


def test_created_demo_project_exposes_transform_configuration(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    config = (target / "scribpy.toml").read_text(encoding="utf-8")

    assert '[document]\ntitle = "Scribpy Demo Manual"' in config
    assert (
        '[document.toc]\nenabled = true\nmax_level = 3\nstyle = "bullet"'
        in config
    )
    assert (
        '[document.numbering]\nenabled = true\nmax_level = 3\nstyle = "decimal"'
        in config
    )
    assert (
        '[builders.html]\nmode = "single-page"\ncss_files = ["theme/demo.css"]\n'
        'theme = "readthedocs"' in config
    )
    assert '[builders.pdf]\ncss = ["theme/pdf.css"]' in config


def test_create_invalid_demo_project_passes_index_check(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target, variant="invalid")

    result = run_index_check(target)

    assert result.failed is False
    assert result.diagnostics == ()


def test_create_demo_project_refuses_existing_demo_files_without_force(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    (target / "doc").mkdir(parents=True)
    (target / "doc/index.md").write_text("# Existing\n", encoding="utf-8")

    result = create_demo_project(target)

    assert result.failed is True
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "DEMO001"
    assert result.diagnostics[0].path == target / "doc/index.md"


def test_create_demo_project_overwrites_demo_files_with_force(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    (target / "doc").mkdir(parents=True)
    existing = target / "doc/index.md"
    existing.write_text("# Existing\n", encoding="utf-8")

    result = create_demo_project(target, force=True)

    assert result.failed is False
    assert "# Scribpy Demo" in existing.read_text(encoding="utf-8")


def test_create_demo_project_rejects_unknown_variant(tmp_path: Path) -> None:
    result = create_demo_project(tmp_path, variant="broken")  # type: ignore[arg-type]

    assert result.failed is True
    assert result.diagnostics[0].code == "DEMO003"


def test_create_demo_project_refuses_file_target(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    target.write_text("not a directory\n", encoding="utf-8")

    result = create_demo_project(target)

    assert result.failed is True
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "DEMO001"


def test_create_demo_project_reports_write_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def fail_write_text(
        self: Path,
        data: str,
        encoding: str | None = None,
    ) -> int:
        raise OSError("disk full")

    monkeypatch.setattr(Path, "write_text", fail_write_text)

    result = create_demo_project(tmp_path / "external-demo")

    assert result.failed is True
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "DEMO002"


# ---------------------------------------------------------------------------
# Phase 3 integration — valid demo passes parse check
# ---------------------------------------------------------------------------


def test_created_demo_project_passes_parse_check(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    assert result.failed is False
    assert len(result.documents) == 33


def test_created_demo_project_documents_in_index_order(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    titles = [d.title for d in result.documents]
    assert titles[:4] == [
        "Scribpy Demo",
        "Getting Started Overview",
        "Installation Guide",
        "Quickstart",
    ]
    assert titles[-3:] == ["Glossary", "Roadmap", "Changelog"]


def test_created_demo_project_uses_document_oriented_copy(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    page = (target / "doc/guide/getting-started/overview.md").read_text(
        encoding="utf-8"
    )

    assert "This section belongs" in page
    assert "## In the assembled manual" in page
    assert "previous page" not in page
    assert "next page" not in page


def test_created_demo_project_contains_complex_plantuml_examples(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    pipeline = (target / "doc/architecture/pipeline.md").read_text(
        encoding="utf-8"
    )
    data_model = (target / "doc/architecture/data-model.md").read_text(
        encoding="utf-8"
    )
    overview = (target / "doc/architecture/overview.md").read_text(
        encoding="utf-8"
    )

    assert "```plantuml" in pipeline
    assert "alt diagnostics contain errors" in pipeline
    assert "class BuildResult" in data_model
    assert "Bundled PlantUML MIT JAR" in overview


def test_created_demo_project_contains_complex_mermaid_examples(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    functional_chains = (
        target / "doc/concepts/functional-chains.md"
    ).read_text(encoding="utf-8")
    extensions = (target / "doc/architecture/extensions.md").read_text(
        encoding="utf-8"
    )
    ci = (target / "doc/operations/ci.md").read_text(encoding="utf-8")

    assert "```mermaid" in functional_chains
    assert "Delivery Control Flow" in functional_chains
    assert "classDiagram" in extensions
    assert "sequenceDiagram" in ci


def test_created_demo_project_frontmatter_extracted(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    index_doc = result.documents[0]
    assert index_doc.frontmatter["author"] == "Demo Author"
    assert index_doc.frontmatter["version"] == 1
    assert index_doc.frontmatter["tags"] == ["scribpy", "docs-as-code"]


def test_created_demo_project_links_extracted(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    index_doc = result.documents[0]
    all_targets = [link.target for link in index_doc.links]
    assert any("guide/getting-started/overview.md" in t for t in all_targets)
    assert any("github.com" in t for t in all_targets)


def test_created_demo_project_assets_extracted(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    index_doc = result.documents[0]
    assert len(index_doc.assets) == 1
    assert index_doc.assets[0].target == "assets/architecture.svg"


def test_created_demo_project_headings_extracted(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    index_doc = result.documents[0]
    levels = [h.level for h in index_doc.headings]
    assert 1 in levels
    assert 2 in levels


def test_invalid_demo_fails_parse_check(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target, variant="invalid")

    result = parse_project_documents(target)

    assert result.failed is False


def test_created_demo_project_passes_lint(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = lint_project(target)

    assert result.failed is False
    assert result.diagnostics == ()


def test_created_demo_project_builds_with_configured_document_transforms(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = build_project(target)

    assert result.success is True
    artifact = result.artifacts[0]
    content = artifact.path.read_text(encoding="utf-8")
    assert content.startswith(
        "# Scribpy Demo Manual\n\n"
        "## Table of Contents\n"
        "- [1 Scribpy Demo](#1-scribpy-demo)\n"
    )
    assert "  - [2.1 Overview](#21-overview)" in content
    assert "### 2.1 Overview" in content


def test_created_demo_project_readme_documents_end_to_end_html_flow(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    readme = (target / "README.md").read_text(encoding="utf-8")

    assert "## End-to-end walkthrough" in readme
    assert "scribpy build html --mode single-page --root ." in readme
    assert "scribpy build html --mode site --root ." in readme
    assert (
        "Scribpy prepares the MkDocs inputs and wraps `mkdocs build` itself."
        in readme
    )
    assert "build/site/site/index.html" in readme
    assert "scribpy build markdown --root ." in readme
    assert "builders.html.theme" in readme
    assert "## Execution logs" in readme
    assert "scribpy --log-level INFO build html --mode site --root ." in readme
    assert "with scribpy.logging_context" in readme
    assert "complex PlantUML and Mermaid diagrams" in readme
    assert 'renderer = "java"' in readme


def test_invalid_demo_reports_phase_4_lint_diagnostics(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target, variant="invalid")

    result = lint_project(target)

    assert result.failed is True
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        "LINT001",
        "LINT002",
        "LINT003",
        "LINT004",
    )
