"""CLI argument helpers shared by build subcommands."""

from __future__ import annotations

import argparse
from pathlib import Path

_OUTPUT_DIR_HELP = (
    "Build directory override. Relative paths are resolved from the project "
    "root; absolute paths are used as-is."
)


def add_output_dir_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared build output directory override argument.

    Args:
        parser: Build subcommand parser to extend.
    """
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=_OUTPUT_DIR_HELP,
    )


__all__ = ["add_output_dir_argument"]
