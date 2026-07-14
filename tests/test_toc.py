"""Tests for table of contents generation."""

from __future__ import annotations

from scribpy.core.assembly.toc import (
    _extract_headings,
    _insert_toc,
    _mask_fenced_blocks,
    _render_toc,
    generate_toc,
)


class TestMaskFencedBlocks:
    """Tests for _mask_fenced_blocks."""

    def test_mask_fenced_blocks_replaces_content_with_newlines(
        self,
    ) -> None:
        """Requirement: fenced block content replaced preserving line count."""
        content = "before\n```python\ndef foo():\n    pass\n```\nafter"
        masked = _mask_fenced_blocks(content)
        assert masked.count("\n") == content.count("\n")
        assert "def foo" not in masked

    def test_mask_fenced_blocks_preserves_content_outside_fences(
        self,
    ) -> None:
        """Requirement: text outside fenced blocks is not altered."""
        content = "# Title\n\n```\ncode\n```\n\n## Section"
        masked = _mask_fenced_blocks(content)
        assert "# Title" in masked
        assert "## Section" in masked

    def test_mask_fenced_blocks_no_fences_returns_unchanged(self) -> None:
        """Requirement: content without fences is returned unchanged."""
        content = "# Title\n\nParagraph."
        assert _mask_fenced_blocks(content) == content


class TestExtractHeadings:
    """Tests for _extract_headings."""

    def test_extract_headings_returns_level_and_title(self) -> None:
        """Requirement: each heading is returned as (level, title) pair."""
        content = "# Title\n## Section\n### Sub"
        assert _extract_headings(content) == [
            (1, "Title"),
            (2, "Section"),
            (3, "Sub"),
        ]

    def test_extract_headings_ignores_headings_in_fenced_blocks(
        self,
    ) -> None:
        """Requirement: headings inside fenced blocks are ignored."""
        content = "# Title\n\n```\n## Not a heading\n```\n\n## Real"
        headings = _extract_headings(content)
        assert headings == [(1, "Title"), (2, "Real")]

    def test_extract_headings_empty_document_returns_empty(self) -> None:
        """Requirement: documents without headings yield an empty list."""
        assert _extract_headings("Just a paragraph.") == []

    def test_extract_headings_strips_trailing_whitespace_from_title(
        self,
    ) -> None:
        """Requirement: heading titles have trailing whitespace stripped."""
        content = "## Section   "
        assert _extract_headings(content) == [(2, "Section")]


class TestRenderToc:
    """Tests for _render_toc."""

    def test_render_toc_flat_list(self) -> None:
        """Requirement: same-level entries render without indentation."""
        entries = [(2, "Alpha"), (2, "Beta")]
        result = _render_toc(entries)
        assert result == "- [Alpha](#alpha)\n- [Beta](#beta)"

    def test_render_toc_nested_list(self) -> None:
        """Requirement: deeper entries indented relative to the shallowest."""
        entries = [(2, "Section"), (3, "Sub")]
        result = _render_toc(entries)
        assert result == "- [Section](#section)\n  - [Sub](#sub)"

    def test_render_toc_relative_indentation(self) -> None:
        """Requirement: indentation relative to the minimum level present."""
        entries = [(3, "Alpha"), (4, "Beta")]
        result = _render_toc(entries)
        assert result == "- [Alpha](#alpha)\n  - [Beta](#beta)"

    def test_render_toc_uses_slugify_for_anchors(self) -> None:
        """Requirement: anchor slugs follow GitHub heading slug rules."""
        entries = [(2, "My Section: A & B")]
        result = _render_toc(entries)
        assert "(#my-section-a-b)" in result

    def test_render_toc_numbered_title(self) -> None:
        """Requirement: numbered titles produce slugs matching the renderer."""
        entries = [(2, "1. Installation")]
        result = _render_toc(entries)
        assert result == "- [1. Installation](#1-installation)"


class TestInsertToc:
    """Tests for _insert_toc."""

    def test_insert_toc_after_h1(self) -> None:
        """Requirement: TOC block is inserted after the first H1 line."""
        content = "# Guide\n\n## Section"
        result = _insert_toc(content, "- [Section](#section)")
        assert result == "# Guide\n\n- [Section](#section)\n\n## Section"

    def test_insert_toc_prepends_when_no_h1(self) -> None:
        """Requirement: TOC is prepended when the document has no H1."""
        content = "## Section\n\nText."
        result = _insert_toc(content, "- [Section](#section)")
        assert result.startswith("- [Section](#section)\n\n## Section")

    def test_insert_toc_preserves_content_after_insertion(self) -> None:
        """Requirement: content after the H1 is preserved intact."""
        content = "# Title\n\nIntro text.\n\n## Chapter"
        toc = "- [Chapter](#chapter)"
        result = _insert_toc(content, toc)
        assert "Intro text." in result
        assert "## Chapter" in result


class TestGenerateToc:
    """Tests for generate_toc."""

    def test_generate_toc_inserts_after_h1(self) -> None:
        """Requirement: TOC is inserted after the first H1."""
        content = "# Guide\n\n## Installation\n\n## Configuration"
        result = generate_toc(content)
        lines = result.split("\n")
        h1_idx = next(
            i for i, line in enumerate(lines) if line.startswith("# ")
        )
        toc_idx = next(
            i for i, line in enumerate(lines) if line.startswith("- [")
        )
        assert toc_idx > h1_idx

    def test_generate_toc_excludes_h1_from_entries(self) -> None:
        """Requirement: the H1 title does not appear as a TOC entry."""
        content = "# Guide\n\n## Section"
        result = generate_toc(content)
        assert "[Guide]" not in result
        assert "[Section]" in result

    def test_generate_toc_no_subheadings_returns_unchanged(self) -> None:
        """Requirement: document with only H1 is returned unchanged."""
        content = "# Guide\n\nParagraph."
        assert generate_toc(content) == content

    def test_generate_toc_empty_document_returns_unchanged(self) -> None:
        """Requirement: empty document is returned unchanged."""
        assert generate_toc("") == ""

    def test_generate_toc_no_h1_prepends_toc(self) -> None:
        """Requirement: TOC is prepended when no H1 is present."""
        content = "## Section\n\nText."
        result = generate_toc(content)
        assert result.startswith("- [Section](#section)")

    def test_generate_toc_ignores_headings_in_code_blocks(self) -> None:
        """Requirement: headings inside fenced blocks are not TOC entries."""
        content = "# Guide\n\n```\n## Not an entry\n```\n\n## Real Section"
        result = generate_toc(content)
        assert "[Not an entry]" not in result
        assert "[Real Section]" in result

    def test_generate_toc_with_numbered_headings(self) -> None:
        """Requirement: TOC slugs match numbered heading anchors."""
        content = "# Guide\n\n## 1. Installation\n\n### 1.1. Prerequis"
        result = generate_toc(content)
        assert "(#1-installation)" in result
        assert "(#11-prerequis)" in result

    def test_generate_toc_deep_nesting(self) -> None:
        """Requirement: deeply nested headings are indented correctly."""
        content = "# G\n\n## H2\n\n### H3\n\n#### H4"
        result = generate_toc(content)
        assert "- [H2]" in result
        assert "  - [H3]" in result
        assert "    - [H4]" in result

    def test_generate_toc_integration_full_document(self) -> None:
        """Requirement: full pipeline output has correct TOC structure."""
        content = (
            "# User Guide\n\n"
            "## Installation\n\n"
            "### Prerequisites\n\n"
            "## Configuration\n\n"
            "## Reference API\n"
        )
        result = generate_toc(content)
        assert "- [Installation](#installation)" in result
        assert "  - [Prerequisites](#prerequisites)" in result
        assert "- [Configuration](#configuration)" in result
        assert "- [Reference API](#reference-api)" in result

    def test_generate_toc_max_depth_excludes_deeper_headings(self) -> None:
        """Requirement: headings deeper than max_depth are excluded."""
        content = "# Guide\n\n## Section\n\n### Sub\n\n#### Deep\n"
        result = generate_toc(content, max_depth=1)
        assert "- [Section](#section)" in result
        assert "[Sub]" not in result
        assert "[Deep]" not in result

    def test_generate_toc_max_depth_two_includes_h3(self) -> None:
        """Requirement: max_depth=2 includes H2 and H3 but not H4."""
        content = "# Guide\n\n## Section\n\n### Sub\n\n#### Deep\n"
        result = generate_toc(content, max_depth=2)
        assert "- [Section](#section)" in result
        assert "  - [Sub](#sub)" in result
        assert "[Deep]" not in result

    def test_generate_toc_max_depth_default_is_three(self) -> None:
        """Requirement: default max_depth includes H2, H3, and H4."""
        content = "# Guide\n\n## H2\n\n### H3\n\n#### H4\n\n##### H5\n"
        result = generate_toc(content)
        assert "[H2]" in result
        assert "[H3]" in result
        assert "[H4]" in result
        assert "[H5]" not in result

    def test_generate_toc_max_depth_no_entries_returns_unchanged(
        self,
    ) -> None:
        """Requirement: document unchanged when all headings exceed depth."""
        content = "# Guide\n\n### Deep only\n"
        result = generate_toc(content, max_depth=1)
        assert result == content
