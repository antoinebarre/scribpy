"""Execution helpers for Scribpy CLI commands."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TextIO

from scribpy.cli.reporting import (
    print_build_report,
    print_index_report,
    print_lint_report,
    print_parse_report,
)
from scribpy.core import (
    DemoVariant,
    build_project,
    create_demo_project,
    lint_project,
    parse_project_documents,
    run_index_check,
)
from scribpy.logging import logging_context
from scribpy.utils import format_diagnostics


class LogLevel(StrEnum):
    """Supported logging levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class Runtime:
    """Execution dependencies shared by CLI commands.

    Attributes:
        stdout: Stream receiving normal command output.
        stderr: Stream receiving diagnostics and usage errors.
        log_level: Optional execution log level.
        log_console: Whether execution logs should also be written to stderr.
        log_file: Optional custom log file path.
    """

    stdout: TextIO
    stderr: TextIO
    log_level: LogLevel | None = None
    log_console: bool = False
    log_file: Path | None = None


def run_with_optional_logging(runtime: Runtime, action: Callable[[], int]) -> int:
    """Run a command, enabling logs only when requested.

    Args:
        runtime: Shared execution runtime.
        action: Command action to execute.

    Returns:
        Process exit code returned by ``action``.
    """
    if not (runtime.log_level or runtime.log_console or runtime.log_file):
        return action()
    with logging_context(
        level=(runtime.log_level or LogLevel.INFO).value,
        console=runtime.log_console,
        file=True,
        file_path=runtime.log_file,
    ):
        return action()


def run_parse_check_command(root: Path | None, stdout: TextIO, stderr: TextIO) -> int:
    """Run ``parse check``.

    Args:
        root: Optional project root override.
        stdout: Stream receiving the execution report.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
    result = parse_project_documents(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    print_parse_report(result, stdout)
    return 1 if result.failed else 0


def run_index_check_command(root: Path | None, stdout: TextIO, stderr: TextIO) -> int:
    """Run ``index check``.

    Args:
        root: Optional project root override.
        stdout: Stream receiving the execution report.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
    result = run_index_check(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    print_index_report(result, stdout)
    return 1 if result.failed else 0


def run_lint_command(root: Path | None, stdout: TextIO, stderr: TextIO) -> int:
    """Run ``lint``.

    Args:
        root: Optional project root override.
        stdout: Stream receiving the execution report.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
    result = lint_project(root)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    print_lint_report(result, stdout)
    return 1 if result.failed else 0


def run_build_markdown_command(
    root: Path | None,
    output_dir: Path | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run ``build markdown``.

    Args:
        root: Optional project root override.
        output_dir: Optional build directory override.
        stdout: Stream receiving the execution report.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
    result = build_project(root, target="markdown", output_dir=output_dir)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    print_build_report(result, "Markdown", stdout)
    return 0 if result.success else 1


def run_build_html_command(
    root: Path | None,
    mode: str,
    output_dir: Path | None,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run ``build html``.

    Args:
        root: Optional project root override.
        mode: HTML output mode.
        output_dir: Optional build directory override.
        stdout: Stream receiving the execution report.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
    result = build_project(root, target="html", html_mode=mode, output_dir=output_dir)
    if result.diagnostics:
        print(format_diagnostics(result.diagnostics), file=stderr)
    print_build_report(result, f"HTML ({mode})", stdout)
    return 0 if result.success else 1


def run_demo_create_command(
    target: Path,
    force: bool,
    variant: DemoVariant,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Run ``demo create``.

    Args:
        target: Directory receiving the generated demo project.
        force: Whether managed demo files may be overwritten.
        variant: Demo project variant to generate.
        stdout: Stream receiving normal command output.
        stderr: Stream receiving diagnostics.

    Returns:
        Process exit code.
    """
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
    print(f"  scribpy build markdown --root {target}", file=stdout)
    print(f"  scribpy build html --mode single-page --root {target}", file=stdout)
    print(f"  scribpy build html --mode site --root {target}", file=stdout)
    return 0
