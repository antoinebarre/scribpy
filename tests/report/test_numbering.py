"""Tests for automatic section numbering."""

from scribpy.report.numbering import NumberingContext, numbered_title


class TestNumberingContext:
    def test_single_level(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()
        assert ctx.prefix() == "1."

    def test_two_items_same_level(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()
        ctx.next()
        assert ctx.prefix() == "2."

    def test_two_levels(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()
        ctx.push()
        ctx.next()
        assert ctx.prefix() == "1.1."

    def test_second_chapter_after_pop(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()        # chapter 1
        ctx.push()
        ctx.next()        # section 1.1
        ctx.pop()
        ctx.next()        # chapter 2
        assert ctx.prefix() == "2."

    def test_numbered_title(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()
        assert numbered_title("Intro", ctx) == "1. Intro"

    def test_nested_numbered_title(self):
        ctx = NumberingContext()
        ctx.push()
        ctx.next()
        ctx.push()
        ctx.next()
        assert numbered_title("Details", ctx) == "1.1. Details"
