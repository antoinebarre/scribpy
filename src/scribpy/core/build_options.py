"""Typed build override objects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class HtmlBuildOverrides:
    """Per-run HTML build overrides.

    Attributes:
        mode: Optional HTML output mode.
        output_dir: Optional output directory override.
        extra_css: Additional CSS files appended for one build.
        plantuml_renderer: Optional PlantUML renderer override.
        plantuml_server_url: Optional PlantUML server URL override.
    """

    mode: str | None = None
    output_dir: Path | None = None
    extra_css: tuple[Path, ...] = ()
    plantuml_renderer: str | None = None
    plantuml_server_url: str | None = None


__all__ = ["HtmlBuildOverrides"]
