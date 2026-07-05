"""Tests for collection diagnostics."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.core import (
    CollectionDiagnostic,
    CollectionDiagnosticReport,
    DiagnosticSeverity,
    MarkdownCollection,
    MarkdownFile,
)
from scribpy.core.collection_diagnostics import (
    HEADING_LEVEL_OVERFLOW,
    CollectionDiagnosticContext,
    diagnose_collection,
)


class TestCollectionDiagnosticReport:
    """Tests for collection diagnostic reports."""

    def test_empty_report_has_no_errors_and_summary(self) -> None:
        """Requirement: empty diagnostic reports expose a neutral summary."""
        report = CollectionDiagnosticReport()

        assert report.has_errors is False
        assert report.summary() == "No collection diagnostics."

    def test_report_filters_diagnostics_by_severity(self) -> None:
        """Requirement: diagnostic reports can filter by severity."""
        error = CollectionDiagnostic(
            code="ERROR_CODE",
            severity=DiagnosticSeverity.ERROR,
            message="error",
        )
        warning = CollectionDiagnostic(
            code="WARNING_CODE",
            severity=DiagnosticSeverity.WARNING,
            message="warning",
        )
        report = CollectionDiagnosticReport((error, warning))

        assert report.has_errors is True
        assert report.by_severity(DiagnosticSeverity.ERROR) == (error,)
        assert report.by_severity(DiagnosticSeverity.INFO) == ()

    def test_report_summary_formats_locations(self) -> None:
        """Requirement: diagnostic summaries include optional locations."""
        report = CollectionDiagnosticReport(
            (
                CollectionDiagnostic(
                    code="WITH_LINE",
                    severity=DiagnosticSeverity.ERROR,
                    message="line message",
                    path=Path("index.md"),
                    line=3,
                ),
                CollectionDiagnostic(
                    code="WITHOUT_LINE",
                    severity=DiagnosticSeverity.WARNING,
                    message="path message",
                    path=Path("guide"),
                ),
                CollectionDiagnostic(
                    code="WITHOUT_PATH",
                    severity=DiagnosticSeverity.INFO,
                    message="global message",
                ),
            ),
        )

        assert report.summary() == (
            "ERROR WITH_LINE index.md:3: line message\n"
            "WARNING WITHOUT_LINE guide: path message\n"
            "INFO WITHOUT_PATH: global message"
        )


class TestDiagnoseCollection:
    """Tests for collection diagnostic execution."""

    def test_diagnose_collection_runs_default_heading_overflow_rule(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: default diagnostics find heading level overflow."""
        markdown_file = MarkdownFile(tmp_path / "index.md", "###### Deep\n")

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.has_errors is True
        assert report.diagnostics == (
            CollectionDiagnostic(
                code=HEADING_LEVEL_OVERFLOW,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Heading would exceed Markdown level 6 after collection "
                    "assembly: 'Deep'."
                ),
                path=tmp_path / "index.md",
                line=1,
            ),
        )

    def test_diagnose_collection_ignores_fenced_code_headings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostics ignore headings inside fenced code."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "```markdown\n###### Example\n```\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_detects_nested_file_overflow(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostics account for folder heading offsets."""
        markdown_file = MarkdownFile(
            tmp_path / "guide" / "deep" / "page.md",
            "#### Too deep\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics[0].code == HEADING_LEVEL_OVERFLOW
        assert report.diagnostics[0].path == markdown_file.path

    def test_diagnose_collection_treats_external_files_as_root_files(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostics support manually supplied files."""
        markdown_file = MarkdownFile(Path("external.md"), "##### Accepted\n")

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_uses_injected_rules(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostic rules can be injected as strategies."""
        markdown_file = MarkdownFile(tmp_path / "index.md", "# Title\n")

        report = diagnose_collection(
            tmp_path,
            (markdown_file,),
            rules=(_FakeDiagnosticRule(),),
        )

        assert report.diagnostics == (
            CollectionDiagnostic(
                code="FAKE",
                severity=DiagnosticSeverity.INFO,
                message="1 file(s) inspected.",
            ),
        )


class TestMarkdownCollectionDiagnose:
    """Tests for MarkdownCollection diagnostic integration."""

    def test_diagnose_uses_default_rules(self, tmp_path: Path) -> None:
        """Requirement: collections expose default diagnostics."""
        _write(tmp_path / "index.md", "# Title\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        report = collection.diagnose()

        assert report == CollectionDiagnosticReport()

    def test_diagnose_accepts_injected_rules(self, tmp_path: Path) -> None:
        """Requirement: collections accept custom diagnostic strategies."""
        _write(tmp_path / "index.md", "# Title\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        report = collection.diagnose(rules=(_FakeDiagnosticRule(),))

        assert report.diagnostics[0].code == "FAKE"


class _FakeDiagnosticRule:
    """Diagnostic rule used to verify rule injection."""

    code = "FAKE"

    def diagnose(
        self,
        context: CollectionDiagnosticContext,
    ) -> Iterable[CollectionDiagnostic]:
        """Return a predictable diagnostic for tests.

        Args:
            context: Collection diagnostic context.

        Returns:
            Single informational diagnostic.
        """
        return (
            CollectionDiagnostic(
                code=self.code,
                severity=DiagnosticSeverity.INFO,
                message=f"{len(context.files)} file(s) inspected.",
            ),
        )


def _write(path: Path, content: str) -> None:
    """Write UTF-8 test content, creating parent directories as needed.

    Args:
        path: Destination path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
