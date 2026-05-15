"""Shared context passed to lint rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scribpy.model import Document, DocumentIndex


@dataclass(frozen=True)
class LintContext:
    """Immutable data needed by documentation lint rules."""

    source_root: Path
    documents: tuple[Document, ...]
    document_index: DocumentIndex

    @property
    def documents_by_path(self) -> dict[Path, Document]:
        """Return documents keyed by source-relative path."""
        return {document.relative_path: document for document in self.documents}


__all__ = ["LintContext"]
