"""Extension registry for lint rules and transforms."""

from __future__ import annotations

from dataclasses import dataclass

from scribpy.lint import LintRule, native_lint_rules
from scribpy.transforms import (
    Transform,
    native_html_transforms,
    native_markdown_transforms,
)


@dataclass(frozen=True)
class ExtensionRegistry:
    """Registered extensions available to the current execution.

    Attributes:
        lint_rules: Lint rules available to the current execution.
        markdown_transforms: Ordered transforms for Markdown output.
        html_transforms: Ordered transforms for HTML output.
    """

    lint_rules: tuple[LintRule, ...] = ()
    markdown_transforms: tuple[Transform, ...] = ()
    html_transforms: tuple[Transform, ...] = ()

    def with_lint_rule(self, rule: LintRule) -> ExtensionRegistry:
        """Return a new registry with one additional lint rule.

        Args:
            rule: Lint rule to append.

        Returns:
            New registry containing the added rule.
        """
        return ExtensionRegistry(
            lint_rules=(*self.lint_rules, rule),
            markdown_transforms=self.markdown_transforms,
            html_transforms=self.html_transforms,
        )

    def with_markdown_transform(self, transform: Transform) -> ExtensionRegistry:
        """Return a new registry with one additional Markdown transform.

        Args:
            transform: Markdown transform to append.

        Returns:
            New registry containing the added transform.
        """
        return ExtensionRegistry(
            lint_rules=self.lint_rules,
            markdown_transforms=(*self.markdown_transforms, transform),
            html_transforms=self.html_transforms,
        )

    @classmethod
    def native(cls) -> ExtensionRegistry:
        """Return a registry preloaded with built-in extensions.

        Returns:
            Registry containing Scribpy's built-in extensions.
        """
        return cls(
            lint_rules=native_lint_rules(),
            markdown_transforms=native_markdown_transforms(),
            html_transforms=native_html_transforms(),
        )


__all__ = ["ExtensionRegistry"]
