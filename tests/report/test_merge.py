"""Tests for Markdown merge utilities."""

from __future__ import annotations

from scribpy.report.merge import MergeSection, _strip_frontmatter, merge_markdown


class TestMergeMarkdown:
    def test_single_section(self):
        s = MergeSection(content="# Hello\n\nWorld.")
        result = merge_markdown(s)
        assert result == "# Hello\n\nWorld."

    def test_two_sections_joined_by_separator(self):
        a = MergeSection(content="# A")
        b = MergeSection(content="# B")
        result = merge_markdown(a, b)
        assert "---" in result
        assert "# A" in result
        assert "# B" in result

    def test_custom_separator(self):
        a = MergeSection(content="part1")
        b = MergeSection(content="part2")
        result = merge_markdown(a, b, separator="\n\n===\n\n")
        assert "===" in result

    def test_heading_offset_zero_unchanged(self):
        s = MergeSection(content="# Title\n## Sub", heading_offset=0)
        result = merge_markdown(s)
        assert "# Title" in result
        assert "## Sub" in result

    def test_heading_offset_demotes(self):
        s = MergeSection(content="# Title\n## Sub", heading_offset=1)
        result = merge_markdown(s)
        assert "## Title" in result
        assert "### Sub" in result

    def test_heading_capped_at_h6(self):
        s = MergeSection(content="##### H5\n###### H6", heading_offset=2)
        result = merge_markdown(s)
        assert result.count("###### ") == 2

    def test_second_section_frontmatter_stripped(self):
        a = MergeSection(content="# First")
        b = MergeSection(content="---\ntitle: B\n---\n\n# Second")
        result = merge_markdown(a, b)
        assert "title: B" not in result
        assert "# Second" in result

    def test_first_section_frontmatter_preserved(self):
        a = MergeSection(content="---\ntitle: A\n---\n\n# First")
        b = MergeSection(content="# Second")
        result = merge_markdown(a, b)
        assert "title: A" in result

    def test_strips_and_rejoins_whitespace(self):
        a = MergeSection(content="  \n\n# A\n\n  ")
        b = MergeSection(content="  \n\n# B\n\n  ")
        result = merge_markdown(a, b)
        assert result.startswith("# A")
        assert result.endswith("# B")


class TestStripFrontmatter:
    def test_strips_yaml_block(self):
        text = "---\ntitle: T\n---\n\n# Body"
        assert _strip_frontmatter(text) == "# Body"

    def test_no_frontmatter_unchanged(self):
        text = "# Just content"
        assert _strip_frontmatter(text) == "# Just content"

    def test_unclosed_frontmatter_unchanged(self):
        text = "---\ntitle: T\n# Body"
        assert _strip_frontmatter(text) == "# Body\ntitle: T\n# Body" or \
               _strip_frontmatter(text) == text

    def test_leading_whitespace_before_fence(self):
        text = "\n---\ntitle: T\n---\n\nContent"
        result = _strip_frontmatter(text)
        assert "title" not in result
        assert "Content" in result
