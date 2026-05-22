"""Tests for PDF builder support objects."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from scribpy.builders.pdf import (
    DEFAULT_PDF_CSS,
    MarkdownPdfRenderer,
    PdfDocument,
    PdfOptions,
    PdfRenderResult,
    read_pdf_css,
)


def _document(tmp_path: Path, css_files: tuple[Path, ...] = ()) -> PdfDocument:
    return PdfDocument(
        markdown="# Home\n",
        root=tmp_path,
        css_files=css_files,
        default_css=DEFAULT_PDF_CSS,
        options=PdfOptions(),
    )


def test_pdf_render_result_success_requires_artifact() -> None:
    result = PdfRenderResult(artifact=None)

    assert result.success is False


def test_read_pdf_css_combines_default_and_user_css(tmp_path: Path) -> None:
    css_path = tmp_path / "pdf.css"
    css_path.write_text("h1 { color: teal; }\n", encoding="utf-8")

    css, diagnostics = read_pdf_css(_document(tmp_path, (css_path,)))

    assert diagnostics == ()
    assert DEFAULT_PDF_CSS in css
    assert "color: teal" in css


def test_read_pdf_css_reports_unreadable_css(tmp_path: Path) -> None:
    css, diagnostics = read_pdf_css(
        _document(tmp_path, (tmp_path / "none.css",))
    )

    assert css.startswith(DEFAULT_PDF_CSS)
    assert [diagnostic.code for diagnostic in diagnostics] == ["PDF003"]


def test_markdown_pdf_renderer_reports_missing_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def missing_module(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr("scribpy.builders.pdf.import_module", missing_module)

    result = MarkdownPdfRenderer().render(
        _document(tmp_path), tmp_path / "document.pdf"
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PDF001"]


def test_markdown_pdf_renderer_writes_pdf_with_optional_dependency(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[tuple[str, object]] = []

    class FakeMarkdownPdf:
        def __init__(self, *, toc_level: int, optimize: bool) -> None:
            calls.append(("init", (toc_level, optimize)))

        def add_section(self, section: object, *, user_css: str) -> None:
            calls.append(("section", section))
            calls.append(("css", user_css))

        def save(self, output_path: str) -> None:
            Path(output_path).write_bytes(b"%PDF-FAKE")

    class FakeSection:
        def __init__(
            self, markdown: str, *, root: str, paper_size: str
        ) -> None:
            self.markdown = markdown
            self.root = root
            self.paper_size = paper_size

    def fake_module(name: str) -> object:
        return SimpleNamespace(
            MarkdownPdf=FakeMarkdownPdf, Section=FakeSection
        )

    monkeypatch.setattr("scribpy.builders.pdf.import_module", fake_module)

    result = MarkdownPdfRenderer().render(
        _document(tmp_path), tmp_path / "document.pdf"
    )

    assert result.success is True
    assert result.artifact is not None
    assert result.artifact.path == tmp_path / "document.pdf"
    assert calls[0] == ("init", (3, True))


def test_markdown_pdf_renderer_stops_when_css_read_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_module(name: str) -> object:
        return SimpleNamespace(MarkdownPdf=object, Section=object)

    monkeypatch.setattr("scribpy.builders.pdf.import_module", fake_module)

    result = MarkdownPdfRenderer().render(
        _document(tmp_path, (tmp_path / "missing.css",)),
        tmp_path / "document.pdf",
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PDF003"]


def test_markdown_pdf_renderer_reports_render_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    class BrokenMarkdownPdf:
        def __init__(self, *, toc_level: int, optimize: bool) -> None:
            raise RuntimeError("boom")

    def fake_module(name: str) -> object:
        return SimpleNamespace(MarkdownPdf=BrokenMarkdownPdf, Section=object)

    monkeypatch.setattr("scribpy.builders.pdf.import_module", fake_module)

    result = MarkdownPdfRenderer().render(
        _document(tmp_path), tmp_path / "document.pdf"
    )

    assert result.success is False
    assert [diagnostic.code for diagnostic in result.diagnostics] == ["PDF002"]
