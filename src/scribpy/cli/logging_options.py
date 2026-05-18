"""CLI helpers for Scribpy execution logging options."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path

from scribpy.logging import logging_context

_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")


def add_logging_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared logging arguments to the root parser.

    Args:
        parser: Parser to extend.
    """
    parser.add_argument(
        "--log-level",
        choices=_LOG_LEVELS,
        default=None,
        help="Enable execution logs at the selected level.",
    )
    parser.add_argument(
        "--log-console",
        action="store_true",
        help="Also write execution logs to stderr.",
    )
    parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help=(
            "Write logs to this file. Relative paths are resolved from the "
            "project root. Defaults to build/logs/scribpy.log when logging is enabled."
        ),
    )


def run_with_optional_logging(
    args: argparse.Namespace, action: Callable[[], int | None]
) -> int | None:
    """Run a command, enabling logs only when requested.

    Args:
        args: Parsed root CLI arguments.
        action: Command execution callback.

    Returns:
        Exit code returned by ``action``, or ``None`` when dispatch found no
        matching command.
    """
    if not (args.log_level or args.log_console or args.log_file):
        return action()
    with logging_context(
        level=args.log_level or "INFO",
        console=args.log_console,
        file=True,
        file_path=args.log_file,
    ):
        return action()


__all__ = ["add_logging_arguments", "run_with_optional_logging"]
