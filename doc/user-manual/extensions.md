# Extensions

Most users do not need the extension API. The useful public entry point is
`ExtensionRegistry`, which lets advanced callers add rules or transforms for a
single execution without changing Scribpy internals.

```python
from scribpy.extensions import ExtensionRegistry

registry = ExtensionRegistry.native()
registry = registry.with_lint_rule(custom_rule)
registry = registry.with_markdown_transform(custom_transform)
```

## When to use it

- add a project-specific lint rule;
- add a Markdown transform before a custom build;
- compose built-in behavior with one local extension in tests or automation.

## What is intentionally small

The “enabler” methods are immutable helpers:

- `ExtensionRegistry.native()` starts from Scribpy’s built-ins;
- `with_lint_rule()` returns a new registry with one extra rule;
- `with_markdown_transform()` returns a new registry with one extra Markdown
  transform.

They do not mutate the original registry. Keep custom extensions focused and
pass the registry to lower-level core functions only when you need that degree
of control.
