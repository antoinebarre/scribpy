"""Tests for scribpy.yml manifest loading."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribpy.core.manifest import (
    FolderManifest,
    RootManifest,
    load_folder_manifest,
    load_root_manifest,
)
from scribpy.errors import InvalidScribpyManifestError, ScribpyManifestWarning


class TestRootManifest:
    """Tests for root scribpy.yml manifests."""

    def test_missing_root_manifest_returns_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing root manifests produce default settings."""
        manifest = load_root_manifest(tmp_path)

        assert manifest == RootManifest()

    def test_root_manifest_loads_project_build_and_order(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: root manifests expose metadata and global settings."""
        _write(
            tmp_path / "scribpy.yml",
            "project:\n"
            "  title: Demo\n"
            "build:\n"
            "  toc: true\n"
            "  renumber_headings: false\n"
            "order:\n"
            "  - intro.md\n"
            "  - guide/\n",
        )

        manifest = load_root_manifest(tmp_path)

        assert manifest.project == {"title": "Demo"}
        assert manifest.build == {"toc": True, "renumber_headings": False}
        assert manifest.order == ("intro.md", "guide")

    def test_root_manifest_warns_for_unknown_key(self, tmp_path: Path) -> None:
        """Requirement: unknown root keys are ignored with a warning."""
        _write(tmp_path / "scribpy.yml", "unknown: true\n")

        with pytest.warns(ScribpyManifestWarning):
            manifest = load_root_manifest(tmp_path)

        assert manifest.project == {}


class TestFolderManifest:
    """Tests for folder-level scribpy.yml manifests."""

    def test_missing_folder_manifest_returns_defaults(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: missing folder manifests produce default settings."""
        manifest = load_folder_manifest(tmp_path)

        assert manifest == FolderManifest()

    def test_folder_manifest_loads_title_and_order(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: folder manifests expose title and local order."""
        _write(
            tmp_path / "scribpy.yml",
            "title: Guide\norder:\n  - install.md\n  - run.md\n",
        )

        manifest = load_folder_manifest(tmp_path)

        assert manifest.title == "Guide"
        assert manifest.order == ("install.md", "run.md")

    def test_folder_manifest_title_is_optional(self, tmp_path: Path) -> None:
        """Requirement: folder manifests may omit the folder title."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - install.md\n",
        )

        manifest = load_folder_manifest(tmp_path)

        assert manifest.title is None
        assert manifest.order == ("install.md",)

    def test_folder_manifest_warns_and_ignores_build_settings(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: folder build settings are ignored with warning."""
        _write(
            tmp_path / "scribpy.yml",
            "title: Guide\nbuild:\n  toc: false\n",
        )

        with pytest.warns(ScribpyManifestWarning):
            manifest = load_folder_manifest(tmp_path)

        assert manifest.title == "Guide"
        assert manifest.order == ()


class TestManifestValidation:
    """Tests for manifest validation errors."""

    def test_manifest_must_be_mapping(self, tmp_path: Path) -> None:
        """Requirement: manifest YAML must be a mapping."""
        _write(tmp_path / "scribpy.yml", "- intro.md\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_empty_manifest_returns_defaults(self, tmp_path: Path) -> None:
        """Requirement: empty YAML manifests produce default settings."""
        _write(tmp_path / "scribpy.yml", "")

        manifest = load_root_manifest(tmp_path)

        assert manifest == RootManifest(path=tmp_path / "scribpy.yml")

    def test_invalid_yaml_raises_manifest_error(self, tmp_path: Path) -> None:
        """Requirement: invalid YAML raises a manifest error."""
        _write(tmp_path / "scribpy.yml", "project: [\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_manifest_keys_must_be_strings(self, tmp_path: Path) -> None:
        """Requirement: manifest keys must be strings."""
        _write(tmp_path / "scribpy.yml", "1: value\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_project_must_be_mapping(self, tmp_path: Path) -> None:
        """Requirement: project metadata must be a mapping."""
        _write(tmp_path / "scribpy.yml", "project: Demo\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_none_project_is_empty_mapping(self, tmp_path: Path) -> None:
        """Requirement: null project metadata is treated as empty."""
        _write(tmp_path / "scribpy.yml", "project:\n")

        manifest = load_root_manifest(tmp_path)

        assert manifest.project == {}

    def test_folder_title_must_be_string(self, tmp_path: Path) -> None:
        """Requirement: folder manifest titles must be strings."""
        _write(tmp_path / "scribpy.yml", "title: 1\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_folder_manifest(tmp_path)

    def test_order_must_be_list(self, tmp_path: Path) -> None:
        """Requirement: manifest order must be a list."""
        _write(tmp_path / "scribpy.yml", "order: intro.md\n")

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_null_order_is_empty_order(self, tmp_path: Path) -> None:
        """Requirement: null manifest order is treated as empty."""
        _write(tmp_path / "scribpy.yml", "order:\n")

        manifest = load_root_manifest(tmp_path)

        assert manifest.order == ()

    def test_order_entries_must_be_strings(self, tmp_path: Path) -> None:
        """Requirement: manifest order entries must be strings."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - 1\n",
        )

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)

    def test_order_entries_must_be_direct_children(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: manifest order entries name direct children only."""
        _write(
            tmp_path / "scribpy.yml",
            "order:\n  - guide/install.md\n",
        )

        with pytest.raises(InvalidScribpyManifestError):
            load_root_manifest(tmp_path)


def _write(path: Path, content: str) -> None:
    """Write UTF-8 test content, creating parent directories as needed.

    Args:
        path: Destination path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
