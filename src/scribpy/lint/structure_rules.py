"""Native lint rules for document heading structure."""

from __future__ import annotations

from scribpy.lint.context import LintContext
from scribpy.model import Diagnostic


class MissingH1Rule:
    """Require every document to contain at least one H1."""

    code = "LINT001"

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return one diagnostic for each document without an H1."""
        return tuple(
            Diagnostic(
                severity="error",
                code=self.code,
                message="Document is missing a level-1 heading.",
                path=document.relative_path,
                hint="Add one top-level '# Heading' to the document.",
            )
            for document in context.documents
            if not any(heading.level == 1 for heading in document.headings)
        )


class HeadingHierarchyRule:
    """Reject heading jumps larger than one level."""

    code = "LINT002"

    def run(self, context: LintContext) -> tuple[Diagnostic, ...]:
        """Return diagnostics for heading-level jumps larger than one."""
        diagnostics: list[Diagnostic] = []
        for document in context.documents:
            previous_level = 0
            for heading in document.headings:
                if heading.level > previous_level + 1:
                    diagnostics.append(
                        Diagnostic(
                            severity="error",
                            code=self.code,
                            message="Heading hierarchy jumps more than one level.",
                            path=document.relative_path,
                            line=heading.line,
                            hint="Increase heading depth one level at a time.",
                        )
                    )
                previous_level = heading.level
        return tuple(diagnostics)


__all__ = ["HeadingHierarchyRule", "MissingH1Rule"]
