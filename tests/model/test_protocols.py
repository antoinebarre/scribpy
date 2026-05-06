"""Tests for service protocols exposed by scribpy.model."""

from collections.abc import Iterable, Sequence
from pathlib import Path

from scribpy.model import (
    DiagramRenderer,
    FileSystem,
    HtmlRenderer,
    MarkdownAst,
    MarkdownParser,
    PdfRenderer,
)


class InMemoryFileSystem:
    """Test double implementing the FileSystem protocol."""

    def __init__(self) -> None:
        self._files: dict[Path, str] = {}

    def read_text(self, path: Path) -> str:
        return self._files[path]

    def write_text(self, path: Path, content: str) -> None:
        self._files[path] = content

    def exists(self, path: Path) -> bool:
        return path in self._files

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        return root.glob(pattern)


class TestMarkdownParser:
    """Test double implementing the MarkdownParser protocol."""

    def parse(self, source: str) -> MarkdownAst:
        return MarkdownAst(
            backend="test",
            tokens=({"type": "text", "content": source},),
        )


class TestHtmlRenderer:
    """Test double implementing the HtmlRenderer protocol."""

    def render(self, document: object, css_files: Sequence[Path]) -> str:
        return f"<html>{document!s}:{len(css_files)}</html>"


class TestPdfRenderer:
    """Test double implementing the PdfRenderer protocol."""

    def render(self, html: str, css_files: Sequence[Path], output_path: Path) -> None:
        _ = html, css_files, output_path


class TestDiagramRenderer:
    """Test double implementing the DiagramRenderer protocol."""

    def render(self, source: str, output_format: str) -> bytes:
        return f"{output_format}:{source}".encode()


def test_file_system_protocol_accepts_structural_double() -> None:
    fs: FileSystem = InMemoryFileSystem()
    path = Path("docs/index.md")

    fs.write_text(path, "# Index")

    assert isinstance(fs, FileSystem)
    assert fs.exists(path) is True
    assert fs.read_text(path) == "# Index"


def test_markdown_parser_protocol_accepts_structural_double() -> None:
    parser: MarkdownParser = TestMarkdownParser()

    ast = parser.parse("# Title")

    assert isinstance(parser, MarkdownParser)
    assert ast.backend == "test"


def test_html_renderer_protocol_accepts_structural_double() -> None:
    renderer: HtmlRenderer = TestHtmlRenderer()

    html = renderer.render("body", (Path("theme.css"),))

    assert isinstance(renderer, HtmlRenderer)
    assert html == "<html>body:1</html>"


def test_pdf_renderer_protocol_accepts_structural_double() -> None:
    renderer: PdfRenderer = TestPdfRenderer()

    renderer.render("<html></html>", (), Path("out.pdf"))

    assert isinstance(renderer, PdfRenderer)


def test_diagram_renderer_protocol_accepts_structural_double() -> None:
    renderer: DiagramRenderer = TestDiagramRenderer()

    result = renderer.render("graph TD; A-->B", "svg")

    assert isinstance(renderer, DiagramRenderer)
    assert result == b"svg:graph TD; A-->B"
