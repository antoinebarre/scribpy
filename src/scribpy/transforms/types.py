"""Contracts for target-aware document transforms."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scribpy.model import Diagnostic, Document, TransformedDocument

BuildTarget = Literal["markdown", "html"]
Transform = Callable[["TransformContext"], "TransformResult"]


@dataclass(frozen=True)
class TransformContext:
    """Inputs available to one transform execution.

    Attributes:
        target: Output target currently being prepared.
        documents: Parsed source documents in deterministic build order.
        transformed_documents: Current target-ready values.
    """

    target: BuildTarget
    documents: tuple[Document, ...]
    transformed_documents: tuple[TransformedDocument, ...]

    @property
    def source_documents_by_path(self) -> dict[Path, Document]:
        """Return parsed source documents keyed by relative path.

        Returns:
            Parsed source documents keyed by relative path.
        """
        return {document.relative_path: document for document in self.documents}


@dataclass(frozen=True)
class TransformResult:
    """Result returned by one transform stage.

    Attributes:
        documents: Updated target-ready documents.
        diagnostics: Diagnostics emitted by the transform.
    """

    documents: tuple[TransformedDocument, ...]
    diagnostics: tuple[Diagnostic, ...] = ()


__all__ = ["BuildTarget", "Transform", "TransformContext", "TransformResult"]
