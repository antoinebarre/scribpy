"""Tests for lint_project (FC-04)."""

from pathlib import Path

from scribpy.core import lint_project


def _write_config(root: Path, content: str) -> None:
    (root / "scribpy.toml").write_text(content, encoding="utf-8")


def _write_source(root: Path, relative_path: str, content: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_lint_project_returns_zero_diagnostics_for_valid_project(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n\n[Guide](guide.md#setup)\n")
    _write_source(tmp_path, "doc/guide.md", "# Guide\n\n## Setup\n")

    result = lint_project(tmp_path)

    assert result.failed is False
    assert result.diagnostics == ()


def test_lint_project_reports_native_rule_diagnostics(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(
        tmp_path,
        "doc/index.md",
        "## Missing H1\n\n[Ghost](ghost.md)\n\n![Logo](assets/logo.png)\n",
    )

    result = lint_project(tmp_path)

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "LINT001",
        "LINT002",
        "LINT003",
        "LINT004",
    ]


def test_lint_project_propagates_parse_diagnostics_without_running_rules(
    tmp_path: Path,
) -> None:
    result = lint_project(tmp_path)

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CFG001"]


def test_lint_project_stops_on_invalid_config(tmp_path: Path) -> None:
    _write_config(tmp_path, "[paths]\nsource = 42\n")

    result = lint_project(tmp_path)

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["CFG003"]


def test_lint_project_stops_on_missing_source_directory(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "missing"\n')

    result = lint_project(tmp_path)

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PRJ001"]


def test_lint_project_stops_on_invalid_explicit_index(tmp_path: Path) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n[index]\nmode = "explicit"\nfiles = ["ghost.md"]\n',
    )
    (tmp_path / "doc").mkdir()

    result = lint_project(tmp_path)

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "PRJ002",
        "IDX002",
    ]


def test_lint_project_stops_on_parse_error(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    class FailingParser:
        def parse(self, text: str):
            raise RuntimeError("boom")

    result = lint_project(tmp_path, parser=FailingParser())

    assert result.failed is True
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PRS003"]
