"""Tests for scribpy.render.html_renderer."""

from pathlib import Path

from scribpy.config import CssConfig, TocConfig
from scribpy.core.document import Heading, ImageRef, ParsedDocument
from scribpy.render.html_renderer import render_html


def _make_doc(
    html: str = "<p>Hello</p>",
    headings: tuple[Heading, ...] = (),
    images: tuple[ImageRef, ...] = (),
) -> ParsedDocument:
    """Build a minimal ParsedDocument for testing.

    Args:
        html: HTML body content.
        headings: Document headings.
        images: Image references.

    Returns:
        A ParsedDocument instance.
    """
    return ParsedDocument(html=html, headings=headings, images=images)


class TestRenderHtml:
    """Tests for the render_html function."""

    def test_produces_index_html(self, tmp_path: Path) -> None:
        """Requirement: Generates an index.html file (REQ-001)."""
        doc = _make_doc()
        result = render_html(doc, tmp_path / "out")

        assert result.name == "index.html"
        assert result.is_file()

    def test_html_contains_body(self, tmp_path: Path) -> None:
        """Requirement: Output contains the document body."""
        doc = _make_doc(html="<p>Test content</p>")
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert "<p>Test content</p>" in content

    def test_title_from_first_heading(self, tmp_path: Path) -> None:
        """Requirement: Title is extracted from first heading."""
        doc = _make_doc(
            headings=(Heading(level=1, text="My Doc", anchor="my-doc"),),
        )
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert "<title>My Doc</title>" in content

    def test_title_defaults_to_untitled(self, tmp_path: Path) -> None:
        """Requirement: Missing heading yields 'Untitled'."""
        doc = _make_doc(headings=())
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert "<title>Untitled</title>" in content

    def test_css_linked(self, tmp_path: Path) -> None:
        """Requirement: User CSS is linked in output (REQ-002)."""
        css_file = tmp_path / "style.css"
        css_file.write_text("body { color: red; }")

        doc = _make_doc()
        output_dir = tmp_path / "out"
        render_html(doc, output_dir, css=CssConfig(path=css_file))

        content = (output_dir / "index.html").read_text(encoding="utf-8")
        assert 'href="style.css"' in content
        assert (output_dir / "style.css").is_file()

    def test_css_missing_no_crash(self, tmp_path: Path) -> None:
        """Requirement: Missing CSS file does not crash rendering."""
        doc = _make_doc()
        css = CssConfig(path=Path("/nonexistent/style.css"))
        result = render_html(doc, tmp_path / "out", css=css)

        assert result.is_file()

    def test_toc_enabled(self, tmp_path: Path) -> None:
        """Requirement: TOC widget is included when enabled (REQ-003)."""
        doc = _make_doc(
            headings=(Heading(level=1, text="Title", anchor="title"),),
        )
        result = render_html(
            doc,
            tmp_path / "out",
            toc=TocConfig(enabled=True),
        )

        content = result.read_text(encoding="utf-8")
        assert "scribpy-toc-toggle" in content

    def test_toc_disabled(self, tmp_path: Path) -> None:
        """Requirement: TOC widget is absent when disabled."""
        doc = _make_doc(
            headings=(Heading(level=1, text="Title", anchor="title"),),
        )
        result = render_html(
            doc,
            tmp_path / "out",
            toc=TocConfig(enabled=False),
        )

        content = result.read_text(encoding="utf-8")
        assert "scribpy-toc-toggle" not in content

    def test_images_copied(self, tmp_path: Path) -> None:
        """Requirement: Referenced images are copied (REQ-007)."""
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "photo.png").write_bytes(b"\x89PNG")

        doc = _make_doc(images=(ImageRef(src="photo.png"),))
        output_dir = tmp_path / "out"
        render_html(doc, output_dir, source_dir=src_dir)

        assert (output_dir / "photo.png").is_file()

    def test_images_in_subdirectory(self, tmp_path: Path) -> None:
        """Requirement: Subdirectory images preserve structure."""
        src_dir = tmp_path / "src"
        (src_dir / "img").mkdir(parents=True)
        (src_dir / "img" / "logo.svg").write_text("<svg/>")

        doc = _make_doc(images=(ImageRef(src="img/logo.svg"),))
        output_dir = tmp_path / "out"
        render_html(doc, output_dir, source_dir=src_dir)

        assert (output_dir / "img" / "logo.svg").is_file()

    def test_diagram_svgs_injected(self, tmp_path: Path) -> None:
        """Requirement: Diagram SVGs replace code blocks."""
        html = (
            '<pre><code class="language-plantuml">'
            "@startuml\nA-&gt;B\n@enduml</code></pre>"
        )
        doc = _make_doc(html=html)
        diagrams_svg = {0: "<svg><circle/></svg>"}

        result = render_html(
            doc,
            tmp_path / "out",
            diagrams_svg=diagrams_svg,
        )

        content = result.read_text(encoding="utf-8")
        assert "<svg><circle/></svg>" in content
        assert "language-plantuml" not in content

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Requirement: Output directory is created if absent."""
        output_dir = tmp_path / "deep" / "nested" / "out"
        doc = _make_doc()
        result = render_html(doc, output_dir)

        assert result.is_file()

    def test_valid_html_structure(self, tmp_path: Path) -> None:
        """Requirement: Output is valid HTML5 structure."""
        doc = _make_doc()
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "<head>" in content
        assert "<body>" in content
        assert "<main>" in content

    def test_heading_ids_extra_html_headings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: Extra HTML headings are unchanged."""
        doc = _make_doc(
            html="<h1>Known</h1>\n<h2>Unknown</h2>",
            headings=(Heading(level=1, text="Known", anchor="known"),),
        )
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert '<h1 id="known">' in content
        assert "<h2>Unknown</h2>" in content

    def test_heading_ids_injected(self, tmp_path: Path) -> None:
        """Requirement: Headings have id attributes for TOC links."""
        doc = _make_doc(
            html="<h1>Title</h1>\n<h2>Section</h2>",
            headings=(
                Heading(level=1, text="Title", anchor="title"),
                Heading(level=2, text="Section", anchor="section"),
            ),
        )
        result = render_html(doc, tmp_path / "out")

        content = result.read_text(encoding="utf-8")
        assert '<h1 id="title">' in content
        assert '<h2 id="section">' in content

    def test_diagram_svg_no_placeholder(self, tmp_path: Path) -> None:
        """Requirement: Missing placeholder leaves HTML unchanged."""
        doc = _make_doc(html="<p>No code blocks here</p>")
        diagrams_svg = {0: "<svg>orphan</svg>"}

        result = render_html(
            doc,
            tmp_path / "out",
            diagrams_svg=diagrams_svg,
        )

        content = result.read_text(encoding="utf-8")
        assert "<p>No code blocks here</p>" in content

    def test_partial_diagram_rendering(self, tmp_path: Path) -> None:
        """Requirement: Only rendered diagrams are replaced."""
        html = (
            '<pre><code class="language-plantuml">'
            "A-&gt;B</code></pre>\n"
            '<pre><code class="language-mermaid">'
            "graph TD</code></pre>"
        )
        doc = _make_doc(html=html)
        diagrams_svg = {1: "<svg>mermaid-only</svg>"}

        result = render_html(
            doc,
            tmp_path / "out",
            diagrams_svg=diagrams_svg,
        )

        content = result.read_text(encoding="utf-8")
        assert "language-plantuml" in content
        assert "<svg>mermaid-only</svg>" in content
