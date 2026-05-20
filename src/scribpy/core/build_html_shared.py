"""Shared helpers for single-page and site HTML build chains."""

from __future__ import annotations

from pathlib import Path

from scribpy.config.types import HtmlBuilderConfig
from scribpy.core.project_pipeline_state import ResolvedPipelineState
from scribpy.extensions import ExtensionRegistry
from scribpy.model import BuildArtifact, Diagnostic, TransformedDocument
from scribpy.model.protocols import CodeBlockPlugin, DiagramRenderer
from scribpy.plugins import MermaidPlugin, PlantUmlPlugin
from scribpy.transforms import Transform, TransformOptions
from scribpy.transforms.pipeline import native_html_transforms
from scribpy.utils import has_errors


def transform_options(state: ResolvedPipelineState) -> TransformOptions:
    """Build transform options from the project configuration.

    Args:
        state: Fully resolved pipeline state.

    Returns:
        Transform options derived from the project configuration.
    """
    return TransformOptions(
        document_title=state.config.document.title
        or state.config.project.name
        or "Document",
        toc_enabled=state.config.document.toc.enabled,
        toc_max_level=state.config.document.toc.max_level,
        toc_style=state.config.document.toc.style,
        numbering_enabled=state.config.document.numbering.enabled,
        numbering_max_level=state.config.document.numbering.max_level,
        numbering_style=state.config.document.numbering.style,
    )


def render_code_blocks(
    documents: tuple[TransformedDocument, ...],
    diagnostics: tuple[Diagnostic, ...],
    plugins: tuple[CodeBlockPlugin, ...],
    output_dir: Path,
    *,
    flattened: bool,
    target: str,
) -> tuple[
    tuple[TransformedDocument, ...],
    tuple[BuildArtifact, ...],
    tuple[Diagnostic, ...],
]:
    """Render fenced-code-block plugins and append diagnostics.

    Args:
        documents: Target-ready documents to inspect.
        diagnostics: Diagnostics already collected by the build.
        plugins: Ordered code-block plugins to apply.
        output_dir: Destination root for plugin-generated assets.
        flattened: Whether output documents will be merged into one page.
        target: Artifact target label.

    Returns:
        Rewritten documents, generated artifacts, and accumulated diagnostics.
    """
    rendered_documents = documents
    artifacts: list[BuildArtifact] = []
    for plugin in plugins:
        rendered_documents, plugin_artifacts, plugin_diags = (
            plugin.render_documents(
                rendered_documents,
                output_dir=output_dir,
                flattened=flattened,
                target=target,
            )
        )
        artifacts.extend(plugin_artifacts)
        diagnostics = (*diagnostics, *plugin_diags)
        if has_errors(diagnostics):
            break
    return rendered_documents, tuple(artifacts), diagnostics


def preflight_code_block_plugins(
    state: ResolvedPipelineState,
    plugins: tuple[CodeBlockPlugin, ...],
) -> tuple[Diagnostic, ...]:
    """Run early plugin validation only for plugins present in source Markdown.

    Args:
        state: Fully resolved pipeline state.
        plugins: Code-block plugins to validate.

    Returns:
        Preflight diagnostics from plugins whose blocks appear in the source.
    """
    diagnostics: list[Diagnostic] = []
    for plugin in plugins:
        if any(
            plugin.has_blocks(document.source) for document in state.documents
        ):
            diagnostics.extend(plugin.preflight())
    return tuple(diagnostics)


def code_block_plugins(
    registry: ExtensionRegistry,
    html_config: HtmlBuilderConfig,
    override: DiagramRenderer | None,
) -> tuple[CodeBlockPlugin, ...]:
    """Return built-in and registry-provided code-block plugins.

    Args:
        registry: Extension registry providing additional plugins.
        html_config: HTML builder configuration.
        override: Optional diagram renderer override.

    Returns:
        Ordered tuple of code-block plugins to apply.
    """
    return (
        PlantUmlPlugin(html_config.plantuml, override),
        MermaidPlugin(html_config.mermaid),
        *registry.code_block_plugins,
    )


def custom_html_transforms(
    registry: ExtensionRegistry,
) -> tuple[Transform, ...]:
    """Return registry HTML transforms that are not already native.

    Args:
        registry: Extension registry to query.

    Returns:
        Non-native HTML transforms registered by extensions.
    """
    native = native_html_transforms()
    return tuple(t for t in registry.html_transforms if t not in native)


__all__ = [
    "code_block_plugins",
    "custom_html_transforms",
    "preflight_code_block_plugins",
    "render_code_blocks",
    "transform_options",
]
