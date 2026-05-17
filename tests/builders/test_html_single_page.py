"""Tests for the single-page HTML builder."""

from pathlib import Path

from scribpy.builders.html_single_page import (
    build_single_page_html,
    render_markdown_to_html,
    write_single_page_artifact,
)
from scribpy.utils.file_utils import RealFileSystem


def test_render_heading_levels() -> None:
    html = render_markdown_to_html("# H1\n## H2\n### H3\n")
    assert '<h1 id="h1">H1</h1>' in html
    assert '<h2 id="h2">H2</h2>' in html
    assert '<h3 id="h3">H3</h3>' in html


def test_render_paragraph() -> None:
    html = render_markdown_to_html("Hello world.\n")
    assert "<p>Hello world.</p>" in html


def test_render_empty_lines_produce_empty_output() -> None:
    html = render_markdown_to_html("\n\n")
    assert html.strip() == ""


def test_render_code_block() -> None:
    html = render_markdown_to_html("```python\nprint('hi')\n```\n")
    assert "<pre><code" in html
    assert "print(&#x27;hi&#x27;)" in html or "print('hi')" in html


def test_render_code_block_with_language_attr() -> None:
    html = render_markdown_to_html("```python\npass\n```\n")
    assert 'class="language-python"' in html


def test_render_inline_bold() -> None:
    html = render_markdown_to_html("**bold text**\n")
    assert "<strong>bold text</strong>" in html


def test_render_inline_italic() -> None:
    html = render_markdown_to_html("*italic*\n")
    assert "<em>italic</em>" in html


def test_render_inline_code() -> None:
    html = render_markdown_to_html("`code`\n")
    assert "<code>code</code>" in html


def test_render_link() -> None:
    html = render_markdown_to_html("[text](https://example.com)\n")
    assert '<a href="https://example.com">text</a>' in html


def test_render_image() -> None:
    html = render_markdown_to_html("![alt](img.png)\n")
    assert '<img src="img.png" alt="alt">' in html


def test_render_hr() -> None:
    html = render_markdown_to_html("---\n")
    assert "<hr>" in html


def test_build_single_page_html_structure() -> None:
    html = build_single_page_html("<p>body</p>", "My Doc", [])
    assert "<!DOCTYPE html>" in html
    assert "<title>My Doc</title>" in html
    assert "<p>body</p>" in html
    assert "</html>" in html


def test_build_single_page_html_with_css() -> None:
    html = build_single_page_html("<p>x</p>", "Doc", ["css/style.css"])
    assert 'href="css/style.css"' in html
    assert 'rel="stylesheet"' in html


def test_build_single_page_html_no_css_has_no_link_tag() -> None:
    html = build_single_page_html("<p>x</p>", "Doc", [])
    assert "<link" not in html


def test_build_single_page_html_escapes_title() -> None:
    html = build_single_page_html("", "A & B <test>", [])
    assert "A &amp; B &lt;test&gt;" in html


def test_write_single_page_artifact_creates_file(tmp_path: Path) -> None:
    html = "<!DOCTYPE html><html><body></body></html>"
    artifact, diagnostics = write_single_page_artifact(
        tmp_path, html, Path("build/html"), RealFileSystem()
    )

    assert diagnostics == ()
    assert artifact is not None
    assert artifact.path == tmp_path / "build/html/index.html"
    assert artifact.target == "html"
    assert artifact.artifact_type == "document"
    assert artifact.path.read_text(encoding="utf-8") == html


def test_write_single_page_artifact_reports_write_failure(tmp_path: Path) -> None:
    class FailFS(RealFileSystem):
        def write_text(self, path: Path, content: str) -> None:
            raise OSError("disk full")

    artifact, diagnostics = write_single_page_artifact(
        tmp_path, "html", Path("build/html"), FailFS()
    )

    assert artifact is None
    assert len(diagnostics) == 1
    assert diagnostics[0].code == "BLD005"
