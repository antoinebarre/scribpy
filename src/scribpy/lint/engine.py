"""Lint rule execution."""

from __future__ import annotations

from collections.abc import Iterable

from scribpy.lint.context import LintContext
from scribpy.lint.rules import LintRule
from scribpy.model import Diagnostic, LintResult
from scribpy.utils import has_errors


def run_lint_rules(
    context: LintContext,
    rules: Iterable[LintRule],
) -> LintResult:
    """Run lint rules in caller-provided order and aggregate diagnostics."""
    diagnostics: list[Diagnostic] = []
    for rule in rules:
        diagnostics.extend(rule.run(context))
    items = tuple(diagnostics)
    return LintResult(diagnostics=items, failed=has_errors(items))


__all__ = ["run_lint_rules"]
