"""Tests for scribpy.core.markdown_parser."""

from scribpy.core.markdown_parser import parse


class TestParseHeadings:
    """Tests for heading extraction."""

    def test_single_heading(self) -> None:
        """Requirement: Parser extracts a single top-level heading."""
        doc = parse("# Hello World\n")

        assert len(doc.headings) == 1
        assert doc.headings[0].level == 1
        assert doc.headings[0].text == "Hello World"
        assert doc.headings[0].anchor == "hello-world"

    def test_multiple_heading_levels(self) -> None:
        """Requirement: Parser extracts headings at different levels."""
        md = "# Title\n\n## Section\n\n### Subsection\n"
        doc = parse(md)

        assert len(doc.headings) == 3
        assert doc.headings[0].level == 1
        assert doc.headings[1].level == 2
        assert doc.headings[2].level == 3

    def test_heading_with_special_characters(self) -> None:
        """Requirement: Anchor slugifies special characters."""
        doc = parse("## Héllo & Wörld!\n")

        assert doc.headings[0].text == "Héllo & Wörld!"
        assert "hello" in doc.headings[0].anchor

    def test_no_headings(self) -> None:
        """Requirement: Document without headings yields empty tuple."""
        doc = parse("Just a paragraph.\n")

        assert doc.headings == ()


class TestParseImages:
    """Tests for image reference extraction."""

    def test_single_image(self) -> None:
        """Requirement: Parser extracts image src and alt text."""
        doc = parse('![Alt text](image.png "Title")\n')

        assert len(doc.images) == 1
        assert doc.images[0].src == "image.png"
        assert doc.images[0].alt == "Alt text"
        assert doc.images[0].title == "Title"

    def test_image_without_title(self) -> None:
        """Requirement: Parser handles images without title attribute."""
        doc = parse("![Logo](logo.svg)\n")

        assert len(doc.images) == 1
        assert doc.images[0].src == "logo.svg"
        assert doc.images[0].alt == "Logo"
        assert doc.images[0].title == ""

    def test_multiple_images(self) -> None:
        """Requirement: Parser extracts all images in order."""
        md = "![A](a.png)\n\n![B](b.png)\n"
        doc = parse(md)

        assert len(doc.images) == 2
        assert doc.images[0].src == "a.png"
        assert doc.images[1].src == "b.png"

    def test_no_images(self) -> None:
        """Requirement: Document without images yields empty tuple."""
        doc = parse("No images here.\n")

        assert doc.images == ()


class TestParseDiagrams:
    """Tests for diagram block extraction."""

    def test_plantuml_block(self) -> None:
        """Requirement: Parser identifies plantuml fenced blocks."""
        md = "```plantuml\n@startuml\nA -> B\n@enduml\n```\n"
        doc = parse(md)

        assert len(doc.diagrams) == 1
        assert doc.diagrams[0].engine == "plantuml"
        assert "@startuml" in doc.diagrams[0].source
        assert doc.diagrams[0].index == 0

    def test_mermaid_block(self) -> None:
        """Requirement: Parser identifies mermaid fenced blocks."""
        md = "```mermaid\ngraph TD\n  A-->B\n```\n"
        doc = parse(md)

        assert len(doc.diagrams) == 1
        assert doc.diagrams[0].engine == "mermaid"
        assert "graph TD" in doc.diagrams[0].source

    def test_multiple_diagram_blocks(self) -> None:
        """Requirement: Parser indexes diagram blocks sequentially."""
        md = (
            "```plantuml\n@startuml\nA->B\n@enduml\n```\n\n"
            "```mermaid\ngraph TD\n```\n"
        )
        doc = parse(md)

        assert len(doc.diagrams) == 2
        assert doc.diagrams[0].index == 0
        assert doc.diagrams[1].index == 1

    def test_non_diagram_code_block_ignored(self) -> None:
        """Requirement: Regular code blocks are not treated as diagrams."""
        md = "```python\nprint('hello')\n```\n"
        doc = parse(md)

        assert doc.diagrams == ()

    def test_diagram_engine_case_insensitive(self) -> None:
        """Requirement: Engine detection is case-insensitive."""
        md = "```PlantUML\n@startuml\nA->B\n@enduml\n```\n"
        doc = parse(md)

        assert len(doc.diagrams) == 1
        assert doc.diagrams[0].engine == "plantuml"


class TestParseHtml:
    """Tests for HTML rendering."""

    def test_renders_paragraph(self) -> None:
        """Requirement: Parser renders paragraph to HTML."""
        doc = parse("Hello world.\n")

        assert "<p>Hello world.</p>" in doc.html

    def test_renders_heading(self) -> None:
        """Requirement: Parser renders heading tags in HTML."""
        doc = parse("# Title\n")

        assert "<h1>Title</h1>" in doc.html

    def test_empty_input(self) -> None:
        """Requirement: Empty input produces empty HTML."""
        doc = parse("")

        assert doc.html == ""
        assert doc.headings == ()
        assert doc.images == ()
        assert doc.diagrams == ()
