# Functional pipelines

Scribpy is easier to use when you know which stages each command runs. The CLI
reports these same large stages during execution.

## Shared project preparation pipeline

```mermaid
flowchart LR
    A[Start path] --> B[Resolve scribpy.toml]
    B --> C[Load and validate config]
    C --> D[Discover Markdown sources]
    D --> E[Build document index]
    E --> F[Parse documents]
```

This shared pipeline is used by `parse check`, `lint`, and all build commands.
It accumulates diagnostics from configuration, project discovery, indexing, and
parsing.

## `index check`

```mermaid
flowchart LR
    A[Resolve config] --> B[Load config]
    B --> C[Discover sources]
    C --> D[Build and validate index]
```

`index check` intentionally stops before parsing Markdown content. It is the
fastest way to validate project layout and index configuration.

## `parse check`

```mermaid
flowchart LR
    A[Shared project preparation] --> B[Order source files]
    B --> C[Parse Markdown]
    C --> D[Extract frontmatter, headings, links, assets]
```

## `lint`

```mermaid
flowchart LR
    A[Shared project preparation] --> B[Build lint context]
    B --> C[Run lint rules]
    C --> D[Return diagnostics]
```

## `build markdown`

```mermaid
flowchart LR
    A[Shared project preparation] --> B[Run lint rules]
    B --> C[Apply Markdown transforms]
    C --> D[Merge documents]
    D --> E[Write document.md]
```

## `build html --mode single-page`

```mermaid
flowchart LR
    A[Shared project preparation] --> B[Run lint rules]
    B --> C[Apply transforms]
    C --> D[Copy CSS]
    D --> E[Rewrite asset links]
    E --> F[Render HTML]
    F --> G[Write support files]
    G --> H[Copy assets]
```

## `build html --mode site`

```mermaid
flowchart LR
    A[Shared project preparation] --> B[Run lint rules]
    B --> C[Apply HTML transforms]
    C --> D[Write MkDocs scaffold]
    D --> E[Copy assets]
    E --> F[Run MkDocs build]
```
