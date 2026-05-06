"""Tests for project source discovery."""

from pathlib import Path

from scribpy.config.types import Config, PathConfig
from scribpy.project.scanner import resolve_project_root, scan_project


def test_resolve_project_root_uses_config_file_parent(tmp_path: Path) -> None:
    config_path = tmp_path / "scribpy.toml"
    config_path.write_text("[project]\n", encoding="utf-8")

    assert resolve_project_root(config_path) == tmp_path.resolve()


def test_scan_project_discovers_markdown_sources_deterministically(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "doc"
    nested_dir = source_dir / "guide"
    nested_dir.mkdir(parents=True)
    (source_dir / "z.md").write_text("# Z\n", encoding="utf-8")
    (source_dir / "a.md").write_text("# A\n", encoding="utf-8")
    (source_dir / "notes.txt").write_text("not markdown\n", encoding="utf-8")
    (nested_dir / "setup.md").write_text("# Setup\n", encoding="utf-8")

    source_files, diagnostics = scan_project(tmp_path, Config())

    assert diagnostics == ()
    assert tuple(source.relative_path for source in source_files) == (
        Path("a.md"),
        Path("guide/setup.md"),
        Path("z.md"),
    )
    assert tuple(source.path for source in source_files) == (
        source_dir / "a.md",
        nested_dir / "setup.md",
        source_dir / "z.md",
    )


def test_scan_project_uses_configured_source_directory(tmp_path: Path) -> None:
    source_dir = tmp_path / "docs"
    source_dir.mkdir()
    (source_dir / "index.md").write_text("# Index\n", encoding="utf-8")

    source_files, diagnostics = scan_project(
        tmp_path,
        Config(paths=PathConfig(source=Path("docs"))),
    )

    assert diagnostics == ()
    assert len(source_files) == 1
    assert source_files[0].relative_path == Path("index.md")
    assert source_files[0].path == source_dir / "index.md"


def test_scan_project_returns_prj001_when_source_directory_is_missing(
    tmp_path: Path,
) -> None:
    source_files, diagnostics = scan_project(tmp_path, Config())

    assert source_files == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "PRJ001"
    assert diagnostics[0].severity == "error"
    assert diagnostics[0].path == Path("doc")


def test_scan_project_returns_prj002_when_source_directory_has_no_markdown(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "doc"
    source_dir.mkdir()
    (source_dir / "notes.txt").write_text("not markdown\n", encoding="utf-8")

    source_files, diagnostics = scan_project(tmp_path, Config())

    assert source_files == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "PRJ002"
    assert diagnostics[0].severity == "warning"
    assert diagnostics[0].path == Path("doc")


def test_scan_project_returns_prj003_when_source_path_leaves_project(
    tmp_path: Path,
) -> None:
    project_root = tmp_path / "project"
    outside_dir = tmp_path / "outside"
    project_root.mkdir()
    outside_dir.mkdir()

    source_files, diagnostics = scan_project(
        project_root,
        Config(paths=PathConfig(source=Path("../outside"))),
    )

    assert source_files == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "PRJ003"
    assert diagnostics[0].severity == "error"
    assert diagnostics[0].path == Path("../outside")
