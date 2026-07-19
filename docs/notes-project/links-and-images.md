# Links and images

Links and images are resolved from the file that contains the Markdown
reference. This is the most important path rule in a Scribpy project.

## Link to another source page

Given this layout:

```text
handbook/
├── index.md
└── guide/
    ├── installation.md
    └── workflow.md
```

`index.md` links down into the folder:

```markdown
[Install the project](guide/installation.md)
```

`guide/workflow.md` links to a sibling and back to the root:

```markdown
[Installation](installation.md)
[Welcome](../index.md)
```

Targets must exist, remain inside the collection root, and end with a
recognized Markdown suffix. During single-document assembly Scribpy replaces
the file target with the generated anchor for the target page's H1. During
`mkdocs-export`, the file link remains a file link.

## Step by step: how a link is rewritten

Assembly runs the link rewriter (`scribpy.core.assembly.link_rewriter`) after
optional heading numbering and before the TOC and diagrams. Given source
`installation.md` whose first H1 is `# Setup`, and a page linking to it with:

```markdown
[Setup](setup.md)
```

1. Scribpy builds a filename → slug map for every source file that has an H1,
   using the same GitHub-style slug algorithm as anchors (lowercase, strip
   inline markers, replace non-word characters, collapse whitespace to
   hyphens). `Setup` slugifies to `setup`.
2. Every `[label](target.md)` pattern in the assembled content (a link, not an
   image — `![...]` is excluded) is scanned. If the target's bare filename
   (the part after the last `/`) is in the map, the whole `(target.md)` is
   replaced by `(#slug)`.
3. `[Setup](setup.md)` becomes `[Setup](#setup)`.

Links whose target filename is absent from the map (for example, a file with
no H1) are left untouched rather than rewritten to a broken anchor.

### The numbered-heading variant

When `build.heading_numbering.enabled` is true, heading numbering runs
*first*. If MkForge renders the `Setup` heading as `1.2 Setup` in the
assembled document, the rewriter instead builds its slug map from the final
numbered heading text, so the same link becomes:

```markdown
[Setup](#12-setup)
```

matching the exact anchor MkDocs Material (or GitHub) generates for that
numbered heading. This is why link rewriting must run after numbering: it has
to point at the anchor that actually exists in the output, not the
unnumbered source title.

## Do not write source anchors

Both forms below are invalid:

```markdown
[Local section](#steps)
[Remote section](installation.md#steps)
```

`LocalAnchorLinkRule` rejects every link target containing `#`. Page headings
are shifted and may be numbered during assembly, so Scribpy owns final anchor
generation. Link to the page, then let the output navigation expose its
sections.

This is deliberate, not a missing feature: a source-written anchor like
`#steps` would need to guess the exact slug the assembled document ends up
with — which depends on folder depth (heading shift), the numbering setting,
and MkDocs Material's own slug rules. Any of those changing later would
silently break the link. Writing `[Remote section](installation.md)` and
letting the pipeline compute `#steps`, `#12-steps`, or whatever the final
anchor is keeps the link correct across those changes.

## Add a local image

For an image stored beside a page:

```text
guide/
├── images/
│   └── terminal.png
└── installation.md
```

write:

```markdown
![Successful installation](images/terminal.png)
```

For a shared image under the project root, a nested page walks upward:

```markdown
![Project logo](../assets/logo.png "Project logo")
```

The optional quoted text is the Markdown image title. Always provide useful
alt text for accessibility.

## What happens during export

For `scribpy build handbook build/handbook.md`, Scribpy:

1. resolves each local target against its source page;
2. verifies that the target exists and stays inside `handbook/`;
3. copies it under `build/assets/`;
4. rewrites the assembled Markdown reference to the copied asset.

`mkdocs-export` performs equivalent collection while keeping separate pages
and calculating a path relative to each exported page. Images with the same
filename from different source directories do not overwrite each other.

Do not edit rewritten paths in generated output; edit the source reference and
export again.

## Image handling rules

Every image reference is classified as local (inside the project, resolving
to a real file), local-but-missing, local-but-escaping-the-root, or external
(a URL). Each case has one diagnostic rule, run independently so a new check
can be added without touching the others:

| Source target | Diagnostic rule | Code | Severity | Build behavior |
|---|---|---|---|---|
| `images/terminal.png` (exists, inside root) | — | — | — | Copied to `assets/` (or export-relative path) and rewritten. |
| `images/missing.png` (does not exist) | `LocalImageMissingRule` | `LOCAL_IMAGE_MISSING` | ERROR | Assembly is blocked. |
| `../../private/logo.png` (exists but outside root) | `ImageOutsideRootRule` | `IMAGE_OUTSIDE_ROOT` | ERROR | Assembly is blocked, even though the file exists. |
| `https://example.com/logo.png` | `ExternalImageReferenceRule` | `EXTERNAL_IMAGE_REFERENCE` | WARNING | URL remains external; Scribpy does not fetch or copy it. |

External images make output depend on network availability and the remote
owner. Prefer checked-in local images for reproducible publication.

## Diagram images

Fenced `plantuml` and `mermaid` blocks are different from ordinary images.
Scribpy sends them to the selected renderer and writes PNG files under
`assets/generated/`, named from a SHA-256 digest of the diagram source.
Identical diagram blocks can reuse the same generated file.

The default PlantUML backend uses PlantUML Server and the default Mermaid
backend uses Kroki, so diagram builds require network access. Mermaid CLI can
render locally when `mmdc` is installed. The PlantUML `local` backend is only a
placeholder and always raises `NotImplementedError`. See [Diagram
sources](diagrams.md) for full backend configuration and worked examples.
