"""Tests for the Scribpy command-line entry point."""

import importlib
from pathlib import Path

import click
import pytest

from scribpy.cli.main import _exit_code, _runtime, main

cli_main_module = importlib.import_module("scribpy.cli.main")


def test_index_check_returns_zero_for_valid_project(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    exit_code = main(["index", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Resolve project configuration" in captured.out
    assert "Build document index" in captured.out
    assert captured.err == ""


def test_cli_logging_writes_default_log_file(tmp_path: Path, capsys) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    exit_code = main(
        ["--log-level", "INFO", "index", "check", "--root", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Build document index" in captured.out
    assert captured.err == ""
    assert (tmp_path / "build/logs/scribpy.log").exists()


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


def test_demo_create_invalid_variant_creates_project_with_lint_diagnostics(
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
    assert check_exit_code == 0
    assert check_output.err == ""

    lint_exit_code = main(["lint", "--root", str(target)])
    lint_output = capsys.readouterr()
    assert lint_exit_code == 1
    assert "error LINT001" in lint_output.err
    assert "error LINT002" in lint_output.err
    assert "error LINT003" in lint_output.err
    assert "error LINT004" in lint_output.err


def test_demo_create_help_documents_variants_and_examples(capsys) -> None:
    exit_code = main(["demo", "create", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy demo create dd1 --variant invalid" in captured.out
    assert (
        "valid    creates a project expected to pass index, parse, and lint checks"
        in captured.out
    )
    assert (
        "invalid  creates a project with intentional lint diagnostics"
        in captured.out
    )


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
    assert "scribpy build markdown --root" in captured.out
    assert "scribpy build html --mode single-page --root" in captured.out
    assert "scribpy build html --mode site --root" in captured.out
    assert "scribpy build pdf --root" in captured.out
    assert "scribpy index check" in captured.out
    assert "scribpy parse check" in captured.out
    assert "scribpy lint" in captured.out
    assert captured.err == ""


def test_index_check_returns_one_and_prints_diagnostics_for_invalid_project(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(["index", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error CFG001" in captured.err
    assert "failed" in captured.out


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
    assert "Build document index" in captured.out


def test_invalid_cli_usage_returns_two(capsys) -> None:
    exit_code = main(["unknown"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid choice" in captured.err


def test_build_html_cli_accepts_plantuml_overrides(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(
        tmp_path, "doc/index.md", "# Home\n\n```plantuml\nA -> B\n```\n"
    )

    class FakeRenderer:
        def render(self, source: str, output_format: str) -> bytes:
            return b"<svg/>"

    monkeypatch.setattr(
        "scribpy.plugins.plantuml.WebPlantUmlRenderer",
        lambda _: FakeRenderer(),
    )

    exit_code = main(
        [
            "build",
            "html",
            "--root",
            str(tmp_path),
            "--plantuml-renderer",
            "web",
            "--plantuml-server-url",
            "https://example.test/plantuml",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "HTML (single-page)" in captured.out


def test_build_pdf_cli_reports_missing_optional_renderer(
    tmp_path: Path, capsys, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    def missing_module(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr("scribpy.builders.pdf.import_module", missing_module)

    exit_code = main(["build", "pdf", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "PDF" in captured.out
    assert "error PDF001" in captured.err


def test_missing_subcommand_returns_two(capsys) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage:" in captured.err


def test_non_integer_system_exit_code_maps_to_usage_error() -> None:
    assert _exit_code(SystemExit("bad usage")) == 2


def test_integer_system_exit_code_is_preserved() -> None:
    assert _exit_code(SystemExit(7)) == 7


def test_main_returns_click_exit_code(monkeypatch) -> None:
    def fake_app(*args, **kwargs):
        raise click.exceptions.Exit(7)

    monkeypatch.setattr(cli_main_module, "app", fake_app)

    assert main(["lint"]) == 7


def test_main_renders_generic_click_exception(monkeypatch, capsys) -> None:
    def fake_app(*args, **kwargs):
        raise click.ClickException("boom")

    monkeypatch.setattr(cli_main_module, "app", fake_app)

    assert main(["lint"]) == 1
    assert "Error: boom" in capsys.readouterr().err


def test_runtime_rejects_uninitialized_context() -> None:
    class Context:
        def find_root(self):
            return self

        obj = None

    with pytest.raises(RuntimeError, match="CLI runtime was not initialized"):
        _runtime(Context())


def test_parse_check_returns_zero_for_valid_project(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md")

    exit_code = main(["parse", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Parse Markdown documents" in captured.out
    assert "Parsed 1 document(s)." in captured.out
    assert captured.err == ""


def test_parse_check_returns_one_when_config_missing(
    tmp_path: Path,
    capsys,
) -> None:
    exit_code = main(["parse", "check", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error CFG001" in captured.err
    assert "failed" in captured.out


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
    assert "Parsed 1 document(s)." in captured.out


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
    assert "Run lint rules" in captured.out
    assert captured.err == ""


def test_lint_returns_one_and_prints_diagnostics(
    tmp_path: Path, capsys
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    exit_code = main(["lint", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error LINT001" in captured.err
    assert "error LINT002" in captured.err
    assert "Run lint rules — failed" in captured.out


def test_lint_help_documents_examples(capsys) -> None:
    exit_code = main(["lint", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy lint --root dd1" in captured.out


def test_build_markdown_returns_zero_and_prints_artifact_path(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(["build", "markdown", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Build Markdown — done" in captured.out
    assert "Primary artifact:" in captured.out
    assert "build/markdown/document.md" in captured.out
    assert captured.err == ""


def test_build_markdown_accepts_output_dir_override(
    tmp_path: Path, capsys
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(
        [
            "build",
            "markdown",
            "--root",
            str(tmp_path),
            "--output-dir",
            "ci/markdown",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ci/markdown/document.md" in captured.out
    assert (tmp_path / "ci/markdown/document.md").is_file()


def test_build_markdown_returns_one_when_lint_fails(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    exit_code = main(["build", "markdown", "--root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "error LINT001" in captured.err
    assert "error BLD002" in captured.err
    assert "Run lint rules — failed" in captured.out


def test_build_markdown_help_documents_examples(capsys) -> None:
    exit_code = main(["build", "markdown", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "scribpy build markdown --root dd1" in captured.out


def test_build_without_subcommand_returns_usage_error(capsys) -> None:
    exit_code = main(["build"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "usage:" in captured.err


def test_build_html_single_page_returns_zero_and_prints_artifact(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(
        ["build", "html", "--mode", "single-page", "--root", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Build HTML (single-page) — done" in captured.out
    assert "index.html" in captured.out
    assert captured.err == ""


def test_build_html_site_returns_zero_and_prints_site_artifact(
    tmp_path: Path,
    capsys,
    monkeypatch,
) -> None:
    from scribpy.model import BuildArtifact

    def fake_run(project_root: Path, output_dir: Path):
        site_dir = project_root / output_dir / "site"
        site_dir.mkdir(parents=True, exist_ok=True)
        return BuildArtifact(site_dir, "html-site", "site"), ()

    monkeypatch.setattr(
        "scribpy.core.build_html_site.run_mkdocs_build", fake_run
    )
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(
        ["build", "html", "--mode", "site", "--root", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Build HTML (site) — done" in captured.out
    assert "build/site/site" in captured.out


def test_build_html_returns_one_when_lint_fails(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "## Missing H1\n")

    exit_code = main(
        ["build", "html", "--mode", "single-page", "--root", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "LINT001" in captured.err
    assert "Run lint rules — failed" in captured.out


def test_build_html_defaults_to_single_page_mode(
    tmp_path: Path,
    capsys,
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(["build", "html", "--root", str(tmp_path)])

    capsys.readouterr()
    assert exit_code == 0
    assert (tmp_path / "build/html/index.html").exists()


def test_build_html_accepts_output_dir_override(
    tmp_path: Path, capsys
) -> None:
    _write_config(tmp_path, '[paths]\nsource = "doc"\n')
    _write_source(tmp_path, "doc/index.md", "# Home\n")

    exit_code = main(
        [
            "build",
            "html",
            "--root",
            str(tmp_path),
            "--output-dir",
            "ci/html",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "ci/html/index.html" in captured.out
    assert (tmp_path / "ci/html/index.html").is_file()


def test_build_html_help_documents_modes(capsys) -> None:
    exit_code = main(["build", "html", "-h"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "single-page" in captured.out
    assert "site" in captured.out


def _write_config(root: Path, content: str) -> Path:
    config_path = root / "scribpy.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _write_source(
    root: Path, relative_path: str, content: str = "# Title\n"
) -> Path:
    source_path = root / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(content, encoding="utf-8")
    return source_path
