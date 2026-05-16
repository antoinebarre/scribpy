"""Tests for the target-aware transform pipeline."""

from pathlib import Path

from scribpy.model import Document, Heading, MarkdownAst
from scribpy.transforms import (
    apply_transforms,
    native_html_transforms,
    TransformOptions,
    native_markdown_transforms,
)


def _document(path: str, source: str, headings: tuple[Heading, ...]) -> Document:
    return Document(
        path=Path("/project/doc") / path,
        relative_path=Path(path),
        source=source,
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=headings,
        links=(),
        assets=(),
    )


def test_markdown_transforms_number_headings_generate_toc_and_rewrite_links() -> None:
    index = _document(
        "index.md",
        "---\ntitle: Home\n---\n# Home\n\n[Guide](guide.md#setup)\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )
    guide = _document(
        "guide.md",
        "# Guide\n\n## Setup\n",
        (
            Heading(level=1, title="Guide", anchor="guide"),
            Heading(level=2, title="Setup", anchor="setup"),
        ),
    )

    result = apply_transforms(
        (index, guide),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(document_title="Manual"),
    )

    assert result.diagnostics == ()
    assert result.documents[0].content == (
        "# Manual\n\n"
        "## Table of Contents\n"
        "- [1 Home](#1-home)\n"
        "- [2 Guide](#2-guide)\n"
        "  - [2.1 Setup](#21-setup)\n\n"
        "## 1 Home\n\n"
        "[Guide](#21-setup)\n"
    )
    assert result.documents[1].content == "## 2 Guide\n\n### 2.1 Setup\n"


def test_html_transforms_rewrite_markdown_links_to_html() -> None:
    index = _document(
        "index.md",
        "# Home\n\n[Guide](guide.md#setup)\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )

    result = apply_transforms(
        (index,),
        target="html",
        transforms=native_html_transforms(),
    )

    assert "[Guide](guide.html#setup)" in result.documents[0].content


def test_transform_context_indexes_source_documents() -> None:
    from scribpy.model import TransformedDocument
    from scribpy.transforms import TransformContext

    index = _document(
        "index.md",
        "# Home\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )
    context = TransformContext(
        target="markdown",
        documents=(index,),
        transformed_documents=(TransformedDocument.from_document(index),),
    )

    assert context.source_documents_by_path == {Path("index.md"): index}


def test_target_specific_transforms_are_noops_for_other_targets() -> None:
    from scribpy.model import TransformedDocument
    from scribpy.transforms import (
        TransformContext,
        resolve_cross_references,
        rewrite_links_for_target,
    )

    index = _document(
        "index.md",
        "# Home\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )
    transformed = (TransformedDocument.from_document(index),)

    markdown_context = TransformContext(
        target="markdown",
        documents=(index,),
        transformed_documents=transformed,
    )
    html_context = TransformContext(
        target="html",
        documents=(index,),
        transformed_documents=transformed,
    )

    assert rewrite_links_for_target(markdown_context).documents == transformed
    assert resolve_cross_references(html_context).documents == transformed


def test_markdown_transforms_keep_unresolved_and_non_document_links() -> None:
    index = _document(
        "index.md",
        "# Home\n\n[Anchor](#home) [External](https://example.com) [Missing](ghost.md#x)\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )

    result = apply_transforms(
        (index,),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(document_title="Manual"),
    )

    assert "[Anchor](#home)" in result.documents[0].content
    assert "[External](https://example.com)" in result.documents[0].content
    assert "[Missing](ghost.md#x)" in result.documents[0].content


def test_toc_is_inserted_after_global_title_when_source_has_no_h1() -> None:
    index = _document(
        "index.md",
        "## Setup\n",
        (Heading(level=2, title="Setup", anchor="setup"),),
    )

    result = apply_transforms(
        (index,),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(document_title="Manual"),
    )

    assert result.documents[0].content.startswith("# Manual\n\n## Table of Contents\n")


def test_html_transforms_keep_external_and_anchor_links() -> None:
    index = _document(
        "index.md",
        "# Home\n\n[External](https://example.com) [Anchor](#home)\n",
        (Heading(level=1, title="Home", anchor="home"),),
    )

    result = apply_transforms(
        (index,),
        target="html",
        transforms=native_html_transforms(),
    )

    assert "[External](https://example.com)" in result.documents[0].content
    assert "[Anchor](#home)" in result.documents[0].content


def test_markdown_transforms_can_disable_toc_and_numbering() -> None:
    index = _document(
        "index.md",
        "# Home\n\n## Setup\n",
        (
            Heading(level=1, title="Home", anchor="home"),
            Heading(level=2, title="Setup", anchor="setup"),
        ),
    )

    result = apply_transforms(
        (index,),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(
            document_title="Manual",
            toc_enabled=False,
            numbering_enabled=False,
        ),
    )

    assert result.documents[0].content == "# Manual\n\n## Home\n\n### Setup\n"


def test_markdown_transforms_support_toc_depth_and_numbering_styles() -> None:
    index = _document(
        "index.md",
        "# Home\n\n## Setup\n\n### Deep\n",
        (
            Heading(level=1, title="Home", anchor="home"),
            Heading(level=2, title="Setup", anchor="setup"),
            Heading(level=3, title="Deep", anchor="deep"),
        ),
    )

    result = apply_transforms(
        (index,),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(
            document_title="Manual",
            toc_max_level=3,
            toc_style="numbered",
            numbering_max_level=3,
            numbering_style="alpha",
        ),
    )

    assert result.documents[0].content == (
        "# Manual\n\n"
        "## Table of Contents\n"
        "1. [A Home](#a-home)\n"
        "  1. [A.A Setup](#aa-setup)\n\n"
        "## A Home\n\n"
        "### A.A Setup\n\n"
        "#### Deep\n"
    )


def test_markdown_transforms_support_roman_numbering() -> None:
    index = _document(
        "index.md",
        "# Home\n\n## Setup\n",
        (
            Heading(level=1, title="Home", anchor="home"),
            Heading(level=2, title="Setup", anchor="setup"),
        ),
    )

    result = apply_transforms(
        (index,),
        target="markdown",
        transforms=native_markdown_transforms(),
        options=TransformOptions(
            document_title="Manual",
            numbering_style="roman",
        ),
    )

    assert "## I Home" in result.documents[0].content
    assert "### I.I Setup" in result.documents[0].content
