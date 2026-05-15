"""Minimal result-pipeline primitive for functional chains."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from scribpy.model import Diagnostic


@dataclass(frozen=True)
class PipelineResult[T]:
    """Value plus diagnostics flowing through a functional chain."""

    value: T | None
    diagnostics: tuple[Diagnostic, ...] = ()
    failed: bool = False

    @classmethod
    def ok(
        cls,
        value: T,
        diagnostics: tuple[Diagnostic, ...] = (),
    ) -> PipelineResult[T]:
        """Build a successful pipeline result."""
        return cls(value=value, diagnostics=diagnostics, failed=False)

    @classmethod
    def fail(
        cls,
        diagnostics: tuple[Diagnostic, ...],
        value: T | None = None,
    ) -> PipelineResult[T]:
        """Build a failed pipeline result, optionally preserving a value."""
        return cls(value=value, diagnostics=diagnostics, failed=True)

    def bind[U](
        self,
        step: Callable[[T], PipelineResult[U]],
    ) -> PipelineResult[U]:
        """Apply the next step unless the pipeline has already failed."""
        if self.failed or self.value is None:
            return PipelineResult(value=None, diagnostics=self.diagnostics, failed=True)

        next_result = step(self.value)
        return PipelineResult(
            value=next_result.value,
            diagnostics=(*self.diagnostics, *next_result.diagnostics),
            failed=next_result.failed,
        )


__all__ = ["PipelineResult"]
