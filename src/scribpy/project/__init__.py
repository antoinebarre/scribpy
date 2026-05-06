"""Project scanning and document index management for scribpy.

Builds the project view from configuration and filesystem discovery.
Filesystem access is injected via the FileSystem protocol.

Index modes: explicit | filesystem | hybrid
    explicit   — order fully controlled by scribpy.toml (recommended)
    filesystem — files sorted by discovery order
    hybrid     — auto-discovery with optional overrides

Main functions:
    scan_project(root, config, fs)                -> tuple[SourceFile, ...]
    build_document_index(config, files)
        -> tuple[DocumentIndex, list[Diagnostic]]
    validate_document_index(index, files)         -> list[Diagnostic]
    load_project(root, services)
        -> tuple[Project | None, list[Diagnostic]]
    resolve_project_paths(project)                -> Project
"""
