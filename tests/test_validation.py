"""Tests for Scribpy project validation and console reporting."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

import mkforge
import pytest
from rich.console import Console

from scribpy import (
    DiagnosticSeverity,
    ProjectDiagnostic,
    ProjectValidationReport,
    render_validation_report,
    valid_report,
    validate_project,
)
from scribpy.core.markdown_file import MarkdownFile


def _write(path: Path, content: str) -> None:
    """Write UTF-8 test content after creating parent directories.

    Args:
        path: Test file destination.
        content: UTF-8 text written to the destination.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class TestProjectValidationReport:
    """Tests for the project validation result model."""

    def test_report_exposes_validity_and_severity_filters(self) -> None:
        """Requirement: reports derive validity and filter diagnostics."""
        warning = ProjectDiagnostic(
            code="WARNING",
            severity=DiagnosticSeverity.WARNING,
            message="Warning.",
        )
        valid_report_result = ProjectValidationReport(
            root=Path("project"), diagnostics=(warning,)
        )
        error = ProjectDiagnostic(
            code="ERROR",
            severity=DiagnosticSeverity.ERROR,
            message="Error.",
        )
        invalid_report = ProjectValidationReport(
            root=Path("project"), diagnostics=(warning, error)
        )

        assert valid_report_result.is_valid is True
        assert valid_report_result.has_errors is False
        assert invalid_report.is_valid is False
        assert invalid_report.has_errors is True
        assert invalid_report.by_severity(DiagnosticSeverity.WARNING) == (
            warning,
        )


class TestValidateProject:
    """Tests for project validation orchestration."""

    def test_validate_project_accepts_conformant_project(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Requirement: a conformant project passes without console output."""
        _write(tmp_path / "scribpy.yml", "order:\n  - index.md\n")
        _write(tmp_path / "index.md", "# Title\n")

        report = validate_project(tmp_path)

        assert report.is_valid is True
        assert report.diagnostics == ()
        assert report.manifest_count == 1
        assert report.markdown_count == 1
        assert capsys.readouterr().out == ""

    def test_validate_project_rejects_missing_root(
        self, tmp_path: Path
    ) -> None:
        """Requirement: a missing project root produces a blocking finding."""
        missing = tmp_path / "missing"

        report = validate_project(missing)

        assert report.is_valid is False
        assert report.diagnostics[0].code == "PROJECT_ROOT_NOT_DIRECTORY"
        assert report.diagnostics[0].path == missing

    def test_validate_project_reports_all_manifest_failures(
        self, tmp_path: Path
    ) -> None:
        """Requirement: invalid manifests and order entries are reported."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - missing.md\n  - missing.md\n  - notes.txt\n",
        )
        _write(tmp_path / "notes.txt", "Notes.\n")
        _write(tmp_path / "chapter" / "scribpy.yml", "order: invalid\n")

        report = validate_project(tmp_path)

        codes = [item.code for item in report.diagnostics]
        assert report.is_valid is False
        assert report.manifest_count == 2
        assert codes.count("MANIFEST_ORDER_INVALID") == 4
        assert codes.count("MANIFEST_INVALID") == 1
        assert any(item.target == "missing.md" for item in report.diagnostics)

    def test_validate_project_reports_unreadable_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Requirement: manifest I/O failures become blocking diagnostics."""
        path = tmp_path / "scribpy.yml"
        _write(path, "order: []\n")

        def fail_read_text(
            self: Path, encoding: str | None = None, errors: str | None = None
        ) -> str:
            """Raise a simulated manifest read failure.

            Args:
                self: Path requested by the manifest loader.
                encoding: Requested text encoding.
                errors: Requested decoding error policy.

            Raises:
                OSError: Always, to simulate inaccessible storage.
            """
            del self, encoding, errors
            message = "cannot read"
            raise OSError(message)

        monkeypatch.setattr(Path, "read_text", fail_read_text)

        report = validate_project(tmp_path)

        assert report.diagnostics[0].code == "MANIFEST_INVALID"
        assert report.diagnostics[0].message == "cannot read"

    def test_validate_project_reports_collection_loading_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Requirement: Markdown loading failures become diagnostics."""
        path = tmp_path / "index.md"
        _write(path, "# Title\n")

        def fail_from_path(
            cls: type[MarkdownFile],
            source_path: Path,
            *,
            encoding: str = "utf-8",
        ) -> MarkdownFile:
            """Raise a simulated Markdown read failure.

            Args:
                cls: Markdown file domain type.
                source_path: Markdown path requested by the collection.
                encoding: Requested source encoding.

            Raises:
                OSError: Always, to simulate inaccessible storage.
            """
            del cls, source_path, encoding
            message = "Markdown unavailable"
            raise OSError(message)

        monkeypatch.setattr(
            MarkdownFile, "from_path", classmethod(fail_from_path)
        )

        report = validate_project(tmp_path)

        assert report.diagnostics[0].code == "PROJECT_LOAD_FAILED"
        assert "Markdown unavailable" in report.diagnostics[0].message

    def test_validate_project_adapts_mkforge_metadata(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Requirement: Mkforge diagnostics retain structured metadata."""
        path = tmp_path / "index.md"
        _write(path, "# Title\n")
        diagnostic = mkforge.Diagnostic(
            rule_id="MD999",
            name="Example",
            line=4,
            column=7,
            message="Example failure.",
            category="markdown-contract",
            severity="warning",
            target="asset.png",
        )

        def fake_verify(
            self: MarkdownFile,
            settings: mkforge.VerificationSettings | None = None,
            custom_rules: object = (),
        ) -> mkforge.VerificationReport:
            """Return one deterministic Mkforge diagnostic.

            Args:
                self: Markdown file being verified.
                settings: Optional Mkforge verification settings.
                custom_rules: Optional custom verification rules.

            Returns:
                Report containing the configured diagnostic.
            """
            del self, settings, custom_rules
            return mkforge.VerificationReport("test", (diagnostic,))

        monkeypatch.setattr(MarkdownFile, "verify", fake_verify)

        report = validate_project(tmp_path)

        finding = next(
            item for item in report.diagnostics if item.code == "MD999"
        )
        assert finding.severity == DiagnosticSeverity.ERROR
        assert finding.path == path
        assert finding.line == 4
        assert finding.column == 7
        assert finding.category == "markdown-contract"
        assert finding.target == "asset.png"

    def test_validate_project_includes_collection_diagnostics(
        self, tmp_path: Path
    ) -> None:
        """Requirement: project-aware collection findings are aggregated."""
        path = tmp_path / "index.md"
        _write(path, "Text without a title.\n")

        report = validate_project(tmp_path)

        finding = next(
            item
            for item in report.diagnostics
            if item.code == "SOURCE_H1_COUNT_INVALID"
        )
        assert finding.category == "collection"
        assert finding.path == path

    def test_validate_project_reports_ignored_manifest_child(
        self, tmp_path: Path
    ) -> None:
        """Requirement: ignored manifest children produce warnings."""
        _write(tmp_path / "scribpy.yml", "order:\n  - index.md\n")
        _write(tmp_path / "index.md", "# Title\n")
        _write(tmp_path / "ignored.md", "# Ignored\n")

        report = validate_project(tmp_path)

        finding = next(
            item
            for item in report.diagnostics
            if item.code == "MANIFEST_WARNING"
        )
        assert report.is_valid is True
        assert finding.severity == DiagnosticSeverity.WARNING


class TestValidationConsole:
    """Tests for Rich validation report presentation."""

    def test_render_validation_report_displays_success(self) -> None:
        """Requirement: valid reports render a clean successful summary."""
        output = StringIO()
        console = Console(file=output, color_system=None, width=120)
        report = ProjectValidationReport(
            root=Path("project"), manifest_count=2, markdown_count=3
        )

        render_validation_report(report, console=console)

        rendered = output.getvalue()
        assert "Project validation" in rendered
        assert "2 manifest(s), 3 Markdown file(s)" in rendered
        assert "Project valid: True" in rendered

    def test_valid_report_displays_diagnostic_and_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Requirement: valid_report renders failures and returns False."""
        path = tmp_path / "index.md"
        _write(path, "Text without a title.\n")
        output = StringIO()
        console = Console(file=output, color_system=None, width=160)

        result = valid_report(tmp_path, console=console)

        rendered = output.getvalue()
        assert result is False
        assert "SOURCE_H1_COUNT_INVALID" in rendered
        assert "index.md" in rendered
        assert "Project valid: False" in rendered

    def test_render_validation_report_uses_default_console(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Requirement: report rendering defaults to the standard console."""
        report = ProjectValidationReport(root=Path("project"))

        render_validation_report(report)

        assert "Project valid: True" in capsys.readouterr().out

    def test_render_validation_report_formats_line_and_column(self) -> None:
        """Requirement: diagnostic locations include line and column."""
        output = StringIO()
        console = Console(file=output, color_system=None, width=160)
        finding = ProjectDiagnostic(
            code="MD001",
            severity=DiagnosticSeverity.INFO,
            message="Information.",
            path=Path("guide.md"),
            line=3,
            column=5,
        )
        project_finding = ProjectDiagnostic(
            code="PROJECT_INFO",
            severity=DiagnosticSeverity.INFO,
            message="Project information.",
        )
        report = ProjectValidationReport(
            root=Path("project"), diagnostics=(finding, project_finding)
        )

        render_validation_report(report, console=console)

        assert "guide.md:3:5" in output.getvalue()
        assert "—" in output.getvalue()
