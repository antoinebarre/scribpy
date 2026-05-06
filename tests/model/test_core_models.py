"""Tests for core scribpy.model dataclasses."""

from dataclasses import FrozenInstanceError, is_dataclass
from pathlib import Path

import pytest

from scribpy.model import (
    AssetRef,
    Diagnostic,
    Document,
    DocumentIndex,
    Heading,
    MarkdownAst,
    Project,
    Reference,
    SourceFile,
)


def test_model_objects_are_frozen_dataclasses() -> None:
    model_types = (
        AssetRef,
        Diagnostic,
        Document,
        DocumentIndex,
        Heading,
        MarkdownAst,
        Project,
        Reference,
        SourceFile,
    )

    for model_type in model_types:
        assert is_dataclass(model_type)
        assert model_type.__dataclass_params__.frozen is True


def test_source_file_stores_paths_without_filesystem_access() -> None:
    source_file = SourceFile(
        path=Path("/project/docs/index.md"),
        relative_path=Path("docs/index.md"),
    )

    assert source_file.path == Path("/project/docs/index.md")
    assert source_file.relative_path == Path("docs/index.md")

    with pytest.raises(FrozenInstanceError):
        source_file.path = Path("other.md")


def test_document_index_uses_immutable_path_collection() -> None:
    index = DocumentIndex(
        paths=(Path("docs/index.md"), Path("docs/usage.md")),
        mode="explicit",
    )

    assert index.paths == (Path("docs/index.md"), Path("docs/usage.md"))
    assert index.mode == "explicit"


def test_markdown_nodes_store_parser_and_extraction_data() -> None:
    ast = MarkdownAst(
        backend="markdown-it-py",
        tokens=({"type": "heading_open", "level": 1},),
    )
    heading = Heading(level=1, title="Overview", anchor="overview", line=1)
    reference = Reference(
        kind="link",
        target="usage.md",
        text="Usage",
        path=Path("docs/usage.md"),
        line=8,
    )
    asset = AssetRef(
        kind="image",
        target="assets/logo.png",
        path=Path("docs/assets/logo.png"),
        title="Logo",
        line=12,
    )

    assert ast.tokens == ({"type": "heading_open", "level": 1},)
    assert heading.anchor == "overview"
    assert reference.path == Path("docs/usage.md")
    assert asset.title == "Logo"


def test_document_composes_markdown_data_with_immutable_collections() -> None:
    ast = MarkdownAst(backend="test", tokens=())
    heading = Heading(level=1, title="Title")
    reference = Reference(kind="xref", target="#title")
    asset = AssetRef(kind="static", target="style.css")

    document = Document(
        path=Path("/project/docs/index.md"),
        relative_path=Path("docs/index.md"),
        source="# Title",
        frontmatter={"title": "Title"},
        ast=ast,
        title="Title",
        headings=(heading,),
        links=(reference,),
        assets=(asset,),
    )

    assert document.ast == ast
    assert document.title == "Title"
    assert document.headings == (heading,)
    assert document.links == (reference,)
    assert document.assets == (asset,)


def test_project_composes_sources_and_optional_index() -> None:
    source_file = SourceFile(
        path=Path("/project/docs/index.md"),
        relative_path=Path("docs/index.md"),
    )
    index = DocumentIndex(paths=(source_file.relative_path,), mode="filesystem")

    project = Project(
        root=Path("/project"),
        config={"project": {"name": "scribpy"}},
        source_files=(source_file,),
        index=index,
    )

    assert project.root == Path("/project")
    assert project.source_files == (source_file,)
    assert project.index == index
