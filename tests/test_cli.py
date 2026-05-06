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


def test_demo_create_returns_zero_and_creates_valid_project(
    tmp_path: Path,
    capsys,
) -> None:
    target = tmp_path / "external-demo"

    exit_code = main(["demo", "create", str(target)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Created Scribpy demo project" in captured.out
    assert captured.err == ""
    assert (target / "scribpy.toml").is_file()

    check_exit_code = main(["index", "check", "--root", str(target)])
    check_output = capsys.readouterr()
    assert check_exit_code == 0
    assert check_output.err == ""


def test_demo_create_returns_one_when_target_contains_demo_files(
    tmp_path: Path,
    capsys,
) -> None:
    target = tmp_path / "external-demo"
    (target / "doc").mkdir(parents=True)
    (target / "doc/index.md").write_text("# Existing\n", encoding="utf-8")

    exit_code = main(["demo", "create", str(target)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error DEMO001" in captured.err
    assert captured.out == ""


def test_demo_create_force_overwrites_demo_files(
    tmp_path: Path,
    capsys,
) -> None:
    target = tmp_path / "external-demo"
    (target / "doc").mkdir(parents=True)
    (target / "doc/index.md").write_text("# Existing\n", encoding="utf-8")

    exit_code = main(["demo", "create", str(target), "--force"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Next: scribpy index check" in captured.out
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
