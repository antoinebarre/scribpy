"""Command-line parser and command dispatch."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from scribpy.core import run_index_check
from scribpy.utils import format_diagnostics


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Scribpy command-line entry point.

    Args:
        argv: Optional command arguments excluding the executable name. When
            omitted, arguments are read from ``sys.argv``.

    Returns:
        Process exit code. ``0`` means success, ``1`` means user-facing
        diagnostics contain at least one error, and ``2`` means invalid CLI
        usage.
    """
    return _main(argv, stderr=sys.stderr)


def _main(argv: Sequence[str] | None, stderr: TextIO) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return _exit_code(error)

    if args.command == "index" and args.index_command == "check":
        return _run_index_check_command(args.root, stderr)

    parser.print_help(file=stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scribpy")
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser("index", help="Manage the document index")
    index_subparsers = index_parser.add_subparsers(dest="index_command")

    check_parser = index_subparsers.add_parser(
        "check",
        help="Validate project source discovery and document index configuration",
    )
    check_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root, path inside a project, or path to scribpy.toml",
    )

    return parser


def _run_index_check_command(root: Path | None, stderr: TextIO) -> int:
    result = run_index_check(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    return 1 if result.failed else 0


def _exit_code(error: SystemExit) -> int:
    if isinstance(error.code, int):
        return error.code
    return 2


__all__ = ["main"]
