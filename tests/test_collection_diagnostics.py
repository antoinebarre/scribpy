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
from scribpy.core.diagnostics import (
    EXTERNAL_IMAGE_REFERENCE,
    HEADING_LEVEL_OVERFLOW,
    IMAGE_OUTSIDE_ROOT,
    INTERNAL_MARKDOWN_LINK_MISSING,
    INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT,
    LOCAL_ANCHOR_LINK,
    LOCAL_IMAGE_MISSING,
    SOURCE_FIRST_HEADING_NOT_H1,
    SOURCE_H1_COUNT_INVALID,
    CollectionDiagnosticContext,
    HeadingLevelOverflowRule,
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
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n###### Deep\n",
        )

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
                line=3,
            ),
        )

    def test_diagnose_collection_ignores_fenced_code_headings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostics ignore headings inside fenced code."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n```markdown\n###### Example\n```\n",
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
            "# Title\n\n#### Too deep\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics[0].code == HEADING_LEVEL_OVERFLOW
        assert report.diagnostics[0].path == markdown_file.path

    def test_diagnose_collection_treats_external_files_as_root_files(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: diagnostics support manually supplied files."""
        markdown_file = MarkdownFile(
            Path("external.md"),
            "# Title\n\n##### Accepted\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_missing_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: source files must contain one H1 heading."""
        markdown_file = MarkdownFile(tmp_path / "index.md", "## Missing\n")

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=SOURCE_FIRST_HEADING_NOT_H1,
                severity=DiagnosticSeverity.ERROR,
                message="First Markdown heading must be H1; found H2.",
                path=tmp_path / "index.md",
                line=1,
            ),
            CollectionDiagnostic(
                code=SOURCE_H1_COUNT_INVALID,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Markdown file must contain exactly one H1 heading; "
                    "found 0."
                ),
                path=tmp_path / "index.md",
            ),
        )

    def test_diagnose_collection_allows_files_without_headings_to_h1_rule(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: first-heading diagnostics need an actual heading."""
        markdown_file = MarkdownFile(tmp_path / "index.md", "Body only.\n")

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=SOURCE_H1_COUNT_INVALID,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Markdown file must contain exactly one H1 heading; "
                    "found 0."
                ),
                path=tmp_path / "index.md",
            ),
        )

    def test_diagnose_collection_reports_multiple_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: source files must not contain multiple H1 headings."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# First\n\n# Second\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=SOURCE_H1_COUNT_INVALID,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Markdown file must contain exactly one H1 heading; "
                    "found 2."
                ),
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_ignores_fenced_code_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: H1 count diagnostics ignore fenced code headings."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n```markdown\n# Example\n```\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_first_heading_not_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: source files must start headings with H1."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "Intro text.\n\n## First heading\n\n# Later title\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=SOURCE_FIRST_HEADING_NOT_H1,
                severity=DiagnosticSeverity.ERROR,
                message="First Markdown heading must be H1; found H2.",
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_ignores_fenced_code_first_heading(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: first-heading diagnostics ignore fenced code."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "```markdown\n## Example\n```\n\n# Title\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_can_run_one_rule(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: callers can run one diagnostic strategy."""
        markdown_file = MarkdownFile(tmp_path / "index.md", "###### Deep\n")

        report = diagnose_collection(
            tmp_path,
            (markdown_file,),
            rules=(HeadingLevelOverflowRule(),),
        )

        assert report.diagnostics[0].code == HEADING_LEVEL_OVERFLOW

    def test_diagnose_collection_accepts_existing_local_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: existing local image references are valid."""
        _write(tmp_path / "assets" / "logo.png", "fake image")
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Logo](assets/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_missing_local_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing local image references are errors."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Missing](assets/missing.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=LOCAL_IMAGE_MISSING,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Local image file does not exist: 'assets/missing.png'."
                ),
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_reports_empty_image_target(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: empty image targets are missing local images."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Missing]( )\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=LOCAL_IMAGE_MISSING,
                severity=DiagnosticSeverity.ERROR,
                message="Local image file does not exist: ''.",
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_resolves_root_absolute_local_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: root-absolute image paths resolve from root."""
        _write(tmp_path / "assets" / "logo.png", "fake image")
        markdown_file = MarkdownFile(
            tmp_path / "guide" / "index.md",
            "# Title\n\n![Logo](/assets/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_external_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: external image references are reported as warnings."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Remote](https://example.com/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=EXTERNAL_IMAGE_REFERENCE,
                severity=DiagnosticSeverity.WARNING,
                message=(
                    "External image reference is not fetched by core "
                    "diagnostics: 'https://example.com/logo.png'."
                ),
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_reports_image_outside_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: local images outside the collection root are errors."""
        markdown_file = MarkdownFile(
            tmp_path / "guide" / "index.md",
            "# Title\n\n![Logo](../../outside/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert any(d.code == IMAGE_OUTSIDE_ROOT for d in report.diagnostics)
        outside = next(
            d for d in report.diagnostics if d.code == IMAGE_OUTSIDE_ROOT
        )
        assert outside.severity == DiagnosticSeverity.ERROR
        assert outside.path == tmp_path / "guide" / "index.md"
        assert outside.line == 3

    def test_diagnose_collection_accepts_image_inside_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: local images inside the collection root are valid."""
        _write(tmp_path / "assets" / "logo.png", "fake image")
        markdown_file = MarkdownFile(
            tmp_path / "guide" / "index.md",
            "# Title\n\n![Logo](../assets/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        codes = [d.code for d in report.diagnostics]
        assert IMAGE_OUTSIDE_ROOT not in codes

    def test_diagnose_collection_ignores_external_image_for_outside_root(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: external images are not checked for outside-root."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Remote](https://example.com/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        codes = [d.code for d in report.diagnostics]
        assert IMAGE_OUTSIDE_ROOT not in codes

    def test_diagnose_collection_reports_protocol_relative_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: protocol-relative image URLs are external."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Remote](//example.com/logo.png)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics[0].code == EXTERNAL_IMAGE_REFERENCE

    def test_diagnose_collection_accepts_existing_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: existing internal Markdown file links are valid."""
        _write(tmp_path / "guide" / "page.md", "# Page\n")
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            '# Title\n\n[Page](guide/page.md "Guide page")\n',
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_accepts_markdown_suffix_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: .markdown links are treated as Markdown links."""
        _write(tmp_path / "guide" / "page.markdown", "# Page\n")
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Page](guide/page.markdown)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_accepts_root_absolute_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: root-absolute Markdown links resolve from root."""
        _write(tmp_path / "guide" / "page.md", "# Page\n")
        markdown_file = MarkdownFile(
            tmp_path / "nested" / "index.md",
            "# Title\n\n[Page](/guide/page.md)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_missing_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing internal Markdown links are errors."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Missing](guide/missing.md)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=INTERNAL_MARKDOWN_LINK_MISSING,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Internal Markdown link target does not exist: "
                    "'guide/missing.md'."
                ),
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_reports_malformed_markdown_link_body(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: malformed Markdown link bodies are still diagnosed."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            '# Title\n\n[Broken]("guide/missing.md)\n',
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics[0].code == INTERNAL_MARKDOWN_LINK_MISSING

    def test_diagnose_collection_reports_outside_root_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: Markdown links cannot escape collection root."""
        markdown_file = MarkdownFile(
            tmp_path / "guide" / "index.md",
            "# Title\n\n[Outside](../../outside.md)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Internal Markdown link target must stay inside "
                    "collection root: '../../outside.md'."
                ),
                path=tmp_path / "guide" / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_ignores_external_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: external Markdown links are not internal links."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Remote](https://example.com/page.md)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_anchor_only_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: anchor-only links are forbidden in collection."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Section](#section)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report.diagnostics == (
            CollectionDiagnostic(
                code=LOCAL_ANCHOR_LINK,
                severity=DiagnosticSeverity.ERROR,
                message=(
                    "Anchor fragments are forbidden in collection source "
                    "files; anchors in the assembled document are managed "
                    "by the assembly pipeline: '#section'."
                ),
                path=tmp_path / "index.md",
                line=3,
            ),
        )

    def test_diagnose_collection_reports_multiple_anchor_links(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: every anchor-only link in a file is reported."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[First](#first)\n\n[Second](#second)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        anchor_codes = [d.code for d in report.diagnostics]
        assert anchor_codes.count(LOCAL_ANCHOR_LINK) == 2

    def test_diagnose_collection_ignores_anchor_in_fenced_code(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: anchor links inside fenced code are not reported."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n```markdown\n[Section](#section)\n```\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_reports_cross_file_anchor_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: cross-file links with anchors are also forbidden."""
        _write(tmp_path / "guide" / "page.md", "# Page\n")
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Page](guide/page.md#section)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert any(d.code == LOCAL_ANCHOR_LINK for d in report.diagnostics)

    def test_diagnose_collection_ignores_non_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: non-Markdown links are ignored by link rule."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[PDF](assets/file.pdf)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_ignores_empty_link_target(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: empty link targets are ignored by link rule."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n[Empty]()\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_ignores_image_markdown_target_as_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: image references are not handled as Markdown links."""
        _write(tmp_path / "image.md", "fake image")
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n![Image](image.md)\n",
        )

        report = diagnose_collection(tmp_path, (markdown_file,))

        assert report == CollectionDiagnosticReport()

    def test_diagnose_collection_ignores_fenced_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: Markdown links in fenced code are ignored."""
        markdown_file = MarkdownFile(
            tmp_path / "index.md",
            "# Title\n\n```markdown\n[Missing](missing.md)\n```\n",
        )

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
