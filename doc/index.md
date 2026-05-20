# Scribpy

**Scribpy** is a documentation compiler and Docs-as-Code toolkit for Python (≥ 3.12).
It parses, lints, transforms, and exports Markdown files into structured output formats:
self-contained HTML, MkDocs-backed sites, and assembled Markdown documents.

---

## Why Scribpy?

Writing documentation as code means keeping your Markdown sources in the same repository as
your code, reviewing them in pull requests, and building them in CI. Scribpy is designed for
this workflow:

- **Typed, immutable result objects** — every operation returns a result carrying both output
  and diagnostics; exceptions are reserved for programmer errors.
- **Functional pipeline** — parse → lint → transform → build. Each stage is independently
  accessible through the Python API or CLI.
- **Extensible** — add your own lint rules or transforms without touching Scribpy's internals.
- **Single artefact or full site** — produce a single self-contained HTML page or scaffold
  a MkDocs project and render it in one command.

---

## Quick start

=== "CLI"

    ```bash
    pip install scribpy

    # Create a runnable demo project
    scribpy demo create scribpy-demo

    # Validate → lint → build
    scribpy index check --root scribpy-demo
    scribpy lint --root scribpy-demo
    scribpy build html --mode site --root scribpy-demo
    ```

=== "Python"

    ```python
    import scribpy

    scribpy.create_demo("scribpy-demo")
    result = scribpy.build_html("scribpy-demo", mode="site")
    scribpy.print_result(result)
    ```

---

## Documentation sections

| Section | What you will find |
|---|---|
| [Getting Started](user-manual/getting-started.md) | Installation, demo project, first build |
| [Configuration](user-manual/configuration.md) | `scribpy.toml` reference with all keys and defaults |
| [Pipelines](user-manual/pipelines.md) | How each command executes stage by stage |
| [CLI Reference](user-manual/cli-reference.md) | Every command, option, and exit code |
| [Python API](user-manual/python-api-reference.md) | Full signature, behaviour, and examples for every public function |
| [Public Classes & Types](user-manual/public-classes.md) | Every result, data, and configuration class |
| [Extensions](user-manual/extensions.md) | Custom lint rules and transforms |
| [Markdown Guide](user-manual/markdown-guide.md) | Best practices for writing Scribpy-compatible Markdown |
