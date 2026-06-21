"""Frozen configuration dataclasses for scribpy.

Every tuneable value lives here as a typed, immutable field.  No magic
constants elsewhere in the code — callers build a :class:`ScribpyConfig`
and thread it through the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class RenderMode(Enum):
    """Diagram rendering strategy (REQ-024).

    A single mode applies to all diagram blocks in the document.
    """

    WEB = "web"
    OFFLINE = "offline"


class OutputFormat(Enum):
    """Target format for the export step."""

    HTML = "html"
    PDF = "pdf"


@dataclass(frozen=True)
class CssConfig:
    """User-supplied CSS settings.

    Attributes:
        path: Path to a CSS file to embed in the output.
            ``None`` means use the default built-in style.
    """

    path: Path | None = None


@dataclass(frozen=True)
class TocConfig:
    """Table-of-contents / hamburger menu settings.

    Attributes:
        enabled: Whether to generate the interactive TOC widget
            (REQ-003).
    """

    enabled: bool = False


@dataclass(frozen=True)
class DiagramConfig:
    """Diagram rendering settings.

    Attributes:
        render_mode: Global render mode for all diagram blocks
            (REQ-024).
        plantuml_jar: Path to the PlantUML JAR file used in offline
            mode.  ``None`` lets the renderer search the default
            locations.
    """

    render_mode: RenderMode = RenderMode.OFFLINE
    plantuml_jar: Path | None = None


@dataclass(frozen=True)
class ScribpyConfig:
    """Top-level configuration for a scribpy run.

    Attributes:
        source: Path to the input ``.md`` file or directory.
        output_dir: Directory where output artefacts are written.
        output_format: Target format (HTML or PDF).
        css: CSS settings.
        toc: Table-of-contents settings.
        diagrams: Diagram rendering settings.
    """

    source: Path = field(default_factory=Path)
    output_dir: Path = field(default_factory=lambda: Path("work/build"))
    output_format: OutputFormat = OutputFormat.HTML
    css: CssConfig = field(default_factory=CssConfig)
    toc: TocConfig = field(default_factory=TocConfig)
    diagrams: DiagramConfig = field(default_factory=DiagramConfig)
