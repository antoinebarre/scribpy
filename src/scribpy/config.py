"""Frozen configuration dataclasses for scribpy.

Every tuneable value lives here as a typed, immutable field.  No magic
constants elsewhere in the code — callers build a :class:`ScribpyConfig`
and thread it through the pipeline.

Hard-coded defaults are defined once as module-level constants
(``DEFAULT_*``) and referenced by the dataclass field defaults and
the config loader.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# -- Hard-coded defaults (single source of truth) -------------------------

DEFAULT_SOURCE = Path()
DEFAULT_OUTPUT_DIR = Path("work/build")
DEFAULT_OUTPUT_FORMAT = "html"
DEFAULT_RENDER_MODE = "offline"
DEFAULT_TOC_ENABLED = False
DEFAULT_CSS_PATH: Path | None = None
DEFAULT_PLANTUML_JAR: Path | None = None


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

    path: Path | None = DEFAULT_CSS_PATH


@dataclass(frozen=True)
class TocConfig:
    """Table-of-contents / hamburger menu settings.

    Attributes:
        enabled: Whether to generate the interactive TOC widget
            (REQ-003).
    """

    enabled: bool = DEFAULT_TOC_ENABLED


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

    render_mode: RenderMode = field(
        default_factory=lambda: RenderMode(DEFAULT_RENDER_MODE),
    )
    plantuml_jar: Path | None = DEFAULT_PLANTUML_JAR


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

    source: Path = field(
        default_factory=lambda: Path(DEFAULT_SOURCE),
    )
    output_dir: Path = field(
        default_factory=lambda: Path(DEFAULT_OUTPUT_DIR),
    )
    output_format: OutputFormat = field(
        default_factory=lambda: OutputFormat(DEFAULT_OUTPUT_FORMAT),
    )
    css: CssConfig = field(default_factory=CssConfig)
    toc: TocConfig = field(default_factory=TocConfig)
    diagrams: DiagramConfig = field(default_factory=DiagramConfig)
