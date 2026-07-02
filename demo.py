"""Scribpy feature demo — exercises every public API element.

Run::

    uv run python demo.py

Outputs go to ``work/demo/``.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import scribpy
from scribpy.config import CssConfig, RenderMode, TocConfig
from scribpy.core.diagram_renderer import (
    register_renderer,
    render_all_diagrams,
)
from scribpy.core.image_resolver import resolve_images
from scribpy.core.markdown_parser import parse
from scribpy.diagrams.mermaid_web import MermaidWebRenderer
from scribpy.diagrams.plantuml_web import PlantUmlWebRenderer
from scribpy.render.html_renderer import render_html

WORK_DIR = Path("work/demo")
DEMO_ASSETS = Path("demo_assets")

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


def demo_markdown_parser() -> None:
    """Demonstrate the Markdown parser (Lot 1)."""
    _section("Markdown Parser (core)")

    sample_md = """\
# Project Overview

Welcome to **Scribpy**.

## Architecture

![Diagram](img/architecture.png "Architecture diagram")

Here is a PlantUML diagram:

```plantuml
@startuml
Alice -> Bob: Hello
Bob --> Alice: Hi!
@enduml
```

And a Mermaid diagram:

```mermaid
graph TD
    A[Start] --> B[End]
```

### Implementation details

Some regular code that is not a diagram:

```python
print("hello world")
```
"""

    console.print("[dim]Parsing sample Markdown...[/]")
    console.print()

    doc = parse(sample_md)

    # Headings
    table = Table(title="Extracted headings", show_lines=True)
    table.add_column("Level", style="bold")
    table.add_column("Text")
    table.add_column("Anchor", style="dim")
    for h in doc.headings:
        table.add_row(str(h.level), h.text, h.anchor)
    console.print(table)
    console.print()

    # Images
    table = Table(title="Extracted image references", show_lines=True)
    table.add_column("Src", style="bold")
    table.add_column("Alt")
    table.add_column("Title", style="dim")
    for img in doc.images:
        table.add_row(img.src, img.alt, img.title)
    console.print(table)
    console.print()

    # Diagrams
    table = Table(title="Extracted diagram blocks", show_lines=True)
    table.add_column("Index", style="bold")
    table.add_column("Engine")
    table.add_column("Source (first line)", style="dim")
    for d in doc.diagrams:
        first_line = d.source.strip().splitlines()[0]
        table.add_row(str(d.index), d.engine, first_line)
    console.print(table)
    console.print()

    # HTML snippet
    html_preview = doc.html[:200] + "..." if len(doc.html) > 200 else doc.html
    console.print(
        Panel(
            html_preview,
            title="Rendered HTML (preview)",
            expand=False,
        ),
    )

    console.print()
    console.print(
        f"[green]Parser extracted {len(doc.headings)} headings, "
        f"{len(doc.images)} images, {len(doc.diagrams)} diagrams.[/]",
    )


def demo_html_export() -> None:
    """Demonstrate the full HTML export pipeline (Lot 3)."""
    _section("HTML Export Pipeline (full)")

    md_file = DEMO_ASSETS / "document.md"
    css_file = DEMO_ASSETS / "style.css"
    output_dir = WORK_DIR / "html-export"

    console.print(f"[dim]Source:  {md_file}[/]")
    console.print(f"[dim]CSS:    {css_file}[/]")
    console.print(f"[dim]Output: {output_dir}/[/]")
    console.print()

    # Step 1: Parse Markdown
    console.print("[bold]Step 1:[/] Parsing Markdown...")
    md_text = md_file.read_text(encoding="utf-8")
    doc = parse(md_text)
    console.print(
        f"  [green]✓[/] {len(doc.headings)} headings, "
        f"{len(doc.images)} images, "
        f"{len(doc.diagrams)} diagram blocks",
    )

    # Step 2: Resolve images
    console.print("[bold]Step 2:[/] Resolving images...")
    resolved = resolve_images(doc, DEMO_ASSETS)
    console.print(
        f"  [green]✓[/] {len(resolved.valid)} valid, "
        f"{len(resolved.warnings)} warnings",
    )
    for w in resolved.warnings:
        console.print(f"  [yellow]⚠[/] {w.message}")

    # Step 3: Render diagrams (web mode)
    console.print("[bold]Step 3:[/] Rendering diagrams (web mode)...")
    register_renderer("plantuml", RenderMode.WEB, PlantUmlWebRenderer())
    register_renderer("mermaid", RenderMode.WEB, MermaidWebRenderer())

    diagrams_svg = render_all_diagrams(doc.diagrams, RenderMode.WEB)
    console.print(
        f"  [green]✓[/] {len(diagrams_svg)}/{len(doc.diagrams)} "
        f"diagrams rendered successfully",
    )
    for idx, svg in diagrams_svg.items():
        engine = doc.diagrams[idx].engine
        size = len(svg)
        console.print(
            f"  [dim]  diagram-{idx} ({engine}): "
            f"{size:,} bytes SVG[/]",
        )

    # Step 4: Render HTML
    console.print("[bold]Step 4:[/] Generating HTML output...")
    result_path = render_html(
        doc,
        output_dir,
        source_dir=DEMO_ASSETS,
        css=CssConfig(path=css_file),
        toc=TocConfig(enabled=True),
        diagrams_svg=diagrams_svg,
    )
    console.print(f"  [green]✓[/] Written: {result_path}")

    # Show output structure
    console.print()
    console.print("[bold]Output directory structure:[/]")
    for p in sorted(output_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(output_dir)
            size = p.stat().st_size
            console.print(f"  {rel} ({size:,} bytes)")

    # Show HTML preview
    console.print()
    html_content = result_path.read_text(encoding="utf-8")
    console.print(
        Panel(
            html_content[:500] + "\n...",
            title=str(result_path),
            subtitle=f"{len(html_content):,} bytes total",
            expand=False,
        ),
    )

    console.print()
    console.print(
        "[bold green]HTML export complete![/] "
        f"Open [link=file://{result_path.resolve()}]"
        f"{result_path}[/link] in a browser.",
    )


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
    demo_markdown_parser()
    demo_html_export()

    _section("Summary")
    console.print(
        Panel(
            "[bold green]All features demonstrated successfully.[/]\n\n"
            f"[dim]Artifacts in {WORK_DIR}/:\n"
            f"  - {WORK_DIR / 'scribpy.log'}\n"
            f"  - {WORK_DIR / 'html-export/'} (full HTML site)[/]",
            title="Done",
            expand=False,
        ),
    )


if __name__ == "__main__":
    main()
