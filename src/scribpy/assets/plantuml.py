"""Offline PlantUML rendering backed by the bundled MIT PlantUML JAR."""

from __future__ import annotations

import hashlib
import shutil
import subprocess  # nosec B404
import zlib
from dataclasses import dataclass, replace
from importlib import resources
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import DiagramRenderer

_PLANTUML_OPEN = "```plantuml"
_PLANTUML_CLOSE = "```"
_DIAGRAMS_DIR = PurePosixPath("assets/diagrams")
logger = get_logger(__name__)


@dataclass(frozen=True)
class PlantUmlRenderResult:
    """Rendered PlantUML content plus generated assets and diagnostics.

    Attributes:
        content: Markdown content after PlantUML fences have been replaced.
        artifacts: Generated local SVG artifacts.
        diagnostics: Rendering or write diagnostics.
    """

    content: str
    artifacts: tuple[BuildArtifact, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


class PlantUmlRenderError(RuntimeError):
    """Raised when one PlantUML backend cannot render a diagram.

    Attributes:
        backend: Renderer backend that failed, either ``"java"`` or ``"web"``.
    """

    def __init__(self, backend: str, detail: str) -> None:
        """Create a typed PlantUML render error.

        Args:
            backend: Renderer backend that failed.
            detail: Backend-specific failure detail.
        """
        super().__init__(detail)
        self.backend = backend


class JavaPlantUmlRenderer:
    """Render PlantUML through the JAR shipped inside Scribpy."""

    def render(self, source: str, output_format: str) -> bytes:
        """Render PlantUML source with the bundled JAR through Java.

        Args:
            source: Raw PlantUML source.
            output_format: Requested PlantUML output format.

        Returns:
            Rendered bytes produced by PlantUML.

        Raises:
            RuntimeError: If PlantUML cannot render the source.
            OSError: If Java cannot be executed.
        """
        jar_path = resources.files("scribpy").joinpath("vendor/plantuml-mit.jar")
        command = ("java", "-jar", str(jar_path), f"-t{output_format}", "-pipe")
        logger.debug("Executing bundled PlantUML renderer: %s", " ".join(command))
        completed = subprocess.run(
            command,
            input=source.encode("utf-8"),
            capture_output=True,
            check=False,
        )  # nosec B603
        if completed.returncode != 0:
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            logger.error(
                "Bundled PlantUML renderer failed: %s", detail or "<no stderr>"
            )
            raise PlantUmlRenderError("java", detail or "PlantUML rendering failed.")
        logger.debug("Bundled PlantUML renderer completed successfully")
        return completed.stdout


class WebPlantUmlRenderer:
    """Render PlantUML by calling a configured PlantUML web server."""

    _USER_AGENT = "python-plantuml"

    def __init__(self, server_url: str) -> None:
        """Create the web renderer.

        Args:
            server_url: Base PlantUML server URL, without the output path.
        """
        self._server_url = server_url.rstrip("/")

    def render(self, source: str, output_format: str) -> bytes:
        """Render PlantUML source through the configured web server.

        Args:
            source: Raw PlantUML source.
            output_format: Requested PlantUML output format.

        Returns:
            Rendered bytes returned by the server.

        Raises:
            RuntimeError: If the server cannot be reached.
        """
        encoded = _encode_server_payload(source)
        url = f"{self._server_url}/{output_format}/{encoded}"
        _validate_http_url(url)
        request = Request(url, headers={"User-Agent": self._USER_AGENT})
        logger.info("Rendering PlantUML through web server %s", self._server_url)
        try:
            with urlopen(request, timeout=30) as response:  # nosec B310
                return cast("bytes", response.read())
        except (OSError, URLError) as exc:
            raise PlantUmlRenderError("web", str(exc)) from exc


def validate_java_plantuml_environment() -> tuple[Diagnostic, ...]:
    """Check that Java PlantUML execution can start before the build begins.

    Returns:
        Diagnostics describing an unavailable Java runtime.
    """
    java = shutil.which("java")
    if java is None:
        return (_java_missing_diagnostic("Could not find the `java` executable."),)
    try:
        completed = subprocess.run(
            (java, "-version"),
            capture_output=True,
            check=False,
        )  # nosec B603
    except OSError as exc:
        return (_java_missing_diagnostic(f"Could not execute Java: {exc}"),)
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        return (
            _java_missing_diagnostic(
                detail or f"`java -version` exited with code {completed.returncode}."
            ),
        )
    return ()


def _validate_http_url(url: str) -> None:
    """Validate that a renderer URL targets an HTTP(S) endpoint."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise PlantUmlRenderError(
            "web", "PlantUML renderer URL must use http or https."
        )


def render_plantuml_blocks(
    content: str,
    *,
    renderer: DiagramRenderer,
    output_dir: Path,
    href_prefix: PurePosixPath = _DIAGRAMS_DIR,
    target: str = "html",
) -> PlantUmlRenderResult:
    """Render fenced PlantUML blocks to local SVG image references.

    Args:
        content: Markdown content that may contain fenced ``plantuml`` blocks.
        renderer: Local diagram renderer adapter.
        output_dir: Absolute destination directory for generated SVG files.
        href_prefix: Relative output path used in generated Markdown links.
        target: Artifact target label.

    Returns:
        Rewritten content plus generated artifacts and diagnostics.
    """
    rewritten: list[str] = []
    artifacts: list[BuildArtifact] = []
    lines = content.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() != _PLANTUML_OPEN:
            rewritten.append(line)
            index += 1
            continue

        index += 1
        source_lines: list[str] = []
        while index < len(lines) and lines[index].strip() != _PLANTUML_CLOSE:
            source_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return PlantUmlRenderResult(
                content=content,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="UML001",
                        message="Unclosed PlantUML fenced block.",
                        hint="Close the block with a line containing only ```.",
                    ),
                ),
            )

        source = "".join(source_lines)
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        filename = f"plantuml-{digest}.svg"
        artifact_path = output_dir / filename
        logger.info("Rendering PlantUML block %s to %s", digest, artifact_path)
        try:
            svg = renderer.render(source, "svg").decode("utf-8")
        except PlantUmlRenderError as exc:
            logger.error("PlantUML block %s failed to render: %s", digest, exc)
            return PlantUmlRenderResult(
                content=content,
                diagnostics=(_render_failure_diagnostic(exc),),
            )
        except (OSError, RuntimeError, UnicodeDecodeError) as exc:
            logger.error("PlantUML block %s failed to render: %s", digest, exc)
            return PlantUmlRenderResult(
                content=content,
                diagnostics=(_java_render_failure_diagnostic(str(exc)),),
            )
        try:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(svg, encoding="utf-8")
        except Exception as exc:
            logger.error("PlantUML block %s failed to write: %s", digest, exc)
            return PlantUmlRenderResult(
                content=content,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="UML003",
                        message=f"Cannot write PlantUML SVG asset: {exc}",
                        path=artifact_path,
                        hint="Check that the build directory is writable.",
                    ),
                ),
            )
        artifacts.append(BuildArtifact(artifact_path, target, "diagram"))
        logger.info("Rendered PlantUML block %s", digest)
        rewritten.append(f"![PlantUML diagram]({href_prefix / filename})\n")
        index += 1
    return PlantUmlRenderResult(
        content="".join(rewritten),
        artifacts=tuple(artifacts),
    )


def render_plantuml_documents(
    documents: tuple[TransformedDocument, ...],
    *,
    renderer: DiagramRenderer,
    diagrams_dir: Path,
    flattened: bool,
    target: str,
) -> tuple[
    tuple[TransformedDocument, ...], tuple[BuildArtifact, ...], tuple[Diagnostic, ...]
]:
    """Render PlantUML blocks across transformed documents.

    Args:
        documents: Target-ready Markdown documents.
        renderer: Local PlantUML renderer adapter.
        diagrams_dir: Absolute destination directory for generated SVGs.
        flattened: Whether all documents will be merged into one output page.
        target: Artifact target label.

    Returns:
        Rewritten documents, unique diagram artifacts, and diagnostics.
    """
    rendered_documents: list[TransformedDocument] = []
    artifacts: dict[Path, BuildArtifact] = {}
    for document in documents:
        logger.debug("Scanning %s for PlantUML blocks", document.relative_path)
        href_prefix = _href_prefix(document, flattened)
        result = render_plantuml_blocks(
            document.content,
            renderer=renderer,
            output_dir=diagrams_dir,
            href_prefix=href_prefix,
            target=target,
        )
        if result.diagnostics:
            logger.error(
                "PlantUML rendering stopped while processing %s",
                document.relative_path,
            )
            return documents, (), result.diagnostics
        rendered_documents.append(replace(document, content=result.content))
        artifacts.update({artifact.path: artifact for artifact in result.artifacts})
    return tuple(rendered_documents), tuple(artifacts.values()), ()


def _href_prefix(
    document: TransformedDocument,
    flattened: bool,
) -> PurePosixPath:
    """Return the correct relative diagrams path for one output mode."""
    if flattened or document.relative_path.parent == Path("."):
        return _DIAGRAMS_DIR
    depth = len(document.relative_path.parent.parts)
    return PurePosixPath(*([".."] * depth), *_DIAGRAMS_DIR.parts)


def _java_missing_diagnostic(detail: str) -> Diagnostic:
    """Create the early Java-environment diagnostic."""
    return Diagnostic(
        severity="error",
        code="UML004",
        message=f"Java PlantUML renderer is unavailable: {detail}",
        hint=(
            "Install a Java runtime and ensure `java` is available on PATH, "
            "or configure builders.html.plantuml.renderer = 'web'."
        ),
    )


def _render_failure_diagnostic(error: PlantUmlRenderError) -> Diagnostic:
    """Return a backend-specific PlantUML render diagnostic."""
    if error.backend == "web":
        return Diagnostic(
            severity="error",
            code="UML005",
            message=f"PlantUML web rendering failed: {error}",
            hint=(
                "Check builders.html.plantuml.server_url and server policy, "
                "or use a self-hosted PlantUML server."
            ),
        )
    return _java_render_failure_diagnostic(str(error))


def _java_render_failure_diagnostic(detail: str) -> Diagnostic:
    """Return a Java-renderer failure diagnostic."""
    return Diagnostic(
        severity="error",
        code="UML002",
        message=f"Cannot render PlantUML block: {detail}",
        hint=(
            "Ensure the bundled PlantUML runtime can execute through Java and "
            "the diagram syntax is valid."
        ),
    )


def _encode_server_payload(source: str) -> str:
    """Encode PlantUML source using the server URL format."""
    compressed = zlib.compress(source.encode("utf-8"))[2:-4]
    return "".join(
        _encode6bit(byte >> 2)
        + _encode6bit(((byte & 0x3) << 4) | (next_byte >> 4))
        + _encode6bit(((next_byte & 0xF) << 2) | (last_byte >> 6))
        + _encode6bit(last_byte & 0x3F)
        for byte, next_byte, last_byte in _triples(compressed)
    )


def _triples(payload: bytes) -> tuple[tuple[int, int, int], ...]:
    """Pad compressed bytes into triples."""
    padded = payload + b"\0" * ((3 - len(payload) % 3) % 3)
    return tuple(
        (padded[index], padded[index + 1], padded[index + 2])
        for index in range(0, len(padded), 3)
    )


def _encode6bit(value: int) -> str:
    """Encode one six-bit PlantUML server symbol."""
    if value < 10:
        return chr(48 + value)
    value -= 10
    if value < 26:
        return chr(65 + value)
    value -= 26
    if value < 26:
        return chr(97 + value)
    value -= 26
    return "-" if value == 0 else "_"


__all__ = [
    "JavaPlantUmlRenderer",
    "PlantUmlRenderError",
    "PlantUmlRenderResult",
    "WebPlantUmlRenderer",
    "render_plantuml_blocks",
    "render_plantuml_documents",
    "validate_java_plantuml_environment",
]
