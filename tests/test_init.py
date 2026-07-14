"""Tests for scribpy.core.init skeleton and scaffold generation."""

from pathlib import Path

import pytest
import yaml

from scribpy.core.init.scaffold import init_from_outline
from scribpy.core.init.skeleton import init_skeleton
from scribpy.errors import OutlineValidationError, ScaffoldCollisionError


def _outline(tmp_path: Path, content: str) -> Path:
    """Write *content* to a temporary outline file and return its path.

    Args:
        tmp_path: pytest-provided temporary directory.
        content: Markdown outline content.

    Returns:
        Path to the created outline file.
    """
    p = tmp_path / "outline.md"
    p.write_text(content, encoding="utf-8")
    return p


class TestInitSkeleton:
    """Tests for init_skeleton()."""

    def test_creates_manifest_and_index(self, tmp_path: Path) -> None:
        """Requirement: init_skeleton writes scribpy.yml and index.md."""
        out = tmp_path / "project"
        init_skeleton(out, title="My Project")
        assert (out / "scribpy.yml").exists()
        assert (out / "index.md").exists()

    def test_manifest_contains_title(self, tmp_path: Path) -> None:
        """Requirement: project.title matches the supplied title."""
        out = tmp_path / "project"
        init_skeleton(out, title="Docs")
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["title"] == "Docs"

    def test_manifest_contains_version(self, tmp_path: Path) -> None:
        """Requirement: project.version matches the supplied version."""
        out = tmp_path / "project"
        init_skeleton(out, title="X", version="1.2.3")
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["version"] == "1.2.3"

    def test_manifest_author_omitted_when_empty(self, tmp_path: Path) -> None:
        """Requirement: project.author is absent when no author is supplied."""
        out = tmp_path / "project"
        init_skeleton(out, title="X")
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert "author" not in data["project"]

    def test_manifest_author_present_when_supplied(
        self, tmp_path: Path
    ) -> None:
        """Requirement: project.author appears in manifest when supplied."""
        out = tmp_path / "project"
        init_skeleton(out, title="X", author="Alice")
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["author"] == "Alice"

    def test_index_md_h1_matches_title(self, tmp_path: Path) -> None:
        """Requirement: index.md starts with the project title as an H1."""
        out = tmp_path / "project"
        init_skeleton(out, title="Hello World")
        content = (out / "index.md").read_text()
        assert content.startswith("# Hello World")

    def test_manifest_order_contains_index(self, tmp_path: Path) -> None:
        """Requirement: root manifest order includes index.md."""
        out = tmp_path / "project"
        init_skeleton(out, title="X")
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert "index.md" in data["order"]

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        """Requirement: init_skeleton creates output_dir when absent."""
        out = tmp_path / "new" / "nested"
        init_skeleton(out, title="X")
        assert out.is_dir()

    def test_collision_raises_when_manifest_exists(
        self, tmp_path: Path
    ) -> None:
        """Requirement: init_skeleton refuses when scribpy.yml exists."""
        out = tmp_path / "project"
        init_skeleton(out, title="First")
        with pytest.raises(ScaffoldCollisionError) as exc_info:
            init_skeleton(out, title="Second")
        assert "scribpy.yml" in exc_info.value.path


class TestInitFromOutline:
    """Tests for init_from_outline()."""

    def test_single_h1_creates_root_manifest(self, tmp_path: Path) -> None:
        """Requirement: a single H1 outline sets project.title in manifest."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# My Docs\n")
        init_from_outline(path, out)
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["title"] == "My Docs"

    def test_h2_children_become_files(self, tmp_path: Path) -> None:
        """Requirement: leaf H2 headings produce .md stub files."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Root\n## Alpha\n## Beta\n")
        init_from_outline(path, out)
        assert (out / "alpha.md").exists()
        assert (out / "beta.md").exists()

    def test_h2_children_in_root_order(self, tmp_path: Path) -> None:
        """Requirement: root manifest order reflects H2 outline order."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Root\n## Alpha\n## Beta\n")
        init_from_outline(path, out)
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["order"] == ["alpha.md", "beta.md"]

    def test_h2_with_h3_children_creates_subdir(self, tmp_path: Path) -> None:
        """Requirement: H2 with children becomes a subdirectory."""
        out = tmp_path / "project"
        path = _outline(
            tmp_path, "# Root\n## Architecture\n### Backend\n### Frontend\n"
        )
        init_from_outline(path, out)
        assert (out / "architecture").is_dir()
        assert (out / "architecture" / "scribpy.yml").exists()

    def test_folder_manifest_title_and_order(self, tmp_path: Path) -> None:
        """Requirement: folder manifest contains the title and child order."""
        out = tmp_path / "project"
        path = _outline(
            tmp_path, "# Root\n## Architecture\n### Backend\n### Frontend\n"
        )
        init_from_outline(path, out)
        data = yaml.safe_load(
            (out / "architecture" / "scribpy.yml").read_text()
        )
        assert data["title"] == "Architecture"
        assert data["order"] == ["backend.md", "frontend.md"]

    def test_leaf_stub_contains_h1(self, tmp_path: Path) -> None:
        """Requirement: each stub .md starts with the section title as H1."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Root\n## Alpha\n")
        init_from_outline(path, out)
        content = (out / "alpha.md").read_text()
        assert content.startswith("# Alpha")

    def test_collision_raises_when_manifest_exists(
        self, tmp_path: Path
    ) -> None:
        """Requirement: init_from_outline refuses when scribpy.yml exists."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Root\n")
        init_from_outline(path, out)
        with pytest.raises(ScaffoldCollisionError):
            init_from_outline(path, out)

    def test_invalid_outline_propagates_error(self, tmp_path: Path) -> None:
        """Requirement: a malformed outline raises an error before writing."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "## Not H1\n")
        with pytest.raises(OutlineValidationError):
            init_from_outline(path, out)
        assert not (out / "scribpy.yml").exists()

    def test_creates_output_dir_if_missing(self, tmp_path: Path) -> None:
        """Requirement: init_from_outline creates output_dir when absent."""
        out = tmp_path / "new" / "nested"
        path = _outline(tmp_path, "# Root\n")
        init_from_outline(path, out)
        assert out.is_dir()

    def test_unicode_title_in_manifest(self, tmp_path: Path) -> None:
        """Requirement: non-ASCII titles are preserved in the root manifest."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Présentation\n")
        init_from_outline(path, out)
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["title"] == "Présentation"

    def test_integration_deep_hierarchy(self, tmp_path: Path) -> None:
        """Requirement: a four-level outline produces the correct full tree."""
        content = (
            "# Project\n"
            "## Architecture\n"
            "### Backend\n"
            "#### Database\n"
            "### Frontend\n"
            "## API\n"
        )
        out = tmp_path / "project"
        path = _outline(tmp_path, content)
        init_from_outline(path, out, max_depth=4)

        assert (out / "architecture").is_dir()
        assert (out / "architecture" / "backend").is_dir()
        assert (out / "architecture" / "backend" / "database.md").exists()
        assert (out / "architecture" / "frontend.md").exists()
        assert (out / "api.md").exists()

    def test_multiple_h1_roots_become_top_level_entries(
        self, tmp_path: Path
    ) -> None:
        """Requirement: multiple H1 headings scaffold as top-level entries."""
        out = tmp_path / "project"
        path = _outline(tmp_path, "# Alpha\n# Beta\n")
        init_from_outline(path, out)
        assert (out / "alpha.md").exists()
        assert (out / "beta.md").exists()
        data = yaml.safe_load((out / "scribpy.yml").read_text())
        assert data["project"]["title"] == "Project"
        assert data["order"] == ["alpha.md", "beta.md"]
