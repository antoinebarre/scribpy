"""Command-line parser and command dispatch."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from scribpy.cli.build_help import (
    BUILD_DESCRIPTION,
    BUILD_EPILOG,
    BUILD_MARKDOWN_DESCRIPTION,
    BUILD_MARKDOWN_EPILOG,
)
from scribpy.cli.help_text import (
    _DEMO_CREATE_DESCRIPTION,
    _DEMO_CREATE_EPILOG,
    _DEMO_DESCRIPTION,
    _DEMO_EPILOG,
    _INDEX_CHECK_DESCRIPTION,
    _INDEX_CHECK_EPILOG,
    _INDEX_DESCRIPTION,
    _INDEX_EPILOG,
    _LINT_DESCRIPTION,
    _LINT_EPILOG,
    _PARSE_CHECK_DESCRIPTION,
    _PARSE_CHECK_EPILOG,
    _PARSE_DESCRIPTION,
    _PARSE_EPILOG,
    _ROOT_DESCRIPTION,
    _ROOT_EPILOG,
)
from scribpy.core import (
    DemoVariant,
    build_project,
    create_demo_project,
    lint_project,
    parse_project_documents,
    run_index_check,
)
from scribpy.utils import format_diagnostics

_VALID_DEMO_VARIANTS = ("valid", "invalid")


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

    exit_code = _dispatch(args, stdout, stderr)
    if exit_code is not None:
        return exit_code

    parser.print_help(file=stderr)
    return 2


def _dispatch(args: argparse.Namespace, stdout: TextIO, stderr: TextIO) -> int | None:
    if args.command == "index" and args.index_command == "check":
        return _run_index_check_command(args.root, stderr)
    if args.command == "parse" and args.parse_command == "check":
        return _run_parse_check_command(args.root, stdout, stderr)
    if args.command == "lint":
        return _run_lint_command(args.root, stderr)
    if args.command == "build" and args.build_command == "markdown":
        return _run_build_markdown_command(args.root, stdout, stderr)
    if args.command == "demo" and args.demo_command == "create":
        return _run_demo_create_command(
            args.target,
            args.force,
            args.variant,
            stdout,
            stderr,
        )
    return None


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scribpy",
        description=_ROOT_DESCRIPTION,
        epilog=_ROOT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    parse_parser = subparsers.add_parser(
        "parse",
        help="Parse Markdown sources and report semantic extraction diagnostics",
        description=_PARSE_DESCRIPTION,
        epilog=_PARSE_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parse_subparsers = parse_parser.add_subparsers(dest="parse_command")
    parse_check_parser = parse_subparsers.add_parser(
        "check",
        help="Parse all Markdown sources and report diagnostics",
        description=_PARSE_CHECK_DESCRIPTION,
        epilog=_PARSE_CHECK_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parse_check_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            "Project root, any path inside a project, or a direct path to "
            "scribpy.toml. Defaults to the current working directory."
        ),
    )

    lint_parser = subparsers.add_parser(
        "lint",
        help="Check documentation quality",
        description=_LINT_DESCRIPTION,
        epilog=_LINT_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lint_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            "Project root, any path inside a project, or a direct path to "
            "scribpy.toml. Defaults to the current working directory."
        ),
    )

    build_parser = subparsers.add_parser(
        "build",
        help="Build documentation artifacts",
        description=BUILD_DESCRIPTION,
        epilog=BUILD_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    build_subparsers = build_parser.add_subparsers(dest="build_command")
    build_markdown_parser = build_subparsers.add_parser(
        "markdown",
        help="Build assembled Markdown",
        description=BUILD_MARKDOWN_DESCRIPTION,
        epilog=BUILD_MARKDOWN_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    build_markdown_parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help=(
            "Project root, any path inside a project, or a direct path to "
            "scribpy.toml. Defaults to the current working directory."
        ),
    )

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


def _run_parse_check_command(root: Path | None, stdout: TextIO, stderr: TextIO) -> int:
    result = parse_project_documents(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    if result.failed:
        return 1
    print(
        f"Parsed {len(result.documents)} document(s) successfully.",
        file=stdout,
    )
    return 0


def _run_index_check_command(root: Path | None, stderr: TextIO) -> int:
    result = run_index_check(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    return 1 if result.failed else 0


def _run_lint_command(root: Path | None, stderr: TextIO) -> int:
    result = lint_project(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    return 1 if result.failed else 0


def _run_build_markdown_command(
    root: Path | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    result = build_project(root, target="markdown")
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    if not result.success:
        return 1
    for artifact in result.artifacts:
        print(f"Built {artifact.target} artifact: {artifact.path}", file=stdout)
    return 0


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
    print("", file=stdout)
    print("Next steps:", file=stdout)
    print(f"  scribpy index check --root {target}", file=stdout)
    print(f"  scribpy parse check --root {target}", file=stdout)
    print(f"  scribpy lint --root {target}", file=stdout)
    return 0


def _exit_code(error: SystemExit) -> int:
    if isinstance(error.code, int):
        return error.code
    return 2


__all__ = ["main"]
