"""Tests for demo project creation."""

from pathlib import Path

import pytest

from scribpy.core import create_demo_project, parse_project_documents, run_index_check


def test_create_demo_project_writes_tutorial_files(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"

    result = create_demo_project(target)

    assert result.failed is False
    assert result.diagnostics == ()
    assert (target / "scribpy.toml").is_file()
    assert (target / "doc/index.md").is_file()
    assert (target / "doc/guide/setup.md").is_file()
    assert (target / "README.md").is_file()


def test_created_demo_project_passes_index_check(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = run_index_check(target)

    assert result.failed is False
    assert result.diagnostics == ()


def test_create_invalid_demo_project_produces_index_diagnostics(
    tmp_path: Path,
) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target, variant="invalid")

    result = run_index_check(target)

    assert result.failed is True
    assert tuple(diagnostic.code for diagnostic in result.diagnostics) == (
        "IDX003",
        "IDX002",
        "IDX005",
    )


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


def test_create_demo_project_overwrites_demo_files_with_force(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    (target / "doc").mkdir(parents=True)
    existing = target / "doc/index.md"
    existing.write_text("# Existing\n", encoding="utf-8")

    result = create_demo_project(target, force=True)

    assert result.failed is False
    assert "# Scribpy Demo" in existing.read_text(encoding="utf-8")


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
    assert len(result.documents) == 2


def test_created_demo_project_documents_in_index_order(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    titles = [d.title for d in result.documents]
    assert titles == ["Scribpy Demo", "Setup Guide"]


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
    assert any("guide/setup.md" in t for t in all_targets)
    assert any("github.com" in t for t in all_targets)


def test_created_demo_project_assets_extracted(tmp_path: Path) -> None:
    target = tmp_path / "external-demo"
    create_demo_project(target)

    result = parse_project_documents(target)

    index_doc = result.documents[0]
    assert len(index_doc.assets) == 1
    assert index_doc.assets[0].target == "assets/architecture.png"


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

    assert result.failed is True
