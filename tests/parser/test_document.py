"""Tests for parse_document_file and parse_documents (étape 5 — ADR-0002)."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from scribpy.model import Document, DocumentIndex, ParseResult, SourceFile
from scribpy.model.protocols import FileSystem
from scribpy.parser import order_by_index, parse_document_file, parse_documents


# ---------------------------------------------------------------------------
# Test doubles
# ---------------------------------------------------------------------------


class InMemoryFileSystem:
    """Minimal FileSystem backed by an in-memory dict."""

    def __init__(self, files: dict[str, str]) -> None:
        self._files = files

    def read_text(self, path: Path) -> str:
        key = str(path)
        if key not in self._files:
            raise FileNotFoundError(f"No such file: {path}")
        return self._files[key]

    def write_text(self, path: Path, content: str) -> None:
        self._files[str(path)] = content

    def exists(self, path: Path) -> bool:
        return str(path) in self._files

    def glob(self, root: Path, pattern: str) -> Iterable[Path]:
        return []


def _source(relative: str, content: str) -> tuple[SourceFile, InMemoryFileSystem]:
    """Build a SourceFile + matching InMemoryFileSystem for one file."""
    abs_path = Path("/project") / relative
    fs = InMemoryFileSystem({str(abs_path): content})
    sf = SourceFile(path=abs_path, relative_path=Path(relative))
    return sf, fs


# ---------------------------------------------------------------------------
# parse_document_file — happy paths
# ---------------------------------------------------------------------------


class TestParseDocumentFileHappyPath:
    def test_returns_document_on_valid_file(self) -> None:
        sf, fs = _source("index.md", "# Hello\n\nBody.\n")
        doc, diags = parse_document_file(sf, fs)
        assert isinstance(doc, Document)
        assert diags == ()

    def test_document_paths_match_source_file(self) -> None:
        sf, fs = _source("docs/guide.md", "# Guide\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.path == sf.path
        assert doc.relative_path == sf.relative_path

    def test_source_field_contains_raw_text(self) -> None:
        content = "# Title\n\nSome body.\n"
        sf, fs = _source("a.md", content)
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.source == content

    def test_ast_is_populated(self) -> None:
        sf, fs = _source("a.md", "# Title\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert len(doc.ast.tokens) > 0

    # Title resolution
    def test_title_from_frontmatter(self) -> None:
        sf, fs = _source("a.md", "---\ntitle: FM Title\n---\n# H1 Title\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.title == "FM Title"

    def test_title_from_first_h1_when_no_frontmatter(self) -> None:
        sf, fs = _source("a.md", "# My H1\n\nBody.\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.title == "My H1"

    def test_title_is_none_when_no_frontmatter_and_no_h1(self) -> None:
        sf, fs = _source("a.md", "## Only H2\n\nBody.\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.title is None

    # Frontmatter
    def test_yaml_frontmatter_parsed(self) -> None:
        sf, fs = _source("a.md", "---\nauthor: Alice\nversion: 2\n---\n# T\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.frontmatter["author"] == "Alice"
        assert doc.frontmatter["version"] == 2

    def test_toml_frontmatter_parsed(self) -> None:
        sf, fs = _source("a.md", '+++\nauthor = "Bob"\n+++\n# T\n')
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.frontmatter["author"] == "Bob"

    def test_no_frontmatter_gives_empty_dict(self) -> None:
        sf, fs = _source("a.md", "# Title\n\nBody.\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.frontmatter == {}

    # Semantic extraction
    def test_headings_extracted(self) -> None:
        sf, fs = _source("a.md", "# H1\n\n## H2\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert len(doc.headings) == 2
        assert doc.headings[0].level == 1
        assert doc.headings[1].level == 2

    def test_links_extracted(self) -> None:
        sf, fs = _source("a.md", "See [example](https://example.com).\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert len(doc.links) == 1
        assert doc.links[0].target == "https://example.com"

    def test_assets_extracted(self) -> None:
        sf, fs = _source("a.md", "![logo](assets/logo.png)\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert len(doc.assets) == 1
        assert doc.assets[0].target == "assets/logo.png"

    def test_no_links_and_no_assets_in_plain_document(self) -> None:
        sf, fs = _source("a.md", "# Title\n\nJust text.\n")
        doc, _ = parse_document_file(sf, fs)
        assert doc is not None
        assert doc.links == ()
        assert doc.assets == ()


# ---------------------------------------------------------------------------
# parse_document_file — error paths
# ---------------------------------------------------------------------------


class TestParseDocumentFileErrors:
    def test_unreadable_file_returns_none_document(self) -> None:
        sf = SourceFile(path=Path("/missing/file.md"), relative_path=Path("file.md"))
        fs = InMemoryFileSystem({})
        doc, diags = parse_document_file(sf, fs)
        assert doc is None

    def test_unreadable_file_emits_prs001(self) -> None:
        sf = SourceFile(path=Path("/missing/file.md"), relative_path=Path("file.md"))
        fs = InMemoryFileSystem({})
        _, diags = parse_document_file(sf, fs)
        assert len(diags) == 1
        assert diags[0].code == "PRS001"
        assert diags[0].severity == "error"
        assert diags[0].path == sf.path

    def test_invalid_yaml_frontmatter_emits_prs002_and_returns_document(self) -> None:
        sf, fs = _source("a.md", "---\nkey: [unclosed\n---\n# Title\n")
        doc, diags = parse_document_file(sf, fs)
        # PRS002 is non-blocking: document is returned with empty frontmatter
        assert doc is not None
        assert any(d.code == "PRS002" for d in diags)
        assert doc.frontmatter == {}

    def test_invalid_toml_frontmatter_emits_prs002_and_returns_document(self) -> None:
        sf, fs = _source("a.md", "+++\nnot valid toml !!!\n+++\n# Title\n")
        doc, diags = parse_document_file(sf, fs)
        assert doc is not None
        assert any(d.code == "PRS002" for d in diags)
        assert doc.frontmatter == {}

    def test_unclosed_frontmatter_block_returns_document_with_empty_frontmatter(self) -> None:
        sf, fs = _source("a.md", "---\ntitle: Broken\n# Title\n")
        doc, diags = parse_document_file(sf, fs)
        assert doc is not None
        assert any(d.code == "PRS002" for d in diags)
        assert doc.frontmatter == {}

    def test_prs003_emitted_when_parser_raises(self) -> None:
        class BrokenParser:
            def parse(self, source: str):  # noqa: ANN001, ANN201
                raise RuntimeError("parser exploded")

        sf, fs = _source("a.md", "# Title\n")
        doc, diags = parse_document_file(sf, fs, parser=BrokenParser())  # type: ignore[arg-type]
        assert doc is None
        assert len(diags) == 1
        assert diags[0].code == "PRS003"
        assert diags[0].severity == "error"
        assert diags[0].path == sf.path


# ---------------------------------------------------------------------------
# parse_documents — batch parsing
# ---------------------------------------------------------------------------


class TestParseDocuments:
    def _make_fs_and_files(
        self, entries: list[tuple[str, str]]
    ) -> tuple[InMemoryFileSystem, list[SourceFile]]:
        files: dict[str, str] = {}
        source_files: list[SourceFile] = []
        for relative, content in entries:
            abs_path = Path("/project") / relative
            files[str(abs_path)] = content
            source_files.append(SourceFile(path=abs_path, relative_path=Path(relative)))
        return InMemoryFileSystem(files), source_files

    def test_returns_parse_result(self) -> None:
        fs, sfs = self._make_fs_and_files([("a.md", "# A\n")])
        result = parse_documents(sfs, fs)
        assert isinstance(result, ParseResult)

    def test_all_valid_files_parsed(self) -> None:
        fs, sfs = self._make_fs_and_files(
            [("a.md", "# A\n"), ("b.md", "# B\n"), ("c.md", "# C\n")]
        )
        result = parse_documents(sfs, fs)
        assert len(result.documents) == 3
        assert result.failed is False
        assert result.diagnostics == ()

    def test_order_preserved(self) -> None:
        fs, sfs = self._make_fs_and_files(
            [("first.md", "# First\n"), ("second.md", "# Second\n"), ("third.md", "# Third\n")]
        )
        result = parse_documents(sfs, fs)
        assert [d.relative_path for d in result.documents] == [
            Path("first.md"),
            Path("second.md"),
            Path("third.md"),
        ]

    def test_missing_file_excluded_from_documents(self) -> None:
        fs, sfs = self._make_fs_and_files([("a.md", "# A\n")])
        missing = SourceFile(path=Path("/project/missing.md"), relative_path=Path("missing.md"))
        result = parse_documents([sfs[0], missing], fs)
        assert len(result.documents) == 1
        assert result.documents[0].relative_path == Path("a.md")

    def test_missing_file_sets_failed(self) -> None:
        missing = SourceFile(path=Path("/project/x.md"), relative_path=Path("x.md"))
        result = parse_documents([missing], InMemoryFileSystem({}))
        assert result.failed is True

    def test_missing_file_produces_prs001_diagnostic(self) -> None:
        missing = SourceFile(path=Path("/project/x.md"), relative_path=Path("x.md"))
        result = parse_documents([missing], InMemoryFileSystem({}))
        assert any(d.code == "PRS001" for d in result.diagnostics)

    def test_valid_files_still_parsed_when_one_missing(self) -> None:
        fs, sfs = self._make_fs_and_files([("a.md", "# A\n"), ("b.md", "# B\n")])
        missing = SourceFile(path=Path("/project/x.md"), relative_path=Path("x.md"))
        result = parse_documents([sfs[0], missing, sfs[1]], fs)
        assert len(result.documents) == 2
        assert result.failed is True

    def test_empty_list_returns_empty_result(self) -> None:
        result = parse_documents([], InMemoryFileSystem({}))
        assert result.documents == ()
        assert result.diagnostics == ()
        assert result.failed is False

    def test_diagnostics_aggregated_across_files(self) -> None:
        fs, sfs = self._make_fs_and_files(
            [
                ("a.md", "---\nkey: [unclosed\n---\n# A\n"),
                ("b.md", "---\nkey: [unclosed\n---\n# B\n"),
            ]
        )
        result = parse_documents(sfs, fs)
        prs002 = [d for d in result.diagnostics if d.code == "PRS002"]
        assert len(prs002) == 2

    def test_injected_parser_used_for_all_files(self) -> None:
        from unittest.mock import MagicMock

        from scribpy.model.markdown import MarkdownAst

        fake_ast = MarkdownAst(backend="fake", tokens=())
        mock_parser = MagicMock()
        mock_parser.parse.return_value = fake_ast

        fs, sfs = self._make_fs_and_files([("a.md", "# A\n"), ("b.md", "# B\n")])
        result = parse_documents(sfs, fs, parser=mock_parser)

        assert mock_parser.parse.call_count == 2
        for doc in result.documents:
            assert doc.ast.backend == "fake"

    def test_full_document_chain_with_yaml_frontmatter(self) -> None:
        content = "---\ntitle: Guide\nauthor: Alice\n---\n# Guide\n\nSee [docs](https://docs.example.com).\n\n![logo](assets/logo.png)\n"
        fs, sfs = self._make_fs_and_files([("guide.md", content)])
        result = parse_documents(sfs, fs)

        assert result.failed is False
        doc = result.documents[0]
        assert doc.title == "Guide"
        assert doc.frontmatter["author"] == "Alice"
        assert len(doc.headings) == 1
        assert doc.headings[0].anchor == "guide"
        assert len(doc.links) == 1
        assert len(doc.assets) == 1


# ===========================================================================
# order_by_index
# ===========================================================================


class TestOrderByIndex:
    def _sf(self, relative: str) -> SourceFile:
        return SourceFile(
            path=Path("/project") / relative,
            relative_path=Path(relative),
        )

    def test_returns_files_in_index_order(self) -> None:
        sfs = (self._sf("a.md"), self._sf("b.md"), self._sf("c.md"))
        index = DocumentIndex(paths=(Path("c.md"), Path("a.md"), Path("b.md")), mode="explicit")

        ordered, diags = order_by_index(index, sfs)

        assert [sf.relative_path for sf in ordered] == [Path("c.md"), Path("a.md"), Path("b.md")]
        assert diags == ()

    def test_missing_index_entry_produces_prs001(self) -> None:
        sfs = (self._sf("a.md"),)
        index = DocumentIndex(paths=(Path("a.md"), Path("ghost.md")), mode="explicit")

        ordered, diags = order_by_index(index, sfs)

        assert len(ordered) == 1
        assert ordered[0].relative_path == Path("a.md")
        assert len(diags) == 1
        assert diags[0].code == "PRS001"
        assert diags[0].path == Path("ghost.md")

    def test_empty_index_returns_empty_list(self) -> None:
        sfs = (self._sf("a.md"),)
        index = DocumentIndex(paths=(), mode="explicit")

        ordered, diags = order_by_index(index, sfs)

        assert ordered == []
        assert diags == ()

    def test_empty_source_files_produces_diagnostic_for_each_index_entry(self) -> None:
        index = DocumentIndex(paths=(Path("a.md"), Path("b.md")), mode="explicit")

        ordered, diags = order_by_index(index, ())

        assert ordered == []
        assert len(diags) == 2

    def test_filesystem_index_order_preserved(self) -> None:
        sfs = (self._sf("a.md"), self._sf("b.md"))
        index = DocumentIndex(paths=(Path("b.md"), Path("a.md")), mode="filesystem")

        ordered, diags = order_by_index(index, sfs)

        assert [sf.relative_path for sf in ordered] == [Path("b.md"), Path("a.md")]
        assert diags == ()
