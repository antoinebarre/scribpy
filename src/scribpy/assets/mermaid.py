"""Mermaid web rendering for fenced Markdown blocks."""

from __future__ import annotations

import base64
import hashlib
import json
import zlib
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from scribpy.logging import get_logger
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument

_MERMAID_OPEN = "```mermaid"
_MERMAID_CLOSE = "```"
_DIAGRAMS_DIR = PurePosixPath("assets/diagrams")
logger = get_logger(__name__)


@dataclass(frozen=True)
class MermaidRenderResult:
    """Rendered Mermaid content plus generated assets and diagnostics.

    Attributes:
        content: Markdown content after Mermaid fences have been replaced.
        artifacts: Generated local SVG artifacts.
        diagnostics: Rendering or write diagnostics.
    """

    content: str
    artifacts: tuple[BuildArtifact, ...] = ()
    diagnostics: tuple[Diagnostic, ...] = ()


class MermaidRenderError(RuntimeError):
    """Raised when the Mermaid web renderer cannot render a diagram."""


class WebMermaidRenderer:
    """Render Mermaid diagrams through a Mermaid web service."""

    _USER_AGENT = "scribpy-mermaid"

    def __init__(self, server_url: str, theme: str = "default") -> None:
        """Create the web renderer.

        Args:
            server_url: Base Mermaid server URL, for example
                ``https://mermaid.ink``.
            theme: Mermaid theme passed to the rendering service.
        """
        self._server_url = server_url.rstrip("/")
        self._theme = theme

    def render(self, source: str, output_format: str) -> bytes:
        """Render Mermaid source through the configured web server.

        Args:
            source: Raw Mermaid source.
            output_format: Requested Mermaid output format.

        Returns:
            Rendered bytes returned by the server.

        Raises:
            MermaidRenderError: If the server cannot render the diagram.
        """
        encoded = _encode_mermaid_payload(source, self._theme)
        url = f"{self._server_url}/{output_format}/{encoded}"
        request = Request(url, headers={"User-Agent": self._USER_AGENT})
        logger.info(
            "Rendering Mermaid through web server %s with theme %s",
            self._server_url,
            self._theme,
        )
        logger.debug("Mermaid encoded payload length: %d", len(encoded))
        try:
            with urlopen(request, timeout=30) as response:
                return cast("bytes", response.read())
        except HTTPError as exc:
            detail = exc.read(500).decode("utf-8", errors="replace").strip()
            reason = f"HTTP Error {exc.code}: {exc.reason}"
            raise MermaidRenderError(
                f"{reason}: {detail}" if detail else reason
            ) from exc
        except (OSError, URLError) as exc:
            raise MermaidRenderError(str(exc)) from exc


def render_mermaid_blocks(
    content: str,
    *,
    renderer: WebMermaidRenderer,
    output_dir: Path,
    href_prefix: PurePosixPath = _DIAGRAMS_DIR,
    target: str = "html",
    source_label: str | None = None,
) -> MermaidRenderResult:
    """Render fenced Mermaid blocks to local SVG image references.

    Args:
        content: Markdown content that may contain fenced ``mermaid`` blocks.
        renderer: Mermaid web renderer adapter.
        output_dir: Absolute destination directory for generated SVG files.
        href_prefix: Relative output path used in generated Markdown links.
        target: Artifact target label.
        source_label: Optional source document label used in logs.

    Returns:
        Rewritten content plus generated artifacts and diagnostics.
    """
    rewritten: list[str] = []
    artifacts: list[BuildArtifact] = []
    lines = content.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        line = lines[index]
        if line.strip() != _MERMAID_OPEN:
            rewritten.append(line)
            index += 1
            continue

        index += 1
        source_lines: list[str] = []
        while index < len(lines) and lines[index].strip() != _MERMAID_CLOSE:
            source_lines.append(lines[index])
            index += 1
        if index >= len(lines):
            return MermaidRenderResult(
                content=content,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="MRM001",
                        message="Unclosed Mermaid fenced block.",
                        hint="Close the block with a line containing only ```.",
                    ),
                ),
            )

        source = "".join(source_lines)
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]
        filename = f"mermaid-{digest}.svg"
        artifact_path = output_dir / filename
        label = source_label or "<unknown document>"
        logger.info(
            "Rendering Mermaid block %s from %s to %s",
            digest,
            label,
            artifact_path,
        )
        try:
            svg = renderer.render(source, "svg").decode("utf-8")
        except (MermaidRenderError, UnicodeDecodeError) as exc:
            logger.error(
                "Mermaid block %s from %s failed to render: %s",
                digest,
                label,
                exc,
            )
            return MermaidRenderResult(
                content=content,
                diagnostics=(_render_failure_diagnostic(str(exc)),),
            )
        try:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_text(svg, encoding="utf-8")
        except Exception as exc:
            logger.error(
                "Mermaid block %s from %s failed to write: %s",
                digest,
                label,
                exc,
            )
            return MermaidRenderResult(
                content=content,
                diagnostics=(
                    Diagnostic(
                        severity="error",
                        code="MRM003",
                        message=f"Cannot write Mermaid SVG asset: {exc}",
                        path=artifact_path,
                        hint="Check that the build directory is writable.",
                    ),
                ),
            )
        artifacts.append(BuildArtifact(artifact_path, target, "diagram"))
        logger.info("Rendered Mermaid block %s from %s", digest, label)
        rewritten.append(f"![Mermaid diagram]({href_prefix / filename})\n")
        index += 1
    return MermaidRenderResult(content="".join(rewritten), artifacts=tuple(artifacts))


def render_mermaid_documents(
    documents: tuple[TransformedDocument, ...],
    *,
    renderer: WebMermaidRenderer,
    diagrams_dir: Path,
    flattened: bool,
    target: str,
) -> tuple[
    tuple[TransformedDocument, ...], tuple[BuildArtifact, ...], tuple[Diagnostic, ...]
]:
    """Render Mermaid blocks across transformed documents.

    Args:
        documents: Target-ready Markdown documents.
        renderer: Mermaid web renderer adapter.
        diagrams_dir: Absolute destination directory for generated SVGs.
        flattened: Whether all documents will be merged into one output page.
        target: Artifact target label.

    Returns:
        Rewritten documents, unique diagram artifacts, and diagnostics.
    """
    rendered_documents: list[TransformedDocument] = []
    artifacts: dict[Path, BuildArtifact] = {}
    for document in documents:
        logger.debug("Scanning %s for Mermaid blocks", document.relative_path)
        href_prefix = _href_prefix(document, flattened)
        result = render_mermaid_blocks(
            document.content,
            renderer=renderer,
            output_dir=diagrams_dir,
            href_prefix=href_prefix,
            target=target,
            source_label=str(document.relative_path),
        )
        if result.diagnostics:
            logger.error(
                "Mermaid rendering stopped while processing %s",
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


def _render_failure_diagnostic(detail: str) -> Diagnostic:
    """Return a Mermaid web-renderer failure diagnostic."""
    return Diagnostic(
        severity="error",
        code="MRM002",
        message=f"Mermaid web rendering failed: {detail}",
        hint=(
            "Check builders.html.mermaid.server_url, Mermaid syntax, "
            "and network access to the configured rendering service."
        ),
    )


def _encode_mermaid_payload(source: str, theme: str) -> str:
    """Encode Mermaid source using the mermaid.ink pako URL format."""
    payload = json.dumps(
        {"code": source, "mermaid": {"theme": theme}},
        separators=(",", ":"),
    ).encode("utf-8")
    compressed = zlib.compress(payload)
    encoded = base64.urlsafe_b64encode(compressed).decode("ascii").rstrip("=")
    return f"pako:{encoded}"


__all__ = [
    "MermaidRenderError",
    "MermaidRenderResult",
    "WebMermaidRenderer",
    "render_mermaid_blocks",
    "render_mermaid_documents",
]
