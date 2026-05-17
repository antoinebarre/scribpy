"""Tests for public Scribpy logging configuration."""

from pathlib import Path

import scribpy


def _write_project(root: Path) -> None:
    (root / "doc").mkdir()
    (root / "scribpy.toml").write_text('[paths]\nsource = "doc"\n', encoding="utf-8")
    (root / "doc/index.md").write_text("# Home\n", encoding="utf-8")


def test_logging_context_writes_default_project_log_file(tmp_path: Path) -> None:
    _write_project(tmp_path)

    with scribpy.logging_context(level="INFO"):
        result = scribpy.build_markdown(tmp_path)

    assert result.success is True
    log = tmp_path / "build/logs/scribpy.log"
    assert log.exists()
    content = log.read_text(encoding="utf-8")
    assert "Discovered 1 Markdown source file(s)" in content
    assert "Built Markdown artifact" in content


def test_logging_context_writes_custom_relative_log_file(tmp_path: Path) -> None:
    _write_project(tmp_path)

    with scribpy.logging_context(level="DEBUG", file_path="logs/custom.log"):
        scribpy.check_parse(tmp_path)

    assert (tmp_path / "logs/custom.log").exists()
