"""Tests for offline PlantUML rendering helpers."""

from pathlib import Path
from types import SimpleNamespace
from urllib.error import URLError

from scribpy.assets.plantuml import (
    EmbeddedPlantUmlRenderer,
    PlantUmlRenderError,
    WebPlantUmlRenderer,
    _encode6bit,
    validate_local_plantuml_environment,
    render_plantuml_blocks,
    render_plantuml_documents,
)
from scribpy.model import Document, MarkdownAst, TransformedDocument


class FakeRenderer:
    """Deterministic local renderer used by tests."""

    def render(self, source: str, output_format: str) -> bytes:
        """Return a tiny SVG payload."""
        assert output_format == "svg"
        return f"<svg>{source.strip()}</svg>".encode()


class FailingRenderer:
    """Renderer that simulates a local PlantUML failure."""

    def render(self, source: str, output_format: str) -> bytes:
        """Raise a render error."""
        raise RuntimeError("bad uml")


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


def test_render_plantuml_blocks_writes_svg_and_rewrites_markdown(
    tmp_path: Path,
) -> None:
    result = render_plantuml_blocks(
        "Before\n```plantuml\nAlice -> Bob\n```\nAfter\n",
        renderer=FakeRenderer(),
        output_dir=tmp_path / "assets/diagrams",
    )

    assert result.diagnostics == ()
    assert "![PlantUML diagram](assets/diagrams/plantuml-" in result.content
    assert len(result.artifacts) == 1
    svg = result.artifacts[0].path.read_text(encoding="utf-8")
    assert "<svg>Alice -> Bob</svg>" == svg


def test_render_plantuml_blocks_reports_unclosed_fence(tmp_path: Path) -> None:
    result = render_plantuml_blocks(
        "```plantuml\nAlice -> Bob\n",
        renderer=FakeRenderer(),
        output_dir=tmp_path,
    )

    assert result.artifacts == ()
    assert result.diagnostics[0].code == "UML001"


def test_render_plantuml_blocks_reports_renderer_failure(tmp_path: Path) -> None:
    result = render_plantuml_blocks(
        "```plantuml\nAlice -> Bob\n```\n",
        renderer=FailingRenderer(),
        output_dir=tmp_path,
    )

    assert result.artifacts == ()
    assert result.diagnostics[0].code == "UML002"


def test_embedded_renderer_invokes_local_jar(monkeypatch) -> None:
    """The embedded renderer shells out to the bundled local JAR."""
    seen: dict[str, object] = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["input"] = kwargs["input"]
        return SimpleNamespace(returncode=0, stdout=b"<svg/>", stderr=b"")

    monkeypatch.setattr("scribpy.assets.plantuml.subprocess.run", fake_run)

    rendered = EmbeddedPlantUmlRenderer().render("A -> B", "svg")

    assert rendered == b"<svg/>"
    assert seen["command"][0:3] == ("java", "-jar", seen["command"][2])
    assert seen["command"][-2:] == ("-tsvg", "-pipe")
    assert seen["input"] == b"A -> B"


def test_embedded_renderer_reports_local_process_error(monkeypatch) -> None:
    """PlantUML stderr becomes a Python exception."""

    def fake_run(command, **kwargs):
        return SimpleNamespace(returncode=1, stdout=b"", stderr=b"syntax error")

    monkeypatch.setattr("scribpy.assets.plantuml.subprocess.run", fake_run)

    try:
        EmbeddedPlantUmlRenderer().render("broken", "svg")
    except PlantUmlRenderError as exc:
        assert exc.backend == "local"
        assert str(exc) == "syntax error"
    else:
        raise AssertionError("Expected RuntimeError")


def test_validate_local_environment_reports_missing_java(monkeypatch) -> None:
    monkeypatch.setattr("scribpy.assets.plantuml.shutil.which", lambda _: None)

    diagnostics = validate_local_plantuml_environment()

    assert diagnostics[0].code == "UML004"


def test_validate_local_environment_accepts_java(monkeypatch) -> None:
    monkeypatch.setattr("scribpy.assets.plantuml.shutil.which", lambda _: "/bin/java")
    monkeypatch.setattr(
        "scribpy.assets.plantuml.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0),
    )

    assert validate_local_plantuml_environment() == ()


def test_validate_local_environment_reports_unexecutable_java(monkeypatch) -> None:
    monkeypatch.setattr("scribpy.assets.plantuml.shutil.which", lambda _: "/bin/java")

    def fail_run(*args, **kwargs):
        raise OSError("broken")

    monkeypatch.setattr("scribpy.assets.plantuml.subprocess.run", fail_run)

    diagnostics = validate_local_plantuml_environment()

    assert diagnostics[0].code == "UML004"


def test_web_renderer_fetches_svg(monkeypatch) -> None:
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

    monkeypatch.setattr("scribpy.assets.plantuml.urlopen", fake_urlopen)

    rendered = WebPlantUmlRenderer("https://example.test/plantuml").render(
        "A -> B", "svg"
    )

    assert rendered == b"<svg/>"
    assert seen["url"].startswith("https://example.test/plantuml/svg/")
    assert seen["user_agent"] == "python-plantuml"


def test_web_renderer_reports_server_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "scribpy.assets.plantuml.urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(URLError("offline")),
    )

    try:
        WebPlantUmlRenderer("https://example.test/plantuml").render("A -> B", "svg")
    except PlantUmlRenderError as exc:
        assert exc.backend == "web"
        assert "offline" in str(exc)
    else:
        raise AssertionError("Expected PlantUmlRenderError")


def test_encode_server_payload_uses_full_plantuml_alphabet() -> None:
    assert _encode6bit(62) == "-"
    assert _encode6bit(63) == "_"


def test_render_plantuml_blocks_reports_web_failure(tmp_path: Path) -> None:
    class FailingWebRenderer:
        def render(self, source: str, output_format: str) -> bytes:
            raise PlantUmlRenderError("web", "HTTP Error 403: Forbidden")

    result = render_plantuml_blocks(
        "```plantuml\nA -> B\n```\n",
        renderer=FailingWebRenderer(),
        output_dir=tmp_path,
    )

    assert result.diagnostics[0].code == "UML005"
    assert "server_url" in result.diagnostics[0].hint


def test_render_plantuml_blocks_reports_typed_local_failure(tmp_path: Path) -> None:
    class FailingLocalRenderer:
        def render(self, source: str, output_format: str) -> bytes:
            raise PlantUmlRenderError("local", "syntax error")

    result = render_plantuml_blocks(
        "```plantuml\nA -> B\n```\n",
        renderer=FailingLocalRenderer(),
        output_dir=tmp_path,
    )

    assert result.diagnostics[0].code == "UML002"
    assert "bundled PlantUML runtime" in result.diagnostics[0].hint


def test_server_encoding_uses_underscore_branch() -> None:
    from scribpy.assets.plantuml import _encode6bit

    assert _encode6bit(63) == "_"


def test_render_plantuml_blocks_reports_write_failure(tmp_path: Path) -> None:
    output_dir = tmp_path / "occupied"
    output_dir.write_text("not a directory", encoding="utf-8")

    result = render_plantuml_blocks(
        "```plantuml\nA -> B\n```\n",
        renderer=FakeRenderer(),
        output_dir=output_dir,
    )

    assert result.artifacts == ()
    assert result.diagnostics[0].code == "UML003"


def test_render_plantuml_documents_uses_nested_relative_links(
    tmp_path: Path,
) -> None:
    docs, artifacts, diagnostics = render_plantuml_documents(
        (_document("guide/page.md", "```plantuml\nA -> B\n```\n"),),
        renderer=FakeRenderer(),
        diagrams_dir=tmp_path / "assets/diagrams",
        flattened=False,
        target="html-site",
    )

    assert diagnostics == ()
    assert "../assets/diagrams/plantuml-" in docs[0].content
    assert artifacts[0].target == "html-site"


def test_render_plantuml_documents_deduplicates_identical_diagrams(
    tmp_path: Path,
) -> None:
    docs, artifacts, diagnostics = render_plantuml_documents(
        (
            _document("a.md", "```plantuml\nA -> B\n```\n"),
            _document("b.md", "```plantuml\nA -> B\n```\n"),
        ),
        renderer=FakeRenderer(),
        diagrams_dir=tmp_path / "assets/diagrams",
        flattened=True,
        target="html",
    )

    assert diagnostics == ()
    assert len(docs) == 2
    assert len(artifacts) == 1


def test_render_plantuml_documents_propagates_diagnostics(tmp_path: Path) -> None:
    original = (_document("index.md", "```plantuml\nA -> B\n"),)

    docs, artifacts, diagnostics = render_plantuml_documents(
        original,
        renderer=FakeRenderer(),
        diagrams_dir=tmp_path / "assets/diagrams",
        flattened=False,
        target="html-site",
    )

    assert docs == original
    assert artifacts == ()
    assert diagnostics[0].code == "UML001"


def test_render_plantuml_documents_root_page_uses_direct_asset_link(
    tmp_path: Path,
) -> None:
    docs, _, diagnostics = render_plantuml_documents(
        (_document("index.md", "```plantuml\nA -> B\n```\n"),),
        renderer=FakeRenderer(),
        diagrams_dir=tmp_path / "assets/diagrams",
        flattened=False,
        target="html-site",
    )

    assert diagnostics == ()
    assert "](assets/diagrams/" in docs[0].content
