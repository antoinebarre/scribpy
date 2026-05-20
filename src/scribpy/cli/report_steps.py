"""Step rendering for CLI reports."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TextIO


def print_steps(steps: Sequence[tuple[str, bool]], stream: TextIO) -> None:
    """Print a compact list of workflow steps.

    Args:
        steps: Ordered pairs of step labels and success states.
        stream: Output stream receiving the rendered steps.
    """
    for label, succeeded in steps:
        mark = "✔" if succeeded else "✘"
        status = "done" if succeeded else "failed"
        print(f"{mark} {label} — {status}", file=stream)


__all__ = ["print_steps"]
