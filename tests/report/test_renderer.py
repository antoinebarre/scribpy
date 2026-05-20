"""Tests for GFM rendering of report nodes."""

import pytest

from unittest.mock import MagicMock

from scribpy.report import (
    BlockQuote,
    BulletList,
    Chapter,
    CodeBlock,
    FigureAsset,
    HorizontalRule,
    Image,
    ImageFile,
    LineBreak,
    NumberedList,
    Paragraph,
    Report,
    Section,
    Table,
    Text,
)
from scribpy.report.renderer import (
    _render_block_quote,
    _render_bullet_list,
    _render_code_block,
    _render_figure_asset,
    _render_image,
    _render_image_file,
    _render_inline_element,
    _render_numbered_list,
    _render_paragraph,
    _render_table,
    _render_text,
)


# ---------------------------------------------------------------------------
# Leaf renderers
# ---------------------------------------------------------------------------

class TestTextRenderer:
    def test_plain(self):
        assert _render_text(Text("hi")) == "hi"

    def test_bold(self):
        assert _render_text(Text("hi", style="bold")) == "**hi**"

    def test_italic(self):
        assert _render_text(Text("hi", style="italic")) == "*hi*"

    def test_code(self):
        assert _render_text(Text("x", style="code")) == "`x`"

    def test_strikethrough(self):
        assert _render_text(Text("x", style="strikethrough")) == "~~x~~"


class TestParagraphRenderer:
    def test_string_paragraph(self):
        assert _render_paragraph(Paragraph("Hello")) == "Hello"

    def test_inline_paragraph(self):
        p = Paragraph([Text("Hello ", style="plain"), Text("world", style="bold")])
        assert _render_paragraph(p) == "Hello **world**"


class TestCodeBlockRenderer:
    def test_with_language(self):
        result = _render_code_block(CodeBlock("x = 1", language="python"))
        assert result.startswith("```python")
        assert "x = 1" in result
        assert result.endswith("```")

    def test_without_language(self):
        result = _render_code_block(CodeBlock("x = 1"))
        assert result.startswith("```\n")


class TestTableRenderer:
    def test_basic_table(self):
        t = Table(headers=["Col A", "Col B"], rows=[["v1", "v2"]])
        result = _render_table(t)
        lines = result.splitlines()
        assert lines[0] == "| Col A | Col B |"
        assert lines[1] == "| --- | --- |"
        assert lines[2] == "| v1 | v2 |"

    def test_no_data_rows(self):
        t = Table(headers=["H"], rows=[])
        result = _render_table(t)
        lines = result.splitlines()
        assert len(lines) == 2


class TestListRenderers:
    def test_bullet_list(self):
        result = _render_bullet_list(BulletList(items=["a", "b"]))
        assert result == "- a\n- b"

    def test_numbered_list(self):
        result = _render_numbered_list(NumberedList(items=["first", "second"]))
        assert result == "1. first\n2. second"


class TestImageRenderer:
    def test_basic_image(self):
        assert _render_image(Image(path="img.png", alt="logo")) == "![logo](img.png)"

    def test_image_with_title(self):
        result = _render_image(Image(path="img.png", alt="logo", title="My Logo"))
        assert result == '![logo](img.png "My Logo")'


class TestBlockQuoteRenderer:
    def test_single_line(self):
        assert _render_block_quote(BlockQuote("note")) == "> note"

    def test_multiline(self):
        result = _render_block_quote(BlockQuote("line1\nline2"))
        assert result == "> line1\n> line2"


# ---------------------------------------------------------------------------
# Full report render
# ---------------------------------------------------------------------------

class TestReportRender:
    def test_title_in_output(self):
        r = Report(title="My Report")
        assert "# My Report" in r.render()

    def test_chapter_rendered_as_h1(self):
        r = Report(title="R").add(Chapter(title="Intro"))
        assert "# Intro" in r.render()

    def test_section_rendered_as_h2(self):
        r = (
            Report(title="R")
            .add(Chapter(title="C").add(Section(title="Scope")))
        )
        assert "## Scope" in r.render()

    def test_nested_section_rendered_as_h3(self):
        r = (
            Report(title="R")
            .add(
                Chapter(title="C")
                .add(
                    Section(title="S1")
                    .add(Section(title="S2"))
                )
            )
        )
        assert "### S2" in r.render()

    def test_toc_included_when_enabled(self):
        r = Report(title="R", toc=True).add(Chapter(title="Intro"))
        output = r.render()
        assert "[Intro]" in output

    def test_auto_numbering_chapter(self):
        r = Report(title="R", auto_numbering=True).add(Chapter(title="Intro"))
        output = r.render()
        assert "1. Intro" in output

    def test_auto_numbering_section(self):
        r = (
            Report(title="R", auto_numbering=True)
            .add(Chapter(title="C").add(Section(title="Scope")))
        )
        output = r.render()
        assert "1.1. Scope" in output

    def test_horizontal_rule(self):
        r = Report(title="R").add(Chapter(title="C").add(HorizontalRule()))
        assert "---" in r.render()

    def test_all_leaf_types_render(self):
        chapter = (
            Chapter(title="All Leaves")
            .add(Paragraph("Some text."))
            .add(Text("inline", style="bold"))
            .add(CodeBlock("pass", language="python"))
            .add(Table(headers=["X"], rows=[["1"]]))
            .add(BulletList(items=["item"]))
            .add(NumberedList(items=["first"]))
            .add(Image(path="img.png", alt="alt"))
            .add(HorizontalRule())
            .add(BlockQuote("note"))
        )
        r = Report(title="R").add(chapter)
        output = r.render()
        assert "Some text." in output
        assert "**inline**" in output
        assert "```python" in output
        assert "| X |" in output
        assert "- item" in output
        assert "1. first" in output
        assert "![alt](img.png)" in output
        assert "---" in output
        assert "> note" in output


# ---------------------------------------------------------------------------
# LineBreak renderer
# ---------------------------------------------------------------------------

class TestLineBreakRenderer:
    def test_linebreak_renders_hard_break(self):
        result = _render_inline_element(LineBreak())
        assert result == "  \n"

    def test_text_passthrough_in_inline_element(self):
        result = _render_inline_element(Text("hello", style="bold"))
        assert result == "**hello**"

    def test_paragraph_with_linebreak(self):
        p = Paragraph([Text("line1"), LineBreak(), Text("line2")])
        result = _render_paragraph(p)
        assert "  \n" in result
        assert "line1" in result
        assert "line2" in result


# ---------------------------------------------------------------------------
# FigureAsset renderer
# ---------------------------------------------------------------------------

class _StubRenderer:
    """Minimal AssetRenderer stub that satisfies the runtime_checkable protocol."""

    def __init__(self, return_path: str) -> None:
        self._return_path = return_path
        self.calls: list[str] = []

    def render(self, output_path: str) -> str:
        self.calls.append(output_path)
        return self._return_path


class TestFigureAssetRenderer:
    def _make_renderer(self, tmp_path):
        return _StubRenderer(return_path=str(tmp_path / "chart.png"))

    def test_figure_asset_embeds_image(self, tmp_path):
        renderer = self._make_renderer(tmp_path)
        node = FigureAsset(
            renderer=renderer,
            output_path=str(tmp_path / "chart.png"),
            alt="My chart",
        )
        result = _render_figure_asset(node)
        assert "![My chart]" in result
        assert len(renderer.calls) == 1

    def test_figure_asset_with_caption(self, tmp_path):
        renderer = self._make_renderer(tmp_path)
        node = FigureAsset(
            renderer=renderer,
            output_path=str(tmp_path / "chart.png"),
            alt="chart",
            caption="Figure 1 — test.",
        )
        result = _render_figure_asset(node)
        assert "*Figure 1 — test.*" in result

    def test_figure_asset_no_caption(self, tmp_path):
        renderer = self._make_renderer(tmp_path)
        node = FigureAsset(
            renderer=renderer,
            output_path=str(tmp_path / "chart.png"),
            alt="chart",
        )
        result = _render_figure_asset(node)
        assert "*" not in result

    def test_figure_asset_invalid_renderer_raises(self, tmp_path):
        node = FigureAsset(
            renderer=object(),
            output_path=str(tmp_path / "chart.png"),
            alt="chart",
        )
        with pytest.raises(AssertionError):
            _render_figure_asset(node)

    def test_figure_asset_in_full_report(self, tmp_path):
        renderer = self._make_renderer(tmp_path)
        r = (
            Report(title="R")
            .add(Chapter(title="C").add(
                FigureAsset(
                    renderer=renderer,
                    output_path=str(tmp_path / "chart.png"),
                    alt="chart",
                )
            ))
        )
        output = r.render()
        assert "![chart]" in output


# ---------------------------------------------------------------------------
# ImageFile renderer
# ---------------------------------------------------------------------------

class TestImageFileRenderer:
    def test_render_without_assets_dir_uses_source_path(self):
        node = ImageFile(source_path="images/photo.png", alt="Photo")
        result = _render_image_file(node, assets_dir=None)
        assert result == "![Photo](images/photo.png)"

    def test_render_with_caption_no_assets_dir(self):
        node = ImageFile(source_path="img.png", alt="fig", caption="My caption.")
        result = _render_image_file(node, assets_dir=None)
        assert "*My caption.*" in result
        assert "![fig](img.png)" in result

    def test_render_with_assets_dir_copies_file(self, tmp_path):
        src = tmp_path / "photo.png"
        src.write_bytes(b"\x89PNG")
        assets_dir = tmp_path / "out" / "assets"
        node = ImageFile(source_path=str(src), alt="Photo")
        result = _render_image_file(node, assets_dir=assets_dir)
        assert (assets_dir / "photo.png").exists()
        assert "assets/photo.png" in result

    def test_save_report_copies_image_file(self, tmp_path):
        src = tmp_path / "logo.png"
        src.write_bytes(b"\x89PNG")
        r = (
            Report(title="R")
            .add(Chapter(title="C").add(
                ImageFile(source_path=str(src), alt="logo", caption="Our logo.")
            ))
        )
        out = tmp_path / "report" / "report.md"
        r.save(str(out))
        copied = tmp_path / "report" / "assets" / "logo.png"
        assert copied.exists()
        content = out.read_text(encoding="utf-8")
        assert "assets/logo.png" in content
        assert "*Our logo.*" in content

    def test_render_string_does_not_copy(self, tmp_path):
        node = ImageFile(source_path="img.png", alt="x")
        result = _render_image_file(node, assets_dir=None)
        assert "img.png" in result

    def test_image_file_in_full_report_render(self):
        r = (
            Report(title="R")
            .add(Chapter(title="C").add(ImageFile(source_path="photo.png", alt="p")))
        )
        output = r.render()
        assert "![p](photo.png)" in output


# ---------------------------------------------------------------------------
# Unknown node guard
# ---------------------------------------------------------------------------

class TestUnknownNodeGuard:
    def test_render_child_raises_on_unknown_type(self):
        from scribpy.report.renderer import _render_child

        with pytest.raises(TypeError, match="Unknown node type"):
            _render_child(object(), depth=1, num_ctx=None, assets_dir=None)


# ---------------------------------------------------------------------------
# save()
# ---------------------------------------------------------------------------

class TestSaveReport:
    def test_save_creates_file(self, tmp_path):
        r = Report(title="Saved").add(Chapter(title="Ch"))
        out = tmp_path / "output" / "report.md"
        r.save(str(out))
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "# Saved" in content

    def test_save_creates_intermediate_dirs(self, tmp_path):
        r = Report(title="R")
        out = tmp_path / "a" / "b" / "c" / "r.md"
        r.save(str(out))
        assert out.exists()
