"""Markdown and documentation quality engine.

A lint rule is a plain callable:
    LintRule = Callable[[LintContext], Sequence[Diagnostic]]

Built-in checks include:
    check_missing_h1          — document must have an H1
    check_heading_hierarchy   — headings must not skip levels
    check_broken_links        — internal links must resolve
    check_broken_images       — image paths must exist
    check_duplicate_anchors   — anchors must be unique per document
    check_missing_frontmatter — frontmatter presence
    check_invalid_structure   — document structure validity

Main functions:
    run_lint_rules(context, rules)           -> list[Diagnostic]
    select_lint_rules(config, registry)      -> tuple[LintRule, ...]
    lint_project(project, documents, registry) -> LintResult
    should_fail_build(diagnostics, config)   -> bool
"""
