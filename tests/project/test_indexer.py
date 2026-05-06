"""Tests for document index construction and validation."""

from pathlib import Path

from scribpy.config.types import Config, IndexConfig
from scribpy.model import DocumentIndex, SourceFile
from scribpy.project.indexer import build_document_index, validate_document_index


def test_build_document_index_uses_filesystem_scan_order() -> None:
    files = _source_files("intro.md", "guide/setup.md", "z.md")

    index, diagnostics = build_document_index(Config(), files)

    assert diagnostics == ()
    assert index == DocumentIndex(
        paths=(Path("intro.md"), Path("guide/setup.md"), Path("z.md")),
        mode="filesystem",
    )


def test_build_document_index_uses_explicit_config_order() -> None:
    files = _source_files("intro.md", "guide/setup.md", "z.md")
    config = Config(
        index=IndexConfig(
            mode="explicit",
            files=(Path("z.md"), Path("intro.md"), Path("guide/setup.md")),
        )
    )

    index, diagnostics = build_document_index(config, files)

    assert diagnostics == ()
    assert index == DocumentIndex(
        paths=(Path("z.md"), Path("intro.md"), Path("guide/setup.md")),
        mode="explicit",
    )


def test_build_document_index_returns_idx001_for_hybrid_mode() -> None:
    config = Config(index=IndexConfig(mode="hybrid"))

    index, diagnostics = build_document_index(config, _source_files("intro.md"))

    assert index is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IDX001"
    assert diagnostics[0].severity == "error"


def test_validate_document_index_returns_idx001_for_unsupported_mode() -> None:
    diagnostics = validate_document_index(
        DocumentIndex(paths=(), mode="hybrid"),
        _source_files("intro.md"),
    )

    assert len(diagnostics) == 1
    assert diagnostics[0].code == "IDX001"
    assert diagnostics[0].severity == "error"


def test_validate_document_index_returns_idx002_for_missing_explicit_file() -> None:
    index = DocumentIndex(
        paths=(Path("intro.md"), Path("missing.md")),
        mode="explicit",
    )

    diagnostics = validate_document_index(index, _source_files("intro.md"))

    assert _diagnostic_codes(diagnostics) == ("IDX002",)
    assert diagnostics[0].path == Path("missing.md")


def test_validate_document_index_returns_idx003_for_duplicate_entries() -> None:
    index = DocumentIndex(
        paths=(Path("intro.md"), Path("intro.md")),
        mode="explicit",
    )

    diagnostics = validate_document_index(index, _source_files("intro.md"))

    assert _diagnostic_codes(diagnostics) == ("IDX003",)
    assert diagnostics[0].path == Path("intro.md")


def test_validate_document_index_returns_idx004_for_unsafe_entries() -> None:
    index = DocumentIndex(
        paths=(Path("/abs.md"), Path("../outside.md")),
        mode="explicit",
    )

    diagnostics = validate_document_index(index, _source_files("intro.md"))

    assert _diagnostic_codes(diagnostics) == ("IDX004", "IDX004", "IDX005")
    assert tuple(diagnostic.path for diagnostic in diagnostics[:2]) == (
        Path("/abs.md"),
        Path("../outside.md"),
    )


def test_validate_document_index_returns_idx005_for_uncovered_discovered_file() -> None:
    index = DocumentIndex(paths=(Path("intro.md"),), mode="explicit")

    diagnostics = validate_document_index(
        index,
        _source_files("intro.md", "guide/setup.md"),
    )

    assert _diagnostic_codes(diagnostics) == ("IDX005",)
    assert diagnostics[0].severity == "warning"
    assert diagnostics[0].path == Path("guide/setup.md")


def test_filesystem_index_validation_does_not_warn_about_discovered_files() -> None:
    index = DocumentIndex(paths=(Path("intro.md"),), mode="filesystem")

    diagnostics = validate_document_index(
        index,
        _source_files("intro.md", "guide/setup.md"),
    )

    assert diagnostics == ()


def _source_files(*relative_paths: str) -> tuple[SourceFile, ...]:
    return tuple(
        SourceFile(
            path=Path("/project/doc") / relative_path,
            relative_path=Path(relative_path),
        )
        for relative_path in relative_paths
    )


def _diagnostic_codes(diagnostics: tuple[object, ...]) -> tuple[str, ...]:
    return tuple(getattr(diagnostic, "code") for diagnostic in diagnostics)
