"""Tests for the minimal extension registry."""

from scribpy.extensions import ExtensionRegistry
from scribpy.lint import MissingH1Rule


def test_native_registry_loads_built_in_lint_rules() -> None:
    registry = ExtensionRegistry.native()

    assert [rule.code for rule in registry.lint_rules] == [
        "LINT001",
        "LINT002",
        "LINT003",
        "LINT004",
    ]


def test_with_lint_rule_returns_extended_registry() -> None:
    registry = ExtensionRegistry().with_lint_rule(MissingH1Rule())

    assert [rule.code for rule in registry.lint_rules] == ["LINT001"]
