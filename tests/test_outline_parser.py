"""Tests for scribpy.core.init.outline_parser and OutlineNode."""

from pathlib import Path

import pytest

from scribpy.core.init.outline_node import OutlineNode
from scribpy.core.init.outline_parser import parse_outline
from scribpy.errors import OutlineValidationError


def _write(tmp_path: Path, content: str) -> Path:
    """Write *content* to a temporary outline file and return its path.

    Args:
        tmp_path: pytest-provided temporary directory.
        content: Markdown text to write.

    Returns:
        Path to the created file.
    """
    p = tmp_path / "outline.md"
    p.write_text(content, encoding="utf-8")
    return p


class TestParseOutlineValid:
    """Tests for parse_outline() with valid outline files."""

    def test_single_h1_returns_one_root(self, tmp_path: Path) -> None:
        """Requirement: a single H1 yields one root OutlineNode."""
        path = _write(tmp_path, "# My Project\n")
        roots = parse_outline(path)
        assert len(roots) == 1
        assert roots[0].title == "My Project"
        assert roots[0].level == 1

    def test_h1_with_h2_children(self, tmp_path: Path) -> None:
        """Requirement: H2 headings become direct children of the H1 node."""
        path = _write(tmp_path, "# Root\n## Alpha\n## Beta\n")
        roots = parse_outline(path)
        assert len(roots) == 1
        assert len(roots[0].children) == 2
        assert roots[0].children[0].title == "Alpha"
        assert roots[0].children[1].title == "Beta"

    def test_nested_hierarchy(self, tmp_path: Path) -> None:
        """Requirement: nested headings build a recursive child tree."""
        content = "# Root\n## Section\n### Sub\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path)
        section = roots[0].children[0]
        assert section.title == "Section"
        assert section.children[0].title == "Sub"

    def test_blank_lines_are_ignored(self, tmp_path: Path) -> None:
        """Requirement: blank lines between headings do not affect parsing."""
        content = "# Root\n\n## Alpha\n\n## Beta\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path)
        assert len(roots[0].children) == 2

    def test_line_numbers_are_correct(self, tmp_path: Path) -> None:
        """Requirement: OutlineNode.line_number reflects the source line."""
        content = "# Root\n## Child\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path)
        assert roots[0].line_number == 1
        assert roots[0].children[0].line_number == 2

    def test_multiple_h1_roots(self, tmp_path: Path) -> None:
        """Requirement: multiple H1 headings each become a root node."""
        content = "# First\n# Second\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path)
        assert len(roots) == 2
        assert roots[0].title == "First"
        assert roots[1].title == "Second"

    def test_max_depth_respected(self, tmp_path: Path) -> None:
        """Requirement: headings at exactly max_depth are accepted."""
        content = "# Root\n## L2\n### L3\n#### L4\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path, max_depth=4)
        assert roots[0].children[0].children[0].children[0].title == "L4"

    def test_unicode_titles_accepted(self, tmp_path: Path) -> None:
        """Requirement: non-ASCII heading titles are preserved."""
        content = "# Présentation\n## Résumé\n"
        path = _write(tmp_path, content)
        roots = parse_outline(path)
        assert roots[0].title == "Présentation"
        assert roots[0].children[0].title == "Résumé"


class TestParseOutlineInvalid:
    """Tests for parse_outline() with invalid outline files."""

    def test_empty_file_raises(self, tmp_path: Path) -> None:
        """Requirement: an outline with no headings raises an error."""
        path = _write(tmp_path, "")
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert exc_info.value.line_number == 0

    def test_non_heading_line_raises(self, tmp_path: Path) -> None:
        """Requirement: non-heading non-blank content raises an error."""
        content = "# Root\nsome paragraph\n"
        path = _write(tmp_path, content)
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert exc_info.value.line_number == 2

    def test_first_heading_not_h1_raises(self, tmp_path: Path) -> None:
        """Requirement: outline not starting with H1 raises an error."""
        path = _write(tmp_path, "## Not H1\n")
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert "H1" in exc_info.value.detail

    def test_skipped_level_raises(self, tmp_path: Path) -> None:
        """Requirement: skipping a heading level raises an error."""
        content = "# Root\n### Skipped H2\n"
        path = _write(tmp_path, content)
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert "skipped" in exc_info.value.detail

    def test_depth_exceeds_max_raises(self, tmp_path: Path) -> None:
        """Requirement: heading deeper than max_depth raises an error."""
        content = "# Root\n## L2\n### L3\n#### L4\n##### L5\n"
        path = _write(tmp_path, content)
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path, max_depth=4)
        assert "max_depth" in exc_info.value.detail

    def test_sibling_slug_collision_raises(self, tmp_path: Path) -> None:
        """Requirement: siblings with identical slugs raise an error."""
        content = "# Root\n## Alpha Beta\n## Alpha  Beta\n"
        path = _write(tmp_path, content)
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert "duplicate" in exc_info.value.detail

    def test_invalid_max_depth_raises_value_error(
        self, tmp_path: Path
    ) -> None:
        """Requirement: max_depth outside 1-6 raises ValueError."""
        path = _write(tmp_path, "# Root\n")
        with pytest.raises(ValueError, match="max_depth"):
            parse_outline(path, max_depth=0)
        with pytest.raises(ValueError, match="max_depth"):
            parse_outline(path, max_depth=7)

    def test_empty_heading_title_raises(self, tmp_path: Path) -> None:
        """Requirement: a heading with no title text raises an error."""
        path = _write(tmp_path, "# \n")
        with pytest.raises(OutlineValidationError) as exc_info:
            parse_outline(path)
        assert "empty" in exc_info.value.detail


class TestOutlineNode:
    """Tests for OutlineNode dataclass."""

    def test_default_children_list(self) -> None:
        """Requirement: children is an independent list per instance."""
        a = OutlineNode(title="A", level=1, line_number=1)
        b = OutlineNode(title="B", level=1, line_number=2)
        a.children.append(OutlineNode(title="C", level=2, line_number=3))
        assert b.children == []

    def test_fields_accessible(self) -> None:
        """Requirement: all OutlineNode fields are readable."""
        node = OutlineNode(title="Hello", level=2, line_number=5)
        assert node.title == "Hello"
        assert node.level == 2
        assert node.line_number == 5
