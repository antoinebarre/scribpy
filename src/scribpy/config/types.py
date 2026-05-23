"""Typed configuration objects for ``scribpy.toml``."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from scribpy.model import IndexMode

TocStyle = Literal["bullet", "numbered"]
NumberingStyle = Literal["decimal", "alpha", "roman"]
HtmlMode = Literal["single-page", "site"]
PlantUmlRendererMode = Literal["java", "web"]


@dataclass(frozen=True)
class ProjectConfig:
    """Project-level configuration.

    Attributes:
        name: Optional human-readable project name.
    """

    name: str | None = None


@dataclass(frozen=True)
class PathConfig:
    """Filesystem paths used by Scribpy.

    Attributes:
        source: Markdown source directory relative to the project root.
    """

    source: Path = Path("doc")


@dataclass(frozen=True)
class IndexConfig:
    """Document index configuration.

    Attributes:
        mode: Strategy used to build the document index.
        files: Explicit ordered Markdown file list when ``mode`` is
            ``"explicit"``.
    """

    mode: IndexMode = "filesystem"
    files: tuple[Path, ...] = ()


@dataclass(frozen=True)
class TocConfig:
    """Table-of-contents configuration.

    Attributes:
        enabled: Whether to inject a generated table of contents.
        max_level: Deepest heading level included in the table of contents.
        style: Markdown list style used by the table of contents.
    """

    enabled: bool = True
    max_level: int = 6
    style: TocStyle = "bullet"


@dataclass(frozen=True)
class NumberingConfig:
    """Section-numbering configuration.

    Attributes:
        enabled: Whether to prefix headings with generated section numbers.
        max_level: Deepest heading level that receives generated numbering.
        style: Number style used for section prefixes.
    """

    enabled: bool = True
    max_level: int = 6
    style: NumberingStyle = "decimal"


@dataclass(frozen=True)
class DocumentConfig:
    """Document-level output configuration.

    Attributes:
        title: Optional global assembled-document title.
        toc: Generated table-of-contents settings.
        numbering: Section-numbering settings.
    """

    title: str | None = None
    toc: TocConfig = TocConfig()
    numbering: NumberingConfig = NumberingConfig()


@dataclass(frozen=True)
class PlantUmlConfig:
    """PlantUML rendering configuration.

    Attributes:
        renderer: Rendering backend. ``"java"`` uses the bundled JAR;
            ``"web"`` calls a PlantUML server.
        server_url: Base URL of the PlantUML server used by ``"web"`` mode.
    """

    renderer: PlantUmlRendererMode = "web"
    server_url: str = "http://www.plantuml.com/plantuml"


@dataclass(frozen=True)
class MermaidConfig:
    """Mermaid rendering configuration.

    Attributes:
        server_url: Base URL of the Mermaid web rendering service.
        theme: Mermaid theme passed to the rendering service.
    """

    server_url: str = "https://mermaid.ink"
    theme: str = "default"


@dataclass(frozen=True)
class HtmlBuilderConfig:
    """HTML builder configuration.

    Attributes:
        mode: Output mode — ``"single-page"`` for a self-contained HTML file or
            ``"site"`` for a MkDocs project scaffold.
        css_files: Stylesheet paths relative to the project root, applied to
            the output in the order given.
        site_name: Site name written into ``mkdocs.yml`` when ``mode`` is
            ``"site"``. Falls back to the project name when omitted.
        theme: Optional MkDocs theme name written into ``mkdocs.yml`` for site
            output, for example ``"readthedocs"``.
        output_dir: Output directory relative to the project root. Defaults to
            ``build/html`` for ``single-page`` and ``build/site`` for ``site``.
        plantuml: PlantUML rendering settings.
        mermaid: Mermaid rendering settings.
    """

    mode: HtmlMode = "single-page"
    css_files: tuple[Path, ...] = ()
    site_name: str | None = None
    theme: str | None = None
    output_dir: Path | None = None
    plantuml: PlantUmlConfig = PlantUmlConfig()
    mermaid: MermaidConfig = MermaidConfig()

    def resolve_output_dir(self) -> Path:
        """Return the effective output directory for the configured mode.

        Returns:
            Resolved output directory path.
        """
        if self.output_dir is not None:
            return self.output_dir
        return (
            Path("build/html")
            if self.mode == "single-page"
            else Path("build/site")
        )


@dataclass(frozen=True)
class PdfBuilderConfig:
    """PDF builder configuration.

    Attributes:
        css_files: Stylesheet paths relative to the project root, applied after
            the built-in printable defaults.
        output_dir: Output directory relative to the project root. Defaults to
            ``build/pdf``.
        paper_size: Page size forwarded to injected PDF renderers when they
            support it, for example ``"A4"`` or ``"A4-L"``.
        toc_level: Deepest heading level included in renderer-native PDF
            bookmarks when the injected renderer supports them.
    """

    css_files: tuple[Path, ...] = ()
    output_dir: Path | None = None
    paper_size: str = "A4"
    toc_level: int = 3

    def resolve_output_dir(self) -> Path:
        """Return the effective PDF output directory.

        Returns:
            Resolved output directory path.
        """
        return self.output_dir or Path("build/pdf")


@dataclass(frozen=True)
class Config:
    """Minimal project configuration required by the project context chain.

    Attributes:
        project: Project metadata.
        paths: Filesystem paths.
        index: Document index settings.
        document: Document output settings.
        html: HTML builder settings.
        pdf: PDF builder settings.
    """

    project: ProjectConfig = field(default_factory=ProjectConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    index: IndexConfig = field(default_factory=IndexConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)
    html: HtmlBuilderConfig = field(default_factory=HtmlBuilderConfig)
    pdf: PdfBuilderConfig = field(default_factory=PdfBuilderConfig)


__all__ = [
    "Config",
    "DocumentConfig",
    "HtmlBuilderConfig",
    "HtmlMode",
    "IndexConfig",
    "MermaidConfig",
    "NumberingConfig",
    "NumberingStyle",
    "PathConfig",
    "PdfBuilderConfig",
    "PlantUmlConfig",
    "PlantUmlRendererMode",
    "ProjectConfig",
    "TocConfig",
    "TocStyle",
]
