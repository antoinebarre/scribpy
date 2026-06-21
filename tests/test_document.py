"""Tests for scribpy.core.document dataclasses."""

from scribpy.core.document import (
    DiagramBlock,
    Heading,
    ImageRef,
    ParsedDocument,
)


class TestHeading:
    """Tests for the Heading dataclass."""

    def test_creation_with_all_fields(self) -> None:
        """Requirement: Heading stores level, text, and anchor."""
        heading = Heading(level=2, text="Introduction", anchor="introduction")

        assert heading.level == 2
        assert heading.text == "Introduction"
        assert heading.anchor == "introduction"

    def test_frozen(self) -> None:
        """Requirement: Heading instances are immutable."""
        heading = Heading(level=1, text="Title", anchor="title")
        try:
            heading.level = 3  # type: ignore[misc]
        except AttributeError:
            pass
        else:
            msg = "Heading should be frozen"
            raise AssertionError(msg)


class TestImageRef:
    """Tests for the ImageRef dataclass."""

    def test_creation_with_defaults(self) -> None:
        """Requirement: ImageRef defaults alt and title to empty strings."""
        ref = ImageRef(src="img/photo.png")

        assert ref.src == "img/photo.png"
        assert ref.alt == ""
        assert ref.title == ""

    def test_creation_with_all_fields(self) -> None:
        """Requirement: ImageRef stores src, alt, and title."""
        ref = ImageRef(src="a.png", alt="Alt text", title="Title text")

        assert ref.alt == "Alt text"
        assert ref.title == "Title text"


class TestDiagramBlock:
    """Tests for the DiagramBlock dataclass."""

    def test_creation(self) -> None:
        """Requirement: DiagramBlock stores engine, source, and index."""
        block = DiagramBlock(engine="plantuml", source="@startuml", index=0)

        assert block.engine == "plantuml"
        assert block.source == "@startuml"
        assert block.index == 0


class TestParsedDocument:
    """Tests for the ParsedDocument dataclass."""

    def test_defaults(self) -> None:
        """Requirement: ParsedDocument defaults collections to empty tuples."""
        doc = ParsedDocument(html="<p>Hello</p>")

        assert doc.html == "<p>Hello</p>"
        assert doc.headings == ()
        assert doc.images == ()
        assert doc.diagrams == ()

    def test_with_populated_fields(self) -> None:
        """Requirement: ParsedDocument accepts populated collections."""
        heading = Heading(level=1, text="T", anchor="t")
        img = ImageRef(src="x.png")
        diag = DiagramBlock(engine="mermaid", source="graph", index=0)

        doc = ParsedDocument(
            html="<h1>T</h1>",
            headings=(heading,),
            images=(img,),
            diagrams=(diag,),
        )

        assert len(doc.headings) == 1
        assert len(doc.images) == 1
        assert len(doc.diagrams) == 1
