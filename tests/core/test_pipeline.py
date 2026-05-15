"""Tests for generic result-pipeline behavior."""

from scribpy.core.pipeline import PipelineResult
from scribpy.model import Diagnostic


def test_bind_accumulates_diagnostics_across_successful_steps() -> None:
    warning = Diagnostic(severity="warning", code="T001", message="warn")

    result = PipelineResult.ok(1).bind(
        lambda value: PipelineResult.ok(value + 1, (warning,))
    )

    assert result.value == 2
    assert result.diagnostics == (warning,)
    assert result.failed is False


def test_bind_short_circuits_failed_result() -> None:
    error = Diagnostic(severity="error", code="T002", message="fail")

    result = PipelineResult.fail((error,), value=1).bind(
        lambda value: PipelineResult.ok(value + 1)
    )

    assert result.value is None
    assert result.diagnostics == (error,)
    assert result.failed is True


def test_bind_short_circuits_missing_value() -> None:
    result = PipelineResult[int](value=None).bind(
        lambda value: PipelineResult.ok(value + 1)
    )

    assert result.value is None
    assert result.failed is True
