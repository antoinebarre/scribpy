"""Tests for asset collection and copy helpers."""

from pathlib import Path

from scribpy.assets.copy import (
    collect_asset_paths,
    copy_assets,
    copy_css_files_single_page,
    rewrite_asset_links_single_page,
)
from scribpy.model import Document, MarkdownAst, TransformedDocument
from scribpy.model.markdown import AssetRef
from scribpy.utils.file_utils import RealFileSystem


def _document_with_assets(
    path: str, asset_targets: list[str], source_root: Path
) -> Document:
    assets = tuple(
        AssetRef(kind="image", target=t, path=Path(t)) for t in asset_targets
    )
    return Document(
        path=source_root / path,
        relative_path=Path(path),
        source="",
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=assets,
    )


def test_collect_asset_paths_returns_local_assets(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    doc = _document_with_assets("index.md", ["img/photo.png"], source_root)

    paths = collect_asset_paths((doc,), source_root)

    assert len(paths) == 1
    assert paths[0] == (source_root / "img/photo.png").resolve()


def test_collect_asset_paths_resolves_relative_to_source_document(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "doc"
    doc = _document_with_assets("guide/page.md", ["../img/photo.png"], source_root)

    paths = collect_asset_paths((doc,), source_root)

    assert paths[0] == (source_root / "img/photo.png").resolve()


def test_collect_asset_paths_ignores_external_urls(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    assets = (
        AssetRef(kind="image", target="https://example.com/img.png", path=None),
    )
    doc = Document(
        path=source_root / "index.md",
        relative_path=Path("index.md"),
        source="",
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=assets,
    )

    paths = collect_asset_paths((doc,), source_root)

    assert paths == ()


def test_collect_asset_paths_deduplicates(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    doc1 = _document_with_assets("a.md", ["shared.png"], source_root)
    doc2 = _document_with_assets("b.md", ["shared.png"], source_root)

    paths = collect_asset_paths((doc1, doc2), source_root)

    assert len(paths) == 1


def test_collect_asset_paths_empty_documents(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    doc = _document_with_assets("index.md", [], source_root)

    paths = collect_asset_paths((doc,), source_root)

    assert paths == ()


def test_copy_assets_copies_existing_file(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    source_root.mkdir()
    img = source_root / "photo.png"
    img.write_bytes(b"PNG")

    dest_dir = tmp_path / "out"
    artifacts, diagnostics = copy_assets(
        (img,), source_root, dest_dir, RealFileSystem()
    )

    assert diagnostics == ()
    assert len(artifacts) == 1
    assert artifacts[0].target == "assets"
    assert (dest_dir / "photo.png").exists()


def test_copy_assets_warns_for_missing_file(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    source_root.mkdir()
    missing = source_root / "ghost.png"

    artifacts, diagnostics = copy_assets(
        (missing,), source_root, tmp_path / "out", RealFileSystem()
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "ASS001"
    assert diagnostics[0].severity == "warning"


def test_copy_assets_reports_write_failure(tmp_path: Path) -> None:
    source_root = tmp_path / "doc"
    source_root.mkdir()
    img = source_root / "photo.png"
    img.write_bytes(b"PNG")

    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            raise OSError("disk full")

    artifacts, diagnostics = copy_assets(
        (img,), source_root, tmp_path / "out", FailFS()
    )

    assert artifacts == ()
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "ASS002"


def test_copy_css_files_single_page_copies_file(tmp_path: Path) -> None:
    css = tmp_path / "style.css"
    css.write_text("body {}", encoding="utf-8")
    out_dir = tmp_path / "build/html"

    artifacts, diagnostics, hrefs = copy_css_files_single_page(
        tmp_path, (Path("style.css"),), out_dir, RealFileSystem()
    )

    assert diagnostics == ()
    assert (out_dir / "css/style.css").exists()
    assert hrefs == ["css/style.css"]
    assert len(artifacts) == 1
    assert artifacts[0].artifact_type == "stylesheet"


def test_copy_css_files_single_page_missing_reports_css001(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "build/html"

    artifacts, diagnostics, hrefs = copy_css_files_single_page(
        tmp_path, (Path("missing.css"),), out_dir, RealFileSystem()
    )

    assert artifacts == ()
    assert hrefs == []
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CSS001"


def test_copy_css_files_single_page_write_failure_reports_css002(
    tmp_path: Path,
) -> None:
    css = tmp_path / "style.css"
    css.write_text("body {}", encoding="utf-8")
    out_dir = tmp_path / "build/html"

    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            raise OSError("disk full")

    artifacts, diagnostics, hrefs = copy_css_files_single_page(
        tmp_path, (Path("style.css"),), out_dir, FailFS()
    )

    assert artifacts == ()
    assert hrefs == []
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "CSS002"


def test_copy_css_files_single_page_empty_list_returns_empty(
    tmp_path: Path,
) -> None:
    out_dir = tmp_path / "build/html"

    artifacts, diagnostics, hrefs = copy_css_files_single_page(
        tmp_path, (), out_dir, RealFileSystem()
    )

    assert artifacts == ()
    assert diagnostics == ()
    assert hrefs == []


def test_rewrite_asset_links_single_page_flattens_document_relative_paths(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "doc"
    doc = _document_with_assets("guide/page.md", ["../img/photo.png"], source_root)
    transformed = (
        TransformedDocument(
            relative_path=doc.relative_path,
            content="![photo](../img/photo.png)\n",
            source_document=doc,
        ),
    )

    rewritten = rewrite_asset_links_single_page(transformed, source_root)

    assert rewritten[0].content == "![photo](assets/img/photo.png)\n"


def test_collect_asset_paths_with_path_none_and_relative_target(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "doc"
    assets = (AssetRef(kind="image", target="img/photo.png", path=None),)
    doc = Document(
        path=source_root / "index.md",
        relative_path=Path("index.md"),
        source="",
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=assets,
    )

    paths = collect_asset_paths((doc,), source_root)

    assert len(paths) == 1
    assert paths[0] == (source_root / "img/photo.png").resolve()


def test_copy_assets_path_outside_source_root_uses_name(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "doc"
    source_root.mkdir()
    other_dir = tmp_path / "other"
    other_dir.mkdir()
    img = other_dir / "photo.png"
    img.write_bytes(b"PNG")

    dest_dir = tmp_path / "out"
    artifacts, diagnostics = copy_assets(
        (img,), source_root, dest_dir, RealFileSystem()
    )

    assert diagnostics == ()
    assert len(artifacts) == 1
    assert (dest_dir / "photo.png").exists()
