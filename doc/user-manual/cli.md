# CLI

## Main commands

```bash
scribpy demo create TARGET
scribpy index check --root PROJECT
scribpy parse check --root PROJECT
scribpy lint --root PROJECT
scribpy build markdown --root PROJECT
scribpy build html --mode single-page --root PROJECT
scribpy build html --mode site --root PROJECT
```

## Output control

```bash
scribpy build markdown --root docs --output-dir /tmp/markdown-artifacts
scribpy build html --mode site --root docs --output-dir build/pipeline-site
```

`--output-dir` is available on both build commands. Relative paths are resolved
from the project root; absolute paths are used directly.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | command completed successfully |
| `1` | blocking user-facing diagnostics were reported |
| `2` | invalid CLI usage |

## Diagnostics and logs

Normal command output is intentionally terse. Diagnostics are written to stderr
with a stable code and a remediation hint when available.

```bash
scribpy --log-level INFO build html --mode site --root docs
scribpy --log-level DEBUG --log-console --log-file logs/run.log lint --root docs
```

Use logs for execution traces; use diagnostics for actionable user-facing
problems.
