"""Scribpy feature demo — exercises every public API element.

Run::

    uv run python demo.py

Outputs go to ``work/demo/``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import scribpy

WORK_DIR = Path("work/demo")

console = Console()


def _section(title: str) -> None:
    """Print a section header."""
    console.print()
    console.rule(f"[bold cyan]{title}[/]")
    console.print()


def demo_version() -> None:
    """Show package version."""
    _section("Package version")
    console.print(
        Panel(
            f"[bold green]scribpy {scribpy.__version__}[/]",
            title="Version",
            expand=False,
        ),
    )


def demo_public_api() -> None:
    """List every public export from scribpy."""
    _section("Public API (__all__)")

    table = Table(
        title="scribpy public exports",
        show_lines=True,
    )
    table.add_column("Name", style="bold")
    table.add_column("Type", style="dim")
    table.add_column("Category")

    categories = {
        "config": {
            "ScribpyConfig",
            "CssConfig",
            "TocConfig",
            "DiagramConfig",
            "OutputFormat",
            "RenderMode",
        },
        "errors": {
            "ScribpyError",
            "ImageNotFoundError",
            "DiagramRenderError",
            "InvalidMarkdownError",
        },
        "logging": {"logging_context"},
    }
    name_to_cat = {
        name: cat for cat, names in categories.items() for name in names
    }

    for name in sorted(scribpy.__all__):
        obj = getattr(scribpy, name)
        cat = name_to_cat.get(name, "other")
        obj_type = type(obj).__name__
        table.add_row(name, obj_type, cat)

    console.print(table)


def demo_config() -> None:
    """Demonstrate configuration dataclasses."""
    _section("Configuration dataclasses")

    cfg_default = scribpy.ScribpyConfig()
    cfg_custom = scribpy.ScribpyConfig(
        source=Path("docs/readme.md"),
        output_dir=WORK_DIR / "html-output",
        output_format=scribpy.OutputFormat.PDF,
        css=scribpy.CssConfig(path=Path("style.css")),
        toc=scribpy.TocConfig(enabled=True),
        diagrams=scribpy.DiagramConfig(
            render_mode=scribpy.RenderMode.WEB,
            plantuml_jar=Path("/opt/plantuml.jar"),
        ),
    )

    for label, cfg in [("Default", cfg_default), ("Custom", cfg_custom)]:
        table = Table(title=f"{label} ScribpyConfig", show_lines=True)
        table.add_column("Field", style="bold")
        table.add_column("Value")

        table.add_row("source", str(cfg.source))
        table.add_row("output_dir", str(cfg.output_dir))
        table.add_row("output_format", cfg.output_format.value)
        table.add_row("css.path", str(cfg.css.path))
        table.add_row("toc.enabled", str(cfg.toc.enabled))
        table.add_row(
            "diagrams.render_mode",
            cfg.diagrams.render_mode.value,
        )
        table.add_row(
            "diagrams.plantuml_jar",
            str(cfg.diagrams.plantuml_jar),
        )
        console.print(table)
        console.print()

    console.print(
        "[green]All config objects are frozen (immutable).[/]",
    )

    try:
        cfg_default.source = Path("/tmp")  # type: ignore[misc]
    except AttributeError:
        console.print(
            "[dim]Verified: assignment to frozen field raises "
            "AttributeError.[/]",
        )


def demo_enums() -> None:
    """Demonstrate RenderMode and OutputFormat enums."""
    _section("Enums")

    table = Table(title="RenderMode", show_lines=True)
    table.add_column("Member", style="bold")
    table.add_column("Value")
    for member in scribpy.RenderMode:
        table.add_row(member.name, member.value)
    console.print(table)

    console.print()

    table = Table(title="OutputFormat", show_lines=True)
    table.add_column("Member", style="bold")
    table.add_column("Value")
    for member in scribpy.OutputFormat:
        table.add_row(member.name, member.value)
    console.print(table)


def demo_errors() -> None:
    """Demonstrate exception hierarchy."""
    _section("Exception hierarchy")

    errors: list[tuple[str, Exception]] = [
        (
            "ImageNotFoundError",
            scribpy.ImageNotFoundError("img/missing.png"),
        ),
        (
            "DiagramRenderError",
            scribpy.DiagramRenderError(
                "arch-overview",
                "plantuml",
                "web",
                "connection refused",
            ),
        ),
        (
            "InvalidMarkdownError",
            scribpy.InvalidMarkdownError(
                "no heading level 1 found",
            ),
        ),
    ]

    for name, err in errors:
        is_scribpy = isinstance(err, scribpy.ScribpyError)
        status = (
            Text("catchable via ScribpyError", style="green")
            if is_scribpy
            else Text("NOT a ScribpyError", style="red")
        )
        console.print(
            Panel(
                f"[bold]{name}[/]\n"
                f"[dim]str:[/] {err}\n"
                f"[dim]hierarchy:[/] {status}",
                expand=False,
            ),
        )


def demo_logging() -> None:
    """Demonstrate the logging context manager."""
    _section("Logging context manager")

    log_file = WORK_DIR / "scribpy.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    console.print(
        "[dim]Activating logging_context with level=DEBUG, "
        f"file={log_file}[/]",
    )
    console.print()

    with scribpy.logging_context(
        level="DEBUG",
        file=log_file,
    ) as logger:
        logger.debug("Pipeline started")
        logger.info("Parsed 3 documents")
        logger.warning("Image 'logo.png' not found, skipping")
        logger.info("Rendered 2 PlantUML diagrams (mode=offline)")
        logger.info("Build completed: 1 HTML artifact produced")

        child = logging.getLogger("scribpy.core.parser")
        child.info("Child logger inherits context automatically")

    console.print()
    console.print(
        f"[green]Log file written:[/] {log_file}",
    )
    console.print()

    content = log_file.read_text(encoding="utf-8")
    console.print(
        Panel(
            content.strip(),
            title=str(log_file),
            subtitle="file output",
        ),
    )

    console.print()
    console.print("[dim]Logging context exited — handlers cleaned up.[/]")

    root_logger = logging.getLogger("scribpy")
    console.print(
        f"[dim]Handlers remaining on 'scribpy' logger: "
        f"{len(root_logger.handlers)}[/]",
    )


def demo_logging_levels() -> None:
    """Show that log level filtering works."""
    _section("Logging level filtering")

    console.print(
        "[dim]With level=WARNING, INFO messages are suppressed:[/]",
    )
    console.print()

    with scribpy.logging_context(level="WARNING") as logger:
        logger.info("This INFO message is suppressed")
        logger.warning("This WARNING message is visible")

    console.print()
    console.print("[dim]With console=False, stderr is silent:[/]")
    console.print()

    with scribpy.logging_context(
        level="INFO",
        console=False,
    ) as logger:
        logger.info("This goes nowhere (no file, no console)")

    console.print("[green]No output above — as expected.[/]")


def main() -> None:
    """Run all feature demos."""
    console.print(
        Panel(
            "[bold]Scribpy Feature Demo[/]\n"
            f"[dim]Version {scribpy.__version__} "
            f"— Output: {WORK_DIR}/[/]",
            style="blue",
        ),
    )

    WORK_DIR.mkdir(parents=True, exist_ok=True)

    demo_version()
    demo_public_api()
    demo_config()
    demo_enums()
    demo_errors()
    demo_logging()
    demo_logging_levels()

    _section("Summary")
    console.print(
        Panel(
            "[bold green]All features demonstrated successfully.[/]\n\n"
            f"[dim]Artifacts in {WORK_DIR}/:\n"
            f"  - {WORK_DIR / 'scribpy.log'}[/]",
            title="Done",
            expand=False,
        ),
    )


if __name__ == "__main__":
    main()
