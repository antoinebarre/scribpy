"""Command-line parser and command dispatch."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from scribpy.core import DemoVariant, create_demo_project, run_index_check
from scribpy.utils import format_diagnostics

_VALID_DEMO_VARIANTS = ("valid", "invalid")
_ROOT_DESCRIPTION = """\
Scribpy command-line tools for Docs-as-Code project checks and tutorial setup.

The CLI is intentionally small: it parses commands, calls application services,
prints diagnostics, and returns stable exit codes.
"""
_ROOT_EPILOG = """\
Common workflows:
  1. Create a valid tutorial project:
       scribpy demo create dd1

  2. Validate the generated project:
       scribpy index check --root dd1

  3. Create a broken tutorial project to learn diagnostics:
       scribpy demo create dd1 --variant invalid --force
       scribpy index check --root dd1

More help:
  scribpy demo create -h
  scribpy index check -h
"""
_INDEX_DESCRIPTION = """\
Inspect project source discovery and document index configuration.

Index commands do not parse Markdown content yet. They only validate the phase
2 project-context chain: configuration loading, source discovery, and document
index consistency.
"""
_INDEX_EPILOG = """\
Examples:
  scribpy index check --root dd1
  scribpy index check --root dd1/scribpy.toml
  scribpy index check

Use `scribpy demo create dd1` first if you need a project to try.
"""
_INDEX_CHECK_DESCRIPTION = """\
Validate that a Scribpy project can load scribpy.toml, discover Markdown files,
and build a coherent DocumentIndex.

The command prints diagnostics to stderr. A valid project prints nothing and
returns exit code 0.
"""
_INDEX_CHECK_EPILOG = """\
Examples:
  scribpy index check --root dd1
  scribpy index check --root dd1/scribpy.toml
  scribpy index check --root .

What is checked:
  - scribpy.toml can be found and loaded
  - paths.source exists and stays inside the project
  - Markdown files are discovered deterministically
  - explicit index entries exist, are relative, and are not duplicated
  - discovered files missing from an explicit index are reported as warnings

Exit codes:
  0  no blocking error diagnostics
  1  at least one error diagnostic
  2  invalid CLI usage
"""
_DEMO_DESCRIPTION = """\
Create small Scribpy tutorial projects that can be checked with
`scribpy index check`.

The demo command is useful when trying Scribpy in another repository because it
creates a complete mini project without requiring you to write scribpy.toml by
hand.
"""
_DEMO_EPILOG = """\
Examples:
  scribpy demo create dd1
  scribpy demo create dd1 --variant invalid
  scribpy demo create dd1 --force

After creation:
  scribpy index check --root dd1
"""
_DEMO_CREATE_DESCRIPTION = """\
Create a tutorial project containing scribpy.toml, README.md, and Markdown
files under doc/.

The valid variant passes index check. The invalid variant intentionally creates
index diagnostics for learning and troubleshooting.
"""
_DEMO_CREATE_EPILOG = """\
Examples:
  scribpy demo create dd1
  scribpy demo create dd1 --variant valid
  scribpy demo create dd1 --variant invalid
  scribpy demo create dd1 --variant invalid --force

What it creates:
  dd1/scribpy.toml
  dd1/README.md
  dd1/doc/index.md
  dd1/doc/guide/setup.md

Next steps:
  scribpy index check --root dd1

Variants:
  valid    creates a project expected to pass index check
  invalid  creates a project with missing, duplicate, and unindexed files

Overwrite behavior:
  Existing demo files are not overwritten unless --force is passed.
"""


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
    return _main(argv, stdout=sys.stdout, stderr=sys.stderr)


def _main(argv: Sequence[str] | None, stdout: TextIO, stderr: TextIO) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return _exit_code(error)

    if args.command == "index" and args.index_command == "check":
        return _run_index_check_command(args.root, stderr)

    if args.command == "demo" and args.demo_command == "create":
        return _run_demo_create_command(
            args.target,
            args.force,
            args.variant,
            stdout,
            stderr,
        )

    parser.print_help(file=stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scribpy",
        description=_ROOT_DESCRIPTION,
        epilog=_ROOT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    index_parser = subparsers.add_parser(
        "index",
        help="Manage and validate the document index",
        description=_INDEX_DESCRIPTION,
        epilog=_INDEX_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    index_subparsers = index_parser.add_subparsers(dest="index_command")

    check_parser = index_subparsers.add_parser(
        "check",
        help="Validate project source discovery and document index configuration",
        description=_INDEX_CHECK_DESCRIPTION,
        epilog=_INDEX_CHECK_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    check_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            "Project root, any path inside a project, or a direct path to "
            "scribpy.toml. Defaults to the current working directory."
        ),
    )

    demo_parser = subparsers.add_parser(
        "demo",
        help="Create tutorial projects",
        description=_DEMO_DESCRIPTION,
        epilog=_DEMO_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    demo_subparsers = demo_parser.add_subparsers(dest="demo_command")

    create_parser = demo_subparsers.add_parser(
        "create",
        help="Create a small Scribpy demo project",
        description=_DEMO_CREATE_DESCRIPTION,
        epilog=_DEMO_CREATE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    create_parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path("scribpy-demo"),
        help=(
            "Directory where the demo project should be created. Defaults to "
            "'scribpy-demo'."
        ),
    )
    create_parser.add_argument(
        "--variant",
        choices=_VALID_DEMO_VARIANTS,
        default="valid",
        help=(
            "Demo base to generate. 'valid' passes index check; 'invalid' "
            "creates missing, duplicate, and unindexed file diagnostics."
        ),
    )
    create_parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite files managed by the selected demo template. Existing "
            "unrelated files are left untouched."
        ),
    )

    return parser


def _run_index_check_command(root: Path | None, stderr: TextIO) -> int:
    result = run_index_check(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    return 1 if result.failed else 0


def _run_demo_create_command(
    target: Path,
    force: bool,
    variant: DemoVariant,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    result = create_demo_project(target, force=force, variant=variant)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    if result.failed:
        return 1

    print(f"Created {variant} Scribpy demo project at {target}", file=stdout)
    print(f"Next: scribpy index check --root {target}", file=stdout)
    return 0


def _exit_code(error: SystemExit) -> int:
    if isinstance(error.code, int):
        return error.code
    return 2


__all__ = ["main"]
