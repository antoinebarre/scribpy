"""Tests for scribpy.core.image_resolver."""

from pathlib import Path

from scribpy.core.document import ImageRef, ParsedDocument
from scribpy.core.image_resolver import resolve_images


def _make_document(images: tuple[ImageRef, ...]) -> ParsedDocument:
    """Build a minimal ParsedDocument with given images.

    Args:
        images: Image references to include.

    Returns:
        A ParsedDocument with only images populated.
    """
    return ParsedDocument(html="", images=images)


class TestResolveImages:
    """Tests for the resolve_images function."""

    def test_valid_image_found(self, tmp_path: Path) -> None:
        """Requirement: Existing images are reported as valid."""
        img_file = tmp_path / "photo.png"
        img_file.write_bytes(b"\x89PNG")

        doc = _make_document((ImageRef(src="photo.png"),))
        result = resolve_images(doc, tmp_path)

        assert len(result.valid) == 1
        assert result.valid[0].src == "photo.png"
        assert result.warnings == ()

    def test_missing_image_produces_warning(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: Missing images produce warnings (REQ-004)."""
        doc = _make_document((ImageRef(src="missing.png"),))
        result = resolve_images(doc, tmp_path)

        assert result.valid == ()
        assert len(result.warnings) == 1
        assert "missing.png" in result.warnings[0].message

    def test_mixed_valid_and_missing(self, tmp_path: Path) -> None:
        """Requirement: Valid images kept despite missing ones."""
        (tmp_path / "a.png").write_bytes(b"\x89PNG")

        doc = _make_document(
            (
                ImageRef(src="a.png"),
                ImageRef(src="b.png"),
            )
        )
        result = resolve_images(doc, tmp_path)

        assert len(result.valid) == 1
        assert len(result.warnings) == 1
        assert result.valid[0].src == "a.png"
        assert "b.png" in result.warnings[0].src

    def test_no_images(self, tmp_path: Path) -> None:
        """Requirement: Empty image list yields empty results."""
        doc = _make_document(())
        result = resolve_images(doc, tmp_path)

        assert result.valid == ()
        assert result.warnings == ()

    def test_subdirectory_image(self, tmp_path: Path) -> None:
        """Requirement: Relative paths in subdirectories are resolved."""
        sub = tmp_path / "img"
        sub.mkdir()
        (sub / "logo.svg").write_text("<svg/>")

        doc = _make_document((ImageRef(src="img/logo.svg"),))
        result = resolve_images(doc, tmp_path)

        assert len(result.valid) == 1
        assert result.warnings == ()
