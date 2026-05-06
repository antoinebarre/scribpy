"""Tests for parse_project_documents (étape 6 — ADR-0002)."""

from __future__ import annotations

from pathlib import Path

from scribpy.core import parse_project_documents
from scribpy.model import ParseResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_config(root: Path, content: str) -> Path:
    config_path = root / "scribpy.toml"
    config_path.write_text(content, encoding="utf-8")
    return config_path


def _write_source(root: Path, relative_path: str, content: str = "# Title\n") -> Path:
    source_path = root / relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(content, encoding="utf-8")
    return source_path


def _codes(result: ParseResult) -> tuple[str, ...]:
    return tuple(d.code for d in result.diagnostics)


# ---------------------------------------------------------------------------
# Happy path — filesystem index
# ---------------------------------------------------------------------------


class TestParseProjectDocumentsSuccess:
    def test_returns_parse_result(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md")

        result = parse_project_documents(tmp_path)

        assert isinstance(result, ParseResult)

    def test_single_file_is_parsed(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md", "# Index\n\nBody.\n")

        result = parse_project_documents(tmp_path)

        assert result.failed is False
        assert len(result.documents) == 1

    def test_document_title_extracted(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md", "# My Title\n\nBody.\n")

        result = parse_project_documents(tmp_path)

        assert result.documents[0].title == "My Title"

    def test_multiple_files_parsed_in_index_order(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/a.md", "# A\n")
        _write_source(tmp_path, "doc/b.md", "# B\n")
        _write_source(tmp_path, "doc/c.md", "# C\n")

        result = parse_project_documents(tmp_path)

        assert result.failed is False
        assert len(result.documents) == 3
        titles = [d.title for d in result.documents]
        assert titles == ["A", "B", "C"]

    def test_accepts_direct_config_path(self, tmp_path: Path) -> None:
        config_path = _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md")

        result = parse_project_documents(config_path)

        assert result.failed is False
        assert len(result.documents) == 1

    def test_accepts_path_inside_project(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md")

        result = parse_project_documents(tmp_path / "doc")

        assert result.failed is False

    def test_explicit_index_order_respected(self, tmp_path: Path) -> None:
        _write_config(
            tmp_path,
            '[paths]\nsource = "doc"\n\n[index]\nmode = "explicit"\nfiles = ["b.md", "a.md"]\n',
        )
        _write_source(tmp_path, "doc/a.md", "# A\n")
        _write_source(tmp_path, "doc/b.md", "# B\n")

        result = parse_project_documents(tmp_path)

        assert result.failed is False
        assert [d.title for d in result.documents] == ["B", "A"]

    def test_yaml_frontmatter_preserved(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md", "---\nauthor: Alice\n---\n# Doc\n")

        result = parse_project_documents(tmp_path)

        assert result.documents[0].frontmatter["author"] == "Alice"

    def test_links_and_assets_extracted(self, tmp_path: Path) -> None:
        content = "# T\n\nSee [ref](https://example.com).\n\n![img](img.png)\n"
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md", content)

        result = parse_project_documents(tmp_path)

        doc = result.documents[0]
        assert len(doc.links) == 1
        assert len(doc.assets) == 1

    def test_no_diagnostics_for_valid_project(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md")

        result = parse_project_documents(tmp_path)

        assert result.diagnostics == ()


# ---------------------------------------------------------------------------
# Error paths — config / scan / index failures
# ---------------------------------------------------------------------------


class TestParseProjectDocumentsErrors:
    def test_cfg001_when_no_config(self, tmp_path: Path) -> None:
        result = parse_project_documents(tmp_path)

        assert result.failed is True
        assert "CFG001" in _codes(result)

    def test_cfg001_for_missing_direct_config_path(self, tmp_path: Path) -> None:
        result = parse_project_documents(tmp_path / "scribpy.toml")

        assert result.failed is True
        assert "CFG001" in _codes(result)

    def test_stops_on_invalid_config(self, tmp_path: Path) -> None:
        _write_config(tmp_path, "[paths]\nsource = 42\n")

        result = parse_project_documents(tmp_path)

        assert result.failed is True
        assert "CFG003" in _codes(result)
        assert result.documents == ()

    def test_stops_on_missing_source_dir(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "missing"\n')

        result = parse_project_documents(tmp_path)

        assert result.failed is True
        assert "PRJ001" in _codes(result)
        assert result.documents == ()

    def test_failed_true_when_index_entry_missing_from_sources(
        self, tmp_path: Path
    ) -> None:
        _write_config(
            tmp_path,
            '[paths]\nsource = "doc"\n\n[index]\nmode = "explicit"\nfiles = ["ghost.md"]\n',
        )
        (tmp_path / "doc").mkdir()

        result = parse_project_documents(tmp_path)

        assert result.failed is True

    def test_prs002_warning_does_not_set_failed(self, tmp_path: Path) -> None:
        _write_config(tmp_path, '[paths]\nsource = "doc"\n')
        _write_source(tmp_path, "doc/index.md", "---\nbad: [unclosed\n---\n# T\n")

        result = parse_project_documents(tmp_path)

        assert result.failed is False
        assert any(d.code == "PRS002" for d in result.diagnostics)
        assert len(result.documents) == 1
