"""Static assets and diagram handling for scribpy.

Manages images, diagrams, stylesheets, and other static files
referenced by Markdown documents.

Protocols:
    DiagramRenderer — render(source, output_format) -> bytes

Main functions:
    collect_assets(documents)              -> tuple[AssetRef, ...]
    validate_assets(project, assets)       -> list[Diagnostic]
    copy_assets(assets, output_dir, fs)    -> tuple[BuildArtifact, ...]
    render_mermaid(source, renderer)       -> RenderedAsset
    render_plantuml(source, renderer)      -> RenderedAsset
"""
