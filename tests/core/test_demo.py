"""Tests for demo project creation."""

from pathlib import Path

import pytest

from scribpy.core import create_demo_project, run_index_check


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
    assert existing.read_text(encoding="utf-8").startswith("# Scribpy Demo")


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
