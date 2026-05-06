"""Tests for the Scribpy command-line entry point."""

from pathlib import Path

from scribpy.cli.main import _exit_code, main


def test_index_check_returns_zero_for_valid_project(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    exit_code = main(["index", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_index_check_returns_one_and_prints_diagnostics_for_invalid_project(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(["index", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error CFG001" in captured.err
    assert captured.out == ""


def test_index_check_returns_zero_and_prints_warning_diagnostics(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    (tmp_path / "doc").mkdir()

    exit_code = main(["index", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "warning PRJ002" in captured.err
    assert captured.out == ""


def test_invalid_cli_usage_returns_two(capsys) -> None:
    exit_code = main(["unknown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid choice" in captured.err


def test_missing_subcommand_returns_two(capsys) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage:" in captured.err


def test_non_integer_system_exit_code_maps_to_usage_error() -> None:
    assert _exit_code(SystemExit("bad usage")) == 2


def _write_config(root: Path, content: str) -> Path:
    config_path = root / "scribpy.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _write_source(root: Path, relative_path: str) -> Path:
    source_path = root / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text("# Title\n", encoding="utf-8")
    return source_path
