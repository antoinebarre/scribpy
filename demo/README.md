# Scribpy End-to-End Demo

This small checked-in demo shows the same workflow as the generated tutorial
project, with fewer files so it is easy to inspect by hand.

Run these commands from the repository root:

```bash
scribpy index check --root demo
scribpy parse check --root demo
scribpy lint --root demo
scribpy build markdown --root demo
scribpy build html --mode single-page --root demo
scribpy build html --mode site --root demo
```

Outputs to inspect:

```text
demo/build/markdown/document.md
demo/build/html/index.html
demo/build/html/css/demo.css
demo/build/site/mkdocs.yml
demo/build/site/docs/
demo/build/site/site/index.html
```

The two HTML commands serve different publication needs:

- `single-page` builds one portable HTML document and applies `theme/demo.css`.
- `site` prepares the MkDocs inputs and then lets Scribpy wrap `mkdocs build` to
  render the final multi-page static site.

## Next steps

After editing files under `demo/doc/`, re-run the checks and rebuild the outputs:

```bash
scribpy index check --root demo
scribpy parse check --root demo
scribpy lint --root demo
scribpy build markdown --root demo
scribpy build html --mode single-page --root demo
scribpy build html --mode site --root demo
```

The site builder uses the configured MkDocs theme. This demo sets `builders.html.theme = "readthedocs"`; change it to experiment with another theme.
