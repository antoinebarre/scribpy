# Folder manifests and order

A non-root `scribpy.yml` has a deliberately smaller contract than the root:
only `title` and `order` are meaningful. It cannot set `project` metadata or
`build` settings — those are root-only concerns, described in [Root
manifest](root-manifest.md). Any other key present in a folder manifest is
ignored with `ScribpyManifestWarning`.

## Example

```text
handbook/
├── scribpy.yml
└── guide/
    ├── advanced.md
    ├── installation.md
    ├── scribpy.yml
    └── workflow.md
```

```yaml title="handbook/guide/scribpy.yml"
title: User guide
order:
  - installation.md
  - workflow.md
  - advanced.md
```

`title` becomes the intermediate folder heading in the assembled document and
the navigation group label in MkDocs export. Without `title`, Scribpy derives a
readable label from the directory name.

`order` controls only `guide/` direct children. The root manifest still needs
to list `guide/` among its own direct children.

## `title` and `order` in detail

| Key | Type | Default | Scope |
|---|---|---|---|
| `title` | string or absent | folder name | Display heading for this folder only, in the assembled document and MkDocs navigation. |
| `order` | list of strings or absent | alphabetical traversal | Direct children of *this* folder only — never grandchildren. |

Each entry in `order` must name exactly one direct child: a bare filename
(`installation.md`) or directory name with or without a trailing slash
(`reference` or `reference/`). Compound paths, `.`, and `..` are rejected as
invalid manifest entries.

## Each manifest controls only its direct children

This is the single rule that keeps manifests small and composable: a
`scribpy.yml` never reaches past its own folder. To make a nested page appear
in the collection, *every* manifest between the root and that page must list
the next step down.

## Nested directories

For another level:

```text
guide/
├── reference/
│   ├── api.md
│   ├── configuration.md
│   └── scribpy.yml
└── scribpy.yml
```

The parent lists only the directory:

```yaml title="guide/scribpy.yml"
title: User guide
order:
  - reference/
```

The nested manifest owns its pages:

```yaml title="guide/reference/scribpy.yml"
title: Reference
order:
  - configuration.md
  - api.md
```

Do not flatten this into `reference/configuration.md` in the parent order.
Every entry must name one direct child—never a compound path, `.`, or `..`.

## Worked multi-level example

Extending the tree one level further shows the rule holding at every depth:

```text
handbook/
├── scribpy.yml            # root: order = [index.md, guide/]
├── index.md
└── guide/
    ├── scribpy.yml        # order = [installation.md, reference/]
    ├── installation.md
    └── reference/
        ├── scribpy.yml    # order = [api/, configuration.md]
        ├── configuration.md
        └── api/
            ├── scribpy.yml    # order = [overview.md, endpoints.md]
            ├── overview.md
            └── endpoints.md
```

For `guide/reference/api/endpoints.md` to appear in the assembled document,
every manifest on the path down must name the next segment:

1. `handbook/scribpy.yml` must list `guide/`;
2. `handbook/guide/scribpy.yml` must list `reference/`;
3. `handbook/guide/reference/scribpy.yml` must list `api/`;
4. `handbook/guide/reference/api/scribpy.yml` must list `endpoints.md`.

Leaving out any single one of those four entries removes the whole subtree
below it from the build — a missing `guide/` entry in the root manifest hides
`installation.md`, `reference/`, and everything reference contains, even
though their own manifests are perfectly valid. There is no way to "reach
past" an intermediate manifest.

Each folder's assembled heading level also compounds with this depth: a page
inside `guide/reference/api/` sits three folders below the root, so its
source H1 is shifted further than a root-level page. See [Markdown source
files](markdown-sources.md) for the exact shift table.

## Missing and unlisted children

If `order` lists `missing.md`, loading raises
`InvalidScribpyManifestError`. If `advanced.md` exists but is absent from a
non-empty order, Scribpy emits `ScribpyManifestWarning` and excludes it from
the collection and exported navigation.

This exclusion is intentional, but it can surprise authors. After adding or
moving a page:

1. update the manifest in that page's immediate parent directory;
2. update any relative links affected by the move;
3. run `scribpy validate PROJECT`;
4. inspect manifest warnings before publishing.

When no folder manifest exists—or its order is empty—supported children are
visited alphabetically.

## Titles without a manifest

A folder can be included in the collection (via its parent's `order`, or by
alphabetical traversal) without carrying its own `scribpy.yml`. In that case
its display title falls back to the directory name exactly as written on
disk — `api-reference` stays `api-reference` rather than being reformatted.
Add a folder manifest with just a `title` key when the directory name is not
a good heading:

```yaml title="api-reference/scribpy.yml"
title: API reference
```

This manifest carries no `order`, so its children still fall back to
alphabetical traversal — `title` and `order` can be set independently.
