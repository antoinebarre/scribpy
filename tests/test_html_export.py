"""Tests for the HTML export module."""

from __future__ import annotations

from pathlib import Path

import pytest

from scribpy.core.html import html_export
from scribpy.core.html.converter import to_html
from scribpy.core.html.page_builder import (
    _burger_icons,
    _render_nav_items,
    build_page,
)
from scribpy.core.html.toc_extractor import (
    build_nav_entries,
    extract_headings,
    strip_toc_block,
)

# ---------------------------------------------------------------------------
# toc_extractor — extract_headings
# ---------------------------------------------------------------------------

_MD_WITH_HEADINGS = """\
# Title

## Section One

Some text.

### Sub One A

#### Deep level

## Section Two
"""

_MD_IN_CODE_FENCE = """\
# Title

```
## Not a heading
### Also not
```

## Real Section
"""


def test_extract_headings_returns_eligible_levels() -> None:
    """Requirement: H2 and H3 are returned when toc_depth=2."""
    result = extract_headings(_MD_WITH_HEADINGS, toc_depth=2)
    levels = [level for level, _ in result]
    assert levels == [2, 3, 2]


def test_extract_headings_excludes_h1() -> None:
    """Requirement: H1 is never included in extracted headings."""
    result = extract_headings(_MD_WITH_HEADINGS, toc_depth=3)
    assert all(level > 1 for level, _ in result)


def test_extract_headings_respects_toc_depth() -> None:
    """Requirement: headings deeper than toc_depth+1 are excluded."""
    result = extract_headings(_MD_WITH_HEADINGS, toc_depth=1)
    levels = [level for level, _ in result]
    assert all(level == 2 for level in levels)


def test_extract_headings_ignores_fenced_blocks() -> None:
    """Requirement: headings inside fenced code blocks are not extracted."""
    result = extract_headings(_MD_IN_CODE_FENCE, toc_depth=3)
    titles = [title for _, title in result]
    assert titles == ["Real Section"]
    assert "Not a heading" not in titles


def test_extract_headings_empty_document() -> None:
    """Requirement: empty content returns an empty list."""
    assert extract_headings("", toc_depth=3) == []


# ---------------------------------------------------------------------------
# toc_extractor — strip_toc_block
# ---------------------------------------------------------------------------

_MD_WITH_TOC = """\
# Title

- [Section One](#section-one)
  - [Sub One A](#sub-one-a)
- [Section Two](#section-two)

## Section One
"""

_MD_WITHOUT_TOC = """\
# Title

## Section One
"""


def test_strip_toc_block_removes_toc() -> None:
    """Requirement: the TOC list block is removed from the Markdown content."""
    result = strip_toc_block(_MD_WITH_TOC)
    assert "- [Section One]" not in result
    assert "## Section One" in result


def test_strip_toc_block_preserves_content_without_toc() -> None:
    """Requirement: content without a TOC block is returned unchanged."""
    result = strip_toc_block(_MD_WITHOUT_TOC)
    assert result == _MD_WITHOUT_TOC


# ---------------------------------------------------------------------------
# toc_extractor — build_nav_entries
# ---------------------------------------------------------------------------


def test_build_nav_entries_produces_correct_keys() -> None:
    """Requirement: each nav entry has level, title, and slug keys."""
    headings = [(2, "My Section"), (3, "Sub Item")]
    entries = build_nav_entries(headings)
    assert len(entries) == 2
    assert entries[0] == {
        "level": 2,
        "title": "My Section",
        "slug": "my-section",
    }
    assert entries[1] == {
        "level": 3,
        "title": "Sub Item",
        "slug": "sub-item",
    }


def test_build_nav_entries_empty_headings() -> None:
    """Requirement: empty heading list produces empty nav entries."""
    assert build_nav_entries([]) == []


# ---------------------------------------------------------------------------
# converter — to_html
# ---------------------------------------------------------------------------


def test_to_html_converts_heading() -> None:
    """Requirement: ATX headings are converted to HTML heading tags."""
    html = to_html("## Hello World")
    assert "<h2" in html
    assert "Hello World" in html


def test_to_html_converts_table() -> None:
    """Requirement: GFM-style tables are rendered as HTML table elements."""
    md = "| A | B |\n|---|---|\n| 1 | 2 |"
    html = to_html(md)
    assert "<table>" in html


def test_to_html_converts_fenced_code() -> None:
    """Requirement: fenced code blocks are rendered as pre/code elements."""
    md = "```python\nprint('hi')\n```"
    html = to_html(md)
    assert "<pre>" in html
    assert "<code" in html


def test_to_html_empty_content() -> None:
    """Requirement: empty Markdown produces an empty string."""
    assert to_html("") == ""


# ---------------------------------------------------------------------------
# page_builder — _render_nav_items
# ---------------------------------------------------------------------------


def test_render_nav_items_produces_anchor_links() -> None:
    """Requirement: nav items contain href anchors matching entry slugs."""
    entries: list[dict[str, str | int]] = [
        {"level": 2, "title": "Intro", "slug": "intro"},
        {"level": 3, "title": "Details", "slug": "details"},
    ]
    html = _render_nav_items(entries)
    assert 'href="#intro"' in html
    assert 'href="#details"' in html
    assert 'class="depth-2"' in html
    assert 'class="depth-3"' in html


def test_render_nav_items_escapes_special_chars() -> None:
    """Requirement: HTML special characters in titles are escaped."""
    entries: list[dict[str, str | int]] = [
        {"level": 2, "title": "<script>", "slug": "script"},
    ]
    html = _render_nav_items(entries)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_nav_items_empty() -> None:
    """Requirement: empty entries list returns an empty string."""
    assert _render_nav_items([]) == ""


# ---------------------------------------------------------------------------
# page_builder — _burger_icons
# ---------------------------------------------------------------------------


def test_burger_icons_returns_two_svgs() -> None:
    """Requirement: _burger_icons returns two non-empty SVG strings."""
    open_svg, close_svg = _burger_icons()
    assert open_svg.startswith("<svg")
    assert close_svg.startswith("<svg")
    assert open_svg.endswith("</svg>")
    assert close_svg.endswith("</svg>")


# ---------------------------------------------------------------------------
# page_builder — build_page
# ---------------------------------------------------------------------------


def test_build_page_contains_body_html() -> None:
    """Requirement: body HTML fragment appears inside main in the page."""
    html = build_page(
        body_html="<p>Hello</p>",
        nav_entries=[],
        default_css="body {}",
        user_css=None,
        burger_js="// js",
    )
    assert "<p>Hello</p>" in html
    assert "<main>" in html


def test_build_page_embeds_default_css() -> None:
    """Requirement: default CSS is embedded inside a style block."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="body { color: red; }",
        user_css=None,
        burger_js="",
    )
    assert "body { color: red; }" in html
    assert "<style>" in html


def test_build_page_appends_user_css() -> None:
    """Requirement: user CSS is appended after the default CSS."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="body {}",
        user_css="h1 { color: blue; }",
        burger_js="",
    )
    assert "h1 { color: blue; }" in html
    default_pos = html.index("body {}")
    user_pos = html.index("h1 { color: blue; }")
    assert user_pos > default_pos


def test_build_page_embeds_burger_js() -> None:
    """Requirement: burger JS source is embedded inside a script block."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="",
        user_css=None,
        burger_js="var x = 1;",
    )
    assert "var x = 1;" in html
    assert "<script>" in html


def test_build_page_contains_burger_button() -> None:
    """Requirement: the page contains a button with id scribpy-burger."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="",
        user_css=None,
        burger_js="",
    )
    assert 'id="scribpy-burger"' in html


def test_build_page_contains_nav_panel() -> None:
    """Requirement: the page contains a nav element with id scribpy-nav."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="",
        user_css=None,
        burger_js="",
    )
    assert 'id="scribpy-nav"' in html


def test_build_page_no_user_css_omits_user_block() -> None:
    """Requirement: when user_css is None the user styles comment is absent."""
    html = build_page(
        body_html="",
        nav_entries=[],
        default_css="body {}",
        user_css=None,
        burger_js="",
    )
    assert "User styles" not in html


# ---------------------------------------------------------------------------
# html_export — integration
# ---------------------------------------------------------------------------

_FULL_MD = """\
# My Document

- [Section Alpha](#section-alpha)
  - [Sub Alpha](#sub-alpha)
- [Section Beta](#section-beta)

## Section Alpha

Content alpha.

### Sub Alpha

Deep content.

## Section Beta

Content beta.
"""


def test_html_export_writes_file(tmp_path: Path) -> None:
    """Requirement: html_export writes a .html file at the output path."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=3)

    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in content


def test_html_export_toc_not_in_body(tmp_path: Path) -> None:
    """Requirement: the TOC Markdown list is not rendered in the HTML body."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=3)

    content = output.read_text(encoding="utf-8")
    assert "- [Section Alpha]" not in content


def test_html_export_burger_menu_present(tmp_path: Path) -> None:
    """Requirement: the exported HTML contains the burger button and nav."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=3)

    content = output.read_text(encoding="utf-8")
    assert 'id="scribpy-burger"' in content
    assert 'id="scribpy-nav"' in content


def test_html_export_nav_contains_headings(tmp_path: Path) -> None:
    """Requirement: the nav panel lists Section Alpha and Section Beta."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=3)

    content = output.read_text(encoding="utf-8")
    assert "Section Alpha" in content
    assert "Section Beta" in content


def test_html_export_toc_depth_filters_headings(tmp_path: Path) -> None:
    """Requirement: toc_depth=1 excludes H3 from the burger menu."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=1)

    content = output.read_text(encoding="utf-8")
    nav_start = content.index('id="scribpy-nav-list"')
    nav_end = content.index("</ul>", nav_start)
    nav_block = content[nav_start:nav_end]
    assert "Sub Alpha" not in nav_block


def test_html_export_user_css_injected(tmp_path: Path) -> None:
    """Requirement: user CSS file contents appear in the exported HTML."""
    source = tmp_path / "doc.md"
    source.write_text(_FULL_MD, encoding="utf-8")
    css_file = tmp_path / "custom.css"
    css_file.write_text("body { background: pink; }", encoding="utf-8")
    output = tmp_path / "doc.html"

    html_export(source, output, toc_depth=3, css=css_file)

    content = output.read_text(encoding="utf-8")
    assert "background: pink" in content


def test_html_export_source_not_found(tmp_path: Path) -> None:
    """Requirement: FileNotFoundError is raised when source does not exist."""
    with pytest.raises(FileNotFoundError):
        html_export(tmp_path / "missing.md", tmp_path / "out.html")


def test_html_export_css_not_found(tmp_path: Path) -> None:
    """Requirement: FileNotFoundError raised when css path does not exist."""
    source = tmp_path / "doc.md"
    source.write_text("# Title\n", encoding="utf-8")
    with pytest.raises(FileNotFoundError):
        html_export(
            source,
            tmp_path / "out.html",
            css=tmp_path / "missing.css",
        )
