# Diagnostic reference

Collection diagnostics use stable codes and one of `error`, `warning`, or
`info`. Default rules run in deterministic registry order — the order the
rule classes are listed in
`scribpy.core.diagnostics.engine.DEFAULT_COLLECTION_DIAGNOSTIC_RULES` — so
findings from the same source file appear in a repeatable sequence across
runs. Each rule implements the `CollectionDiagnosticRule` protocol
(`code: str` and `diagnose(context) -> Iterable[CollectionDiagnostic]`) and
is entirely independent: adding, removing, or reordering one rule never
requires touching the engine or any other rule. The registry lives in
`scribpy.core.diagnostics.engine.DEFAULT_COLLECTION_DIAGNOSTIC_RULES`,
re-exported from `scribpy.core.diagnostics`. See
[Diagnostics engine](../architecture/diagnostics.md) for the underlying
Strategy + Registry design, and
[Extension API](../python-api/extensions.md) for writing your own rule.

Only `EXTERNAL_IMAGE_REFERENCE` is a warning; every other default rule is an
error. `concatenate()` and `mkdocs_export()` refuse to produce output while
any error-level finding exists — warnings are informational and never block
a build.

## Default collection rules

| Code | Severity | Trigger | Remediation |
|---|---|---|---|
| `SOURCE_FIRST_HEADING_NOT_H1` | error | First discovered Markdown heading is not H1. | Make the page title the first heading and use `#`. |
| `SOURCE_H1_COUNT_INVALID` | error | File contains zero or more than one H1. | Keep exactly one source H1. For multiple H1s, location points to the second. |
| `HEADING_LEVEL_OVERFLOW` | error | Source heading plus assembly folder offset exceeds H6. | Reduce source depth or folder nesting. |
| `LOCAL_IMAGE_MISSING` | error | Empty or local image target does not exist. | Correct target or add file. |
| `IMAGE_OUTSIDE_ROOT` | error | Resolved local image escapes collection root. | Store resource inside project and update path. |
| `EXTERNAL_IMAGE_REFERENCE` | warning | Image target is external. | Accept network dependency or make image local. |
| `INTERNAL_MARKDOWN_LINK_MISSING` | error | Resolved internal `.md` target is absent. | Correct relative path or add target. |
| `INTERNAL_MARKDOWN_LINK_OUTSIDE_ROOT` | error | Internal `.md` link escapes root. | Move/link inside collection. |
| `LOCAL_ANCHOR_LINK` | error | Any Markdown link target contains `#`. | Remove fragment and link to page only. |

`InternalMarkdownLinkRule.code` is the umbrella identifier
`INTERNAL_MARKDOWN_LINK_RULE`, while emitted findings use the two specific
missing/outside codes.

## Worked examples per rule

The examples below show the minimal source content that triggers each rule.
Assume a project root containing only the file shown, with no `order`
restriction.

**`SOURCE_FIRST_HEADING_NOT_H1`** — first heading is H2, not H1:

```markdown
## Getting started

Some text.
```

**`SOURCE_H1_COUNT_INVALID`** — two H1s in one file:

```markdown
# Getting started

# Another Title
```

**`LOCAL_IMAGE_MISSING`** — the referenced file does not exist on disk:

```markdown
# Getting started

![Diagram](diagrams/missing.png)
```

**`EXTERNAL_IMAGE_REFERENCE`** (warning, does not block a build) — an
`http(s)` image target:

```markdown
# Getting started

![Logo](https://example.com/logo.png)
```

**`INTERNAL_MARKDOWN_LINK_MISSING`** — link to a `.md` file that does not
exist:

```markdown
# Getting started

See [the setup guide](setup.md).
```

**`LOCAL_ANCHOR_LINK`** — any link carrying a `#` fragment, even to a real
page:

```markdown
# Getting started

See [the setup section](setup.md#installation).
```

Fix this last one by linking to the page only (`[the setup section
guide](setup.md)`) — anchors are generated automatically by the assembly
pipeline's link rewriter and cannot be written by hand in source. See
[Links and images](../notes-project/links-and-images.md) for the full
rationale.

## Report model

```python
report = collection.diagnose()

print(report.has_errors)
print(report.summary())

warnings = report.by_severity(scribpy.DiagnosticSeverity.WARNING)
```

Each `CollectionDiagnostic` exposes:

| Field | Type | Meaning |
|---|---|---|
| `code` | `str` | Stable machine-readable identifier. |
| `severity` | `DiagnosticSeverity` | Error, warning, or info. |
| `message` | `str` | Human explanation including relevant target. |
| `path` | `Path | None` | Source file when applicable. |
| `line` | `int | None` | One-based source line when available. |

`summary()` returns `No collection diagnostics.` when empty. Otherwise it
renders one line per finding in registry and source traversal order.

A full inspection loop:

```python
collection = scribpy.MarkdownCollection.from_tree("handbook")
report = collection.diagnose()

for finding in report.diagnostics:
    location = f"{finding.path}:{finding.line}" if finding.path else "project"
    print(f"[{finding.severity}] {finding.code} at {location}: {finding.message}")

if report.has_errors:
    raise SystemExit(1)
```

## Project validation diagnostics

`validate_project` combines manifest inspection, MkForge findings, and adapted
collection diagnostics into `ProjectDiagnostic`. It adds `column`, `category`,
and optional structured `target` fields. The report also records root,
Markdown file count, and manifest count.

Consumers should branch on `severity` and `code`, not parse the English
message. Render messages for people with `render_validation_report`.

## Custom rule replacement behavior

```python
report = collection.diagnose([MyRule()])
```

An explicit iterable replaces default rules for that call. To extend defaults,
import the extension API registry and compose a new iterable:

```python
from scribpy.core.diagnostics import DEFAULT_COLLECTION_DIAGNOSTIC_RULES

rules = (*DEFAULT_COLLECTION_DIAGNOSTIC_RULES, MyRule())
report = collection.diagnose(rules)
```

