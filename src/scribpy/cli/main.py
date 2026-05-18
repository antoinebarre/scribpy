"""Typer command tree for the Scribpy CLI."""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import click
import typer

from scribpy.cli.build_help import (
    BUILD_DESCRIPTION,
    BUILD_EPILOG,
    BUILD_HTML_DESCRIPTION,
    BUILD_HTML_EPILOG,
    BUILD_MARKDOWN_DESCRIPTION,
    BUILD_MARKDOWN_EPILOG,
)
from scribpy.cli.execution import (
    LogLevel,
    Runtime,
    run_build_html_command,
    run_build_markdown_command,
    run_demo_create_command,
    run_index_check_command,
    run_lint_command,
    run_parse_check_command,
    run_with_optional_logging,
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

_ROOT_HELP = (
    "Project root, any path inside a project, or a direct path to "
    "scribpy.toml. Defaults to the current working directory."
)
_OUTPUT_DIR_HELP = (
    "Build directory override. Relative paths are resolved from the project "
    "root; absolute paths are used as-is."
)
_LOG_FILE_HELP = (
    "Write logs to this file. Relative paths are resolved from the project root. "
    "Defaults to build/logs/scribpy.log when logging is enabled."
)


class HtmlMode(StrEnum):
    """Supported HTML build modes."""

    SINGLE_PAGE = "single-page"
    SITE = "site"


class PlantUmlRendererOption(StrEnum):
    """Supported PlantUML renderer backends."""

    JAVA = "java"
    WEB = "web"


class DemoVariantOption(StrEnum):
    """Supported demo project variants."""

    VALID = "valid"
    INVALID = "invalid"


def _verbatim(text: str) -> str:
    """Preserve authored multiline help text in Click/Typer rendering."""
    paragraphs = text.strip("\n").split("\n\n")
    return "\n\n".join(f"\b\n{paragraph}" for paragraph in paragraphs)


def _typer(help_text: str, epilog: str) -> typer.Typer:
    """Create one consistently configured Typer application."""
    return typer.Typer(
        help=_verbatim(help_text),
        epilog=_verbatim(epilog),
        no_args_is_help=False,
        rich_markup_mode=None,
        context_settings={"help_option_names": ["-h", "--help"]},
    )


app = _typer(_ROOT_DESCRIPTION, _ROOT_EPILOG)
parse_app = _typer(_PARSE_DESCRIPTION, _PARSE_EPILOG)
build_app = _typer(BUILD_DESCRIPTION, BUILD_EPILOG)
index_app = _typer(_INDEX_DESCRIPTION, _INDEX_EPILOG)
demo_app = _typer(_DEMO_DESCRIPTION, _DEMO_EPILOG)

app.add_typer(
    parse_app,
    name="parse",
    help="Parse Markdown sources and report semantic extraction diagnostics",
)
app.add_typer(build_app, name="build", help="Build documentation artifacts")
app.add_typer(index_app, name="index", help="Manage and validate the document index")
app.add_typer(demo_app, name="demo", help="Create tutorial projects")


@app.callback(invoke_without_command=True)
def _root(
    ctx: typer.Context,
    log_level: Annotated[
        LogLevel | None,
        typer.Option(
            "--log-level", help="Enable execution logs at the selected level."
        ),
    ] = None,
    log_console: Annotated[
        bool,
        typer.Option("--log-console", help="Also write execution logs to stderr."),
    ] = False,
    log_file: Annotated[
        Path | None,
        typer.Option("--log-file", help=_LOG_FILE_HELP),
    ] = None,
) -> None:
    """Configure shared CLI runtime state."""
    ctx.obj = Runtime(sys.stdout, sys.stderr, log_level, log_console, log_file)
    _require_subcommand(ctx, "Missing command.")


@parse_app.callback(invoke_without_command=True)
def _parse_root(ctx: typer.Context) -> None:
    """Require a parse subcommand."""
    _require_subcommand(ctx, "Missing parse command.")


@build_app.callback(invoke_without_command=True)
def _build_root(ctx: typer.Context) -> None:
    """Require a build subcommand."""
    _require_subcommand(ctx, "Missing build command.")


@index_app.callback(invoke_without_command=True)
def _index_root(ctx: typer.Context) -> None:
    """Require an index subcommand."""
    _require_subcommand(ctx, "Missing index command.")


@demo_app.callback(invoke_without_command=True)
def _demo_root(ctx: typer.Context) -> None:
    """Require a demo subcommand."""
    _require_subcommand(ctx, "Missing demo command.")


@parse_app.command(
    "check",
    help=_verbatim(_PARSE_CHECK_DESCRIPTION),
    epilog=_verbatim(_PARSE_CHECK_EPILOG),
)
def parse_check(
    ctx: typer.Context,
    root: Annotated[Path | None, typer.Option("--root", help=_ROOT_HELP)] = None,
) -> None:
    """Parse all Markdown sources and report diagnostics.

    Args:
        ctx: Current command context.
        root: Optional project root override.
    """
    _finish(
        ctx,
        lambda runtime: run_parse_check_command(root, runtime.stdout, runtime.stderr),
    )


@app.command(help=_verbatim(_LINT_DESCRIPTION), epilog=_verbatim(_LINT_EPILOG))
def lint(
    ctx: typer.Context,
    root: Annotated[Path | None, typer.Option("--root", help=_ROOT_HELP)] = None,
) -> None:
    """Check documentation quality.

    Args:
        ctx: Current command context.
        root: Optional project root override.
    """
    _finish(ctx, lambda runtime: run_lint_command(root, runtime.stdout, runtime.stderr))


@build_app.command(
    "markdown",
    help=_verbatim(BUILD_MARKDOWN_DESCRIPTION),
    epilog=_verbatim(BUILD_MARKDOWN_EPILOG),
)
def build_markdown(
    ctx: typer.Context,
    root: Annotated[Path | None, typer.Option("--root", help=_ROOT_HELP)] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help=_OUTPUT_DIR_HELP)
    ] = None,
) -> None:
    """Build assembled Markdown output.

    Args:
        ctx: Current command context.
        root: Optional project root override.
        output_dir: Optional build directory override.
    """
    _finish(
        ctx,
        lambda runtime: run_build_markdown_command(
            root, output_dir, runtime.stdout, runtime.stderr
        ),
    )


@build_app.command(
    "html",
    help=_verbatim(BUILD_HTML_DESCRIPTION),
    epilog=_verbatim(BUILD_HTML_EPILOG),
)
def build_html(
    ctx: typer.Context,
    root: Annotated[Path | None, typer.Option("--root", help=_ROOT_HELP)] = None,
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", help=_OUTPUT_DIR_HELP)
    ] = None,
    mode: Annotated[HtmlMode, typer.Option("--mode", help="Output mode.")] = (
        HtmlMode.SINGLE_PAGE
    ),
    plantuml_renderer: Annotated[
        PlantUmlRendererOption | None,
        typer.Option("--plantuml-renderer", help="Override PlantUML renderer."),
    ] = None,
    plantuml_server_url: Annotated[
        str | None,
        typer.Option("--plantuml-server-url", help="Override PlantUML server URL."),
    ] = None,
) -> None:
    """Build HTML output.

    Args:
        ctx: Current command context.
        root: Optional project root override.
        output_dir: Optional build directory override.
        mode: HTML output mode.
        plantuml_renderer: Optional PlantUML renderer override.
        plantuml_server_url: Optional PlantUML server URL override.
    """
    _finish(
        ctx,
        lambda runtime: run_build_html_command(
            root,
            mode.value,
            output_dir,
            None if plantuml_renderer is None else plantuml_renderer.value,
            plantuml_server_url,
            runtime.stdout,
            runtime.stderr,
        ),
    )


@index_app.command(
    "check",
    help=_verbatim(_INDEX_CHECK_DESCRIPTION),
    epilog=_verbatim(_INDEX_CHECK_EPILOG),
)
def index_check(
    ctx: typer.Context,
    root: Annotated[Path | None, typer.Option("--root", help=_ROOT_HELP)] = None,
) -> None:
    """Validate the document index.

    Args:
        ctx: Current command context.
        root: Optional project root override.
    """
    _finish(
        ctx,
        lambda runtime: run_index_check_command(root, runtime.stdout, runtime.stderr),
    )


@demo_app.command(
    "create",
    help=_verbatim(_DEMO_CREATE_DESCRIPTION),
    epilog=_verbatim(_DEMO_CREATE_EPILOG),
)
def demo_create(
    ctx: typer.Context,
    target: Annotated[
        Path,
        typer.Argument(
            help=(
                "Directory where the demo project should be created. "
                "Defaults to 'scribpy-demo'."
            )
        ),
    ] = Path("scribpy-demo"),
    variant: Annotated[
        DemoVariantOption,
        typer.Option("--variant", help="Demo base to generate."),
    ] = DemoVariantOption.VALID,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help=(
                "Overwrite files managed by the selected demo template. "
                "Existing unrelated files are left untouched."
            ),
        ),
    ] = False,
) -> None:
    """Create a tutorial project.

    Args:
        ctx: Current command context.
        target: Directory receiving the generated demo project.
        variant: Demo project variant.
        force: Whether managed demo files may be overwritten.
    """
    _finish(
        ctx,
        lambda runtime: run_demo_create_command(
            target, force, variant.value, runtime.stdout, runtime.stderr
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Scribpy command-line entry point.

    Args:
        argv: Optional arguments excluding the executable name.

    Returns:
        Process exit code.
    """
    try:
        result = app(
            args=list(argv) if argv is not None else None,
            prog_name="scribpy",
            standalone_mode=False,
        )
    except click.exceptions.Exit as error:
        return error.exit_code
    except click.UsageError as error:
        _show_usage_error(error)
        return error.exit_code
    except click.ClickException as error:
        error.show(file=sys.stderr)
        return error.exit_code
    return result if isinstance(result, int) else 0


def _require_subcommand(ctx: typer.Context, message: str) -> None:
    """Raise a usage error when a command group is incomplete."""
    if ctx.invoked_subcommand is None:
        raise click.UsageError(message)


def _finish(ctx: typer.Context, action: Callable[[Runtime], int]) -> None:
    """Run one command and exit with its process status."""
    runtime = _runtime(ctx)
    exit_code = run_with_optional_logging(runtime, lambda: action(runtime))
    raise typer.Exit(exit_code)


def _runtime(ctx: typer.Context) -> Runtime:
    """Return the root runtime state."""
    runtime = ctx.find_root().obj
    if not isinstance(runtime, Runtime):
        raise RuntimeError("CLI runtime was not initialized")
    return runtime


def _show_usage_error(error: click.UsageError) -> None:
    """Render usage errors close to the legacy argparse contract."""
    if error.ctx is not None:
        print(
            error.ctx.get_usage().replace("Usage:", "usage:"),
            file=sys.stderr,
            end="",
        )
    message = error.format_message()
    if message.startswith("No such command "):
        message = message.replace("No such command", "invalid choice:", 1)
    print(f"scribpy: error: {message}", file=sys.stderr)


def _exit_code(error: SystemExit) -> int:
    """Map a legacy SystemExit value to a usage-oriented exit code."""
    if isinstance(error.code, int):
        return error.code
    return 2


__all__ = ["app", "main"]
