"""Tests for the Scribpy Click command-line adapter."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

import scribpy
from scribpy.cli import cli
from scribpy.cli.main import _raise_cli_error


def test_cli_version_reports_package_version() -> None:
    """Requirement: the root command reports the public package version."""
    result = CliRunner().invoke(cli, ["--version"])

    assert result.exit_code == 0
    assert scribpy.__version__ in result.output


def test_new_calls_public_skeleton_api() -> None:
    """Requirement: new forwards all project metadata to the public API."""
    with patch("scribpy.init_skeleton") as init_skeleton:
        result = CliRunner().invoke(
            cli,
            [
                "new",
                "book",
                "--title",
                "Book",
                "--author",
                "Ada",
                "--project-version",
                "2.0",
            ],
        )

    assert result.exit_code == 0
    init_skeleton.assert_called_once_with(
        Path("book"), title="Book", author="Ada", version="2.0"
    )
    assert "Created Scribpy project" in result.output


def test_new_translates_collision_error() -> None:
    """Requirement: new translates scaffold collisions into exit code one."""
    with patch(
        "scribpy.init_skeleton",
        side_effect=scribpy.ScaffoldCollisionError("scribpy.yml"),
    ):
        result = CliRunner().invoke(cli, ["new", "book", "--title", "Book"])

    assert result.exit_code == 1
    assert "scribpy.yml" in result.output


def test_scaffold_calls_public_outline_api(tmp_path: Path) -> None:
    """Requirement: scaffold delegates outline parsing to the public API."""
    outline = tmp_path / "outline.md"
    outline.write_text("# Book\n", encoding="utf-8")
    with patch("scribpy.init_from_outline") as init_from_outline:
        result = CliRunner().invoke(
            cli,
            ["scaffold", str(outline), "book", "--max-depth", "5"],
        )

    assert result.exit_code == 0
    init_from_outline.assert_called_once_with(
        outline, Path("book"), max_depth=5
    )


def test_scaffold_translates_validation_error(tmp_path: Path) -> None:
    """Requirement: scaffold reports invalid outlines with exit code one."""
    outline = tmp_path / "outline.md"
    outline.write_text("invalid", encoding="utf-8")
    with patch(
        "scribpy.init_from_outline",
        side_effect=scribpy.OutlineValidationError(1, "invalid outline"),
    ):
        result = CliRunner().invoke(cli, ["scaffold", str(outline), "book"])

    assert result.exit_code == 1
    assert "invalid outline" in result.output


def test_validate_returns_zero_for_valid_project() -> None:
    """Requirement: validate returns zero when valid_report succeeds."""
    with patch("scribpy.valid_report", return_value=True) as valid_report:
        result = CliRunner().invoke(cli, ["validate", "book"])

    assert result.exit_code == 0
    valid_report.assert_called_once_with(Path("book"))


def test_validate_returns_one_for_invalid_project() -> None:
    """Requirement: validate returns one for blocking validation findings."""
    with patch("scribpy.valid_report", return_value=False):
        result = CliRunner().invoke(cli, ["validate", "book"])

    assert result.exit_code == 1


def test_diagnose_prints_summary_without_errors() -> None:
    """Requirement: diagnose prints the core report summary."""
    report = scribpy.CollectionDiagnosticReport()
    collection = MagicMock()
    collection.diagnose.return_value = report
    with patch.object(
        scribpy.MarkdownCollection, "from_tree", return_value=collection
    ):
        result = CliRunner().invoke(cli, ["diagnose", "book"])

    assert result.exit_code == 0
    assert "No collection diagnostics." in result.output


def test_diagnose_returns_one_for_error_diagnostic() -> None:
    """Requirement: diagnose returns one when the report has an error."""
    diagnostic = scribpy.CollectionDiagnostic(
        code="DOC001",
        severity=scribpy.DiagnosticSeverity.ERROR,
        message="Broken document",
        path=Path("index.md"),
        line=2,
    )
    collection = MagicMock()
    collection.diagnose.return_value = scribpy.CollectionDiagnosticReport(
        (diagnostic,)
    )
    with patch.object(
        scribpy.MarkdownCollection, "from_tree", return_value=collection
    ):
        result = CliRunner().invoke(cli, ["diagnose", "book"])

    assert result.exit_code == 1
    assert "ERROR DOC001 index.md:2: Broken document" in result.output


def test_diagnose_translates_loading_error() -> None:
    """Requirement: diagnose translates collection loading failures."""
    with patch.object(
        scribpy.MarkdownCollection,
        "from_tree",
        side_effect=NotADirectoryError("book"),
    ):
        result = CliRunner().invoke(cli, ["diagnose", "book"])

    assert result.exit_code == 1
    assert "book" in result.output


def test_build_calls_public_concatenate_api() -> None:
    """Requirement: build loads a collection then delegates assembly."""
    collection = MagicMock()
    with (
        patch.object(
            scribpy.MarkdownCollection,
            "from_tree",
            return_value=collection,
        ),
        patch("scribpy.concatenate") as concatenate,
    ):
        result = CliRunner().invoke(cli, ["build", "book", "output/book.md"])

    assert result.exit_code == 0
    concatenate.assert_called_once_with(collection, Path("output/book.md"))


def test_build_translates_assembly_error() -> None:
    """Requirement: build translates documented assembly failures."""
    collection = MagicMock()
    with (
        patch.object(
            scribpy.MarkdownCollection,
            "from_tree",
            return_value=collection,
        ),
        patch(
            "scribpy.concatenate",
            side_effect=scribpy.InvalidMarkdownError("invalid markdown"),
        ),
    ):
        result = CliRunner().invoke(cli, ["build", "book", "book.md"])

    assert result.exit_code == 1
    assert "invalid markdown" in result.output


def test_html_calls_public_export_api(tmp_path: Path) -> None:
    """Requirement: html forwards navigation and CSS options."""
    css = tmp_path / "custom.css"
    css.write_text("body {}", encoding="utf-8")
    with patch("scribpy.html_export") as html_export:
        result = CliRunner().invoke(
            cli,
            [
                "html",
                "book.md",
                "book.html",
                "--toc-depth",
                "4",
                "--css",
                str(css),
            ],
        )

    assert result.exit_code == 0
    html_export.assert_called_once_with(
        Path("book.md"), Path("book.html"), toc_depth=4, css=css
    )


def test_html_translates_export_error() -> None:
    """Requirement: html translates documented file failures."""
    with patch(
        "scribpy.html_export", side_effect=FileNotFoundError("book.md")
    ):
        result = CliRunner().invoke(cli, ["html", "book.md", "book.html"])

    assert result.exit_code == 1
    assert "book.md" in result.output


def test_mkdocs_export_calls_public_export_api() -> None:
    """Requirement: mkdocs-export delegates to the public export API."""
    with patch("scribpy.mkdocs_export") as mkdocs_export:
        result = CliRunner().invoke(cli, ["mkdocs-export", "book", "site"])

    assert result.exit_code == 0
    mkdocs_export.assert_called_once_with(Path("book"), Path("site"))


def test_mkdocs_export_translates_collision_error() -> None:
    """Requirement: mkdocs-export translates documented failures."""
    with patch(
        "scribpy.mkdocs_export",
        side_effect=scribpy.ScaffoldCollisionError("mkdocs.yml"),
    ):
        result = CliRunner().invoke(cli, ["mkdocs-export", "book", "site"])

    assert result.exit_code == 1
    assert "mkdocs.yml" in result.output


def test_cli_error_uses_exception_class_for_empty_message() -> None:
    """Requirement: translated empty errors retain an actionable name."""
    with pytest.raises(click.ClickException, match="OSError"):
        _raise_cli_error(OSError())


def test_cli_integrates_new_build_and_html(tmp_path: Path) -> None:
    """Requirement: new, build, and html form a real end-to-end workflow."""
    runner = CliRunner()
    root = tmp_path / "book"
    markdown_output = tmp_path / "build" / "book.md"
    html_output = tmp_path / "build" / "book.html"

    new_result = runner.invoke(cli, ["new", str(root), "--title", "My Book"])
    build_result = runner.invoke(
        cli, ["build", str(root), str(markdown_output)]
    )
    html_result = runner.invoke(
        cli, ["html", str(markdown_output), str(html_output)]
    )

    assert new_result.exit_code == 0
    assert build_result.exit_code == 0
    assert html_result.exit_code == 0
    assert "My Book" in html_output.read_text(encoding="utf-8")
