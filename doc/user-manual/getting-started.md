# Getting started

## Install

```bash
pip install scribpy
```

Scribpy requires Python 3.12 or newer.

## Create the demo project

```bash
scribpy demo create scribpy-demo
```

The demo contains a valid `scribpy.toml`, Markdown sources under `doc/`, nested
pages, and assets. It is useful as a runnable reference project.

```bash
scribpy index check --root scribpy-demo
scribpy parse check --root scribpy-demo
scribpy lint --root scribpy-demo
scribpy build markdown --root scribpy-demo
scribpy build html --mode single-page --root scribpy-demo
scribpy build html --mode site --root scribpy-demo
```

## CI/CD-friendly outputs

Every build command can write outside the default `build/` tree:

```bash
scribpy build markdown --root scribpy-demo --output-dir /tmp/artifacts/markdown
scribpy build html --mode site --root scribpy-demo --output-dir /tmp/artifacts/site
```

Relative output directories are resolved from the project root. Absolute paths
are preserved, which is useful when a CI runner expects artifacts in a workspace
or mounted volume chosen by the pipeline.

## Python quick start

```python
import scribpy

result = scribpy.build_html(
    "scribpy-demo",
    mode="site",
    output_dir="/tmp/artifacts/site",
)
scribpy.print_result(result)
```

Successful results stay compact. If a build fails, `print_result()` expands the
diagnostic code, location, message, and hint so the same API remains readable in
an interactive shell.
