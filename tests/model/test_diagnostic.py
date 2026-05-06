"""Tests for scribpy.model.diagnostic."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from scribpy.model import Diagnostic


def test_diagnostic_stores_required_fields() -> None:
    diagnostic = Diagnostic(
        severity="error",
        code="LINT001",
        message="Missing H1 heading",
    )

    assert diagnostic.severity == "error"
    assert diagnostic.code == "LINT001"
    assert diagnostic.message == "Missing H1 heading"
    assert diagnostic.path is None
    assert diagnostic.line is None
    assert diagnostic.hint is None


def test_diagnostic_stores_optional_location_and_hint() -> None:
    path = Path("docs/index.md")
    diagnostic = Diagnostic(
        severity="warning",
        code="LINT007",
        message="Trailing whitespace",
        path=path,
        line=42,
        hint="Remove the trailing spaces.",
    )

    assert diagnostic.path == path
    assert diagnostic.line == 42
    assert diagnostic.hint == "Remove the trailing spaces."


def test_diagnostic_is_frozen() -> None:
    diagnostic = Diagnostic(
        severity="info",
        code="INFO001",
        message="Document checked",
    )

    with pytest.raises(FrozenInstanceError):
        diagnostic.message = "Updated"
