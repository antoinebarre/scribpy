"""Extension registry for lint rules."""

from __future__ import annotations

from dataclasses import dataclass

from scribpy.lint import LintRule, native_lint_rules


@dataclass(frozen=True)
class ExtensionRegistry:
    """Registered extensions available to the current execution."""

    lint_rules: tuple[LintRule, ...] = ()

    def with_lint_rule(self, rule: LintRule) -> ExtensionRegistry:
        """Return a new registry with one additional lint rule."""
        return ExtensionRegistry(lint_rules=(*self.lint_rules, rule))

    @classmethod
    def native(cls) -> ExtensionRegistry:
        """Return a registry preloaded with built-in lint rules."""
        return cls(lint_rules=native_lint_rules())


__all__ = ["ExtensionRegistry"]
