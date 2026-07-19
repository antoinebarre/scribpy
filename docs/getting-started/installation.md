# Installation

Scribpy requires Python 3.12 or newer. The package provides both the `scribpy`
command and the `scribpy` Python module; they are installed together.

## Check Python

```shell
python --version
```

If the command reports an older interpreter, select a Python 3.12+ executable
before creating an environment. Scribpy does not manage Python installations.

## Install from this repository with uv

For contributors and local evaluation, clone or open the repository and run:

```shell
uv sync
uv run scribpy --version
```

`uv sync` creates or updates `.venv` from `pyproject.toml`. `uv run` executes
the command in that environment without requiring manual activation.

To include the tools used to build this documentation:

```shell
uv sync --group docs
uv run --group docs mkdocs build --strict
```

The `docs` group is optional. It contains MkDocs Material and the PlantUML
Markdown extension; it is not needed to use Scribpy.

## Install the local checkout with pip

From the repository root, inside an activated virtual environment:

```shell
python -m pip install .
scribpy --version
```

For editable development:

```shell
python -m pip install -e .
```

An editable installation reflects source changes immediately. It is convenient
for development but not a reproducible deployment artifact.

## Verify both interfaces

```shell
scribpy --help
python -c "import scribpy; print(scribpy.__version__)"
```

Both should report version `0.1.0` for this documentation version.

## Optional external tools and services

Core Markdown assembly needs no Node or Java installation. Diagram rendering
depends on the selected backend:

| Feature | Default requirement | Alternative |
|---|---|---|
| PlantUML blocks | Network access to PlantUML Server | Kroki network backend. Local PlantUML is not implemented. |
| Mermaid blocks | Network access to Kroki | Install Mermaid CLI and select `mermaid_cli`. |
| Mermaid CLI | Not used by default | Install `@mermaid-js/mermaid-cli`; ensure `mmdc` is on `PATH` or configure its path. |

A project without diagram fences never calls a diagram provider.

## Upgrade and uninstall

The exact command depends on how Scribpy was installed. For a local pip
installation:

```shell
python -m pip install --upgrade .
python -m pip uninstall scribpy
```

With uv, update the checkout and run `uv sync` again. Always rerun
`scribpy --version` and validate an existing project after an upgrade.

## Installation problems

- **`scribpy: command not found`** — use `uv run scribpy`, activate the
  environment, or ensure its scripts directory is on `PATH`.
- **Python version rejection** — use Python 3.12 or newer.
- **Import works but command is absent** — reinstall the package so the
  `[project.scripts]` entry point is created.
- **Diagram render fails** — installation may be correct; check the backend,
  network, URL, or `mmdc` separately.

