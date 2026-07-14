"""Tests for the Markdown collection assembly pipeline."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribpy.core import MarkdownCollection
from scribpy.core.assembly.concatenate import concatenate
from scribpy.core.assembly.heading_numbering import number_markdown_headings
from scribpy.core.assembly.image_collector import collect_images
from scribpy.core.assembly.link_rewriter import (
    _extract_h1_title,
    build_file_slug_map,
    build_numbered_file_slug_map,
    rewrite_internal_links,
)
from scribpy.core.assembly.pipeline import (
    AssembledDocument,
    apply_transforms,
)
from scribpy.core.assembly.slug import slugify_heading
from scribpy.core.markdown_file import MarkdownFile


class TestSlugifyHeading:
    """Tests for slugify_heading."""

    def test_slugify_heading_lowercases_ascii(self) -> None:
        """Requirement: ASCII text is lowercased."""
        assert slugify_heading("Hello World") == "hello-world"

    def test_slugify_heading_replaces_spaces_with_hyphens(self) -> None:
        """Requirement: spaces become hyphens in the slug."""
        assert slugify_heading("Mon Chapitre Un") == "mon-chapitre-un"

    def test_slugify_heading_strips_inline_markers(self) -> None:
        """Requirement: Markdown inline markers are removed before slugging."""
        assert slugify_heading("Titre avec **gras**") == "titre-avec-gras"

    def test_slugify_heading_strips_backticks(self) -> None:
        """Requirement: backtick markers are stripped from heading text."""
        assert slugify_heading("`code` block") == "code-block"

    def test_slugify_heading_removes_special_chars(self) -> None:
        """Requirement: non-word characters are removed from the slug."""
        assert slugify_heading("Section: A & B") == "section-a-b"

    def test_slugify_heading_handles_unicode(self) -> None:
        """Requirement: Unicode letters are preserved in the slug."""
        assert slugify_heading("Héros de la Cité") == "héros-de-la-cité"

    def test_slugify_heading_empty_string(self) -> None:
        """Requirement: empty heading text yields an empty slug."""
        assert slugify_heading("") == ""

    def test_slugify_heading_strips_leading_trailing_spaces(self) -> None:
        """Requirement: leading and trailing whitespace are stripped."""
        assert slugify_heading("  title  ") == "title"


class TestExtractH1Title:
    """Tests for the internal _extract_h1_title helper."""

    def test_extract_h1_title_returns_title_from_h1(self) -> None:
        """Requirement: the first H1 title is extracted from content."""
        content = "# Mon Titre\n\nSome text.\n"
        assert _extract_h1_title(content) == "Mon Titre"

    def test_extract_h1_title_returns_none_when_no_h1(self) -> None:
        """Requirement: None is returned when content has no H1."""
        content = "## Section\n\nSome text.\n"
        assert _extract_h1_title(content) is None

    def test_extract_h1_title_returns_first_h1_only(self) -> None:
        """Requirement: only the first H1 is extracted when many exist."""
        content = "# First\n\n# Second\n"
        assert _extract_h1_title(content) == "First"

    def test_extract_h1_title_strips_surrounding_spaces(self) -> None:
        """Requirement: surrounding whitespace is stripped from the title."""
        content = "#  Spaced Title  \n"
        assert _extract_h1_title(content) == "Spaced Title"


class TestBuildFileSlugMap:
    """Tests for build_file_slug_map."""

    def test_build_file_slug_map_maps_filename_to_slug(
        self, tmp_path: Path
    ) -> None:
        """Requirement: each file is mapped by filename to its H1 slug."""
        path = tmp_path / "intro.md"
        path.write_text("# Introduction\n\nSome text.\n", encoding="utf-8")
        files = (MarkdownFile.from_path(path),)

        slug_map = build_file_slug_map(files)

        assert slug_map == {"intro.md": "introduction"}

    def test_build_file_slug_map_skips_files_without_h1(
        self, tmp_path: Path
    ) -> None:
        """Requirement: files without H1 are excluded from the map."""
        path = tmp_path / "notes.md"
        path.write_text("## Section\n\nNo H1 here.\n", encoding="utf-8")
        files = (MarkdownFile.from_path(path),)

        slug_map = build_file_slug_map(files)

        assert slug_map == {}

    def test_build_file_slug_map_handles_multiple_files(
        self, tmp_path: Path
    ) -> None:
        """Requirement: multiple files are all mapped correctly."""
        (tmp_path / "a.md").write_text("# Alpha\n", encoding="utf-8")
        (tmp_path / "b.md").write_text("# Beta\n", encoding="utf-8")
        files = tuple(
            MarkdownFile.from_path(tmp_path / name)
            for name in ("a.md", "b.md")
        )

        slug_map = build_file_slug_map(files)

        assert slug_map == {"a.md": "alpha", "b.md": "beta"}

    def test_build_file_slug_map_empty_collection(self) -> None:
        """Requirement: empty collection yields an empty map."""
        assert build_file_slug_map(()) == {}


class TestBuildNumberedFileSlugMap:
    """Tests for numbered output file slug mapping."""

    def test_build_numbered_file_slug_map_uses_final_numbered_heading(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: numbered output anchors use final heading text."""
        path = tmp_path / "usage.md"
        path.write_text("# 12 - Usage Guide\n", encoding="utf-8")
        files = (MarkdownFile.from_path(path),)
        content = "# 1. Demo\n\n## 1.1. Usage Guide\n"

        slug_map = build_numbered_file_slug_map(files, content)

        assert slug_map == {"usage.md": "11-usage-guide"}

    def test_build_numbered_file_slug_map_skips_missing_heading(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: absent numbered headings are excluded from the map."""
        path = tmp_path / "usage.md"
        path.write_text("# Usage Guide\n", encoding="utf-8")
        files = (MarkdownFile.from_path(path),)

        slug_map = build_numbered_file_slug_map(files, "# 1. Demo\n")

        assert slug_map == {}

    def test_build_numbered_file_slug_map_skips_files_without_h1(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: files without H1 are excluded from numbered maps."""
        path = tmp_path / "notes.md"
        path.write_text("## Notes\n", encoding="utf-8")
        files = (MarkdownFile.from_path(path),)

        slug_map = build_numbered_file_slug_map(files, "## 1.1. Notes\n")

        assert slug_map == {}


class TestRewriteInternalLinks:
    """Tests for rewrite_internal_links."""

    def test_rewrite_internal_links_replaces_known_target(self) -> None:
        """Requirement: links to known files are rewritten as anchors."""
        content = "See [Chapter 1](chapter1.md) for details.\n"
        slug_map = {"chapter1.md": "chapter-1"}

        result = rewrite_internal_links(content, slug_map)

        assert result == "See [Chapter 1](#chapter-1) for details.\n"

    def test_rewrite_internal_links_preserves_unknown_target(self) -> None:
        """Requirement: links to unknown files are left unchanged."""
        content = "See [Other](other.md) for details.\n"
        slug_map = {"chapter1.md": "chapter-1"}

        result = rewrite_internal_links(content, slug_map)

        assert result == content

    def test_rewrite_internal_links_handles_path_prefix(self) -> None:
        """Requirement: links with a path prefix are resolved by filename."""
        content = "See [Intro](folder/intro.md) here.\n"
        slug_map = {"intro.md": "introduction"}

        result = rewrite_internal_links(content, slug_map)

        assert result == "See [Intro](#introduction) here.\n"

    def test_rewrite_internal_links_leaves_external_links(self) -> None:
        """Requirement: external URLs are not rewritten."""
        content = "See [Site](https://example.com) here.\n"
        slug_map = {"example.com": "example"}

        result = rewrite_internal_links(content, slug_map)

        assert result == content

    def test_rewrite_internal_links_leaves_image_syntax(self) -> None:
        """Requirement: image syntax is not treated as a link."""
        content = "![Logo](logo.md)\n"
        slug_map = {"logo.md": "logo"}

        result = rewrite_internal_links(content, slug_map)

        assert result == content

    def test_rewrite_internal_links_empty_map(self) -> None:
        """Requirement: empty slug map leaves all links unchanged."""
        content = "See [Intro](intro.md).\n"
        result = rewrite_internal_links(content, {})
        assert result == content


class TestAssembledDocument:
    """Tests for AssembledDocument."""

    def test_with_content_replaces_content(self, tmp_path: Path) -> None:
        """Requirement: with_content returns a new doc with updated content."""
        doc = AssembledDocument(
            content="original",
            source_root=tmp_path,
            output=tmp_path / "out.md",
        )
        updated = doc.with_content("updated")

        assert updated.content == "updated"
        assert updated.source_root == doc.source_root
        assert updated.output == doc.output

    def test_with_content_does_not_mutate_original(
        self, tmp_path: Path
    ) -> None:
        """Requirement: original document is unchanged after with_content."""
        doc = AssembledDocument(
            content="original",
            source_root=tmp_path,
            output=tmp_path / "out.md",
        )
        doc.with_content("updated")

        assert doc.content == "original"


class TestApplyTransforms:
    """Tests for apply_transforms."""

    def test_apply_transforms_applies_all_in_order(
        self, tmp_path: Path
    ) -> None:
        """Requirement: transforms are applied left-to-right."""

        def _append_b(d: AssembledDocument) -> AssembledDocument:
            return d.with_content(d.content + "b")

        def _append_c(d: AssembledDocument) -> AssembledDocument:
            return d.with_content(d.content + "c")

        doc = AssembledDocument(
            content="a",
            source_root=tmp_path,
            output=tmp_path / "out.md",
        )
        result = apply_transforms(doc, (_append_b, _append_c))

        assert result.content == "abc"

    def test_apply_transforms_empty_tuple_returns_doc_unchanged(
        self, tmp_path: Path
    ) -> None:
        """Requirement: empty transform tuple returns original document."""
        doc = AssembledDocument(
            content="hello",
            source_root=tmp_path,
            output=tmp_path / "out.md",
        )
        result = apply_transforms(doc, ())

        assert result.content == "hello"


class TestHeadingNumbering:
    """Tests for the MkForge heading numbering adapter."""

    def test_number_markdown_headings_delegates_to_mkforge(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Requirement: heading numbering is delegated to MkForge."""
        calls: list[str] = []

        def _renumber(markdown: str) -> str:
            """Record the MkForge renumbering call.

            Args:
                markdown: Markdown source passed to MkForge.

            Returns:
                Numbered Markdown source.
            """
            calls.append(markdown)
            return "numbered"

        monkeypatch.setattr(
            "mkforge.renumber_markdown_headings",
            _renumber,
        )

        result = number_markdown_headings("# Title\n")

        assert result == "numbered"
        assert calls == ["# Title\n"]


class TestCollectImages:
    """Tests for collect_images."""

    def test_collect_images_copies_local_image(self, tmp_path: Path) -> None:
        """Requirement: a local image file is copied to the assets dir."""
        img = tmp_path / "logo.png"
        img.write_bytes(b"\x89PNG")
        assets = tmp_path / "out" / "assets"
        content = "![Logo](logo.png)\n"

        result = collect_images(content, tmp_path, assets)

        assert (assets / "logo.png").exists()
        assert result == "![Logo](assets/logo.png)\n"

    def test_collect_images_preserves_external_url(
        self, tmp_path: Path
    ) -> None:
        """Requirement: external image URLs are left unchanged."""
        assets = tmp_path / "assets"
        content = "![Ext](https://example.com/img.png)\n"

        result = collect_images(content, tmp_path, assets)

        assert result == content

    def test_collect_images_skips_missing_local_file(
        self, tmp_path: Path
    ) -> None:
        """Requirement: missing local file refs are left unchanged."""
        assets = tmp_path / "assets"
        content = "![Missing](missing.png)\n"

        result = collect_images(content, tmp_path, assets)

        assert result == content

    def test_collect_images_deduplicates_by_prefix(
        self, tmp_path: Path
    ) -> None:
        """Requirement: name collision is resolved by parent name prefix."""
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        (tmp_path / "a" / "logo.png").write_bytes(b"\x89PNG_A")
        (tmp_path / "b" / "logo.png").write_bytes(b"\x89PNG_B")
        assets = tmp_path / "out" / "assets"
        content = "![A](a/logo.png)\n![B](b/logo.png)\n"

        result = collect_images(content, tmp_path, assets)

        assert (assets / "logo.png").exists()
        assert (assets / "b_logo.png").exists()
        assert "assets/logo.png" in result
        assert "assets/b_logo.png" in result

    def test_collect_images_does_not_recopy_same_image(
        self, tmp_path: Path
    ) -> None:
        """Requirement: same image referenced twice is copied only once."""
        img = tmp_path / "logo.png"
        img.write_bytes(b"\x89PNG")
        assets = tmp_path / "out" / "assets"
        content = "![A](logo.png)\n![B](logo.png)\n"

        collect_images(content, tmp_path, assets)

        assert len(list(assets.iterdir())) == 1

    def test_collect_images_skips_empty_target(self, tmp_path: Path) -> None:
        """Requirement: empty image target is left unchanged."""
        assets = tmp_path / "assets"
        content = "![]()\n"

        result = collect_images(content, tmp_path, assets)

        assert result == content

    def test_collect_images_handles_absolute_path(
        self, tmp_path: Path
    ) -> None:
        """Requirement: absolute image target is resolved from root."""
        (tmp_path / "logo.png").write_bytes(b"\x89PNG")
        assets = tmp_path / "out" / "assets"
        content = "![Logo](/logo.png)\n"

        result = collect_images(content, tmp_path, assets)

        assert "assets/logo.png" in result


class TestConcatenate:
    """Integration tests for the concatenate function."""

    def test_concatenate_writes_output_file(self, tmp_path: Path) -> None:
        """Requirement: concatenate writes a Markdown file to output."""
        _write(tmp_path / "src" / "01-intro.md", "# Introduction\n\nHello.\n")
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(tmp_path / "src")

        concatenate(collection, output)

        assert output.exists()

    def test_concatenate_rewrites_internal_links(self, tmp_path: Path) -> None:
        """Requirement: internal file links are rewritten as anchor refs."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-intro.md").write_text(
            "# Introduction\n\nSee [Usage](02-usage.md).\n",
            encoding="utf-8",
        )
        (src / "02-usage.md").write_text(
            "# Usage Guide\n\nContent here.\n", encoding="utf-8"
        )
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "#usage-guide" in text
        assert "02-usage.md" not in text

    def test_concatenate_collects_local_images(self, tmp_path: Path) -> None:
        """Requirement: local images are copied to output.parent/assets/."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "logo.png").write_bytes(b"\x89PNG")
        (src / "01-doc.md").write_text(
            "# Doc\n\n![Logo](logo.png)\n", encoding="utf-8"
        )
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        assert (tmp_path / "out" / "assets" / "logo.png").exists()
        text = output.read_text(encoding="utf-8")
        assert "assets/logo.png" in text

    def test_concatenate_empty_collection(self, tmp_path: Path) -> None:
        """Requirement: empty collection produces a minimal output file."""
        src = tmp_path / "src"
        src.mkdir()
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        assert output.exists()

    def test_concatenate_creates_output_directory(
        self, tmp_path: Path
    ) -> None:
        """Requirement: output parent directories are created if missing."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text("# Doc\n\nText.\n", encoding="utf-8")
        output = tmp_path / "deep" / "nested" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        assert output.exists()

    def test_concatenate_numbers_headings_when_enabled(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: YAML heading numbering enables MkForge numbering."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  heading_numbering:\n    enabled: true\n",
            encoding="utf-8",
        )
        (src / "01-doc.md").write_text("# Doc\n\n## Part\n", encoding="utf-8")
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "# 1. src" in text
        assert "## 1.1. Doc" in text

    def test_concatenate_rewrites_links_to_numbered_headings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: numbered output links target final heading anchors."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "scribpy.yml").write_text(
            "build:\n  heading_numbering:\n    enabled: true\n",
            encoding="utf-8",
        )
        (src / "01-intro.md").write_text(
            "# 99. Intro\n\nSee [Usage](02-usage.md).\n",
            encoding="utf-8",
        )
        (src / "02-usage.md").write_text(
            "# 12 - Usage\n",
            encoding="utf-8",
        )
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "## 1.2. Usage" in text
        assert "[Usage](#12-usage)" in text
        assert "#12---usage" not in text

    def test_concatenate_does_not_number_headings_by_default(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing heading numbering leaves headings unchanged."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "01-doc.md").write_text("# Doc\n", encoding="utf-8")
        output = tmp_path / "out" / "doc.md"
        collection = MarkdownCollection.from_tree(src)

        concatenate(collection, output)

        text = output.read_text(encoding="utf-8")
        assert "# src" in text
        assert "# 1. src" not in text


def _write(path: Path, content: str) -> None:
    """Write content to a file, creating parent directories as needed.

    Args:
        path: Destination file path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
