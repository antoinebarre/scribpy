"""Internal data model for scribpy documentation objects.

Defines the core frozen dataclasses that flow through the pipeline:
    Project       — top-level documentation project state
    SourceFile    — a file discovered in the project
    Document      — a parsed Markdown document
    MarkdownAst   — parser output (tokens + backend tag)
    Heading       — a Markdown heading node
    Reference     — a Markdown link or cross-reference
    AssetRef      — an image, diagram, or static asset reference
    DocumentIndex — ordered index of files for assembly
    Diagnostic    — an error, warning, or info message
"""
