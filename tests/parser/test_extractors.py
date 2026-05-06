"""Tests for semantic extractors: extract_headings, extract_links, extract_assets."""

from pathlib import Path

from scribpy.model.markdown import AssetRef, Heading, MarkdownAst, Reference
from scribpy.parser import (
    extract_assets,
    extract_headings,
    extract_links,
    parse_markdown,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ast(markdown: str):
    return parse_markdown(markdown)


# ===========================================================================
# extract_headings
# ===========================================================================


class TestExtractHeadings:
    def test_single_h1(self) -> None:
        ast = _ast("# My Title\n")
        headings = extract_headings(ast)
        assert len(headings) == 1
        assert headings[0].level == 1
        assert headings[0].title == "My Title"

    def test_h2_level(self) -> None:
        ast = _ast("## Section\n")
        headings = extract_headings(ast)
        assert headings[0].level == 2

    def test_h6_level(self) -> None:
        ast = _ast("###### Deep\n")
        headings = extract_headings(ast)
        assert headings[0].level == 6

    def test_multiple_headings_order(self) -> None:
        ast = _ast("# First\n\n## Second\n\n### Third\n")
        headings = extract_headings(ast)
        assert len(headings) == 3
        assert [h.level for h in headings] == [1, 2, 3]
        assert [h.title for h in headings] == ["First", "Second", "Third"]

    def test_anchor_lowercase(self) -> None:
        ast = _ast("# Hello World\n")
        headings = extract_headings(ast)
        assert headings[0].anchor == "hello-world"

    def test_anchor_strips_punctuation(self) -> None:
        ast = _ast("# Hello, World!\n")
        headings = extract_headings(ast)
        assert headings[0].anchor == "hello-world"

    def test_anchor_multiple_spaces_become_single_hyphen(self) -> None:
        ast = _ast("# A  B\n")
        headings = extract_headings(ast)
        assert headings[0].anchor == "a-b"

    def test_anchor_github_compatible_special_chars(self) -> None:
        # Parentheses and dots are stripped
        ast = _ast("# Setup (v1.0)\n")
        headings = extract_headings(ast)
        assert headings[0].anchor == "setup-v10"

    def test_line_number_is_one_based(self) -> None:
        ast = _ast("# Title\n")
        headings = extract_headings(ast)
        assert headings[0].line == 1

    def test_line_number_second_heading(self) -> None:
        ast = _ast("# First\n\n## Second\n")
        headings = extract_headings(ast)
        assert headings[1].line == 3

    def test_empty_ast_returns_empty_tuple(self) -> None:
        ast = _ast("")
        assert extract_headings(ast) == ()

    def test_no_headings_in_plain_text(self) -> None:
        ast = _ast("Just a paragraph.\n")
        assert extract_headings(ast) == ()

    def test_returns_tuple_of_heading(self) -> None:
        ast = _ast("# Title\n")
        headings = extract_headings(ast)
        assert isinstance(headings, tuple)
        assert isinstance(headings[0], Heading)


# ===========================================================================
# extract_links
# ===========================================================================


class TestExtractLinks:
    def test_single_external_link(self) -> None:
        ast = _ast("[click](https://example.com)\n")
        refs = extract_links(ast)
        assert len(refs) == 1
        assert refs[0].kind == "link"
        assert refs[0].target == "https://example.com"

    def test_link_text(self) -> None:
        ast = _ast("[click here](https://example.com)\n")
        refs = extract_links(ast)
        assert refs[0].text == "click here"

    def test_anchor_link_is_xref(self) -> None:
        ast = _ast("[section](#my-anchor)\n")
        refs = extract_links(ast)
        assert refs[0].kind == "xref"
        assert refs[0].target == "#my-anchor"

    def test_relative_link_has_path(self) -> None:
        ast = _ast("[doc](../other.md)\n")
        refs = extract_links(ast)
        assert refs[0].path == Path("../other.md")

    def test_external_link_has_no_path(self) -> None:
        ast = _ast("[ext](https://example.com)\n")
        refs = extract_links(ast)
        assert refs[0].path is None

    def test_multiple_links_order(self) -> None:
        ast = _ast("[a](https://a.com) and [b](https://b.com)\n")
        refs = extract_links(ast)
        assert len(refs) == 2
        assert refs[0].target == "https://a.com"
        assert refs[1].target == "https://b.com"

    def test_images_not_included(self) -> None:
        ast = _ast("![img](photo.png)\n")
        refs = extract_links(ast)
        assert refs == ()

    def test_empty_ast_returns_empty_tuple(self) -> None:
        ast = _ast("")
        assert extract_links(ast) == ()

    def test_plain_paragraph_returns_empty(self) -> None:
        ast = _ast("No links here.\n")
        assert extract_links(ast) == ()

    def test_returns_tuple_of_reference(self) -> None:
        ast = _ast("[x](https://x.com)\n")
        refs = extract_links(ast)
        assert isinstance(refs, tuple)
        assert isinstance(refs[0], Reference)

    def test_ftp_link_has_no_path(self) -> None:
        ast = _ast("[ftp](ftp://files.example.com)\n")
        refs = extract_links(ast)
        assert refs[0].path is None

    def test_mailto_link_has_no_path(self) -> None:
        ast = _ast("[mail](mailto:a@b.com)\n")
        refs = extract_links(ast)
        assert refs[0].path is None


# ===========================================================================
# extract_assets
# ===========================================================================


class TestExtractAssets:
    def test_single_image(self) -> None:
        ast = _ast("![alt text](image.png)\n")
        assets = extract_assets(ast)
        assert len(assets) == 1
        assert assets[0].kind == "image"
        assert assets[0].target == "image.png"

    def test_image_alt_as_title(self) -> None:
        ast = _ast("![my alt](photo.jpg)\n")
        assets = extract_assets(ast)
        assert assets[0].title == "my alt"

    def test_image_no_alt_title_is_none(self) -> None:
        ast = _ast("![](photo.jpg)\n")
        assets = extract_assets(ast)
        assert assets[0].title is None

    def test_local_image_has_path(self) -> None:
        ast = _ast("![x](assets/img.png)\n")
        assets = extract_assets(ast)
        assert assets[0].path == Path("assets/img.png")

    def test_external_image_has_no_path(self) -> None:
        ast = _ast("![x](https://example.com/img.png)\n")
        assets = extract_assets(ast)
        assert assets[0].path is None

    def test_multiple_images(self) -> None:
        ast = _ast("![a](a.png) ![b](b.png)\n")
        assets = extract_assets(ast)
        assert len(assets) == 2
        assert assets[0].target == "a.png"
        assert assets[1].target == "b.png"

    def test_plain_links_not_included(self) -> None:
        ast = _ast("[link](https://example.com)\n")
        assets = extract_assets(ast)
        assert assets == ()

    def test_empty_ast_returns_empty_tuple(self) -> None:
        ast = _ast("")
        assert extract_assets(ast) == ()

    def test_returns_tuple_of_asset_ref(self) -> None:
        ast = _ast("![x](x.png)\n")
        assets = extract_assets(ast)
        assert isinstance(assets, tuple)
        assert isinstance(assets[0], AssetRef)

    def test_image_line_number(self) -> None:
        ast = _ast("Paragraph\n\n![x](x.png)\n")
        assets = extract_assets(ast)
        assert assets[0].line == 3


# ===========================================================================
# Mixed document
# ===========================================================================


class TestMixedDocument:
    def test_headings_links_assets_from_same_ast(self) -> None:
        source = (
            "# Title\n"
            "\n"
            "Some text with a [link](https://example.com).\n"
            "\n"
            "## Section\n"
            "\n"
            "![diagram](assets/diag.png)\n"
        )
        ast = _ast(source)

        headings = extract_headings(ast)
        links = extract_links(ast)
        assets = extract_assets(ast)

        assert len(headings) == 2
        assert headings[0].title == "Title"
        assert headings[1].title == "Section"

        assert len(links) == 1
        assert links[0].target == "https://example.com"

        assert len(assets) == 1
        assert assets[0].target == "assets/diag.png"


# ===========================================================================
# Defensive branches — malformed / synthetic tokens
# ===========================================================================


class TestDefensiveBranches:
    """Cover branches that guard against malformed token payloads."""

    # _heading_level: tag string too short or non-numeric → fallback to 1
    def test_heading_level_fallback_on_empty_tag(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {"type": "heading_open", "tag": "", "level": 0, "content": "", "map": [0, 1], "attrs": {}},
                {"type": "inline", "tag": "", "level": 1, "content": "Title", "map": [0, 1], "attrs": {}},
                {"type": "heading_close", "tag": "", "level": 0, "content": "", "map": None, "attrs": {}},
            ),
        )
        headings = extract_headings(ast)
        assert headings[0].level == 1

    def test_heading_level_fallback_on_non_numeric_tag(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {"type": "heading_open", "tag": "hx", "level": 0, "content": "", "map": [0, 1], "attrs": {}},
                {"type": "inline", "tag": "", "level": 1, "content": "Title", "map": [0, 1], "attrs": {}},
                {"type": "heading_close", "tag": "", "level": 0, "content": "", "map": None, "attrs": {}},
            ),
        )
        headings = extract_headings(ast)
        assert headings[0].level == 1

    # _heading_line / _inline_line: map with non-int first element → None
    def test_heading_line_none_when_map_element_not_int(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {"type": "heading_open", "tag": "h1", "level": 0, "content": "", "map": ["bad", 1], "attrs": {}},
                {"type": "inline", "tag": "", "level": 1, "content": "Title", "map": ["bad", 1], "attrs": {}},
                {"type": "heading_close", "tag": "", "level": 0, "content": "", "map": None, "attrs": {}},
            ),
        )
        headings = extract_headings(ast)
        assert headings[0].line is None

    # _heading_line / _inline_line: map absent or not a list → None
    def test_heading_line_none_when_map_is_none(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {"type": "heading_open", "tag": "h1", "level": 0, "content": "", "map": None, "attrs": {}},
                {"type": "inline", "tag": "", "level": 1, "content": "Title", "map": None, "attrs": {}},
                {"type": "heading_close", "tag": "", "level": 0, "content": "", "map": None, "attrs": {}},
            ),
        )
        headings = extract_headings(ast)
        assert headings[0].line is None

    # _inline_line: non-int map element for links/assets
    def test_link_line_none_when_map_element_not_int(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {
                    "type": "inline",
                    "tag": "",
                    "level": 0,
                    "content": "",
                    "map": ["bad", 1],
                    "attrs": {},
                    "children": [
                        {"type": "link_open", "tag": "a", "content": "", "attrs": {"href": "https://x.com"}},
                        {"type": "text", "tag": "", "content": "x", "attrs": {}},
                        {"type": "link_close", "tag": "a", "content": "", "attrs": {}},
                    ],
                },
            ),
        )
        refs = extract_links(ast)
        assert refs[0].line is None

    # _get_children: children is not a list → empty
    def test_get_children_returns_empty_when_children_not_list(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {
                    "type": "inline",
                    "tag": "",
                    "level": 0,
                    "content": "",
                    "map": [0, 1],
                    "attrs": {},
                    "children": "not-a-list",
                },
            ),
        )
        assert extract_links(ast) == ()
        assert extract_assets(ast) == ()

    # _inline_line: map absent (not a list) for an inline token with children → line is None
    def test_link_line_none_when_map_absent(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {
                    "type": "inline",
                    "tag": "",
                    "level": 0,
                    "content": "",
                    "map": None,
                    "attrs": {},
                    "children": [
                        {"type": "link_open", "tag": "a", "content": "", "attrs": {"href": "https://x.com"}},
                        {"type": "text", "tag": "", "content": "x", "attrs": {}},
                        {"type": "link_close", "tag": "a", "content": "", "attrs": {}},
                    ],
                },
            ),
        )
        refs = extract_links(ast)
        assert refs[0].line is None

    # _local_path: empty string → None  (line 195)
    def test_local_path_empty_string_returns_none(self) -> None:
        ast = MarkdownAst(
            backend="test",
            tokens=(
                {
                    "type": "inline",
                    "tag": "",
                    "level": 0,
                    "content": "",
                    "map": [0, 1],
                    "attrs": {},
                    "children": [
                        {"type": "link_open", "tag": "a", "content": "", "attrs": {"href": ""}},
                        {"type": "link_close", "tag": "a", "content": "", "attrs": {}},
                    ],
                },
            ),
        )
        refs = extract_links(ast)
        assert refs[0].path is None
        assert refs[0].target == ""
