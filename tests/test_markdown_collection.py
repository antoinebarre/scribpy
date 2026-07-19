"""Tests for MarkdownCollection."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribpy.core import MarkdownCollection, MarkdownDocument, MarkdownFile
from scribpy.errors import (
    InvalidMarkdownError,
    InvalidScribpyManifestError,
    ScribpyManifestWarning,
)


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

    def test_from_tree_uses_root_and_folder_manifest_order(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: scribpy.yml files control direct child order."""
        _write(
            tmp_path / "scribpy.yml",
            "project:\n"
            "  title: Demo\n"
            "build:\n"
            "  toc: true\n"
            "order:\n"
            "  - guide/\n"
            "  - intro.md\n",
        )
        _write(tmp_path / "intro.md", "# Intro\n")
        _write(
            tmp_path / "guide" / "scribpy.yml",
            "title: Guide\norder:\n  - run.md\n  - install.md\n",
        )
        _write(tmp_path / "guide" / "install.md", "# Install\n")
        _write(tmp_path / "guide" / "run.md", "# Run\n")

        collection = MarkdownCollection.from_tree(tmp_path)

        assert collection.manifest.project == {"title": "Demo"}
        assert collection.manifest.build.toc is True
        assert tuple(
            file.path.relative_to(tmp_path) for file in collection.files
        ) == (
            Path("guide/run.md"),
            Path("guide/install.md"),
            Path("intro.md"),
        )

    def test_from_tree_warns_and_ignores_unlisted_children(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: unlisted children are ignored with a warning."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - intro.md\n",
        )
        _write(tmp_path / "intro.md", "# Intro\n")
        _write(tmp_path / "ignored.md", "# Ignored\n")

        with pytest.warns(ScribpyManifestWarning):
            collection = MarkdownCollection.from_tree(tmp_path)

        assert tuple(file.path.name for file in collection.files) == (
            "intro.md",
        )

    def test_from_tree_raises_for_missing_manifest_entry(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: ordered children must exist."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - missing.md\n",
        )

        with pytest.raises(InvalidScribpyManifestError):
            MarkdownCollection.from_tree(tmp_path)


class TestMarkdownCollectionConcatenation:
    """Tests for Markdown collection concatenation."""

    def test_concatenate_returns_markdown_document(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: collection concatenation returns a MarkdownDocument."""
        _write(tmp_path / "scribpy.yml", "project:\n  title: Demo\n")
        _write(tmp_path / "01-intro.md", "# Intro\n\nIntro text.\n")
        _write(tmp_path / "02-usage.md", "# Usage\n\nUsage text.\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document == MarkdownDocument(
            "# Demo\n\n## Intro\n\nIntro text.\n\n## Usage\n\nUsage text.\n",
        )

    def test_concatenate_refreshes_document_image_references(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: concatenation refreshes combined image references."""
        _write(tmp_path / "intro.png", "fake image")
        _write(tmp_path / "usage.png", "fake image")
        _write(tmp_path / "01-intro.md", "# Intro\n\n![Intro](intro.png)\n")
        _write(tmp_path / "02-usage.md", "# Usage\n\n![Usage](usage.png)\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert tuple(
            reference.target for reference in document.image_references
        ) == (
            "intro.png",
            "usage.png",
        )

    def test_concatenate_uses_root_folder_name_without_project_title(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: concatenation uses root name when title is absent."""
        _write(tmp_path / "index.md", "# Intro\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document.content == f"# {tmp_path.name}\n\n## Intro\n"

    def test_concatenate_adds_manifest_folder_headings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: folder manifests provide assembled headings."""
        _write(tmp_path / "scribpy.yml", "project:\n  title: Demo\n")
        _write(tmp_path / "guide" / "scribpy.yml", "title: User Guide\n")
        _write(tmp_path / "guide" / "install.md", "# Install\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document.content == ("# Demo\n\n## User Guide\n\n### Install\n")

    def test_concatenate_uses_folder_name_without_folder_title(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: folders without titles use their directory name."""
        _write(tmp_path / "scribpy.yml", "project:\n  title: Demo\n")
        _write(tmp_path / "guide" / "install.md", "# Install\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document.content == "# Demo\n\n## guide\n\n### Install\n"

    def test_concatenate_adds_nested_folder_headings_once(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: nested folders create stable hierarchy headings."""
        _write(
            tmp_path / "scribpy.yml",
            "project:\n  title: Demo\norder:\n  - guide\n  - api\n",
        )
        _write(tmp_path / "guide" / "intro.md", "# Intro\n")
        _write(tmp_path / "guide" / "deep" / "detail.md", "# Detail\n")
        _write(tmp_path / "api" / "reference.md", "# Reference\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert document.content == (
            "# Demo\n\n"
            "## guide\n\n"
            "### deep\n\n"
            "#### Detail\n\n"
            "### Intro\n\n"
            "## api\n\n"
            "### Reference\n"
        )

    def test_concatenate_keeps_external_file_as_root_content(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: manually supplied external files remain supported."""
        collection = MarkdownCollection(
            root=tmp_path,
            files=(MarkdownFile(Path("outside.md"), "# Outside\n"),),
        )

        document = collection.concatenate()

        assert document.content == f"# {tmp_path.name}\n\n## Outside\n"

    def test_concatenate_raises_for_empty_file_content(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: empty Markdown files fail source diagnostics."""
        _write(tmp_path / "scribpy.yml", "project:\n  title: Demo\n")
        _write(tmp_path / "empty.md", "\n\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "SOURCE_H1_COUNT_INVALID" in str(exc_info.value)

    def test_concatenate_raises_for_heading_level_overflow(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: invalid assembled heading levels block output."""
        _write(tmp_path / "index.md", "###### Too deep\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "HEADING_LEVEL_OVERFLOW" in str(exc_info.value)

    def test_concatenate_raises_for_multiple_source_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: source files with multiple H1 headings block output."""
        _write(tmp_path / "index.md", "# First\n\n# Second\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "SOURCE_H1_COUNT_INVALID" in str(exc_info.value)

    def test_concatenate_raises_for_first_heading_not_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: source files whose first heading is not H1 fail."""
        _write(tmp_path / "index.md", "## First\n\n# Title\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "SOURCE_FIRST_HEADING_NOT_H1" in str(exc_info.value)

    def test_concatenate_raises_for_missing_local_image(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing local images block collection output."""
        _write(tmp_path / "index.md", "# Title\n\n![Missing](missing.png)\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "LOCAL_IMAGE_MISSING" in str(exc_info.value)

    def test_concatenate_allows_external_image_warning(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: external image warnings do not block output."""
        _write(
            tmp_path / "index.md",
            "# Title\n\n![Remote](https://example.com/logo.png)\n",
        )
        collection = MarkdownCollection.from_tree(tmp_path)

        document = collection.concatenate()

        assert "https://example.com/logo.png" in document.content

    def test_concatenate_raises_for_missing_internal_markdown_link(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing internal Markdown links block output."""
        _write(tmp_path / "index.md", "# Title\n\n[Missing](missing.md)\n")
        collection = MarkdownCollection.from_tree(tmp_path)

        with pytest.raises(InvalidMarkdownError) as exc_info:
            collection.concatenate()

        assert "INTERNAL_MARKDOWN_LINK_MISSING" in str(exc_info.value)

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
