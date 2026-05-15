"""State carried by the shared project preparation pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.config import Config
from scribpy.model import Document, DocumentIndex, SourceFile
from scribpy.model.protocols import FileSystem, MarkdownParser


@dataclass(frozen=True)
class ProjectPipelineState:
    """Intermediate products built while preparing a Scribpy project.

    Attributes:
        start: Initial root, child, or configuration path supplied by caller.
        filesystem: Filesystem service used by parsing steps.
        parser: Optional Markdown parser adapter override.
        config_path: Resolved path to ``scribpy.toml``.
        config: Parsed project configuration.
        project_root: Resolved project root directory.
        source_files: Source files discovered by the project scanner.
        index: Deterministic document index.
        ordered_files: Source files ordered by the document index.
        documents: Semantic documents produced by parsing.
    """

    start: Path
    filesystem: FileSystem
    parser: MarkdownParser | None
    config_path: Path | None = None
    config: Config | None = None
    project_root: Path | None = None
    source_files: tuple[SourceFile, ...] = ()
    index: DocumentIndex | None = None
    ordered_files: tuple[SourceFile, ...] = ()
    documents: tuple[Document, ...] = ()


__all__ = ["ProjectPipelineState"]
