"""Output generation layer for scribpy.

A builder is a plain callable:
    Builder = Callable[[BuildContext], BuildResult]

Supported targets:
    markdown — assembled single-file Markdown output
    html     — HTML output (single-page or multi-page)
    pdf      — PDF output via WeasyPrint or Pandoc

Rendering engines (HtmlRenderer, PdfRenderer) are injected via
the BuildContext so concrete adapters can be swapped.

Main functions:
    build_markdown(context)               -> BuildResult
    build_html(context, renderer)         -> BuildResult
    build_pdf(context, renderer)          -> BuildResult
    build_targets(context, builders_map)  -> BuildResult
"""
