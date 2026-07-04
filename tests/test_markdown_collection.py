"""Tests for MarkdownCollection."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribpy.core import MarkdownCollection, MarkdownDocument


class TestMarkdownCollectionFromTree:
    """Tests for loading Markdown collections from directory trees."""

    def test_from_tree_loads_nested_markdown_files_in_path_order(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: nested Markdown files are loaded in path order."""
        _write(tmp_path / "02-usage.md", "# Usage\n")
        _write(tmp_path / "01-intro.md", "# Intro\n")
        _write(tmp_path / "guide" / "02-run.md", "# Run\n")
        _write(tmp_path / "guide" / "01-install.md", "# Install\n")

        collection = MarkdownCollection.from_tree(tmp_path)

        assert tuple(
            file.path.relative_to(tmp_path) for file in collection.files
        ) == (
            Path("01-intro.md"),
            Path("02-usage.md"),
            Path("guide/01-install.md"),
            Path("guide/02-run.md"),
        )

    def test_from_tree_ignores_non_markdown_files(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: non-Markdown files are ignored during discovery."""
        _write(tmp_path / "index.md", "# Index\n")
        _write(tmp_path / "asset.txt", "text\n")
        _write(tmp_path / "image.png", "not really an image\n")

        collection = MarkdownCollection.from_tree(tmp_path)

        assert tuple(file.path.name for file in collection.files) == (
            "index.md",
        )

    def test_from_tree_accepts_markdown_suffix(self, tmp_path: Path) -> None:
        """Requirement: .markdown files are accepted as Markdown files."""
        _write(tmp_path / "index.markdown", "# Index\n")

        collection = MarkdownCollection.from_tree(tmp_path)

        assert tuple(file.path.name for file in collection.files) == (
            "index.markdown",
        )

    def test_from_tree_raises_for_non_directory(self, tmp_path: Path) -> None:
        """Requirement: loading from a non-directory raises an error."""
        source_path = tmp_path / "index.md"
        _write(source_path, "# Index\n")

        with pytest.raises(NotADirectoryError):
            MarkdownCollection.from_tree(source_path)

    def test_from_tree_returns_empty_collection_for_empty_tree(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: empty directory trees produce empty collections."""
        collection = MarkdownCollection.from_tree(tmp_path)

        assert collection.root == tmp_path
        assert collection.files == ()


class TestMarkdownCollectionConcatenation:
    """Tests for Markdown collection concatenation."""

    def test_concatenate_returns_markdown_document(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: collection concatenation returns a MarkdownDocument."""
        _write(tmp_path / "01-intro.md", "# Intro\n\nIntro text.\n")
        _write(tmp_path / "02-usage.md", "# Usage\n\nUsage text.\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document == MarkdownDocument(
            "# Intro\n\nIntro text.\n\n# Usage\n\nUsage text.\n",
        )

    def test_concatenate_refreshes_document_image_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: concatenation refreshes combined image references."""
        _write(tmp_path / "01-intro.md", "![Intro](intro.png)\n")
        _write(tmp_path / "02-usage.md", "![Usage](usage.png)\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert tuple(
            reference.target for reference in document.image_references
        ) == (
            "intro.png",
            "usage.png",
        )

    def test_concatenate_empty_collection_returns_empty_document(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: empty collections concatenate to an empty document."""
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document == MarkdownDocument("")


def _write(path: Path, content: str) -> None:
    """Write UTF-8 test content, creating parent directories as needed.

    Args:
        path: Destination path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
