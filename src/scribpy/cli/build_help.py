"""Help text for build CLI commands."""

BUILD_DESCRIPTION = """\
Build documentation artifacts from a validated Scribpy project.

Build commands reuse the project preparation and lint chains before writing any
artifact. Phase 5 currently exposes the assembled Markdown target.
"""
BUILD_EPILOG = """\
Examples:
  scribpy build markdown --root dd1
  scribpy build markdown --root dd1/scribpy.toml
  scribpy build markdown
"""
BUILD_MARKDOWN_DESCRIPTION = """\
Build one deterministic assembled Markdown artifact from indexed source files.

The command parses and lints the project first, then writes
build/markdown/document.md only when no blocking diagnostics are present.
"""
BUILD_MARKDOWN_EPILOG = """\
Examples:
  scribpy build markdown --root dd1
  scribpy build markdown --root .

Exit codes:
  0  artifact written successfully
  1  at least one blocking diagnostic
  2  invalid CLI usage
"""

__all__ = [
    "BUILD_DESCRIPTION",
    "BUILD_EPILOG",
    "BUILD_MARKDOWN_DESCRIPTION",
    "BUILD_MARKDOWN_EPILOG",
]
