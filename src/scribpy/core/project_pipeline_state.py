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

    def require_resolved(self) -> ResolvedPipelineState:
        """Return a fully-resolved view of the state with non-optional fields.

        Returns:
            Resolved state with all fields guaranteed non-None.

        Raises:
            AssertionError: If any required field is still ``None``.
        """
        assert self.config_path is not None, "config_path not resolved"
        assert self.config is not None, "config not loaded"
        assert self.project_root is not None, "project_root not resolved"
        assert self.index is not None, "document index not built"
        return ResolvedPipelineState(
            start=self.start,
            filesystem=self.filesystem,
            parser=self.parser,
            config_path=self.config_path,
            config=self.config,
            project_root=self.project_root,
            source_files=self.source_files,
            index=self.index,
            ordered_files=self.ordered_files,
            documents=self.documents,
        )


@dataclass(frozen=True)
class ResolvedPipelineState:
    """Fully-resolved pipeline state: all optional fields are guaranteed set.

    Obtain this via ``ProjectPipelineState.require_resolved()`` once the
    pipeline has completed all setup steps. Consumers receive typed, non-None
    fields and need no ``assert`` guards.

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
    config_path: Path
    config: Config
    project_root: Path
    source_files: tuple[SourceFile, ...]
    index: DocumentIndex
    ordered_files: tuple[SourceFile, ...]
    documents: tuple[Document, ...]


__all__ = ["ProjectPipelineState", "ResolvedPipelineState"]
