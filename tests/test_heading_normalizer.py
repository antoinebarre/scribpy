"""Tests for Markdown heading normalization."""

from __future__ import annotations

from scribpy.core.heading_normalizer import normalize_markdown_headings


class TestNormalizeMarkdownHeadings:
    """Tests for shifting Markdown heading levels."""

    def test_normalize_markdown_headings_shifts_atx_headings(self) -> None:
        """Requirement: heading normalization shifts Markdown headings."""
        content = "# Title\n\nBody\n\n## Detail\n"

        normalized = normalize_markdown_headings(content, 3)

        assert normalized == "### Title\n\nBody\n\n#### Detail\n"

    def test_normalize_markdown_headings_ignores_fenced_code(self) -> None:
        """Requirement: heading normalization ignores fenced code headings."""
        content = "# Title\n\n```markdown\n# Example\n```\n"

        normalized = normalize_markdown_headings(content, 2)

        assert normalized == "## Title\n\n```markdown\n# Example\n```\n"

    def test_normalize_markdown_headings_caps_heading_levels(self) -> None:
        """Requirement: heading normalization keeps heading levels valid."""
        content = "## Deep\n"

        normalized = normalize_markdown_headings(content, 6)

        assert normalized == "###### Deep\n"

    def test_normalize_markdown_headings_keeps_minimum_level(self) -> None:
        """Requirement: heading normalization never creates invalid levels."""
        content = "# Title\n"

        normalized = normalize_markdown_headings(content, 0)

        assert normalized == "# Title\n"
