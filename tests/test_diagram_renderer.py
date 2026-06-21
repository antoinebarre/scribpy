"""Tests for scribpy.core.diagram_renderer."""

from __future__ import annotations

import pytest

from scribpy.config import RenderMode
from scribpy.core.diagram_renderer import (
    _REGISTRY,
    get_renderer,
    register_renderer,
    render_all_diagrams,
    render_diagram,
)
from scribpy.core.document import DiagramBlock
from scribpy.errors import DiagramRenderError


class _FakeRenderer:
    """A fake renderer for testing dispatch."""

    def __init__(self, svg: str = "<svg>ok</svg>") -> None:
        """Initialise with a fixed SVG response.

        Args:
            svg: The SVG string to return on render.
        """
        self.svg = svg
        self.calls: list[str] = []

    def render(self, source: str) -> str:
        """Record the call and return the fixed SVG.

        Args:
            source: Diagram source (recorded).

        Returns:
            The fixed SVG string.
        """
        self.calls.append(source)
        return self.svg


class _FailingRenderer:
    """A renderer that always raises DiagramRenderError."""

    def render(self, source: str) -> str:  # noqa: ARG002
        """Always fail.

        Args:
            source: Ignored.

        Raises:
            DiagramRenderError: Always.
        """
        raise DiagramRenderError(
            block_name="test",
            engine="test",
            mode="test",
            reason="forced failure",
        )


@pytest.fixture(autouse=True)
def _clean_registry() -> None:
    """Clear the renderer registry before each test.

    Requirement: Tests are isolated from global registry state.
    """
    _REGISTRY.clear()


class TestRegisterRenderer:
    """Tests for register_renderer."""

    def test_registers_and_retrieves(self) -> None:
        """Requirement: Registered renderer is retrievable."""
        fake = _FakeRenderer()
        register_renderer("plantuml", RenderMode.WEB, fake)

        result = get_renderer("plantuml", RenderMode.WEB)
        assert result is fake

    def test_get_unregistered_raises(self) -> None:
        """Requirement: Unregistered combo raises DiagramRenderError."""
        with pytest.raises(DiagramRenderError) as exc_info:
            get_renderer("plantuml", RenderMode.OFFLINE)

        assert exc_info.value.engine == "plantuml"
        assert exc_info.value.mode == "offline"


class TestRenderDiagram:
    """Tests for render_diagram."""

    def test_dispatches_to_correct_renderer(self) -> None:
        """Requirement: Dispatch uses engine+mode composite key."""
        fake_web = _FakeRenderer("<svg>web</svg>")
        fake_offline = _FakeRenderer("<svg>offline</svg>")
        register_renderer("mermaid", RenderMode.WEB, fake_web)
        register_renderer("mermaid", RenderMode.OFFLINE, fake_offline)

        block = DiagramBlock(engine="mermaid", source="graph TD", index=0)

        result = render_diagram(block, RenderMode.WEB)
        assert result == "<svg>web</svg>"
        assert fake_web.calls == ["graph TD"]
        assert fake_offline.calls == []

    def test_wraps_unexpected_exception(self) -> None:
        """Requirement: Non-DiagramRenderError is wrapped."""

        class _BadRenderer:
            def render(self, source: str) -> str:  # noqa: ARG002
                msg = "unexpected"
                raise RuntimeError(msg)

        register_renderer(
            "plantuml",
            RenderMode.WEB,
            _BadRenderer(),
        )
        block = DiagramBlock(
            engine="plantuml",
            source="@startuml",
            index=0,
        )

        with pytest.raises(DiagramRenderError) as exc_info:
            render_diagram(block, RenderMode.WEB)

        assert "unexpected" in exc_info.value.reason


class TestRenderAllDiagrams:
    """Tests for render_all_diagrams."""

    def test_renders_all_blocks(self) -> None:
        """Requirement: All blocks are rendered and indexed."""
        fake = _FakeRenderer("<svg/>")
        register_renderer("plantuml", RenderMode.WEB, fake)
        register_renderer("mermaid", RenderMode.WEB, fake)

        blocks = (
            DiagramBlock(engine="plantuml", source="A", index=0),
            DiagramBlock(engine="mermaid", source="B", index=1),
        )

        results = render_all_diagrams(blocks, RenderMode.WEB)

        assert results == {0: "<svg/>", 1: "<svg/>"}

    def test_failure_skips_block_without_stopping(self) -> None:
        """Requirement: One failure does not stop others (REQ-018)."""
        register_renderer(
            "plantuml",
            RenderMode.WEB,
            _FailingRenderer(),
        )
        register_renderer(
            "mermaid",
            RenderMode.WEB,
            _FakeRenderer("<svg>ok</svg>"),
        )

        blocks = (
            DiagramBlock(engine="plantuml", source="fail", index=0),
            DiagramBlock(engine="mermaid", source="ok", index=1),
        )

        results = render_all_diagrams(blocks, RenderMode.WEB)

        assert 0 not in results
        assert results[1] == "<svg>ok</svg>"

    def test_empty_blocks(self) -> None:
        """Requirement: Empty input yields empty results."""
        results = render_all_diagrams((), RenderMode.WEB)
        assert results == {}
