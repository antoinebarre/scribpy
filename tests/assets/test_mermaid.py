"""Tests for Mermaid web rendering helpers."""

from io import BytesIO
from pathlib import Path
from urllib.error import HTTPError, URLError

from scribpy.assets.mermaid import (
    MermaidRenderError,
    WebMermaidRenderer,
    _encode_mermaid_payload,
    render_mermaid_blocks,
    render_mermaid_documents,
)
from scribpy.model import Document, MarkdownAst, TransformedDocument


class FakeMermaidRenderer:
    """Deterministic renderer used by tests."""

    def render(self, source: str, output_format: str) -> bytes:
        """Return a tiny SVG payload."""
        assert output_format == "svg"
        return f"<svg>{source.strip()}</svg>".encode()


class FailingMermaidRenderer:
    """Renderer that simulates Mermaid web rendering failure."""

    def render(self, source: str, output_format: str) -> bytes:
        """Raise a render error."""
        raise MermaidRenderError("offline")


def _document(path: str, content: str) -> TransformedDocument:
    source = Document(
        path=Path("/project/doc") / path,
        relative_path=Path(path),
        source=content,
        frontmatter={},
        ast=MarkdownAst(backend="test", tokens=()),
        title=None,
        headings=(),
        links=(),
        assets=(),
    )
    return TransformedDocument(Path(path), content, source)


def test_render_mermaid_blocks_writes_svg_and_rewrites_markdown(
    tmp_path: Path,
) -> None:
    result = render_mermaid_blocks(
        "Before\n```mermaid\nflowchart LR\nA-->B\n```\nAfter\n",
        renderer=FakeMermaidRenderer(),  # type: ignore[arg-type]
        output_dir=tmp_path / "assets/diagrams",
    )

    assert result.diagnostics == ()
    assert "![Mermaid diagram](assets/diagrams/mermaid-" in result.content
    assert len(result.artifacts) == 1
    svg = result.artifacts[0].path.read_text(encoding="utf-8")
    assert "<svg>flowchart LR\nA-->B</svg>" == svg


def test_render_mermaid_blocks_reports_unclosed_fence(tmp_path: Path) -> None:
    result = render_mermaid_blocks(
        "```mermaid\nflowchart LR\nA-->B\n",
        renderer=FakeMermaidRenderer(),  # type: ignore[arg-type]
        output_dir=tmp_path,
    )

    assert result.artifacts == ()
    assert result.diagnostics[0].code == "MRM001"


def test_render_mermaid_blocks_reports_renderer_failure(tmp_path: Path) -> None:
    result = render_mermaid_blocks(
        "```mermaid\nflowchart LR\nA-->B\n```\n",
        renderer=FailingMermaidRenderer(),  # type: ignore[arg-type]
        output_dir=tmp_path,
    )

    assert result.artifacts == ()
    assert result.diagnostics[0].code == "MRM002"


def test_render_mermaid_blocks_reports_decode_failure(tmp_path: Path) -> None:
    class BinaryRenderer:
        def render(self, source: str, output_format: str) -> bytes:
            return b"\xff"

    result = render_mermaid_blocks(
        "```mermaid\nflowchart LR\nA-->B\n```\n",
        renderer=BinaryRenderer(),  # type: ignore[arg-type]
        output_dir=tmp_path,
    )

    assert result.diagnostics[0].code == "MRM002"


def test_render_mermaid_blocks_reports_write_failure(tmp_path: Path) -> None:
    blocked_dir = tmp_path / "blocked"
    blocked_dir.write_text("not a directory", encoding="utf-8")

    result = render_mermaid_blocks(
        "```mermaid\nflowchart LR\nA-->B\n```\n",
        renderer=FakeMermaidRenderer(),  # type: ignore[arg-type]
        output_dir=blocked_dir,
    )

    assert result.diagnostics[0].code == "MRM003"


def test_render_mermaid_documents_uses_nested_href_prefix(tmp_path: Path) -> None:
    documents, artifacts, diagnostics = render_mermaid_documents(
        (_document("guide/page.md", "```mermaid\nflowchart LR\nA-->B\n```\n"),),
        renderer=FakeMermaidRenderer(),  # type: ignore[arg-type]
        diagrams_dir=tmp_path / "assets/diagrams",
        flattened=False,
        target="html-site",
    )

    assert diagnostics == ()
    assert artifacts[0].target == "html-site"
    assert "../assets/diagrams/mermaid-" in documents[0].content


def test_render_mermaid_documents_stops_on_failure(tmp_path: Path) -> None:
    source = _document("index.md", "```mermaid\nflowchart LR\nA-->B\n```\n")

    documents, artifacts, diagnostics = render_mermaid_documents(
        (source,),
        renderer=FailingMermaidRenderer(),  # type: ignore[arg-type]
        diagrams_dir=tmp_path,
        flattened=True,
        target="html",
    )

    assert documents == (source,)
    assert artifacts == ()
    assert diagnostics[0].code == "MRM002"


def test_web_mermaid_renderer_fetches_svg(monkeypatch) -> None:
    seen: dict[str, str] = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self) -> bytes:
            return b"<svg/>"

    def fake_urlopen(request, timeout: int):
        seen["url"] = request.full_url
        seen["user_agent"] = request.get_header("User-agent")
        assert timeout == 30
        return FakeResponse()

    monkeypatch.setattr("scribpy.assets.mermaid_renderer.urlopen", fake_urlopen)

    rendered = WebMermaidRenderer("https://example.test", "forest").render(
        "flowchart LR\nA-->B", "svg"
    )

    assert rendered == b"<svg/>"
    assert seen["url"].startswith("https://example.test/svg/pako:")
    assert seen["user_agent"] == "scribpy-mermaid"


def test_web_mermaid_renderer_reports_http_failure(monkeypatch) -> None:
    def fail_urlopen(*args, **kwargs):
        raise HTTPError(
            url="https://example.test",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=BytesIO(b"bad diagram"),
        )

    monkeypatch.setattr("scribpy.assets.mermaid_renderer.urlopen", fail_urlopen)

    try:
        WebMermaidRenderer("https://example.test").render("broken", "svg")
    except MermaidRenderError as exc:
        assert "HTTP Error 400" in str(exc)
        assert "bad diagram" in str(exc)
    else:
        raise AssertionError("Expected MermaidRenderError")


def test_web_mermaid_renderer_reports_network_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "scribpy.assets.mermaid_renderer.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(URLError("offline")),
    )

    try:
        WebMermaidRenderer("https://example.test").render("A-->B", "svg")
    except MermaidRenderError as exc:
        assert "offline" in str(exc)
    else:
        raise AssertionError("Expected MermaidRenderError")


def test_web_mermaid_renderer_rejects_non_http_url() -> None:
    try:
        WebMermaidRenderer("file:///tmp/mermaid").render("A-->B", "svg")
    except MermaidRenderError as exc:
        assert "http or https" in str(exc)
    else:
        raise AssertionError("Expected MermaidRenderError")


def test_encode_mermaid_payload_uses_pako_prefix() -> None:
    encoded = _encode_mermaid_payload("flowchart LR\nA-->B", "default")

    assert encoded.startswith("pako:")
