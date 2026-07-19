"""Tests for MarkdownDocument and image references."""

from __future__ import annotations

from scribpy.core import MarkdownDocument, MarkdownImageReference


class TestMarkdownImageReference:
    """Tests for MarkdownImageReference."""

    def test_stores_markdown_image_metadata(self) -> None:
        """Requirement: image references expose Markdown image metadata."""
        reference = MarkdownImageReference(
            alt_text="Logo",
            target="assets/logo.png",
            title="Scribpy logo",
            line=3,
            column=5,
        )

        assert reference.alt_text == "Logo"
        assert reference.target == "assets/logo.png"
        assert reference.title == "Scribpy logo"
        assert reference.line == 3
        assert reference.column == 5


class TestMarkdownDocument:
    """Tests for MarkdownDocument."""

    def test_extracts_image_references(self) -> None:
        """Requirement: MarkdownDocument lists inline image references."""
        document = MarkdownDocument(
            '# Page\n\n![Logo](assets/logo.png "Scribpy logo")\n',
        )

        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Logo",
                target="assets/logo.png",
                title="Scribpy logo",
                line=3,
                column=1,
            ),
        )

    def test_extracts_remote_image_reference(self) -> None:
        """Requirement: image references may target remote URLs."""
        document = MarkdownDocument(
            "Text ![Remote](https://example.com/logo.png)\n",
        )

        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Remote",
                target="https://example.com/logo.png",
                title=None,
                line=1,
                column=6,
            ),
        )

    def test_ignores_images_inside_fenced_code(self) -> None:
        """Requirement: image references inside fenced code are ignored."""
        document = MarkdownDocument(
            "```markdown\n"
            "![Ignored](assets/ignored.png)\n"
            "```\n"
            "![Kept](assets/kept.png)\n",
        )

        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Kept",
                target="assets/kept.png",
                title=None,
                line=4,
                column=1,
            ),
        )

    def test_with_content_refreshes_image_references(self) -> None:
        """Requirement: content replacement refreshes image references."""
        original = MarkdownDocument("![Old](old.png)\n")

        updated = original.with_content("![New](new.png)\n")

        assert original.image_references == (
            MarkdownImageReference(
                alt_text="Old",
                target="old.png",
                title=None,
                line=1,
                column=1,
            ),
        )
        assert updated.image_references == (
            MarkdownImageReference(
                alt_text="New",
                target="new.png",
                title=None,
                line=1,
                column=1,
            ),
        )

    def test_replace_text_refreshes_image_references(self) -> None:
        """Requirement: text replacement refreshes image references."""
        document = MarkdownDocument("![Logo](old.png)\n")

        updated = document.replace_text("old.png", "new.png")

        assert updated.image_references == (
            MarkdownImageReference(
                alt_text="Logo",
                target="new.png",
                title=None,
                line=1,
                column=1,
            ),
        )

    def test_empty_content_has_no_image_references(self) -> None:
        """Requirement: documents without images expose an empty tuple."""
        document = MarkdownDocument("# Page\n\nNo image.\n")

        assert document.image_references == ()

    def test_empty_image_body_has_empty_target(self) -> None:
        """Requirement: empty image bodies are represented explicitly."""
        document = MarkdownDocument("![Empty]( )\n")

        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Empty",
                target="",
                title=None,
                line=1,
                column=1,
            ),
        )

    def test_unclosed_quote_falls_back_to_whitespace_split(self) -> None:
        """Requirement: malformed image body keeps a deterministic target."""
        document = MarkdownDocument('![Broken]("asset path.png)\n')

        assert document.image_references == (
            MarkdownImageReference(
                alt_text="Broken",
                target='"asset',
                title="path.png",
                line=1,
                column=1,
            ),
        )
