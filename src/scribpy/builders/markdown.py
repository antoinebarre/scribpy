"""Markdown assembly and artifact writing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import FileSystem

MARKDOWN_OUTPUT_PATH = Path("build/markdown/document.md")


@dataclass(frozen=True)
class AssembledDocument:
    """Target-ready assembled Markdown payload.

    Attributes:
        content: Complete Markdown content ready to write.
    """

    content: str


def merge_documents(documents: tuple[TransformedDocument, ...]) -> AssembledDocument:
    """Merge documents into deterministic assembled Markdown content.

    Args:
        documents: Documents already ordered by the document index.

    Returns:
        Assembled Markdown payload separated by one blank line between
        non-empty documents and ending with one trailing newline when non-empty.
    """
    parts = [
        document.content.strip("\n")
        for document in documents
        if document.content.strip("\n")
    ]
    if not parts:
        return AssembledDocument(content="")
    return AssembledDocument(content="\n\n".join(parts) + "\n")


def write_markdown_artifact(
    project_root: Path,
    assembled: AssembledDocument,
    filesystem: FileSystem,
) -> tuple[BuildArtifact | None, tuple[Diagnostic, ...]]:
    """Write assembled Markdown and return its artifact descriptor.

    Args:
        project_root: Absolute project root directory.
        assembled: Target-ready Markdown payload.
        filesystem: Filesystem service used for writing.

    Returns:
        Artifact plus diagnostics. On failure the artifact is ``None`` and a
        ``BLD003`` diagnostic explains the write error.
    """
    artifact_path = project_root / MARKDOWN_OUTPUT_PATH
    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        filesystem.write_text(artifact_path, assembled.content)
    except Exception as exc:
        return None, (
            Diagnostic(
                severity="error",
                code="BLD003",
                message=f"Cannot write Markdown artifact: {exc}",
                path=artifact_path,
                hint="Check that the build directory is writable.",
            ),
        )

    return (
        BuildArtifact(
            path=artifact_path,
            target="markdown",
            artifact_type="document",
        ),
        (),
    )


__all__ = [
    "AssembledDocument",
    "MARKDOWN_OUTPUT_PATH",
    "merge_documents",
    "write_markdown_artifact",
]
