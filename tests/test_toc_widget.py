"""Tests for scribpy.render.toc_widget."""

from scribpy.core.document import Heading
from scribpy.render.toc_widget import generate_toc_html


class TestGenerateTocHtml:
    """Tests for the TOC widget generator."""

    def test_generates_button(self) -> None:
        """Requirement: Output includes a toggle button."""
        headings = (Heading(level=1, text="Title", anchor="title"),)
        result = generate_toc_html(headings)

        assert "scribpy-toc-toggle" in result
        assert "&#9776;" in result

    def test_generates_links_for_headings(self) -> None:
        """Requirement: Each heading has an anchor link."""
        headings = (
            Heading(level=1, text="Intro", anchor="intro"),
            Heading(level=2, text="Details", anchor="details"),
        )
        result = generate_toc_html(headings)

        assert 'href="#intro"' in result
        assert 'href="#details"' in result
        assert ">Intro<" in result
        assert ">Details<" in result

    def test_indentation_by_level(self) -> None:
        """Requirement: Deeper headings are indented."""
        headings = (
            Heading(level=1, text="H1", anchor="h1"),
            Heading(level=3, text="H3", anchor="h3"),
        )
        result = generate_toc_html(headings)

        assert "padding-left:0px" in result
        assert "padding-left:32px" in result

    def test_includes_css_and_js(self) -> None:
        """Requirement: Output includes CSS and JavaScript."""
        headings = (Heading(level=1, text="X", anchor="x"),)
        result = generate_toc_html(headings)

        assert "<style>" in result
        assert "<script>" in result

    def test_empty_headings(self) -> None:
        """Requirement: Empty headings produce valid empty list."""
        result = generate_toc_html(())

        assert "<ul>" in result
        assert "</ul>" in result
        assert "<li" not in result
