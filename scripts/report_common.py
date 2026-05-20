"""Shared helpers for quality-check report scripts."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Allow running scripts from the repo root without installing the package.
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from quality_config import load_quality_config

from scribpy.report import Metadata

_PROJECT_NAME = load_quality_config().project_name


def now_iso() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")


def base_metadata(title: str, check: str) -> Metadata:
    """Build standard frontmatter for a check report.

    Args:
        title: Human-readable report title.
        check: Short check identifier (e.g. ``"lint"``).

    Returns:
        A ``Metadata`` instance pre-filled with standard fields.
    """
    return Metadata(
        title=title,
        date=now_iso(),
        extra={"check": check, "generator": f"{_PROJECT_NAME}.report"},
    )
