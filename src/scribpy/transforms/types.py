"""Contracts for target-aware document transforms."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from scribpy.model import Diagnostic, Document, TransformedDocument

BuildTarget = Literal["markdown", "html"]
TocStyle = Literal["bullet", "numbered"]
NumberingStyle = Literal["decimal", "alpha", "roman"]
Transform = Callable[["TransformContext"], "TransformResult"]


@dataclass(frozen=True)
class TransformOptions:
    """Execution options shared by target-aware document transforms.

    Attributes:
        document_title: Global title to use for assembled outputs when relevant.
        toc_enabled: Whether to inject a generated table of contents.
        toc_max_level: Deepest heading level included in the table of contents.
        toc_style: Markdown list style used by the table of contents.
        numbering_enabled: Whether to prefix headings with generated section numbers.
        numbering_max_level: Deepest heading level that receives generated numbering.
        numbering_style: Number style used for section prefixes.
    """

    document_title: str | None = None
    toc_enabled: bool = True
    toc_max_level: int = 6
    toc_style: TocStyle = "bullet"
    numbering_enabled: bool = True
    numbering_max_level: int = 6
    numbering_style: NumberingStyle = "decimal"


@dataclass(frozen=True)
class TransformContext:
    """Inputs available to one transform execution.

    Attributes:
        target: Output target currently being prepared.
        documents: Parsed source documents in deterministic build order.
        transformed_documents: Current target-ready values.
        options: Shared execution options for target-aware transforms.
    """

    target: BuildTarget
    documents: tuple[Document, ...]
    transformed_documents: tuple[TransformedDocument, ...]
    options: TransformOptions = TransformOptions()

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


__all__ = [
    "BuildTarget",
    "NumberingStyle",
    "TocStyle",
    "Transform",
    "TransformContext",
    "TransformOptions",
    "TransformResult",
]
