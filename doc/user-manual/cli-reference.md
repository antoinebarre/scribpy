# CLI Reference

The `scribpy` command provides a hierarchical CLI built with [Typer](https://typer.tiangolo.com/).

---

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Command completed successfully — no blocking errors. |
| `1` | Blocking user-facing diagnostics were reported. |
| `2` | Invalid CLI usage (bad arguments, unknown flags). |

---

## Output model

Normal CLI output is a concise execution report written to stdout:

```text
✔ Resolve project configuration — done
✔ Parse project documents — done
✔ Run lint rules — done
✔ Build HTML (site) — done

Primary artifact: build/site/site
Additional artifacts: 36
```

Diagnostics are printed to **stderr** with stable codes and remediation hints.
This keeps success paths readable while preserving actionable detail on failure:

```text
[error] LINT001 doc/guide/overview.md:1
  No H1 heading found.
  hint: Add a top-level '# Title' as the first heading in the file.
```

---

## Global options

These options apply to the root `scribpy` command and must be placed **before**
any subcommand:

| Option | Type | Default | Description |
|---|---|---|---|
| `--log-level` | `DEBUG` / `INFO` / `WARNING` / `ERROR` | off | Enable execution logging at the selected level. |
| `--log-console` | flag | off | Also stream log output to stderr. |
| `--log-file PATH` | path | auto | Write logs to a custom file. Relative paths are project-relative. |

```bash
# Enable INFO logging to the default file
scribpy --log-level INFO lint --root my-project

# Enable DEBUG logging to stderr and a custom file
scribpy --log-level DEBUG --log-console --log-file /tmp/scribpy.log build html --root my-project
```

---

## `scribpy demo create`

Create a tutorial project containing `scribpy.toml`, Markdown sources, assets,
and examples. Useful as a runnable reference or starting point.

```bash
scribpy demo create [TARGET] [--variant {valid,invalid}] [--force]
```

| Argument / Option | Default | Description |
|---|---|---|
| `TARGET` | `scribpy-demo` | Destination directory (created if absent). |
| `--variant valid` | — | Generate a project that passes all validation. |
| `--variant invalid` | — | Generate a project with intentional lint failures for learning. |
| `--force` | off | Overwrite demo-managed files if they already exist in `TARGET`. |

**Examples:**

```bash
# Create a valid demo in the default directory
scribpy demo create

# Create an invalid demo to explore diagnostics
scribpy demo create bad-demo --variant invalid

# Refresh an existing demo
scribpy demo create scribpy-demo --force
```

---

## `scribpy index check`

Validate project discovery and index configuration **without** parsing Markdown
content. The fastest pipeline command — ideal as a pre-flight check in CI.

```bash
scribpy index check [--root PATH]
```

| Option | Default | Description |
|---|---|---|
| `--root PATH` | current directory | Project root, a child path, or a direct path to `scribpy.toml`. |

**What is checked:**

1. `scribpy.toml` can be found and loaded without errors;
2. `paths.source` stays inside the project root;
3. Markdown files are discovered deterministically;
4. Explicit index entries are valid, non-duplicated, and present on disk;
5. Unindexed discovered files are reported as warnings (for `hybrid` mode).

**Examples:**

```bash
scribpy index check --root my-project
scribpy index check --root my-project/scribpy.toml
```

---

## `scribpy parse check`

Run the full preparation pipeline through Markdown parsing and semantic
extraction (headings, links, assets, frontmatter).

```bash
scribpy parse check [--root PATH]
```

| Option | Default | Description |
|---|---|---|
| `--root PATH` | current directory | Project root, child path, or `scribpy.toml` path. |

On success, reports the number of parsed documents. Diagnostics may still be
warnings — for example, malformed frontmatter that can be recovered from.

**Example:**

```bash
scribpy parse check --root my-project
# → Parsed 12 documents (0 errors, 2 warnings)
```

---

## `scribpy lint`

Run the shared preparation pipeline and all active lint rules.

```bash
scribpy lint [--root PATH]
```

| Option | Default | Description |
|---|---|---|
| `--root PATH` | current directory | Project root, child path, or `scribpy.toml` path. |

The built-in rule set checks heading structure, broken internal references, and
missing local assets. Any error diagnostic produces exit code `1`.

**Built-in rules:**

| Code | Description |
|---|---|
| `LINT001` | Every file must have exactly one `# H1` heading. |
| `LINT002` | Headings must not skip levels (e.g. `## H2` directly after `# H1` is fine; `### H3` directly after `# H1` is not). |
| `LINT003` | Internal links must resolve to an existing indexed file. |
| `LINT004` | Local asset references (images, files) must exist on disk. |

**Example:**

```bash
scribpy lint --root my-project
```

---

## `scribpy build markdown`

Build one deterministic assembled Markdown document from all indexed source files.

```bash
scribpy build markdown [--root PATH] [--output-dir PATH]
```

| Option | Default | Description |
|---|---|---|
| `--root PATH` | current directory | Project root, child path, or `scribpy.toml` path. |
| `--output-dir PATH` | `build/markdown` | Directory receiving `document.md`. Relative paths are project-relative. |

**Pipeline:** preparation → lint → Markdown transforms → merge → write `document.md`

**Examples:**

```bash
scribpy build markdown --root my-project
scribpy build markdown --root my-project --output-dir /tmp/ci-artefacts/markdown
```

---

## `scribpy build html`

Build HTML output either as one self-contained page or as a MkDocs-backed site.

```bash
scribpy build html [--root PATH] [--mode {single-page,site}] [--output-dir PATH]
```

| Option | Default | Description |
|---|---|---|
| `--root PATH` | current directory | Project root, child path, or `scribpy.toml` path. |
| `--mode single-page` | default | Produce one self-contained HTML document. |
| `--mode site` | — | Produce a MkDocs scaffold and rendered static site. |
| `--output-dir PATH` | mode-dependent | Override the configured HTML build directory for this run. |

**Default output directories:**

| Mode | Default output |
|---|---|
| `single-page` | `build/html/index.html` |
| `site` | `build/site/site/` |

Additional CSS files and assets are copied as needed. The CLI summarises them
by count rather than printing each path individually.

**Examples:**

```bash
# Default single-page build
scribpy build html --root my-project

# MkDocs site with custom output dir
scribpy build html --mode site --root my-project --output-dir /tmp/ci-artefacts/site

# Single-page HTML with verbose logging
scribpy --log-level INFO build html --root my-project
```
