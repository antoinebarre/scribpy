"""Tests for TOC generation."""

from scribpy.report import Chapter, Report, Section
from scribpy.report.toc import generate_toc


class TestTocGeneration:
    def test_empty_report(self):
        r = Report(title="R")
        assert generate_toc(r) == ""

    def test_single_chapter(self):
        r = Report(title="R").add(Chapter(title="Intro"))
        toc = generate_toc(r)
        assert "- [Intro](#intro)" in toc

    def test_chapter_with_section(self):
        r = Report(title="R").add(
            Chapter(title="Main").add(Section(title="Details"))
        )
        toc = generate_toc(r)
        assert "- [Main](#main)" in toc
        assert "  - [Details](#details)" in toc

    def test_nested_sections_indent(self):
        r = Report(title="R").add(
            Chapter(title="C").add(
                Section(title="S1").add(Section(title="S2"))
            )
        )
        toc = generate_toc(r)
        assert "    - [S2](#s2)" in toc

    def test_slug_lowercases_and_removes_punctuation(self):
        r = Report(title="R").add(Chapter(title="My Chapter!"))
        toc = generate_toc(r)
        assert "#my-chapter" in toc
