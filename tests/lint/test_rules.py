"""Tests for native lint rules."""

from pathlib import Path

from scribpy.lint import LintContext, run_lint_rules
from scribpy.lint.rules import (
    BrokenInternalLinkRule,
    HeadingHierarchyRule,
    MissingH1Rule,
    MissingLocalAssetRule,
)
from scribpy.model import Document, DocumentIndex
from scribpy.parser import parse_document_file
from scribpy.model import SourceFile
from scribpy.utils.file_utils import RealFileSystem


def _document(root: Path, relative_path: str, content: str) -> Document:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    document, diagnostics = parse_document_file(
        SourceFile(path=path, relative_path=Path(relative_path)),
        RealFileSystem(),
    )
    assert diagnostics == ()
    assert document is not None
    return document


def _context(root: Path, *documents: Document) -> LintContext:
    return LintContext(
        source_root=root,
        documents=documents,
        document_index=DocumentIndex(
            paths=tuple(document.relative_path for document in documents),
            mode="filesystem",
        ),
    )


def test_missing_h1_rule_reports_document_without_h1(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "## Section\n")

    result = run_lint_rules(_context(tmp_path, document), (MissingH1Rule(),))

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT001"]
    assert result.failed is True


def test_heading_hierarchy_rule_reports_jump(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "# Title\n\n### Too deep\n")

    result = run_lint_rules(_context(tmp_path, document), (HeadingHierarchyRule(),))

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT002"]
    assert result.diagnostics[0].line == 3


def test_broken_internal_link_rule_accepts_valid_document_anchor(
    tmp_path: Path,
) -> None:
    current = _document(tmp_path, "index.md", "# Home\n\n[Guide](guide.md#setup)\n")
    target = _document(tmp_path, "guide.md", "# Guide\n\n## Setup\n")

    result = run_lint_rules(
        _context(tmp_path, current, target),
        (BrokenInternalLinkRule(),),
    )

    assert result.diagnostics == ()


def test_broken_internal_link_rule_reports_missing_anchor(tmp_path: Path) -> None:
    current = _document(tmp_path, "index.md", "# Home\n\n[Guide](guide.md#missing)\n")
    target = _document(tmp_path, "guide.md", "# Guide\n\n## Setup\n")

    result = run_lint_rules(
        _context(tmp_path, current, target),
        (BrokenInternalLinkRule(),),
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT003"]


def test_broken_internal_link_rule_reports_missing_document(tmp_path: Path) -> None:
    current = _document(tmp_path, "index.md", "# Home\n\n[Missing](ghost.md)\n")

    result = run_lint_rules(
        _context(tmp_path, current),
        (BrokenInternalLinkRule(),),
    )

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT003"]


def test_broken_internal_link_rule_accepts_external_link(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "# Home\n\n[Site](https://example.com)\n")

    result = run_lint_rules(_context(tmp_path, document), (BrokenInternalLinkRule(),))

    assert result.diagnostics == ()


def test_broken_internal_link_rule_accepts_local_anchor(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "# Home\n\n[Self](#home)\n")

    result = run_lint_rules(_context(tmp_path, document), (BrokenInternalLinkRule(),))

    assert result.diagnostics == ()


def test_broken_internal_link_rule_rejects_path_outside_source_tree(
    tmp_path: Path,
) -> None:
    document = _document(tmp_path, "index.md", "# Home\n\n[Outside](../README.md)\n")

    result = run_lint_rules(_context(tmp_path, document), (BrokenInternalLinkRule(),))

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT003"]


def test_missing_local_asset_rule_reports_missing_file(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "# Home\n\n![Logo](assets/logo.png)\n")

    result = run_lint_rules(_context(tmp_path, document), (MissingLocalAssetRule(),))

    assert [diagnostic.code for diagnostic in result.diagnostics] == ["LINT004"]


def test_missing_local_asset_rule_accepts_existing_file(tmp_path: Path) -> None:
    document = _document(tmp_path, "index.md", "# Home\n\n![Logo](assets/logo.png)\n")
    asset = tmp_path / "assets/logo.png"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"png")

    result = run_lint_rules(_context(tmp_path, document), (MissingLocalAssetRule(),))

    assert result.diagnostics == ()


def test_missing_local_asset_rule_accepts_external_asset(tmp_path: Path) -> None:
    document = _document(
        tmp_path,
        "index.md",
        "# Home\n\n![Logo](https://example.com/logo.png)\n",
    )

    result = run_lint_rules(_context(tmp_path, document), (MissingLocalAssetRule(),))

    assert result.diagnostics == ()
