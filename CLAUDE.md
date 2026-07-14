# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Commands

```bash
# Full quality gate (lint + typecheck + security + tests + metrics)
make check

# Run tests only
make test

# Run a single test file or test by name
uv run pytest tests/test_manifest.py
uv run pytest tests/test_assembly.py::TestLinkRewriter::test_rewrite_link_to_known_file

# Lint only
make lint

# Type-check only
make typecheck

# Format source
make format

# Build wheel
make build

# Clean work/ directory (done automatically by make check)
make clean
```

All tools run through `uv run`. The `work/` directory holds all cache and artifact output (pytest cache, mypy cache, ruff cache, coverage data, build output). Never commit it.

---

## Architecture

scribpy is a **Markdown collection assembler**: it reads a tree of `.md` files described by `scribpy.yml` manifests and produces a single assembled Markdown document with rewritten links, numbered headings, and rendered diagrams.

### Domain model (`src/scribpy/core/`)

| Module | Role |
|---|---|
| `manifest.py` | Load and validate `scribpy.yml` files (root and folder variants) |
| `markdown_file.py` | Single `.md` file on disk; validates via mkforge |
| `markdown_document.py` | In-memory Markdown text; extracts images, manipulates content |
| `markdown_collection.py` | Recursive tree of `MarkdownFile`s; drives traversal and ordering |
| `markdown_image.py` | Represents a local image reference found in Markdown |
| `heading_normalizer.py` | Shifts ATX heading levels in Markdown text |
| `diagram_encoding.py` | zlib + base64url encoding used by Kroki web backend |
| `errors.py` | Domain exception hierarchy |
| `log.py` | Logging context manager |

### Assembly pipeline (`src/scribpy/core/assembly/`)

`concatenate()` in `concatenate.py` is the single public entry point. It builds a `tuple[TransformFn, ...]` and drives them through `apply_transforms()` in `pipeline.py`. Each `TransformFn` is `Callable[[AssembledDocument], AssembledDocument]`.

Pipeline order (fixed):
1. **Heading numbering** (`heading_numbering.py`) — MkForge adapter; enabled by `build.heading_numbering.enabled`
2. **Link rewriting** (`link_rewriter.py`) — rewrites `[label](file.md)` → `[label](#slug)`; uses numbered slugs when step 1 ran
3. **TOC generation** (`toc.py`) — inserts a Markdown list after the H1; enabled by `build.toc: true`; slugs are consistent with step 2
4. **PlantUML rendering** (`plantuml_transform.py`) — renders fenced ` ```plantuml ` blocks via backend
5. **Mermaid rendering** (`mermaid_transform.py`) — renders fenced ` ```mermaid ` blocks via backend
6. **Image collection** (`image_collector.py`) — copies local images to `assets/`, rewrites paths

### Renderer backends (`src/scribpy/core/plantuml/`, `src/scribpy/core/mermaid/`)

Each diagram type defines a `Protocol` (e.g. `PlantUmlRenderer`) and a `make_renderer(backend: str)` factory. The only implemented backend is `"web"` (Kroki). The `"local"` backend raises `NotImplementedError` intentionally.

### Diagnostic engine (`src/scribpy/core/diagnostics/`)

`diagnose_collection()` runs an `Iterable[CollectionDiagnosticRule]` (Strategy + Registry) against a `MarkdownCollection`. Each rule implements a single-method Protocol (`diagnose()`). The 8 default rules live in `diagnostics/rules/`. Adding a rule requires no changes to the engine.

### Manifest contract

Root `scribpy.yml` keys: `project`, `build`, `order`.

`build` supports:
- `toc` (bool, default `false`) — inserts a TOC after the first H1 of the assembled document
- `heading_numbering.enabled` (bool, default `True` when block is present)
- `renumber_headings` (bool, legacy alias — ignored when `heading_numbering` also present)
- `plantuml_backend` / `mermaid_backend` (str, default `"web"`)

### Extension points

- **New diagnostic rule**: implement `CollectionDiagnosticRule` protocol, add to `DEFAULT_COLLECTION_DIAGNOSTIC_RULES` in `diagnostics/rules/__init__.py`.
- **New renderer backend**: implement the relevant `Protocol` (`PlantUmlRenderer` or `MermaidRenderer`), register in the `make_renderer()` factory.
- **New pipeline step**: write a pure `TransformFn`, inject it into the `transforms` tuple in `concatenate()`.

---

## Project Structure

- Source code lives in `src/scribpy/`.
- Tests live in `tests/`.
- Temporary outputs (coverage, caches, build artifacts) go into `work/`.
- Architecture docs and ADRs live in `doc/`.

---

## Coding Standards

- Strictly follow Python PEP rules and the Google Python Style Guide for all
  Python code.
- Keep each function's cyclomatic complexity at or below 10.
- Keep Python modules below 500 lines unless an ADR explicitly justifies a
  larger module.
- Do not split a module purely to reduce its line count or cyclomatic
  complexity. A split is justified only when the resulting modules have
  genuinely independent reasons to change.
- Write Google-style docstrings for every function and class, including private
  functions and classes.
- Write clean, auditable code with simple control flow.
- Favor clarity over cleverness.
- Use precise names for modules, classes, functions, variables, and tests.
- Keep comments rare and useful.
- Apply SOLID principles strictly:
  - Single Responsibility: each module, class, and function must have one
    clear reason to change.
  - Open/Closed: add behavior through new focused implementations, rules,
    strategies, or registries instead of editing large conditional blocks.
  - Liskov Substitution: implementations of a public protocol must remain
    interchangeable.
  - Interface Segregation: depend on narrow protocols or callables rather
    than broad objects with unrelated responsibilities.
  - Dependency Inversion: high-level workflows depend on stable interfaces,
    not concrete low-level details.

## Dependencies

- Minimize external dependencies.
- Prefer Python standard library packages.
- Do not add third-party dependencies unless there is a clear technical need
  that cannot reasonably be met with the standard library.
- Explain the reason for any new dependency before adding it.

## Implementation Guidance

- Start substantial feature work and architecture changes with an Architecture
  Decision Record in `doc/` before implementing code.
- Keep changes focused on the requested behavior.
- Keep public interfaces small.
- Name modules, classes, functions, variables, and tests with business/domain
  vocabulary first.
- Avoid global mutable state unless there is a clear reason.
- Prefer deterministic behavior and explicit inputs.
- Use design patterns deliberately:
  - Strategy when behavior varies by profile, format, rule, or policy.
  - Registry when behavior must be extended without modifying the engine.
  - Adapter when exposing a simple callable or external API.
  - Factory functions when object creation has validation or multiple variants.
- Write tests for new behavior.
- Maintain 100% test coverage.
- Test function docstrings must state the requirement being verified using the
  prefix `Requirement:`.
- Every module, function, class, method, and test must include a strict
  Google-style docstring, including private functions and classes.
- Function and method docstrings must include:
  - a precise summary that explains the domain behavior;
  - `Args:` for every parameter except `self` and `cls`;
  - `Returns:` for every non-`None` return value;
  - `Raises:` for every intentionally raised exception.
- Class docstrings must include `Attributes:` when instances expose public
  attributes.

## Project Structure

- Source code lives in `src/scribpy/`.
- Tests live in `tests/`.
- Temporary outputs (coverage, caches, build artifacts) go into `work/`.

## Quality Checks

Before finishing code changes, run:

```bash
make check
```

Use `make ci` for non-mutating verification.

---

## Mode Architecte

Activate this mode by saying: "mode architecte".

### Posture

- **Challenge first.** Before accepting any feature request, ask: Is this
  feature necessary? What problem does it solve? Can an existing mechanism
  handle it? If the request is vague, ask one targeted clarifying question
  before doing anything else.
- **Incremental ADRs.** Propose one focused ADR per decision. Never bundle
  unrelated decisions in one document.
- **Simplicity over cleverness.** Prefer fewer abstractions. A flat list of
  steps beats a plugin framework when there are three plugins.
- **Injection over inheritance.** Pass dependencies explicitly. Never use
  base-class coupling or hidden global state.
- **Design patterns deliberately.** Use Strategy when behavior varies by
  policy. Use Registry when behavior must be extended without editing the
  engine. Use Adapter to isolate I/O. Use Pipeline for ordered, independently
  testable steps. Do not introduce a pattern for decoration.

### Deliverables

When asked to design a feature, produce documents in this order:

1. **SRS fragment** — list only the requirements that are new or changed. Use
   `REQ-<CATEGORY>-<NN>` identifiers. Each requirement gets one sentence with
   SHALL / SHOULD / MAY. Include acceptance criteria.
2. **ADR** — one decision, one document. Sections: Context, Decision,
   Consequences, Alternatives rejected. Store in `doc/ADR-NNN-slug.md`.
3. **SDD section** — update the relevant section of `doc/SDD.md` to reflect
   the design. Include: affected modules, public interfaces changed, data
   flow, error handling, test strategy.

### Constraints

- SOLID principles strictly applied.
- Each module, class, and function has one clear reason to change.
- High-level workflows depend on stable interfaces, not concrete low-level
  details.
- No module exceeds 500 lines unless an ADR explicitly justifies it.
- No function has cyclomatic complexity above 10.
- Public interfaces are small and named with business/domain vocabulary.
- No global mutable state.

---

## Mode Codeur

Activate this mode by saying: "mode codeur".

### Posture

- **Clarity over cleverness.** Write code a junior can read without
  explanation.
- **PEP-compliant always.** Follow PEP 8, PEP 257 (Google style), PEP 484,
  PEP 526. Run `make check` before declaring done.
- **100% check coverage.** Every code change must leave `make check` passing.
  Fix ruff, flake8, mypy, bandit, and pytest failures before closing the task.
- **Defensive programming at boundaries only.** Validate at entry points (CLI
  args, external API responses, file I/O). Trust internal code and framework
  guarantees. Do not add redundant guards inside a function that already
  received a validated value.
- **Exceptions with intent.** Raise only when the caller genuinely cannot
  continue. Name exceptions with domain vocabulary. Never use bare `except:`.
  Never swallow exceptions silently.
- **Prefer stdlib, then well-known packages.** Use `pathlib`, `dataclasses`,
  `typing`, `importlib.resources`. Do not add a dependency that the stdlib can
  handle.
- **Injection over inheritance.** Pass dependencies as arguments. Avoid global
  state.

### Coding Standards (Codeur)

- Google-style docstrings on every function, method, class — including private
  ones.
- Function docstrings: summary + `Args:` + `Returns:` + `Raises:`.
- Class docstrings: summary + `Attributes:` when public attributes exist.
- Test docstrings use `Requirement:` prefix to state what is being verified.
- Names use business/domain vocabulary.
- Cyclomatic complexity <= 10 per function.
- Module size <= 500 lines (justified by ADR if exceeded).

### Testing Strategy

For every code change, write:

1. **Unit tests** — mock all I/O and subprocess calls. Test one function in
   isolation. Cover the pass path, the fail path, and each `Raises:` clause.
2. **Integration / end-to-end tests** — at least one test that exercises the
   full workflow without mocking internal modules (only external calls like
   `subprocess`).

Test naming: `test_<what>_<condition>`.

### Quality Gate

Before reporting done, run:

```bash
make check
```

When fixing linter/type errors:
- `ruff` errors — fix the code, not `# noqa`.
- `mypy` errors — add proper type annotations; never use `# type: ignore`.
- `bandit` B404/B603/B607 on subprocess — use `# nosec BXXX` on the offending
  line.