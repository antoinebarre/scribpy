"""Tests for minimal Markdown frontmatter parsing."""

from pathlib import Path

from scribpy.parser import FrontmatterResult, parse_frontmatter


def test_parse_frontmatter_returns_original_body_when_absent() -> None:
    source = "# Title\n\nBody\n"

    result = parse_frontmatter(source)

    assert isinstance(result, FrontmatterResult)
    assert result.frontmatter == {}
    assert result.body == source
    assert result.body_start_line == 1
    assert result.diagnostics == ()


def test_parse_frontmatter_extracts_simple_key_value_pairs() -> None:
    source = "---\ntitle: My Document\nowner: Docs Team\n---\n# Title\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {
        "title": "My Document",
        "owner": "Docs Team",
    }
    assert result.body == "# Title\n"
    assert result.body_start_line == 5
    assert result.diagnostics == ()


def test_parse_frontmatter_ignores_blank_metadata_lines() -> None:
    source = "---\ntitle: My Document\n\nstatus: draft\n---\nBody\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {
        "title": "My Document",
        "status": "draft",
    }
    assert result.body == "Body\n"
    assert result.body_start_line == 6
    assert result.diagnostics == ()


def test_parse_frontmatter_only_detects_block_at_start_of_source() -> None:
    source = "\n---\ntitle: Ignored\n---\n# Title\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {}
    assert result.body == source
    assert result.body_start_line == 1
    assert result.diagnostics == ()


def test_parse_frontmatter_reports_unclosed_block() -> None:
    path = Path("doc/index.md")
    source = "---\ntitle: Broken\n# Title\n"

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {}
    assert result.body == ""
    assert result.body_start_line == 4
    assert len(result.diagnostics) == 1
    diagnostic = result.diagnostics[0]
    assert diagnostic.severity == "error"
    assert diagnostic.code == "PRS002"
    assert diagnostic.path == path
    assert diagnostic.line == 1


def test_parse_frontmatter_reports_invalid_metadata_line_and_keeps_body() -> None:
    path = Path("doc/index.md")
    source = "---\ntitle: Valid\ninvalid line\n: missing key\n---\n# Title\n"

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {"title": "Valid"}
    assert result.body == "# Title\n"
    assert result.body_start_line == 6
    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        "PRS002",
        "PRS002",
    ]
    assert [diagnostic.line for diagnostic in result.diagnostics] == [3, 4]
    assert all(diagnostic.path == path for diagnostic in result.diagnostics)
