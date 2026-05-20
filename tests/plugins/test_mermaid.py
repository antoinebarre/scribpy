"""Tests for the internal Mermaid code-block plugin."""

from pathlib import Path

from scribpy.config.types import MermaidConfig
from scribpy.model import Document, MarkdownAst, TransformedDocument
from scribpy.plugins.mermaid import MermaidPlugin


class FakeRenderer:
    """Deterministic Mermaid renderer."""

    def render(self, source: str, output_format: str) -> bytes:
        """Return a tiny SVG payload."""
        return b"<svg/>"


def _document(content: str) -> TransformedDocument:
    source = Document(
        path=Path("/project/doc/index.md"),
        relative_path=Path("index.md"),
        source=content,
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=(),
    )
    return TransformedDocument(Path("index.md"), content, source)


def test_mermaid_plugin_detects_blocks() -> None:
    plugin = MermaidPlugin(MermaidConfig(), FakeRenderer())  # type: ignore[arg-type]

    assert plugin.has_blocks("```mermaid\nflowchart LR\nA-->B\n```\n") is True
    assert plugin.has_blocks("```plantuml\nA -> B\n```\n") is False


def test_mermaid_plugin_has_no_preflight_diagnostics() -> None:
    plugin = MermaidPlugin(MermaidConfig(), FakeRenderer())  # type: ignore[arg-type]

    assert plugin.preflight() == ()


def test_mermaid_plugin_renders_documents(tmp_path: Path) -> None:
    plugin = MermaidPlugin(MermaidConfig(), FakeRenderer())  # type: ignore[arg-type]

    documents, artifacts, diagnostics = plugin.render_documents(
        (_document("```mermaid\nflowchart LR\nA-->B\n```\n"),),
        output_dir=tmp_path / "assets",
        flattened=True,
        target="html",
    )

    assert diagnostics == ()
    assert artifacts[0].artifact_type == "diagram"
    assert "mermaid-" in documents[0].content
