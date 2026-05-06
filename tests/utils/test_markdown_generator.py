"""Tests for scribpy.utils.markdown_generator."""

import random

import pytest

from scribpy.utils.markdown_generator import (
    MarkdownConfig,
    _alert,
    _autolink,
    _blockquote,
    _bold,
    _bold_italic,
    _code_block,
    _core_sections,
    _details,
    _footnote_def,
    _footnote_parts,
    _footnote_ref,
    _heading,
    _horizontal_rule,
    _image,
    _inline_code,
    _issue_ref,
    _italic,
    _link,
    _math_block,
    _math_inline,
    _mention,
    _mermaid,
    _optional_sections,
    _ordered_list,
    _paragraph,
    _random_table,
    _sentence,
    _strikethrough,
    _subscript,
    _superscript,
    _table,
    _table_row,
    _task_item,
    _task_list,
    _unordered_list,
    _words,
    generate_markdown,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rng(seed: int = 0) -> random.Random:
    return random.Random(seed)


# ---------------------------------------------------------------------------
# Element builders — pure, deterministic
# ---------------------------------------------------------------------------


class TestHeading:
    def test_level_1(self) -> None:
        assert _heading(1, "Title") == "# Title"

    def test_level_3(self) -> None:
        assert _heading(3, "Section") == "### Section"

    def test_level_6(self) -> None:
        assert _heading(6, "Deep") == "###### Deep"

    def test_prefix_length_matches_level(self) -> None:
        for level in range(1, 7):
            result = _heading(level, "X")
            assert result.startswith("#" * level + " ")


class TestInlineEmphasis:
    def test_bold(self) -> None:
        assert _bold("hello") == "**hello**"

    def test_italic(self) -> None:
        assert _italic("hello") == "*hello*"

    def test_bold_italic(self) -> None:
        assert _bold_italic("hello") == "***hello***"

    def test_strikethrough(self) -> None:
        assert _strikethrough("hello") == "~~hello~~"

    def test_subscript(self) -> None:
        assert _subscript("2") == "~2~"

    def test_superscript(self) -> None:
        assert _superscript("2") == "^2^"

    def test_inline_code(self) -> None:
        assert _inline_code("x = 1") == "`x = 1`"


class TestLinksAndImages:
    def test_link(self) -> None:
        assert _link("label", "https://example.com") == "[label](https://example.com)"

    def test_image(self) -> None:
        assert _image("alt text", "https://example.com/img.png") == (
            "![alt text](https://example.com/img.png)"
        )

    def test_autolink(self) -> None:
        assert _autolink("https://example.com") == "<https://example.com>"


class TestBlockquote:
    def test_single_line(self) -> None:
        assert _blockquote("hello") == "> hello"

    def test_multiline_prefixes_every_line(self) -> None:
        result = _blockquote("line one\nline two")
        assert result == "> line one\n> line two"

    def test_already_quoted_content_produces_nested(self) -> None:
        inner = _blockquote("inner")
        outer = _blockquote(inner)
        assert outer == "> > inner"


class TestCodeBlock:
    def test_contains_language_tag(self) -> None:
        result = _code_block("python", "x = 1")
        assert result.startswith("```python")

    def test_contains_code_body(self) -> None:
        result = _code_block("python", "x = 1")
        assert "x = 1" in result

    def test_ends_with_closing_fence(self) -> None:
        result = _code_block("python", "x = 1")
        assert result.endswith("```")

    def test_structure(self) -> None:
        assert _code_block("py", "a") == "```py\na\n```"


class TestTable:
    def test_table_row_pipe_delimited(self) -> None:
        assert _table_row(["A", "B", "C"]) == "| A | B | C |"

    def test_table_has_header_separator_and_rows(self) -> None:
        result = _table(["H1", "H2"], [["r1", "r2"]], [":---", "---:"])
        lines = result.splitlines()
        assert lines[0] == "| H1 | H2 |"
        assert lines[1] == "| :--- | ---: |"
        assert lines[2] == "| r1 | r2 |"

    def test_table_row_count(self) -> None:
        result = _table(["A"], [["x"], ["y"], ["z"]], [":---"])
        assert len(result.splitlines()) == 5


class TestTaskItem:
    def test_done(self) -> None:
        assert _task_item(True, "finish") == "- [x] finish"

    def test_not_done(self) -> None:
        assert _task_item(False, "start") == "- [ ] start"


class TestAlerts:
    def test_note(self) -> None:
        assert _alert("NOTE", "pay attention") == "> [!NOTE]\n> pay attention"

    def test_caution(self) -> None:
        result = _alert("CAUTION", "be careful")
        assert result.startswith("> [!CAUTION]")


class TestFootnotes:
    def test_ref(self) -> None:
        assert _footnote_ref(1) == "[^1]"
        assert _footnote_ref(42) == "[^42]"

    def test_def(self) -> None:
        assert _footnote_def(1, "my note") == "[^1]: my note"


class TestMath:
    def test_inline(self) -> None:
        assert _math_inline("x^2") == "$x^2$"

    def test_block_structure(self) -> None:
        result = _math_block("x^2")
        assert result == "$$\nx^2\n$$"


class TestDetails:
    def test_contains_details_tags(self) -> None:
        result = _details("Click me", "Hidden content")
        assert "<details>" in result
        assert "</details>" in result

    def test_contains_summary(self) -> None:
        result = _details("Click me", "Hidden content")
        assert "<summary>Click me</summary>" in result

    def test_contains_body(self) -> None:
        result = _details("S", "my body")
        assert "my body" in result


class TestMermaid:
    def test_is_fenced_mermaid_block(self) -> None:
        result = _mermaid("graph TD\n    A --> B")
        assert result.startswith("```mermaid")
        assert result.endswith("```")
        assert "graph TD" in result


class TestMisc:
    def test_mention(self) -> None:
        assert _mention("alice") == "@alice"

    def test_issue_ref(self) -> None:
        assert _issue_ref(42) == "#42"

    def test_horizontal_rule(self) -> None:
        assert _horizontal_rule() == "---"


# ---------------------------------------------------------------------------
# Text helpers (seeded rng)
# ---------------------------------------------------------------------------


class TestWords:
    def test_returns_correct_word_count(self) -> None:
        result = _words(_rng(), 5)
        assert len(result.split()) == 5

    def test_single_word_has_no_spaces(self) -> None:
        result = _words(_rng(), 1)
        assert " " not in result

    def test_deterministic_with_same_seed(self) -> None:
        assert _words(_rng(42), 10) == _words(_rng(42), 10)


class TestSentence:
    def test_starts_with_uppercase(self) -> None:
        result = _sentence(_rng())
        assert result[0].isupper()

    def test_ends_with_period(self) -> None:
        result = _sentence(_rng())
        assert result.endswith(".")

    def test_deterministic_with_same_seed(self) -> None:
        assert _sentence(_rng(7)) == _sentence(_rng(7))


class TestParagraph:
    def test_ends_with_period(self) -> None:
        result = _paragraph(_rng())
        assert result.endswith(".")

    def test_contains_multiple_sentences(self) -> None:
        result = _paragraph(_rng())
        assert result.count(".") >= 3


# ---------------------------------------------------------------------------
# Compound list builders
# ---------------------------------------------------------------------------


class TestUnorderedList:
    def test_has_top_level_items(self) -> None:
        result = _unordered_list(_rng())
        assert any(line.startswith("- ") for line in result.splitlines())

    def test_has_nested_items(self) -> None:
        result = _unordered_list(_rng())
        assert any(line.startswith("  - ") for line in result.splitlines())

    def test_has_deep_nested_items(self) -> None:
        result = _unordered_list(_rng())
        assert any(line.startswith("    - ") for line in result.splitlines())


class TestOrderedList:
    def test_starts_with_1(self) -> None:
        result = _ordered_list(_rng())
        assert result.startswith("1.")

    def test_has_nested_items(self) -> None:
        result = _ordered_list(_rng())
        assert "   1." in result


class TestTaskList:
    def test_all_items_are_checkboxes(self) -> None:
        result = _task_list(_rng())
        for line in result.splitlines():
            assert "- [x]" in line or "- [ ]" in line

    def test_has_six_items(self) -> None:
        result = _task_list(_rng())
        assert len(result.splitlines()) == 6


class TestRandomTable:
    def test_has_header_row(self) -> None:
        result = _random_table(_rng())
        assert "| Name |" in result.splitlines()[0]

    def test_has_five_data_rows(self) -> None:
        result = _random_table(_rng())
        lines = result.splitlines()
        data_rows = lines[2:]
        assert len(data_rows) == 5


# ---------------------------------------------------------------------------
# Assembly helpers
# ---------------------------------------------------------------------------


class TestCoreSection:
    def test_returns_eight_sections(self) -> None:
        assert len(_core_sections(_rng())) == 8


class TestOptionalSections:
    def test_all_enabled_returns_four(self) -> None:
        result = _optional_sections(_rng(), MarkdownConfig())
        assert len(result) == 4

    def test_all_disabled_returns_empty(self) -> None:
        cfg = MarkdownConfig(
            include_alerts=False,
            include_math=False,
            include_mermaid=False,
            include_details=False,
        )
        assert _optional_sections(_rng(), cfg) == []

    def test_single_flag_controls_count(self) -> None:
        cfg = MarkdownConfig(
            include_alerts=True,
            include_math=False,
            include_mermaid=False,
            include_details=False,
        )
        assert len(_optional_sections(_rng(), cfg)) == 1


class TestFootnoteParts:
    def test_include_false_returns_empty_lists(self) -> None:
        sections, defs = _footnote_parts(_rng(), include=False)
        assert sections == []
        assert defs == []

    def test_include_true_returns_section_and_defs(self) -> None:
        sections, defs = _footnote_parts(_rng(), include=True)
        assert len(sections) == 1
        assert len(defs) == 3

    def test_defs_use_footnote_syntax(self) -> None:
        _, defs = _footnote_parts(_rng(), include=True)
        for i, line in enumerate(defs, start=1):
            assert line.startswith(f"[^{i}]:")


# ---------------------------------------------------------------------------
# MarkdownConfig
# ---------------------------------------------------------------------------


class TestMarkdownConfig:
    def test_default_all_sections_enabled(self) -> None:
        cfg = MarkdownConfig()
        assert cfg.include_math is True
        assert cfg.include_mermaid is True
        assert cfg.include_alerts is True
        assert cfg.include_footnotes is True
        assert cfg.include_details is True

    def test_default_separator(self) -> None:
        assert MarkdownConfig().section_separator == "\n\n---\n\n"

    def test_is_frozen(self) -> None:
        cfg = MarkdownConfig()
        with pytest.raises(AttributeError):
            cfg.include_math = False  # type: ignore[misc]

    def test_custom_separator(self) -> None:
        cfg = MarkdownConfig(section_separator="\n===\n")
        assert cfg.section_separator == "\n===\n"


# ---------------------------------------------------------------------------
# generate_markdown — integration
# ---------------------------------------------------------------------------


class TestGenerateMarkdown:
    def test_returns_non_empty_string(self) -> None:
        result = generate_markdown(seed=0)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_same_seed_is_deterministic(self) -> None:
        assert generate_markdown(seed=42) == generate_markdown(seed=42)

    def test_different_seeds_differ(self) -> None:
        assert generate_markdown(seed=1) != generate_markdown(seed=2)

    def test_contains_mandatory_section_headings(self) -> None:
        result = generate_markdown(seed=0)
        for heading in (
            "## Heading Levels",
            "## Text Formatting",
            "## Lists",
            "## Code",
            "## Links & Images",
            "## Tables",
            "## Blockquotes",
            "## Miscellaneous",
        ):
            assert heading in result, f"Missing section: {heading!r}"

    def test_contains_h1(self) -> None:
        result = generate_markdown(seed=0)
        assert any(line.startswith("# ") for line in result.splitlines())

    def test_default_separator_present(self) -> None:
        result = generate_markdown(seed=0)
        assert "\n\n---\n\n" in result

    def test_code_blocks_are_balanced(self) -> None:
        result = generate_markdown(seed=0)
        fence_count = result.count("```")
        assert fence_count % 2 == 0

    # --- config: optional sections excluded ---

    def test_no_math_when_disabled(self) -> None:
        cfg = MarkdownConfig(include_math=False)
        result = generate_markdown(seed=0, config=cfg)
        assert "$$" not in result
        assert "## Mathematics" not in result

    def test_no_mermaid_when_disabled(self) -> None:
        cfg = MarkdownConfig(include_mermaid=False)
        result = generate_markdown(seed=0, config=cfg)
        assert "```mermaid" not in result
        assert "## Diagrams" not in result

    def test_no_alerts_when_disabled(self) -> None:
        cfg = MarkdownConfig(include_alerts=False)
        result = generate_markdown(seed=0, config=cfg)
        assert "[!NOTE]" not in result
        assert "[!WARNING]" not in result

    def test_no_footnotes_when_disabled(self) -> None:
        cfg = MarkdownConfig(include_footnotes=False)
        result = generate_markdown(seed=0, config=cfg)
        assert "[^1]" not in result
        assert "## Footnotes" not in result

    def test_no_details_when_disabled(self) -> None:
        cfg = MarkdownConfig(include_details=False)
        result = generate_markdown(seed=0, config=cfg)
        assert "<details>" not in result
        assert "## Collapsible Sections" not in result

    def test_all_optional_sections_present_by_default(self) -> None:
        result = generate_markdown(seed=0)
        for marker in ("## Mathematics", "## Diagrams", "## Alerts", "## Footnotes"):
            assert marker in result or "Alerts" in result

    def test_custom_separator_used(self) -> None:
        cfg = MarkdownConfig(section_separator="\n\nXXX_SEP_XXX\n\n")
        result = generate_markdown(seed=0, config=cfg)
        assert "\n\nXXX_SEP_XXX\n\n" in result

    def test_none_config_uses_defaults(self) -> None:
        assert generate_markdown(seed=5) == generate_markdown(seed=5, config=None)