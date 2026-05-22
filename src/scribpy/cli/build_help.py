"""Help text for build CLI commands."""

BUILD_DESCRIPTION = """\
Build documentation artifacts from a validated Scribpy project.

Build commands reuse the project preparation and lint chains before writing any
artifact. Supported targets: markdown, html, pdf.
"""
BUILD_EPILOG = """\
Examples:
  scribpy build markdown --root dd1
  scribpy build html --mode single-page
  scribpy build html --mode site
  scribpy build pdf --css theme/pdf.css
"""
BUILD_MARKDOWN_DESCRIPTION = """\
Build one deterministic assembled Markdown artifact from indexed source files.

The command parses and lints the project first, then writes
build/markdown/document.md only when no blocking diagnostics are present.
"""
BUILD_MARKDOWN_EPILOG = """\
Examples:
  scribpy build markdown --root dd1
  scribpy build markdown --root dd1 --output-dir /tmp/scribpy-artifacts
  scribpy build markdown --root .

Exit codes:
  0  artifact written successfully
  1  at least one blocking diagnostic
  2  invalid CLI usage
"""
BUILD_HTML_DESCRIPTION = """\
Build HTML documentation from indexed Markdown source files.

Two output modes are available:

  single-page  Produces one self-contained build/html/index.html file.
               External CSS files declared in [builders.html] css_files are
               copied into build/html/css/ and linked from the document.

  site         Wraps MkDocs to produce a rendered multi-page HTML site.
               Scribpy writes the MkDocs inputs under build/site/, then invokes
               MkDocs and stores the final static site under build/site/site/.

The command parses and lints the project first. No artifacts are written if
blocking diagnostics are present.
"""
BUILD_HTML_EPILOG = """\
Examples:
  scribpy build html --mode single-page
  scribpy build html --mode site --root path/to/project
  scribpy build html --mode site --root path/to/project --output-dir build/ci-site

Exit codes:
  0  all artifacts written successfully
  1  at least one blocking diagnostic
  2  invalid CLI usage
"""

BUILD_PDF_DESCRIPTION = """\
Build a PDF document from indexed Markdown source files.

The command parses, lints, applies Markdown transforms, copies local assets,
then delegates the final rendering to the injectable PDF renderer. The default
renderer uses the optional markdown-pdf package when installed.

CSS files declared in [builders.pdf] css, or passed with --css, are applied
after Scribpy's built-in printable defaults.
"""
BUILD_PDF_EPILOG = """\
Examples:
  scribpy build pdf
  scribpy build pdf --root path/to/project --css theme/pdf.css
  scribpy build pdf --root path/to/project --output-dir build/release-pdf

Exit codes:
  0  PDF written successfully
  1  at least one blocking diagnostic
  2  invalid CLI usage
"""

__all__ = [
    "BUILD_DESCRIPTION",
    "BUILD_EPILOG",
    "BUILD_HTML_DESCRIPTION",
    "BUILD_HTML_EPILOG",
    "BUILD_MARKDOWN_DESCRIPTION",
    "BUILD_MARKDOWN_EPILOG",
    "BUILD_PDF_DESCRIPTION",
    "BUILD_PDF_EPILOG",
]
