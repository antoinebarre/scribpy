"""Lint rule contracts, registry, and native rule assembly."""

from __future__ import annotations

from typing import Protocol

from scribpy.lint.asset_rules import MissingLocalAssetRule
from scribpy.lint.context import LintContext
from scribpy.lint.reference_rules import BrokenInternalLinkRule
from scribpy.lint.structure_rules import HeadingHierarchyRule, MissingH1Rule
from scribpy.model import Diagnostic


class LintRule(Protocol):
    """Contract implemented by all lint rules.

    Attributes:
        code: Stable diagnostic code emitted by the rule.
    """

    code: str

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics emitted by this rule.

        Args:
            context: Shared lint inputs for the current project.

        Returns:
            Diagnostics emitted by the rule.
        """


class LintRuleRegistry:
    """Open registry of lint rules — register without modifying this module.

    Usage::

        registry = LintRuleRegistry()
        registry.register(MyCustomRule())

        # Or use the decorator form:
        @registry.register
        class MyRule:
            code = "CUSTOM001"
            def run(self, context): ...
    """

    def __init__(self) -> None:
        """Initialise an empty rule registry."""
        self._rules: list[LintRule] = []

    def register(self, rule: LintRule) -> LintRule:
        """Register a rule instance and return it (usable as a decorator).

        Args:
            rule: Lint rule instance to register.

        Returns:
            The same rule instance (allows decorator usage).
        """
        self._rules.append(rule)
        return rule

    def rules(self) -> tuple[LintRule, ...]:
        """Return registered rules in insertion order.

        Returns:
            Registered lint rules as an immutable tuple.
        """
        return tuple(self._rules)


# ---------------------------------------------------------------------------
# Built-in registry — populated below; extend via ExtensionRegistry instead
# of mutating this module-level instance.
# ---------------------------------------------------------------------------

_native_registry = LintRuleRegistry()
_native_registry.register(MissingH1Rule())
_native_registry.register(HeadingHierarchyRule())
_native_registry.register(BrokenInternalLinkRule())
_native_registry.register(MissingLocalAssetRule())


def native_lint_rules() -> tuple[LintRule, ...]:
    """Return the built-in lint rules in deterministic execution order.

    Returns:
        Built-in lint rules in deterministic execution order.
    """
    return _native_registry.rules()


__all__ = [
    "BrokenInternalLinkRule",
    "HeadingHierarchyRule",
    "LintRule",
    "LintRuleRegistry",
    "MissingH1Rule",
    "MissingLocalAssetRule",
    "native_lint_rules",
]
