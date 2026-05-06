"""Tests for Markdown frontmatter parsing (YAML and TOML)."""

from pathlib import Path
from unittest.mock import patch

import yaml

from scribpy.parser import FrontmatterResult, parse_frontmatter
from scribpy.parser.frontmatter import _yaml_error_line

# ---------------------------------------------------------------------------
# No frontmatter
# ---------------------------------------------------------------------------


def test_no_frontmatter_returns_original_body() -> None:
    source = "# Title\n\nBody\n"

    result = parse_frontmatter(source)

    assert isinstance(result, FrontmatterResult)
    assert result.frontmatter == {}
    assert result.body == source
    assert result.body_start_line == 1
    assert result.diagnostics == ()


def test_empty_source_returns_empty_result() -> None:
    result = parse_frontmatter("")

    assert result.frontmatter == {}
    assert result.body == ""
    assert result.body_start_line == 1
    assert result.diagnostics == ()


def test_frontmatter_not_detected_when_not_at_start() -> None:
    source = "\n---\ntitle: Ignored\n---\n# Title\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {}
    assert result.body == source
    assert result.body_start_line == 1


# ---------------------------------------------------------------------------
# YAML frontmatter — valid
# ---------------------------------------------------------------------------


def test_yaml_simple_key_value_pairs() -> None:
    source = "---\ntitle: My Document\nowner: Docs Team\n---\n# Title\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {"title": "My Document", "owner": "Docs Team"}
    assert result.body == "# Title\n"
    assert result.body_start_line == 5
    assert result.diagnostics == ()


def test_yaml_native_types() -> None:
    source = "---\nversion: 3\ndraft: true\ntags:\n  - python\n  - docs\n---\nBody\n"

    result = parse_frontmatter(source)

    assert result.frontmatter["version"] == 3
    assert result.frontmatter["draft"] is True
    assert result.frontmatter["tags"] == ["python", "docs"]
    assert result.diagnostics == ()


def test_yaml_empty_block_returns_empty_dict() -> None:
    source = "---\n---\n# Title\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {}
    assert result.body == "# Title\n"
    assert result.diagnostics == ()


def test_yaml_body_start_line_is_correct() -> None:
    source = "---\ntitle: T\n---\nline4\n"

    result = parse_frontmatter(source)

    assert result.body_start_line == 4
    assert result.body == "line4\n"


# ---------------------------------------------------------------------------
# YAML frontmatter — invalid
# ---------------------------------------------------------------------------


def test_yaml_unclosed_block_produces_prs002() -> None:
    path = Path("doc/index.md")
    source = "---\ntitle: Broken\n# Title\n"

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {}
    assert result.body == ""
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag.code == "PRS002"
    assert diag.severity == "error"
    assert diag.path == path
    assert diag.line == 1


def test_yaml_invalid_syntax_produces_prs002() -> None:
    path = Path("doc/index.md")
    source = "---\nkey: [unclosed\n---\nBody\n"

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {}
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "PRS002"
    assert result.diagnostics[0].path == path


def test_yaml_non_mapping_root_produces_prs002() -> None:
    source = "---\n- item1\n- item2\n---\nBody\n"

    result = parse_frontmatter(source)

    assert result.frontmatter == {}
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "PRS002"


# ---------------------------------------------------------------------------
# TOML frontmatter — valid
# ---------------------------------------------------------------------------


def test_toml_simple_key_value_pairs() -> None:
    source = '+++\ntitle = "My Document"\nowner = "Docs Team"\n+++\n# Title\n'

    result = parse_frontmatter(source)

    assert result.frontmatter == {"title": "My Document", "owner": "Docs Team"}
    assert result.body == "# Title\n"
    assert result.body_start_line == 5
    assert result.diagnostics == ()


def test_toml_native_types() -> None:
    source = '+++\nversion = 3\ndraft = true\ntags = ["python", "docs"]\n+++\nBody\n'

    result = parse_frontmatter(source)

    assert result.frontmatter["version"] == 3
    assert result.frontmatter["draft"] is True
    assert result.frontmatter["tags"] == ["python", "docs"]
    assert result.diagnostics == ()


def test_toml_body_start_line_is_correct() -> None:
    source = '+++\ntitle = "T"\n+++\nline4\n'

    result = parse_frontmatter(source)

    assert result.body_start_line == 4
    assert result.body == "line4\n"


# ---------------------------------------------------------------------------
# TOML frontmatter — invalid
# ---------------------------------------------------------------------------


def test_toml_unclosed_block_produces_prs002() -> None:
    path = Path("doc/index.md")
    source = '+++\ntitle = "Broken"\n# Title\n'

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {}
    assert result.body == ""
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag.code == "PRS002"
    assert diag.severity == "error"
    assert diag.path == path
    assert diag.line == 1


def test_toml_invalid_syntax_produces_prs002() -> None:
    path = Path("doc/index.md")
    source = "+++\nnot valid toml !!!\n+++\nBody\n"

    result = parse_frontmatter(source, path=path)

    assert result.frontmatter == {}
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].code == "PRS002"
    assert result.diagnostics[0].path == path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def test_yaml_error_line_returns_none_when_problem_mark_absent() -> None:
    exc = yaml.YAMLError("no mark")

    assert _yaml_error_line(exc) is None


def test_yaml_error_line_returns_none_via_adapter_when_problem_mark_absent() -> None:
    path = Path("doc/index.md")
    exc = yaml.YAMLError("synthetic error without mark")

    with patch("yaml.safe_load", side_effect=exc):
        result = parse_frontmatter("---\nkey: value\n---\n", path=path)

    assert result.frontmatter == {}
    assert len(result.diagnostics) == 1
    diag = result.diagnostics[0]
    assert diag.code == "PRS002"
    assert diag.line is None
