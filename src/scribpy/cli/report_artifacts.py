"""Artifact summaries for CLI reports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TextIO

from scribpy.model import BuildArtifact


def print_artifact_summary(
    artifacts: Sequence[BuildArtifact],
    stream: TextIO,
) -> None:
    """Print the primary artifact and optional extra artifact count.

    Args:
        artifacts: Build artifacts to summarize.
        stream: Output stream receiving the summary.
    """
    if not artifacts:
        return
    primary = primary_artifact(artifacts)
    print("", file=stream)
    print(f"Primary artifact: {primary.path}", file=stream)
    if len(artifacts) > 1:
        print(f"Additional artifacts: {len(artifacts) - 1}", file=stream)


def primary_artifact(artifacts: Sequence[BuildArtifact]) -> BuildArtifact:
    """Select the artifact that should be presented as primary.

    Args:
        artifacts: Non-empty artifact collection.

    Returns:
        The preferred artifact, or the first artifact when no preferred type
        exists.
    """
    preferred_types = ("document", "site", "page")
    for artifact_type in preferred_types:
        for artifact in artifacts:
            if artifact.artifact_type == artifact_type:
                return artifact
    return artifacts[0]


__all__ = ["primary_artifact", "print_artifact_summary"]
