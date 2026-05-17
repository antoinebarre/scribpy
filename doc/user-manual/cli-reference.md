# CLI reference

## Output model

Normal CLI output is a concise execution report:

```text
✔ Resolve project configuration — done
✔ Parse project documents — done
✔ Run lint rules — done
✔ Build HTML (site) — done

Primary artifact: build/site/site
Additional artifacts: 36
```

Diagnostics are printed separately on stderr with stable codes and remediation
hints. This keeps success paths readable while preserving detail on failure.

## Global options

| Option | Meaning |
| --- | --- |
| `--log-level {DEBUG,INFO,WARNING,ERROR}` | Enable execution logging at the selected level. |
| `--log-console` | Also stream logs to stderr. |
| `--log-file PATH` | Write logs to a custom file. Relative paths are project-relative. |

## `scribpy demo create`

Create a tutorial project containing `scribpy.toml`, Markdown sources, assets,
and examples.

```bash
scribpy demo create [TARGET] [--variant {valid,invalid}] [--force]
```

| Argument | Meaning |
| --- | --- |
| `TARGET` | Destination directory. Defaults to `scribpy-demo`. |
| `--variant valid` | Generate a project expected to pass validation. |
| `--variant invalid` | Generate a project with intentional lint problems. |
| `--force` | Overwrite demo-managed files already present in `TARGET`. |

Exit codes: `0` success, `1` demo creation diagnostics, `2` invalid CLI usage.

## `scribpy index check`

Validate project discovery and index configuration without parsing Markdown
content.

```bash
scribpy index check [--root PATH]
```

Checks:

1. `scribpy.toml` can be found and loaded;
2. `paths.source` stays inside the project;
3. Markdown files are discovered deterministically;
4. explicit index entries are valid, non-duplicated, and present;
5. unindexed discovered files are reported as warnings when relevant.

Exit codes: `0` no blocking errors, `1` blocking diagnostics, `2` invalid usage.

## `scribpy parse check`

Run the full preparation pipeline through Markdown parsing and semantic
extraction.

```bash
scribpy parse check [--root PATH]
```

On success, reports the number of parsed documents. Diagnostics can still be
warnings, for example malformed frontmatter that can be recovered from.

## `scribpy lint`

Run the shared preparation pipeline and all active lint rules.

```bash
scribpy lint [--root PATH]
```

The built-in rule set checks heading structure, broken internal references, and
missing local assets. Any error diagnostic produces exit code `1`.

## `scribpy build markdown`

Build one deterministic assembled Markdown document.

```bash
scribpy build markdown [--root PATH] [--output-dir PATH]
```

| Option | Meaning |
| --- | --- |
| `--root PATH` | Project root, child path, or direct `scribpy.toml` path. |
| `--output-dir PATH` | Directory receiving `document.md`. Defaults to `build/markdown`. |

Pipeline: preparation → lint → Markdown transforms → merge → write artifact.

## `scribpy build html`

Build HTML output either as one self-contained page or as a MkDocs-backed site.

```bash
scribpy build html [--root PATH] [--mode {single-page,site}] [--output-dir PATH]
```

| Option | Meaning |
| --- | --- |
| `--mode single-page` | Produce one HTML document. Default mode. |
| `--mode site` | Produce a MkDocs project scaffold and rendered static site. |
| `--output-dir PATH` | Override the configured HTML build directory for this run. |

### Produced artifacts

| Mode | Default main output |
| --- | --- |
| `single-page` | `build/html/index.html` |
| `site` | `build/site/site/` |

Additional CSS/assets are built as needed but summarized by count in normal CLI
output instead of being printed one by one.
