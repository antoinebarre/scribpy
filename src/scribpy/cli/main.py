"""Adapt Scribpy's public Python API to command-line workflows."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn

import click

import scribpy

_INPUT_PATH = click.Path(path_type=Path)
_EXISTING_FILE = click.Path(exists=True, dir_okay=False, path_type=Path)


def _raise_cli_error(error: BaseException) -> NoReturn:
    """Translate a domain or filesystem failure into a Click error.

    Args:
        error: Failure raised by the public Scribpy API.

    Raises:
        click.ClickException: Always, with the original failure message.
    """
    message = str(error) or error.__class__.__name__
    raise click.ClickException(message) from error


@click.group()
@click.version_option(version=scribpy.__version__)
def cli() -> None:
    """Assemble and export Scribpy Markdown collections."""


@cli.command("new")
@click.argument("output_dir", type=_INPUT_PATH)
@click.option("--title", required=True)
@click.option("--author", default="", show_default=True)
@click.option("--project-version", default="0.1.0", show_default=True)
def new_project(
    output_dir: Path,
    title: str,
    author: str,
    project_version: str,
) -> None:
    """Create a minimal project in OUTPUT_DIR.

    Args:
        output_dir: Destination directory for the project.
        title: Project title.
        author: Optional project author.
        project_version: Initial project version.
    """
    try:
        scribpy.init_skeleton(
            output_dir,
            title=title,
            author=author,
            version=project_version,
        )
    except scribpy.ScaffoldCollisionError as error:
        _raise_cli_error(error)
    click.echo(f"Created Scribpy project at {output_dir}")


@cli.command()
@click.argument("outline_path", type=_EXISTING_FILE)
@click.argument("output_dir", type=_INPUT_PATH)
@click.option("--max-depth", default=4, show_default=True, type=int)
def scaffold(outline_path: Path, output_dir: Path, max_depth: int) -> None:
    """Create a project from OUTLINE_PATH in OUTPUT_DIR.

    Args:
        outline_path: Markdown outline to scaffold.
        output_dir: Destination directory for the project.
        max_depth: Deepest accepted outline heading level.
    """
    try:
        scribpy.init_from_outline(
            outline_path, output_dir, max_depth=max_depth
        )
    except (
        scribpy.OutlineValidationError,
        scribpy.ScaffoldCollisionError,
        ValueError,
    ) as error:
        _raise_cli_error(error)
    click.echo(f"Scaffolded Scribpy project at {output_dir}")


@cli.command()
@click.argument("root", type=_INPUT_PATH)
def validate(root: Path) -> None:
    """Validate the Scribpy project at ROOT.

    Args:
        root: Project root to validate.

    Raises:
        click.exceptions.Exit: If validation reports blocking findings.
    """
    if not scribpy.valid_report(root):
        raise click.exceptions.Exit(1)


@cli.command()
@click.argument("root", type=_INPUT_PATH)
def diagnose(root: Path) -> None:
    """Diagnose the Markdown collection at ROOT.

    Args:
        root: Collection root to diagnose.

    Raises:
        click.exceptions.Exit: If diagnostics contain errors.
    """
    try:
        report = scribpy.MarkdownCollection.from_tree(root).diagnose()
    except (
        scribpy.InvalidScribpyManifestError,
        OSError,
        UnicodeDecodeError,
    ) as error:
        _raise_cli_error(error)
    click.echo(report.summary())
    if report.has_errors:
        raise click.exceptions.Exit(1)


@cli.command()
@click.argument("root", type=_INPUT_PATH)
@click.argument("output", type=_INPUT_PATH)
def build(root: Path, output: Path) -> None:
    """Assemble the project at ROOT into OUTPUT.

    Args:
        root: Collection root to assemble.
        output: Destination Markdown file.
    """
    try:
        collection = scribpy.MarkdownCollection.from_tree(root)
        scribpy.concatenate(collection, output)
    except (
        scribpy.InvalidMarkdownError,
        scribpy.InvalidScribpyManifestError,
        scribpy.MermaidRenderError,
        scribpy.PlantUmlRenderError,
        NotImplementedError,
        OSError,
        UnicodeDecodeError,
    ) as error:
        _raise_cli_error(error)
    click.echo(f"Built Markdown document at {output}")


@cli.command()
@click.argument("source", type=_INPUT_PATH)
@click.argument("output", type=_INPUT_PATH)
@click.option("--toc-depth", default=3, show_default=True, type=int)
@click.option("--css", type=_EXISTING_FILE)
def html(source: Path, output: Path, toc_depth: int, css: Path | None) -> None:
    """Export SOURCE Markdown as standalone HTML at OUTPUT.

    Args:
        source: Assembled Markdown source file.
        output: Destination HTML file.
        toc_depth: Maximum navigation heading depth.
        css: Optional custom stylesheet.
    """
    try:
        scribpy.html_export(source, output, toc_depth=toc_depth, css=css)
    except (OSError, ValueError) as error:
        _raise_cli_error(error)
    click.echo(f"Exported HTML document at {output}")


@cli.command("mkdocs-export")
@click.argument("source", type=_INPUT_PATH)
@click.argument("output", type=_INPUT_PATH)
def mkdocs_export(source: Path, output: Path) -> None:
    """Export SOURCE as a MkDocs project in OUTPUT.

    Args:
        source: Scribpy project root.
        output: Destination MkDocs directory.
    """
    try:
        scribpy.mkdocs_export(source, output)
    except (
        scribpy.InvalidMarkdownError,
        scribpy.InvalidScribpyManifestError,
        scribpy.MermaidRenderError,
        scribpy.PlantUmlRenderError,
        scribpy.ScaffoldCollisionError,
        NotImplementedError,
        OSError,
        UnicodeDecodeError,
    ) as error:
        _raise_cli_error(error)
    click.echo(f"Exported MkDocs project at {output}")
