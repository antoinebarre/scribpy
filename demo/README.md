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

## Execution logs

To inspect the execution chain while keeping diagnostics unchanged:

```bash
scribpy --log-level INFO build html --mode site --root demo
```

This writes `demo/build/logs/scribpy.log` by default. You can also choose the
log path and mirror records to the console:

```bash
scribpy --log-level DEBUG --log-console --log-file logs/demo.log lint --root demo
```

The same workflow is available from Python:

```python
import scribpy

with scribpy.logging_context(level="INFO"):
    scribpy.build_html("demo", mode="site")
```
