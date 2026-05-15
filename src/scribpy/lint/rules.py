"""Lint rule contracts and native rule assembly."""

from __future__ import annotations

from typing import Protocol

from scribpy.lint.asset_rules import MissingLocalAssetRule
from scribpy.lint.context import LintContext
from scribpy.lint.reference_rules import BrokenInternalLinkRule
from scribpy.lint.structure_rules import HeadingHierarchyRule, MissingH1Rule
from scribpy.model import Diagnostic


class LintRule(Protocol):
    """Contract implemented by all lint rules."""

    code: str

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics emitted by this rule."""


def native_lint_rules() -> tuple[LintRule, ...]:
    """Return the built-in lint rules in deterministic execution order."""
    return (
        MissingH1Rule(),
        HeadingHierarchyRule(),
        BrokenInternalLinkRule(),
        MissingLocalAssetRule(),
    )


__all__ = [
    "BrokenInternalLinkRule",
    "HeadingHierarchyRule",
    "LintRule",
    "MissingH1Rule",
    "MissingLocalAssetRule",
    "native_lint_rules",
]
