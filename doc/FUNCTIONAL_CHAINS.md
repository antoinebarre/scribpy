# Functional Chains — Scribpy

**Version:** 0.1.0-draft  
**Date:** 2026-05-06  
**Scope:** functional architecture and development sequencing

---

## 1. Purpose

This document translates the Scribpy Software Design Document into functional
chains, in a systems engineering sense: each chain describes an end-to-end
mission thread from an external trigger to an observable result, with the
functions, data flows, interfaces, controls, and expected outcomes needed to
realize that thread.

The goal is to guide development by implementing coherent operational
capabilities instead of isolated packages.

---

## 2. Functional Chain Definition

For Scribpy, a functional chain is defined as:

```text
trigger -> inputs -> functions -> intermediate products -> outputs -> feedback
```

Each chain identifies:

- the operational objective;
- the initiating actor or event;
- the primary input products;
- the ordered functions;
- the allocated Scribpy packages;
- the output products;
- the diagnostics and failure modes;
- the minimum viable implementation.

This follows the INCOSE-oriented functional architecture mindset: define what
the system must do, decompose behavior into functions, allocate those functions
to system elements, and preserve traceability from need to realization.

---

## 3. System Context

```text
User / CI
    |
    v
scribpy CLI / Python API
    |
    v
Markdown repository + scribpy.toml
    |
    v
Scribpy processing functions
    |
    v
Diagnostics + build artifacts
```

External actors:

| Actor | Role |
|-------|------|
| Documentation author | Writes Markdown and runs local commands |
| CI pipeline | Runs checks and reproducible builds |
| Extension author | Provides custom lint rules, transforms, builders, or renderers |
| External renderer | Converts diagrams, HTML, or PDF through injected adapters |

External systems:

| System | Interface |
|--------|-----------|
| Filesystem | Read sources, write artifacts, discover files |
| Git repository | Versioned source of truth |
| Markdown parser | Parse Markdown into normalized structures |
| HTML/PDF renderers | Produce final output artifacts |
| Diagram renderers | Produce rendered assets from code blocks |

---

## 4. Functional Architecture

Top-level function:

```text
F0 Engineer documentation artifacts from Markdown sources
```

Functional decomposition:

| ID | Function | Primary package |
|----|----------|-----------------|
| F1 | Initialize or locate a Scribpy project | `cli`, `config`, `project` |
| F2 | Load and validate configuration | `config`, `model` |
| F3 | Discover source files and build document index | `project`, `utils` |
| F4 | Parse Markdown documents | `parser`, `model` |
| F5 | Extract semantic document data | `parser`, `model` |
| F6 | Validate documentation quality | `lint`, `extensions` |
| F7 | Transform document set | `transforms`, `assets`, `extensions` |
| F8 | Assemble target document views | `builders`, `model` |
| F9 | Build output artifacts | `builders`, `themes`, `assets` |
| F10 | Report diagnostics and execution status | `utils`, `cli`, `core` |
| F11 | Expose stable user-facing commands and API | `cli`, `core` |

Canonical processing chain:

```text
configure -> scan -> parse -> extract -> lint -> transform -> assemble -> build -> report
```

---

## 5. Functional Chains

### FC-01 Load Project Context

Objective: establish a valid project context from a working directory.

```text
root path
  -> find_config
  -> load_toml_config
  -> parse_config
  -> validate_config
  -> load_project
  -> Project | diagnostics
```

Allocated packages:

| Function | Package |
|----------|---------|
| Find `scribpy.toml` | `config` |
| Parse raw TOML | `config`, `utils.toml` |
| Validate configuration | `config`, `model` |
| Create project state | `project`, `model` |

Inputs:

- current directory or explicit root;
- `scribpy.toml`;
- filesystem service.

Outputs:

- `Config`;
- `Project`;
- `list[Diagnostic]`.

Minimum viable implementation:

- config dataclasses;
- TOML loader;
- path normalization;
- basic validation for required sections and directories.

Development value: this chain creates the foundation for every other chain.

---

### FC-02 Discover and Index Sources

Objective: identify the Markdown source set and establish processing order.

```text
Project + Config
  -> scan_project
  -> build_document_index
  -> validate_document_index
  -> SourceFile[] + DocumentIndex + diagnostics
```

Allocated packages:

| Function | Package |
|----------|---------|
| Discover Markdown files | `project`, `utils.file_utils` |
| Build explicit/filesystem/hybrid index | `project` |
| Validate missing/duplicate entries | `project`, `lint` |

Inputs:

- project root;
- configured source directory;
- index mode;
- filesystem service.

Outputs:

- ordered `SourceFile` collection;
- `DocumentIndex`;
- diagnostics for missing files, duplicates, or invalid paths.

Minimum viable implementation:

- support `filesystem` and `explicit` index modes;
- deterministic ordering;
- relative path preservation.

Development value: this enables deterministic builds and reproducible CI.

---

### FC-03 Parse and Extract Document Semantics

Objective: convert Markdown files into typed document objects.

```text
SourceFile[]
  -> read_text
  -> parse_frontmatter
  -> parse_markdown
  -> extract_headings
  -> extract_links
  -> extract_assets
  -> Document[]
```

Allocated packages:

| Function | Package |
|----------|---------|
| Read source text | `utils.io`, `project` |
| Parse frontmatter | `parser`, `utils.yaml` |
| Parse Markdown | `parser` |
| Extract headings, links, assets | `parser`, `model` |

Inputs:

- indexed source files;
- Markdown parser implementation;
- filesystem service.

Outputs:

- `Document`;
- `MarkdownAst`;
- `Heading`;
- `Reference`;
- `AssetRef`.

Minimum viable implementation:

- parser protocol;
- lightweight default parser adapter;
- heading extraction;
- Markdown link and image extraction.

Development value: this chain creates the semantic model required by lint,
transforms, and builders.

---

### FC-04 Lint Documentation Quality

Objective: detect documentation defects before build.

```text
Project + Document[] + DocumentIndex + Registry
  -> select_lint_rules
  -> run_lint_rules
  -> aggregate diagnostics
  -> should_fail_build
  -> LintResult
```

Allocated packages:

| Function | Package |
|----------|---------|
| Build lint context | `lint`, `model` |
| Select configured rules | `lint`, `extensions` |
| Execute rules | `lint` |
| Format diagnostics | `utils.diagnostics`, `cli` |

Inputs:

- project and documents;
- lint configuration;
- extension registry.

Outputs:

- `LintResult`;
- diagnostics with severity, code, path, line, and hint;
- build failure decision.

Minimum viable implementation:

- `Diagnostic`;
- `LintResult`;
- `LINT001` missing H1;
- `LINT002` heading hierarchy;
- `LINT003` broken internal link;
- CLI command `scribpy lint`.

Development value: this gives users immediate value before the full build chain
exists.

---

### FC-05 Transform Document Set

Objective: produce target-ready document content without mutating sources.

```text
Document[]
  -> resolve_includes
  -> resolve_cross_references
  -> apply_section_numbering
  -> render_diagrams
  -> rewrite_links_for_target
  -> generate_toc_transform
  -> TransformedDocument[]
```

Allocated packages:

| Function | Package |
|----------|---------|
| Select transforms | `transforms`, `extensions` |
| Execute transform pipeline | `transforms` |
| Render diagrams | `assets`, `transforms` |
| Report transform diagnostics | `model`, `utils.diagnostics` |

Inputs:

- parsed documents;
- build target;
- transform configuration;
- extension registry;
- diagram renderer.

Outputs:

- transformed document collection;
- rendered assets;
- diagnostics.

Minimum viable implementation:

- transform protocol;
- transform context/result types;
- table of contents generation;
- section numbering;
- link rewrite for Markdown and HTML targets.

Development value: this is the main behavior multiplier, but it depends on the
document model and lint-visible references.

---

### FC-06 Assemble Markdown Document

Objective: merge the ordered document set into a single assembled Markdown file.

```text
DocumentIndex + TransformedDocument[]
  -> order_documents
  -> merge_documents
  -> normalize_boundaries
  -> write build/markdown/document.md
```

Allocated packages:

| Function | Package |
|----------|---------|
| Order documents | `project`, `builders` |
| Merge content | `core`, `builders` |
| Write artifact | `builders`, `utils.io` |

Inputs:

- transformed documents;
- document index;
- Markdown builder configuration.

Outputs:

- `BuildArtifact` for assembled Markdown;
- diagnostics.

Minimum viable implementation:

- `AssembledDocument`;
- Markdown builder;
- deterministic output path.

Development value: this is the first complete build artifact and should be the
first builder implemented.

---

### FC-07 Build HTML Output

Objective: render assembled documentation as HTML.

```text
AssembledDocument + Theme + CSS
  -> load_theme
  -> resolve_css_files
  -> render_template
  -> HtmlRenderer.render
  -> write build/html/index.html
```

Allocated packages:

| Function | Package |
|----------|---------|
| Resolve theme | `themes` |
| Resolve styles | `themes`, `config` |
| Render HTML | `builders`, renderer adapter |
| Copy assets | `assets` |

Inputs:

- assembled document;
- HTML builder config;
- theme paths;
- assets.

Outputs:

- HTML artifact;
- copied static assets;
- diagnostics.

Minimum viable implementation:

- single-page HTML builder;
- default template;
- CSS resolution;
- asset copy.

Development value: this creates a user-visible output suitable for docs
preview.

---

### FC-08 Build PDF Output

Objective: render documentation into a PDF deliverable.

```text
AssembledDocument or HTML
  -> resolve PDF theme/CSS
  -> render HTML if needed
  -> PdfRenderer.render
  -> write build/pdf/document.pdf
```

Allocated packages:

| Function | Package |
|----------|---------|
| Prepare printable view | `builders`, `themes` |
| Render PDF | `builders`, PDF adapter |
| Handle renderer failures | `builders`, `model` |

Inputs:

- assembled document or HTML;
- PDF builder config;
- PDF renderer.

Outputs:

- PDF artifact;
- diagnostics or `BuildExecutionError`.

Minimum viable implementation:

- PDF renderer protocol;
- one adapter, probably WeasyPrint first;
- graceful error if optional dependency is missing.

Development value: important final deliverable, but it should follow Markdown
and HTML because it has heavier external dependencies.

---

### FC-09 Manage Assets and Diagrams

Objective: validate, render, and copy non-Markdown resources.

```text
Document[]
  -> collect_assets
  -> validate_assets
  -> render_mermaid / render_plantuml
  -> copy_assets
  -> BuildArtifact[]
```

Allocated packages:

| Function | Package |
|----------|---------|
| Extract asset refs | `parser`, `assets` |
| Validate referenced files | `assets`, `lint` |
| Render diagrams | `assets`, renderer adapters |
| Copy static files | `assets`, `utils.io` |

Inputs:

- asset references;
- project paths;
- target output directory;
- diagram renderer protocols.

Outputs:

- rendered assets;
- copied assets;
- diagnostics.

Minimum viable implementation:

- image reference validation;
- static asset copy;
- defer diagram rendering behind protocol stubs.

Development value: asset validation should arrive early with lint; rendering can
arrive later with HTML/PDF.

---

### FC-10 Expose User Commands and API

Objective: provide stable entry points without duplicating business logic.

```text
CLI args / Python call
  -> application service
  -> functional chain
  -> result
  -> formatted output / exit code
```

Allocated packages:

| Function | Package |
|----------|---------|
| Parse command arguments | `cli` |
| Expose stable Python API | `core` |
| Format output | `cli`, `utils.diagnostics` |
| Return exit codes | `cli` |

Inputs:

- command arguments or Python function parameters.

Outputs:

- terminal output;
- exit code;
- public API return types.

Minimum viable implementation:

- `scribpy lint`;
- `scribpy build markdown`;
- `scribpy index check`;
- stable `core` facade for those same services.

Development value: this connects implemented functions to real user workflows.

---

## 6. Cross-Chain Data Products

| Data product | Produced by | Consumed by |
|--------------|-------------|-------------|
| `Config` | FC-01 | all chains |
| `Project` | FC-01 | FC-02 to FC-10 |
| `SourceFile` | FC-02 | FC-03 |
| `DocumentIndex` | FC-02 | FC-04, FC-06 |
| `Document` | FC-03 | FC-04, FC-05, FC-09 |
| `Diagnostic` | all validation chains | FC-10 |
| `TransformedDocument` | FC-05 | FC-06, FC-07, FC-08 |
| `AssembledDocument` | FC-06 | FC-07, FC-08 |
| `BuildArtifact` | FC-06 to FC-09 | FC-10 |

---

## 7. Recommended Development Order

### Phase 1 — Kernel and Contracts

Objective: stabilize the vocabulary and typed interfaces.

Implement:

1. `model` dataclasses: `Diagnostic`, `SourceFile`, `DocumentIndex`,
   `MarkdownAst`, `Heading`, `Reference`, `AssetRef`, `Document`, `Project`.
2. service protocols: `FileSystem`, `MarkdownParser`, `HtmlRenderer`,
   `PdfRenderer`, `DiagramRenderer`.
3. result types: `LintResult`, `BuildResult`, `BuildArtifact`.
4. diagnostic formatting helpers.

Exit criteria:

- data types are frozen and typed;
- mypy strict passes;
- tests cover construction and basic invariants.

Rationale: all chains need shared contracts before implementation can proceed
without churn.

### Phase 2 — Project Context Chain

Objective: make Scribpy able to understand a documentation project.

Implement:

1. FC-01 Load Project Context.
2. FC-02 Discover and Index Sources.
3. CLI command `scribpy index check`.

Exit criteria:

- `scribpy.toml` loads;
- source files are discovered deterministically;
- invalid paths produce diagnostics.

Rationale: this provides the first useful operational capability and enables
all downstream chains.

### Phase 3 — Parse and Semantic Extraction

Objective: convert Markdown sources into typed documents.

Implement:

1. FC-03 Parse and Extract Document Semantics.
2. default Markdown parser adapter.
3. heading, link, and image extraction.
4. `core.load_markdown`, `core.get_headings`, `core.get_links`.

Exit criteria:

- representative Markdown fixtures parse into `Document`;
- frontmatter, headings, links, and assets are tested.

Rationale: lint and transforms should be built on extracted semantics, not raw
text scanning.

### Phase 4 — Lint-First User Value

Objective: give users meaningful checks before build generation exists.

Implement:

1. FC-04 Lint Documentation Quality.
2. `LINT001`, `LINT002`, `LINT003`, `LINT004`.
3. `ExtensionRegistry` for lint rules.
4. CLI command `scribpy lint`.

Exit criteria:

- lint reports stable diagnostic codes;
- exit code reflects configured failure policy;
- broken links and images are caught.

Rationale: linting validates the semantic model and gives immediate Docs-as-Code
value.

### Phase 5 — First Build Artifact: Markdown

Objective: deliver a complete build chain with the simplest output.

Implement:

1. minimal transform protocol.
2. FC-06 Assemble Markdown Document.
3. `scribpy build markdown`.
4. `core.merge_documents`, `core.build_project` for Markdown target.

Exit criteria:

- ordered Markdown files produce one deterministic artifact;
- build fails on lint errors when configured;
- artifact paths are reported.

Rationale: assembled Markdown is the lowest-risk build target and validates
scan, parse, lint, and assemble together.

### Phase 6 — Transform Pipeline

Objective: add document engineering behavior.

Implement:

1. table of contents generation;
2. section numbering;
3. internal reference resolution;
4. target link rewriting;
5. transform registry.

Exit criteria:

- transforms are ordered and configurable;
- transforms return new values;
- output is deterministic and tested.

Rationale: transforms should evolve after the first artifact exists, so each
new transform has visible output.

### Phase 7 — HTML Builder and Assets

Objective: produce browsable documentation.

Implement:

1. FC-07 Build HTML Output.
2. theme loading and default template.
3. CSS resolution.
4. asset validation and static copy from FC-09.
5. `scribpy build html`.

Exit criteria:

- a documentation project builds to `build/html/index.html`;
- linked images are copied and paths are rewritten.

Rationale: HTML introduces templates and assets, so it should follow the stable
Markdown chain.

### Phase 8 — PDF Builder

Objective: produce final distributable documents.

Implement:

1. FC-08 Build PDF Output.
2. PDF renderer protocol and one adapter.
3. printable theme/CSS.
4. `scribpy build pdf`.

Exit criteria:

- missing optional renderer dependencies produce actionable diagnostics;
- PDF output is reproducible in CI.

Rationale: PDF has the heaviest external dependency surface and should not
block earlier capabilities.

### Phase 9 — Extension and Plugin Hardening

Objective: make Scribpy open for extension while protecting core behavior.

Implement:

1. extension loading from config;
2. registration of custom lint rules, transforms, builders, renderers;
3. error isolation around third-party callables.

Exit criteria:

- plugin failures are reported cleanly;
- built-in behavior remains deterministic;
- extension contracts are documented.

Rationale: extension points should stabilize after built-in behavior proves the
contracts.

---

## 8. Suggested Release Slices

| Release | Functional scope |
|---------|------------------|
| `0.0.1b` | package, CLI placeholder, utility baseline |
| `0.0.2b` | model contracts, config loading, project scanning |
| `0.0.3b` | Markdown parsing and semantic extraction |
| `0.0.4b` | lint chain and `scribpy lint` |
| `0.0.5b` | assembled Markdown builder |
| `0.0.6b` | TOC, numbering, link transforms |
| `0.0.7b` | HTML builder and static assets |
| `0.0.8b` | PDF builder |
| `0.1.0` | stabilized public API and CLI for core workflows |

---

## 9. Traceability Matrix

| SDD package | Functional chains |
|-------------|-------------------|
| `cli` | FC-01, FC-04, FC-06, FC-07, FC-08, FC-10 |
| `core` | FC-03, FC-04, FC-06, FC-10 |
| `config` | FC-01 |
| `project` | FC-01, FC-02, FC-06 |
| `model` | all chains |
| `parser` | FC-03, FC-09 |
| `lint` | FC-04, FC-09 |
| `transforms` | FC-05 |
| `builders` | FC-06, FC-07, FC-08 |
| `themes` | FC-07, FC-08 |
| `assets` | FC-05, FC-07, FC-08, FC-09 |
| `extensions` | FC-04, FC-05, FC-09 |
| `utils` | all chains as support functions |

---

## 10. Development Guidance

Develop by vertical chains, not by filling empty package directories in
isolation. A useful implementation slice should connect at least:

```text
CLI/API -> application function -> model/service contract -> tests
```

Preferred implementation rhythm:

1. define or refine data contracts;
2. implement one chain with minimal behavior;
3. expose it through CLI and `core`;
4. add fixtures and diagnostics tests;
5. only then generalize through registries or adapters.

This keeps the project aligned with functional architecture: every package
exists because it participates in an observable system behavior.

---

## 11. References

- `doc/SDD.md`, Scribpy Software Design Document.
- INCOSE, Systems Engineering Handbook, Version 5 overview.
- INCOSE, Systems Engineering definition and systems thinking overview.
- ISO/IEC/IEEE 15288 life cycle process framing, as referenced by the INCOSE
  Systems Engineering Handbook overview.
