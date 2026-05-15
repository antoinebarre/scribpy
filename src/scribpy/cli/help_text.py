"""Help text for non-build CLI commands."""

_ROOT_DESCRIPTION = """\
Scribpy command-line tools for Docs-as-Code project checks and tutorial setup.

The CLI is intentionally small: it parses commands, calls application services,
prints diagnostics, and returns stable exit codes.
"""
_ROOT_EPILOG = """\
Common workflows:
  1. Create a valid tutorial project:
       scribpy demo create dd1

  2. Validate the generated project:
       scribpy index check --root dd1

  3. Create a broken tutorial project to learn diagnostics:
       scribpy demo create dd1 --variant invalid --force
       scribpy index check --root dd1

More help:
  scribpy demo create -h
  scribpy index check -h
"""
_PARSE_DESCRIPTION = """\
Parse Markdown sources and verify the FC-03 semantic extraction chain.

Parse commands load configuration, discover source files, build the document
index, and parse each Markdown file into a typed Document. They report
diagnostics from every stage of the chain.
"""
_PARSE_EPILOG = """\
Examples:
  scribpy parse check --root dd1
  scribpy parse check --root dd1/scribpy.toml
  scribpy parse check

Use `scribpy demo create dd1` first if you need a project to try.
"""
_PARSE_CHECK_DESCRIPTION = """\
Parse all Markdown sources and report diagnostics for the full FC-03 chain:
configuration, source discovery, document index, and Markdown parsing.

A valid project prints the number of successfully parsed documents and returns
exit code 0. Any blocking error returns exit code 1.
"""
_PARSE_CHECK_EPILOG = """\
Examples:
  scribpy parse check --root dd1
  scribpy parse check --root dd1/scribpy.toml
  scribpy parse check --root .

What is checked:
  - scribpy.toml can be found and loaded
  - paths.source exists and stays inside the project
  - Markdown files are discovered and indexed
  - each Markdown file parses without errors
  - frontmatter, headings, links, and assets are extracted

Exit codes:
  0  no blocking error diagnostics
  1  at least one error diagnostic
  2  invalid CLI usage
"""
_LINT_DESCRIPTION = """\
Check documentation quality from the semantic document model.

Lint commands load configuration, discover and parse Markdown sources, then run
the configured documentation quality rules over the extracted semantic model.
"""
_LINT_EPILOG = """\
Examples:
  scribpy lint --root dd1
  scribpy lint --root dd1/scribpy.toml
  scribpy lint
"""
_INDEX_DESCRIPTION = """\
Inspect project source discovery and document index configuration.

Index commands do not parse Markdown content yet. They only validate the phase
2 project-context chain: configuration loading, source discovery, and document
index consistency.
"""
_INDEX_EPILOG = """\
Examples:
  scribpy index check --root dd1
  scribpy index check --root dd1/scribpy.toml
  scribpy index check

Use `scribpy demo create dd1` first if you need a project to try.
"""
_INDEX_CHECK_DESCRIPTION = """\
Validate that a Scribpy project can load scribpy.toml, discover Markdown files,
and build a coherent DocumentIndex.

The command prints diagnostics to stderr. A valid project prints nothing and
returns exit code 0.
"""
_INDEX_CHECK_EPILOG = """\
Examples:
  scribpy index check --root dd1
  scribpy index check --root dd1/scribpy.toml
  scribpy index check --root .

What is checked:
  - scribpy.toml can be found and loaded
  - paths.source exists and stays inside the project
  - Markdown files are discovered deterministically
  - explicit index entries exist, are relative, and are not duplicated
  - discovered files missing from an explicit index are reported as warnings

Exit codes:
  0  no blocking error diagnostics
  1  at least one error diagnostic
  2  invalid CLI usage
"""
_DEMO_DESCRIPTION = """\
Create small Scribpy tutorial projects that can be checked with
`scribpy index check`, `scribpy parse check`, and `scribpy lint`.

The demo command is useful when trying Scribpy in another repository because it
creates a complete mini project without requiring you to write scribpy.toml by
hand.
"""
_DEMO_EPILOG = """\
Examples:
  scribpy demo create dd1
  scribpy demo create dd1 --variant invalid
  scribpy demo create dd1 --force

After creation:
  scribpy index check --root dd1
"""
_DEMO_CREATE_DESCRIPTION = """\
Create a tutorial project containing scribpy.toml, README.md, and Markdown
files under doc/.

The valid variant passes index, parse, and lint checks. The invalid variant
intentionally creates lint diagnostics for learning and troubleshooting.
"""
_DEMO_CREATE_EPILOG = """\
Examples:
  scribpy demo create dd1
  scribpy demo create dd1 --variant valid
  scribpy demo create dd1 --variant invalid
  scribpy demo create dd1 --variant invalid --force

What it creates:
  dd1/scribpy.toml
  dd1/README.md
  dd1/doc/index.md
  dd1/doc/guide/setup.md
  dd1/doc/guide/workflow.md
  dd1/doc/reference/diagnostics.md
  dd1/doc/assets/*.png

Next steps:
  scribpy index check --root dd1
  scribpy parse check --root dd1
  scribpy lint --root dd1

Variants:
  valid    creates a project expected to pass index, parse, and lint checks
  invalid  creates a project with intentional lint diagnostics

Overwrite behavior:
  Existing demo files are not overwritten unless --force is passed.
"""

__all__ = [
    "_ROOT_DESCRIPTION",
    "_ROOT_EPILOG",
    "_PARSE_DESCRIPTION",
    "_PARSE_EPILOG",
    "_PARSE_CHECK_DESCRIPTION",
    "_PARSE_CHECK_EPILOG",
    "_LINT_DESCRIPTION",
    "_LINT_EPILOG",
    "_INDEX_DESCRIPTION",
    "_INDEX_EPILOG",
    "_INDEX_CHECK_DESCRIPTION",
    "_INDEX_CHECK_EPILOG",
    "_DEMO_DESCRIPTION",
    "_DEMO_EPILOG",
    "_DEMO_CREATE_DESCRIPTION",
    "_DEMO_CREATE_EPILOG",
]
