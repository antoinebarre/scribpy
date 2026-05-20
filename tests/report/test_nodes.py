"""Tests for report node construction and validation."""

import pytest

from scribpy.report import (
    BlockQuote,
    BulletList,
    Chapter,
    CodeBlock,
    FigureAsset,
    HorizontalRule,
    Image,
    ImageFile,
    InvalidChildError,
    InvalidTableError,
    LineBreak,
    NumberedList,
    Paragraph,
    Report,
    ReportDepthError,
    Section,
    Table,
    Text,
)
from scribpy.report.nodes import compute_section_depth, MAX_HEADING_DEPTH


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------

class TestText:
    def test_valid_styles(self):
        for style in ("plain", "bold", "italic", "code", "strikethrough"):
            t = Text("hello", style=style)
            assert t.style == style

    def test_invalid_style(self):
        with pytest.raises(ValueError):
            Text("hello", style="underline")

    def test_default_plain(self):
        assert Text("hi").style == "plain"


# ---------------------------------------------------------------------------
# Paragraph
# ---------------------------------------------------------------------------

class TestParagraph:
    def test_string_content(self):
        p = Paragraph("Hello world")
        assert p.content == "Hello world"

    def test_list_content(self):
        p = Paragraph([Text("bold", style="bold"), Text(" text")])
        assert len(p.content) == 2

    def test_list_with_linebreak(self):
        p = Paragraph([Text("line1"), LineBreak(), Text("line2")])
        assert len(p.content) == 3
        assert isinstance(p.content[1], LineBreak)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            Paragraph("")


# ---------------------------------------------------------------------------
# LineBreak
# ---------------------------------------------------------------------------

class TestLineBreak:
    def test_instantiate(self):
        lb = LineBreak()
        assert isinstance(lb, LineBreak)

    def test_valid_in_section(self):
        s = Section(title="S")
        s.add(LineBreak())
        assert isinstance(s.children[0], LineBreak)


# ---------------------------------------------------------------------------
# FigureAsset
# ---------------------------------------------------------------------------

class TestFigureAsset:
    def test_instantiate(self):
        from unittest.mock import MagicMock
        renderer = MagicMock()
        fig = FigureAsset(renderer=renderer, output_path="out/chart.png", alt="chart")
        assert fig.output_path == "out/chart.png"
        assert fig.alt == "chart"
        assert fig.caption == ""

    def test_valid_in_chapter(self):
        from unittest.mock import MagicMock
        renderer = MagicMock()
        c = Chapter(title="C")
        fig = FigureAsset(renderer=renderer, output_path="chart.png")
        c.add(fig)
        assert fig in c.children


# ---------------------------------------------------------------------------
# ImageFile
# ---------------------------------------------------------------------------

class TestImageFile:
    def test_instantiate(self):
        img = ImageFile(source_path="photo.png", alt="Photo", caption="A photo")
        assert img.source_path == "photo.png"
        assert img.alt == "Photo"
        assert img.caption == "A photo"

    def test_defaults(self):
        img = ImageFile(source_path="img.jpg")
        assert img.alt == ""
        assert img.caption == ""

    def test_empty_source_path_raises(self):
        with pytest.raises(ValueError):
            ImageFile(source_path="")

    def test_blank_source_path_raises(self):
        with pytest.raises(ValueError):
            ImageFile(source_path="   ")

    def test_valid_in_section(self):
        s = Section(title="S")
        img = ImageFile(source_path="img.png")
        s.add(img)
        assert img in s.children

    def test_valid_in_chapter(self):
        c = Chapter(title="C")
        img = ImageFile(source_path="img.png")
        c.add(img)
        assert img in c.children


# ---------------------------------------------------------------------------
# Table
# ---------------------------------------------------------------------------

class TestTable:
    def test_valid_table(self):
        t = Table(headers=["A", "B"], rows=[["1", "2"], ["3", "4"]])
        assert t.headers == ["A", "B"]

    def test_empty_headers_raises(self):
        with pytest.raises(InvalidTableError):
            Table(headers=[], rows=[])

    def test_row_column_mismatch_raises(self):
        with pytest.raises(InvalidTableError):
            Table(headers=["A", "B"], rows=[["1"]])


# ---------------------------------------------------------------------------
# Lists
# ---------------------------------------------------------------------------

class TestLists:
    def test_bullet_list(self):
        bl = BulletList(items=["a", "b"])
        assert bl.items == ["a", "b"]

    def test_bullet_list_empty_raises(self):
        with pytest.raises(ValueError):
            BulletList(items=[])

    def test_numbered_list(self):
        nl = NumberedList(items=["first", "second"])
        assert nl.items[0] == "first"

    def test_numbered_list_empty_raises(self):
        with pytest.raises(ValueError):
            NumberedList(items=[])


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------

class TestSection:
    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            Section(title="")

    def test_add_returns_self(self):
        s = Section(title="S")
        assert s.add(Paragraph("p")) is s

    def test_add_invalid_child_raises(self):
        s = Section(title="S")
        with pytest.raises(InvalidChildError):
            s.add(Report(title="R"))  # type: ignore[arg-type]

    def test_nested_section(self):
        outer = Section(title="Outer")
        inner = Section(title="Inner")
        outer.add(inner)
        assert inner in outer.children


# ---------------------------------------------------------------------------
# Chapter
# ---------------------------------------------------------------------------

class TestChapter:
    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            Chapter(title="")

    def test_add_section(self):
        c = Chapter(title="C")
        s = Section(title="S")
        c.add(s)
        assert s in c.children

    def test_add_invalid_child_raises(self):
        c = Chapter(title="C")
        with pytest.raises(InvalidChildError):
            c.add(Chapter(title="Nested"))  # type: ignore[arg-type]

    def test_add_returns_self(self):
        c = Chapter(title="C")
        assert c.add(Paragraph("p")) is c


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_empty_title_raises(self):
        with pytest.raises(ValueError):
            Report(title="")

    def test_add_chapter(self):
        r = Report(title="R")
        c = Chapter(title="C")
        r.add(c)
        assert c in r.children

    def test_add_non_chapter_raises(self):
        r = Report(title="R")
        with pytest.raises(InvalidChildError):
            r.add(Section(title="S"))  # type: ignore[arg-type]

    def test_add_returns_self(self):
        r = Report(title="R")
        assert r.add(Chapter(title="C")) is r


# ---------------------------------------------------------------------------
# Depth guard
# ---------------------------------------------------------------------------

class TestDepthGuard:
    def test_valid_depths(self):
        for d in range(1, 6):
            level = compute_section_depth(d)
            assert 2 <= level <= MAX_HEADING_DEPTH

    def test_depth_overflow_raises(self):
        with pytest.raises(ReportDepthError):
            compute_section_depth(6)
