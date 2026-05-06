"""Typed result objects returned by application-level operations."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from scribpy.model.diagnostic import Diagnostic
from scribpy.model.document import Document


@dataclass(frozen=True)
class ParseResult:
    """Result of a Markdown parsing operation.

    Attributes:
        documents: Documents successfully parsed before completion. Failed
            parses may still contain partial results when other source files
            were valid.
        diagnostics: Diagnostics produced while reading, parsing, or extracting
            semantic document data.
        failed: Whether the operation should be considered failing.
    """

    documents: tuple[Document, ...]
    diagnostics: tuple[Diagnostic, ...]
    failed: bool


@dataclass(frozen=True)
class LintResult:
    """Result of a lint or validation operation.

    Attributes:
        diagnostics: Diagnostics produced during linting or validation.
        failed: Whether the operation should be considered failing according to
            the active lint policy.
    """

    diagnostics: tuple[Diagnostic, ...]
    failed: bool


@dataclass(frozen=True)
class BuildArtifact:
    """A build artifact produced by a builder or asset operation.

    Attributes:
        path: Path to the produced artifact.
        target: Build target that produced the artifact, such as ``"markdown"``,
            ``"html"``, ``"pdf"``, or ``"assets"``.
        artifact_type: Specific artifact category, such as ``"document"``,
            ``"page"``, ``"stylesheet"``, ``"image"``, or ``"diagram"``.
        metadata: Optional structured details about the artifact. Metadata is
            informational and must not be required to locate the artifact.
    """

    path: Path
    target: str
    artifact_type: str
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True)
class BuildResult:
    """Result of a build operation.

    Attributes:
        success: Whether the build completed successfully.
        artifacts: Artifacts produced before the build completed. Failed builds
            may still contain partial artifacts when a builder reports them.
        diagnostics: Diagnostics produced during the build.
    """

    success: bool
    artifacts: tuple[BuildArtifact, ...]
    diagnostics: tuple[Diagnostic, ...]


__all__ = ["BuildArtifact", "BuildResult", "LintResult", "ParseResult"]
