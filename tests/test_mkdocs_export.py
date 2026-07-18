"""Tests for static MkDocs project export."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from scribpy import mkdocs_export
from scribpy.core.assembly import image_collector as assembly_images
from scribpy.core.image_collector import collect_images
from scribpy.errors import InvalidMarkdownError, ScaffoldCollisionError


def _write_project(root: Path) -> None:
    """Write a representative manifest-driven Scribpy project.

    Args:
        root: Project root to populate.
    """
    (root / "architecture" / "images").mkdir(parents=True)
    (root / "scribpy.yml").write_text(
        "project:\n"
        "  title: Guide utilisateur\n"
        "build:\n"
        "  heading_numbering:\n"
        "    enabled: true\n"
        "  plantuml_backend: plantuml_server\n"
        "  mermaid_backend: mermaid_cli\n"
        "  mermaid_command: custom-mmdc\n"
        "order:\n"
        "  - intro.md\n"
        "  - architecture/\n",
        encoding="utf-8",
    )
    (root / "intro.md").write_text(
        "# Introduction\n\n"
        "[Contexte](architecture/contexte.md)\n\n"
        "```plantuml\n@startuml\nA -> B\n@enduml\n```\n",
        encoding="utf-8",
    )
    (root / "architecture" / "scribpy.yml").write_text(
        "title: Architecture système\norder:\n  - contexte.md\n  - images/\n",
        encoding="utf-8",
    )
    (root / "architecture" / "contexte.md").write_text(
        "```markdown\n# Faux titre\n```\n"
        "# Contexte\n\n"
        "![Schéma](images/schema.png)\n\n"
        "[Introduction](../intro.md)\n\n"
        "```mermaid\ngraph TD\nA --> B\n```\n",
        encoding="utf-8",
    )
    (root / "architecture" / "images" / "schema.png").write_bytes(
        b"source-image"
    )


def _assert_configuration(output: Path) -> None:
    """Assert the representative export configuration.

    Args:
        output: MkDocs export root.
    """
    configuration = yaml.safe_load(
        (output / "mkdocs.yml").read_text(encoding="utf-8")
    )
    assert configuration == {
        "site_name": "Guide utilisateur",
        "docs_dir": "docs",
        "nav": [
            {"Introduction": "intro.md"},
            {
                "Architecture système": [
                    {"Contexte": "architecture/contexte.md"}
                ]
            },
        ],
    }


def _assert_exported_files(output: Path) -> None:
    """Assert representative Markdown and asset output.

    Args:
        output: MkDocs export root.
    """
    intro = (output / "docs" / "intro.md").read_text(encoding="utf-8")
    context = (output / "docs" / "architecture" / "contexte.md").read_text(
        encoding="utf-8"
    )
    assert intro.startswith("# Introduction\n")
    assert "[Contexte](architecture/contexte.md)" in intro
    assert "![diagram](assets/generated/" in intro
    assert context.startswith("```markdown\n# Faux titre\n```\n# Contexte")
    assert "[Introduction](../intro.md)" in context
    assert "![Schéma](../assets/schema.png)" in context
    assert "![diagram](../assets/generated/" in context
    assert (output / "docs" / "assets" / "schema.png").read_bytes() == (
        b"source-image"
    )
    generated = output / "docs" / "assets" / "generated"
    assert len(list(generated.iterdir())) == 2


def _assert_renderer_calls(
    make_plantuml: MagicMock,
    make_mermaid: MagicMock,
    plantuml: MagicMock,
    mermaid: MagicMock,
) -> None:
    """Assert manifest backends and render calls.

    Args:
        make_plantuml: Patched PlantUML renderer factory.
        make_mermaid: Patched Mermaid renderer factory.
        plantuml: PlantUML renderer mock.
        mermaid: Mermaid renderer mock.
    """
    make_plantuml.assert_any_call(
        "plantuml_server",
        server_url="https://www.plantuml.com/plantuml",
    )
    make_mermaid.assert_any_call(
        "mermaid_cli",
        command="custom-mmdc",
    )
    plantuml.render.assert_called_once()
    mermaid.render.assert_called_once()


class TestMkDocsExport:
    """Tests for the public MkDocs export workflow."""

    def test_export_writes_hierarchy_navigation_and_assets(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: a complete project becomes static MkDocs input."""
        source = tmp_path / "source"
        output = tmp_path / "output"
        source.mkdir()
        _write_project(source)
        plantuml = MagicMock()
        plantuml.render.return_value = b"plantuml-png"
        mermaid = MagicMock()
        mermaid.render.return_value = b"mermaid-png"

        with (
            patch(
                "scribpy.core.diagram_blocks.make_plantuml_renderer",
                return_value=plantuml,
            ) as make_plantuml,
            patch(
                "scribpy.core.diagram_blocks.make_mermaid_renderer",
                return_value=mermaid,
            ) as make_mermaid,
        ):
            mkdocs_export(source, output)

        _assert_configuration(output)
        _assert_exported_files(output)
        _assert_renderer_calls(
            make_plantuml,
            make_mermaid,
            plantuml,
            mermaid,
        )

    def test_export_rejects_existing_configuration(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: an existing mkdocs.yml blocks every export write."""
        source = tmp_path / "source"
        output = tmp_path / "output"
        source.mkdir()
        output.mkdir()
        configuration = output / "mkdocs.yml"
        configuration.write_text("existing\n", encoding="utf-8")

        with pytest.raises(ScaffoldCollisionError) as error:
            mkdocs_export(source, output)

        assert error.value.path == str(configuration)
        assert configuration.read_text(encoding="utf-8") == "existing\n"
        assert list(output.iterdir()) == [configuration]

    def test_export_uses_fallback_titles_without_manifests(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: absent manifests use ordered title fallbacks."""
        source = tmp_path / "my-project"
        output = tmp_path / "output"
        (source / "api").mkdir(parents=True)
        (source / "zeta.md").write_text("# Zeta\n", encoding="utf-8")
        (source / "api" / "reference.md").write_text(
            "~~~text\n# Ignoré\n~~~\n# Référence\n",
            encoding="utf-8",
        )

        with (
            patch("scribpy.core.diagram_blocks.make_plantuml_renderer"),
            patch("scribpy.core.diagram_blocks.make_mermaid_renderer"),
        ):
            mkdocs_export(source, output)

        configuration = yaml.safe_load(
            (output / "mkdocs.yml").read_text(encoding="utf-8")
        )
        assert configuration["site_name"] == "my-project"
        assert configuration["nav"] == [
            {"Api": [{"Référence": "api/reference.md"}]},
            {"Zeta": "zeta.md"},
        ]

    def test_export_rejects_source_without_h1(self, tmp_path: Path) -> None:
        """Requirement: every navigation leaf requires a source H1."""
        source = tmp_path / "source"
        source.mkdir()
        (source / "notes.md").write_text("## Notes\n", encoding="utf-8")

        with pytest.raises(InvalidMarkdownError, match="Missing H1"):
            mkdocs_export(source, tmp_path / "output")


class TestSharedExportServices:
    """Tests for services shared by merge and MkDocs exports."""

    def test_exports_import_same_diagram_function(self) -> None:
        """Requirement: merge and MkDocs import one diagram function."""
        merge_module = importlib.import_module(
            "scribpy.core.assembly.concatenate"
        )
        mkdocs_module = importlib.import_module(
            "scribpy.core.mkdocs.markdown_exporter"
        )
        assert merge_module.render_diagram_blocks is (
            mkdocs_module.render_diagram_blocks
        )

    def test_mkdocs_package_has_no_assembly_import(self) -> None:
        """Requirement: the MkDocs package remains assembly-independent."""
        module_path = Path(__file__).parents[1] / "src/scribpy/core/mkdocs"
        imports: list[str] = []
        for path in module_path.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            imports.extend(
                node.module or ""
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom)
            )
        assert not any(
            name.startswith("scribpy.core.assembly") for name in imports
        )

    def test_assembly_reexports_shared_image_collector(self) -> None:
        """Requirement: assembly keeps one shared image collector logic."""
        assert assembly_images.collect_images is collect_images

    def test_collect_images_deduplicates_repeated_parent_names(
        self,
        tmp_path: Path,
    ) -> None:
        """Requirement: every homonymous local image gets a unique name."""
        assets = tmp_path / "assets"
        registry: dict[str, Path] = {}
        references: list[str] = []
        for prefix in ("a", "b", "c"):
            source_dir = tmp_path / prefix / "images"
            source_dir.mkdir(parents=True)
            (source_dir / "logo.png").write_bytes(prefix.encode())
            references.append(
                collect_images(
                    "![Logo](logo.png)",
                    source_dir,
                    assets,
                    "../assets",
                    registry,
                )
            )

        assert references == [
            "![Logo](../assets/logo.png)",
            "![Logo](../assets/images_logo.png)",
            "![Logo](../assets/images_2_logo.png)",
        ]
        assert sorted(path.name for path in assets.iterdir()) == [
            "images_2_logo.png",
            "images_logo.png",
            "logo.png",
        ]
