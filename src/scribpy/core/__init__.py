"""Public Python API facade for scribpy.

This is the stable user-facing interface. Internal package structure
may evolve independently.

Markdown document operations:
    load_markdown(path)                      -> Document
    save_markdown(document, path)            -> None
    get_headings(document)                   -> tuple[Heading, ...]
    get_links(document)                      -> tuple[Reference, ...]
    replace_link(document, old, new)         -> Document
    normalize_markdown(document, options)    -> Document
    merge_documents(documents, options)      -> Document
    split_document(document, strategy)       -> tuple[Document, ...]
    generate_toc(document_or_seq, options)   -> str

Project-level operations:
    build_project(root, target)              -> BuildResult
    lint_project(root)                       -> LintResult
"""
