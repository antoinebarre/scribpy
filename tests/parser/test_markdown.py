"""Tests for the markdown-it-py adapter and parse_markdown function."""

from collections.abc import Mapping
from unittest.mock import MagicMock

from scribpy.model import MarkdownAst
from scribpy.parser import parse_markdown

# ---------------------------------------------------------------------------
# Return type and backend
# ---------------------------------------------------------------------------


def test_parse_markdown_returns_markdown_ast() -> None:
    result = parse_markdown("# Hello\n")

    assert isinstance(result, MarkdownAst)


def test_parse_markdown_backend_is_markdown_it_py() -> None:
    result = parse_markdown("# Hello\n")

    assert result.backend == "markdown-it-py"


def test_parse_markdown_tokens_are_mappings() -> None:
    result = parse_markdown("# Hello\n")

    assert len(result.tokens) > 0
    for token in result.tokens:
        assert isinstance(token, Mapping)


# ---------------------------------------------------------------------------
# Headings
# ---------------------------------------------------------------------------


def test_parse_markdown_heading_token_present() -> None:
    result = parse_markdown("# Title\n")

    types = [t["type"] for t in result.tokens]
    assert "heading_open" in types


def test_parse_markdown_heading_tag_reflects_level() -> None:
    result = parse_markdown("## Section\n")

    heading = next(t for t in result.tokens if t["type"] == "heading_open")
    assert heading["tag"] == "h2"


def test_parse_markdown_heading_inline_carries_text() -> None:
    result = parse_markdown("# My Title\n")

    inline = next(t for t in result.tokens if t["type"] == "inline")
    assert inline["content"] == "My Title"


def test_parse_markdown_heading_map_contains_line_numbers() -> None:
    result = parse_markdown("# Title\n")

    heading = next(t for t in result.tokens if t["type"] == "heading_open")
    assert heading["map"] is not None
    assert heading["map"][0] == 0  # type: ignore[index]


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


def test_parse_markdown_link_child_present() -> None:
    result = parse_markdown("A [link](https://example.com) here.\n")

    inline = next(t for t in result.tokens if t["type"] == "inline")
    children = inline.get("children", [])
    link_types = [c["type"] for c in children]  # type: ignore[union-attr]
    assert "link_open" in link_types


def test_parse_markdown_link_href_attr() -> None:
    result = parse_markdown("[click](https://example.com)\n")

    inline = next(t for t in result.tokens if t["type"] == "inline")
    link = next(c for c in inline["children"] if c["type"] == "link_open")  # type: ignore[index]
    assert link["attrs"]["href"] == "https://example.com"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Images
# ---------------------------------------------------------------------------


def test_parse_markdown_image_child_present() -> None:
    result = parse_markdown("![alt text](image.png)\n")

    inline = next(t for t in result.tokens if t["type"] == "inline")
    children = inline.get("children", [])
    types = [c["type"] for c in children]  # type: ignore[union-attr]
    assert "image" in types


def test_parse_markdown_image_src_attr() -> None:
    result = parse_markdown("![alt](assets/photo.jpg)\n")

    inline = next(t for t in result.tokens if t["type"] == "inline")
    image = next(c for c in inline["children"] if c["type"] == "image")  # type: ignore[index]
    assert image["attrs"]["src"] == "assets/photo.jpg"  # type: ignore[index]


# ---------------------------------------------------------------------------
# Fenced code blocks
# ---------------------------------------------------------------------------


def test_parse_markdown_fenced_code_token_present() -> None:
    result = parse_markdown("```python\nprint('hello')\n```\n")

    types = [t["type"] for t in result.tokens]
    assert "fence" in types


def test_parse_markdown_fenced_code_content() -> None:
    result = parse_markdown("```python\nprint('hello')\n```\n")

    fence = next(t for t in result.tokens if t["type"] == "fence")
    assert "print" in str(fence["content"])


# ---------------------------------------------------------------------------
# Empty and plain body
# ---------------------------------------------------------------------------


def test_parse_markdown_empty_body_returns_empty_tokens() -> None:
    result = parse_markdown("")

    assert result.tokens == ()


def test_parse_markdown_plain_paragraph_token_present() -> None:
    result = parse_markdown("Just a paragraph.\n")

    types = [t["type"] for t in result.tokens]
    assert "paragraph_open" in types


# ---------------------------------------------------------------------------
# Injected parser protocol
# ---------------------------------------------------------------------------


def test_parse_markdown_uses_injected_parser_when_provided() -> None:
    fake_ast = MarkdownAst(backend="fake", tokens=())
    mock_parser = MagicMock()
    mock_parser.parse.return_value = fake_ast

    result = parse_markdown("# Hello\n", parser=mock_parser)

    mock_parser.parse.assert_called_once_with("# Hello\n")
    assert result is fake_ast
    assert result.backend == "fake"


def test_parse_markdown_adapter_not_called_when_parser_injected() -> None:
    fake_ast = MarkdownAst(backend="custom", tokens=())
    mock_parser = MagicMock()
    mock_parser.parse.return_value = fake_ast

    result = parse_markdown("ignored body", parser=mock_parser)

    assert result.backend == "custom"
