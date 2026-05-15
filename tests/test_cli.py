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
    assert "Created valid Scribpy demo project" in captured.out
    assert captured.err == ""
    assert (target / "scribpy.toml").is_file()

    check_exit_code = main(["index", "check", "--root", str(target)])
    check_output = capsys.readouterr()
    assert check_exit_code == 0
    assert check_output.err == ""


def test_demo_create_invalid_variant_creates_project_with_diagnostics(
    tmp_path: Path,
    capsys,
) -> None:
    target = tmp_path / "external-demo"

    exit_code = main(["demo", "create", str(target), "--variant", "invalid"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Created invalid Scribpy demo project" in captured.out
    assert captured.err == ""

    check_exit_code = main(["index", "check", "--root", str(target)])
    check_output = capsys.readouterr()
    assert check_exit_code == 1
    assert "error IDX002" in check_output.err
    assert "error IDX003" in check_output.err
    assert "warning IDX005" in check_output.err


def test_demo_create_help_documents_variants_and_examples(capsys) -> None:
    exit_code = main(["demo", "create", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy demo create dd1 --variant invalid" in captured.out
    assert "valid    creates a project expected to pass index check" in captured.out
    assert "invalid  creates a project with missing" in captured.out


def test_root_help_documents_common_workflows(capsys) -> None:
    exit_code = main(["-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Common workflows:" in captured.out
    assert "scribpy demo create dd1" in captured.out
    assert "scribpy index check --root dd1" in captured.out


def test_demo_help_documents_next_step(capsys) -> None:
    exit_code = main(["demo", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "After creation:" in captured.out
    assert "scribpy index check --root dd1" in captured.out


def test_index_check_help_documents_examples_and_exit_codes(capsys) -> None:
    exit_code = main(["index", "check", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy index check --root dd1" in captured.out
    assert "What is checked:" in captured.out
    assert "0  no blocking error diagnostics" in captured.out
    assert "1  at least one error diagnostic" in captured.out


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
    assert "Next steps:" in captured.out
    assert "scribpy index check" in captured.out
    assert "scribpy parse check" in captured.out
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


def test_parse_check_returns_zero_for_valid_project(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    exit_code = main(["parse", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "1 document(s) successfully" in captured.out
    assert captured.err == ""


def test_parse_check_returns_one_when_config_missing(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(["parse", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error CFG001" in captured.err
    assert captured.out == ""


def test_parse_check_prints_warning_but_returns_zero(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "---\nbad: [unclosed\n---\n# T\n")

    exit_code = main(["parse", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "PRS002" in captured.err
    assert "1 document(s) successfully" in captured.out


def test_parse_check_help_documents_examples_and_exit_codes(capsys) -> None:
    exit_code = main(["parse", "check", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy parse check --root dd1" in captured.out
    assert "What is checked:" in captured.out
    assert "0  no blocking error diagnostics" in captured.out


def test_lint_returns_zero_for_valid_project(tmp_path: Path, capsys) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(["lint", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""


def test_lint_returns_one_and_prints_diagnostics(tmp_path: Path, capsys) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    exit_code = main(["lint", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error LINT001" in captured.err
    assert "error LINT002" in captured.err


def test_lint_help_documents_examples(capsys) -> None:
    exit_code = main(["lint", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy lint --root dd1" in captured.out


def _write_config(root: Path, content: str) -> Path:
    config_path = root / "scribpy.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _write_source(root: Path, relative_path: str, content: str = "# Title\n") -> Path:
    source_path = root / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(content, encoding="utf-8")
    return source_path
