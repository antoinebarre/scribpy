"""Tests for Markdown assembly and artifact writing."""

from pathlib import Path

from scribpy.builders import AssembledDocument, merge_documents, write_markdown_artifact
from scribpy.model import Document, MarkdownAst, TransformedDocument
from scribpy.utils.file_utils import RealFileSystem


def _document(path: str, source: str) -> Document:
    return Document(
        path=Path("/project/doc") / path,
        relative_path=Path(path),
        source=source,
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=(),
    )


def _transformed(path: str, content: str) -> TransformedDocument:
    source = _document(path, content)
    return TransformedDocument(relative_path=Path(path), content=content, source_document=source)


def test_merge_documents_normalizes_boundaries() -> None:
    assembled = merge_documents(
        (
            _transformed("a.md", "# A\n\n"),
            _transformed("empty.md", "\n"),
            _transformed("b.md", "# B"),
        )
    )

    assert assembled == AssembledDocument(content="# A\n\n# B\n")


def test_merge_documents_returns_empty_content_for_empty_sources() -> None:
    assembled = merge_documents((_transformed("empty.md", "\n\n"),))

    assert assembled.content == ""


def test_write_markdown_artifact_creates_output(tmp_path: Path) -> None:
    artifact, diagnostics = write_markdown_artifact(
        tmp_path,
        AssembledDocument(content="# Built\n"),
        RealFileSystem(),
    )

    assert diagnostics == ()
    assert artifact is not None
    assert artifact.path == tmp_path / "build/markdown/document.md"
    assert artifact.target == "markdown"
    assert artifact.artifact_type == "document"
    assert artifact.path.read_text(encoding="utf-8") == "# Built\n"


def test_write_markdown_artifact_reports_write_failures(tmp_path: Path) -> None:
    class FailingFileSystem(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            raise OSError("read-only")

    artifact, diagnostics = write_markdown_artifact(
        tmp_path,
        AssembledDocument(content="# Built\n"),
        FailingFileSystem(),
    )

    assert artifact is None
    assert [diagnostic.code for diagnostic in diagnostics] == ["BLD003"]
