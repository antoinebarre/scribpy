"""Tests for the index-check application service."""

from pathlib import Path

from scribpy.core import check_index
from scribpy.core.index_check import run_index_check


def test_run_index_check_returns_success_for_filesystem_project(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    result = run_index_check(tmp_path)

    assert result.failed is False
    assert result.diagnostics == ()


def test_check_index_alias_returns_success_for_explicit_project(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n[index]\nmode = "explicit"\nfiles = ["index.md"]\n',
    )
    _write_source(tmp_path, "doc/index.md")

    result = check_index(tmp_path / "doc")

    assert result.failed is False
    assert result.diagnostics == ()


def test_run_index_check_returns_cfg001_when_config_is_missing(
    tmp_path: Path,
) -> None:
    result = run_index_check(tmp_path)

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("CFG001",)


def test_run_index_check_stops_on_invalid_config(tmp_path: Path) -> None:
    _write_config(tmp_path, "[paths]\nsource = 42\n")

    result = run_index_check(tmp_path)

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("CFG003",)


def test_run_index_check_stops_on_source_scan_error(tmp_path: Path) -> None:
    _write_config(tmp_path, '[paths]\nsource = "missing"\n')

    result = run_index_check(tmp_path)

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("PRJ001",)


def test_run_index_check_aggregates_scan_warning_and_index_error(
    tmp_path: Path,
) -> None:
    _write_config(
        tmp_path,
        '[paths]\nsource = "doc"\n\n'
        '[index]\nmode = "explicit"\nfiles = ["missing.md"]\n',
    )
    (tmp_path / "doc").mkdir()

    result = run_index_check(tmp_path)

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("PRJ002", "IDX002")


def test_run_index_check_returns_idx001_for_hybrid_index_mode(
    tmp_path: Path,
) -> None:
    _write_config(tmp_path, '[index]\nmode = "hybrid"\n')
    _write_source(tmp_path, "doc/index.md")

    result = run_index_check(tmp_path)

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("IDX001",)


def test_run_index_check_accepts_direct_config_path(tmp_path: Path) -> None:
    config_path = _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    result = run_index_check(config_path)

    assert result.failed is False
    assert result.diagnostics == ()


def test_run_index_check_returns_cfg001_for_missing_direct_config_path(
    tmp_path: Path,
) -> None:
    result = run_index_check(tmp_path / "scribpy.toml")

    assert result.failed is True
    assert _diagnostic_codes(result.diagnostics) == ("CFG001",)


def _write_config(root: Path, content: str) -> Path:
    config_path = root / "scribpy.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _write_source(root: Path, relative_path: str) -> Path:
    source_path = root / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("# Title\n", encoding="utf-8")
    return source_path


def _diagnostic_codes(diagnostics: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(getattr(diagnostic, "code") for diagnostic in diagnostics)
