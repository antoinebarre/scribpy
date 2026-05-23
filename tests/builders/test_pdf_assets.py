"""Tests for PDF asset preparation helpers."""

from pathlib import Path

from scribpy.builders.pdf import DEFAULT_PDF_CSS, PdfDocument, PdfOptions
from scribpy.builders.pdf_assets import rasterize_svg_artifacts_for_pdf
from scribpy.model import BuildArtifact


def _document(tmp_path: Path, markdown: str) -> PdfDocument:
    return PdfDocument(
        markdown=markdown,
        root=tmp_path,
        css_files=(),
        default_css=DEFAULT_PDF_CSS,
        options=PdfOptions(),
    )


def test_rasterize_svg_artifacts_for_pdf_rewrites_relative_reference(
    tmp_path: Path, monkeypatch
) -> None:
    svg = tmp_path / "assets" / "diagram.svg"
    svg.parent.mkdir()
    svg.write_text("<svg/>", encoding="utf-8")

    class FakePixmap:
        def save(self, path: Path) -> None:
            Path(path).write_bytes(b"png")

    class FakePage:
        def get_pixmap(self, **kwargs):
            return FakePixmap()

    class FakeSvg:
        def __getitem__(self, index: int):
            return FakePage()

    class FakeFitz:
        @staticmethod
        def open(kind: str, data: bytes):
            return FakeSvg()

        @staticmethod
        def Matrix(x_scale: int, y_scale: int):
            return (x_scale, y_scale)

    monkeypatch.setattr(
        "scribpy.builders.pdf_assets.import_module", lambda _: FakeFitz
    )

    document, artifacts, diagnostics = rasterize_svg_artifacts_for_pdf(
        _document(tmp_path, "![Diagram](assets/diagram.svg)\n"),
        (BuildArtifact(svg, "pdf", "diagram"),),
    )

    assert diagnostics == ()
    assert document.markdown == "![Diagram](assets/diagram.png)\n"
    assert artifacts[0].path == tmp_path / "assets" / "diagram.png"


def test_rasterize_svg_artifacts_for_pdf_uses_filename_outside_root(
    tmp_path: Path, monkeypatch
) -> None:
    svg = tmp_path / "diagram.svg"
    svg.write_text("<svg/>", encoding="utf-8")
    outside_root = tmp_path / "doc"

    class FakePixmap:
        def save(self, path: Path) -> None:
            Path(path).write_bytes(b"png")

    class FakePage:
        def get_pixmap(self, **kwargs):
            return FakePixmap()

    class FakeSvg:
        def __getitem__(self, index: int):
            return FakePage()

    class FakeFitz:
        @staticmethod
        def open(kind: str, data: bytes):
            return FakeSvg()

        @staticmethod
        def Matrix(x_scale: int, y_scale: int):
            return (x_scale, y_scale)

    monkeypatch.setattr(
        "scribpy.builders.pdf_assets.import_module", lambda _: FakeFitz
    )

    document, _, diagnostics = rasterize_svg_artifacts_for_pdf(
        _document(outside_root, "![Diagram](diagram.svg)\n"),
        (BuildArtifact(svg, "pdf", "diagram"),),
    )

    assert diagnostics == ()
    assert document.markdown == "![Diagram](diagram.png)\n"


def test_rasterize_svg_artifacts_for_pdf_skips_when_fitz_missing(
    tmp_path: Path, monkeypatch
) -> None:
    def missing_fitz(name: str) -> object:
        raise ImportError(name)

    monkeypatch.setattr(
        "scribpy.builders.pdf_assets.import_module", missing_fitz
    )

    document, artifacts, diagnostics = rasterize_svg_artifacts_for_pdf(
        _document(tmp_path, "![Diagram](assets/diagram.svg)\n"),
        (BuildArtifact(tmp_path / "assets/diagram.svg", "pdf", "diagram"),),
    )

    assert artifacts == ()
    assert diagnostics == ()
    assert document.markdown == "![Diagram](assets/diagram.svg)\n"


def test_rasterize_svg_artifacts_for_pdf_reports_failure(
    tmp_path: Path, monkeypatch
) -> None:
    svg = tmp_path / "assets" / "diagram.svg"
    svg.parent.mkdir()
    svg.write_text("<svg/>", encoding="utf-8")

    class BrokenFitz:
        @staticmethod
        def open(kind: str, data: bytes):
            raise RuntimeError("bad svg")

    monkeypatch.setattr(
        "scribpy.builders.pdf_assets.import_module", lambda _: BrokenFitz
    )

    document, artifacts, diagnostics = rasterize_svg_artifacts_for_pdf(
        _document(tmp_path, "![Diagram](assets/diagram.svg)\n"),
        (BuildArtifact(svg, "pdf", "diagram"),),
    )

    assert artifacts == ()
    assert document.markdown == "![Diagram](assets/diagram.svg)\n"
    assert [diagnostic.code for diagnostic in diagnostics] == ["PDF004"]


def test_rasterize_svg_artifacts_for_pdf_ignores_non_svg(
    tmp_path: Path, monkeypatch
) -> None:
    class FakeFitz:
        pass

    monkeypatch.setattr(
        "scribpy.builders.pdf_assets.import_module", lambda _: FakeFitz
    )

    document, artifacts, diagnostics = rasterize_svg_artifacts_for_pdf(
        _document(tmp_path, "![Image](assets/image.png)\n"),
        (BuildArtifact(tmp_path / "assets/image.png", "pdf", "image"),),
    )

    assert artifacts == ()
    assert diagnostics == ()
    assert document.markdown == "![Image](assets/image.png)\n"
