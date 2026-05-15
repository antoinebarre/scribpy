"""Enforce facade-only package ``__init__.py`` modules."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

_SOURCE_ROOT = Path("src")


@dataclass(frozen=True)
class InitModuleViolation:
    """One forbidden top-level statement inside an ``__init__.py`` file.

    Attributes:
        path: Path to the offending initializer module.
        line: One-based line number of the statement.
        kind: AST node kind of the statement.
        detail: Human-readable statement detail.
    """

    path: Path
    line: int
    kind: str
    detail: str


def main() -> int:
    """Check initializer modules and print violations.

    Returns:
        Process exit code where ``0`` means all initializer modules are pure
        facades.
    """
    violations = collect_init_module_violations(_SOURCE_ROOT)
    if not violations:
        print("Initializer module check passed.")
        return 0

    print("Initializer module check failed:\n")
    for violation in violations:
        print(
            f"{violation.path}:{violation.line}: top-level {violation.kind} "
            f"{violation.detail} is not allowed in __init__.py"
        )
    return 1


def collect_init_module_violations(root: Path) -> tuple[InitModuleViolation, ...]:
    """Collect non-facade statements from initializer modules.

    Args:
        root: Source tree to search below.

    Returns:
        Violations sorted by path and line number.
    """
    violations: list[InitModuleViolation] = []
    for path in sorted(root.rglob("__init__.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        violations.extend(_violations_for_module(path, tree))
    return tuple(violations)


def _violations_for_module(
    path: Path,
    tree: ast.Module,
) -> tuple[InitModuleViolation, ...]:
    violations: list[InitModuleViolation] = []
    for index, node in enumerate(tree.body):
        if _is_allowed_statement(node, index=index):
            continue
        violations.append(
            InitModuleViolation(
                path=path,
                line=node.lineno,
                kind=type(node).__name__,
                detail=_describe_statement(node),
            )
        )
    return tuple(violations)


def _is_allowed_statement(node: ast.stmt, *, index: int) -> bool:
    if index == 0 and _is_module_docstring(node):
        return True
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return True
    return _is_all_assignment(node)


def _is_module_docstring(node: ast.stmt) -> bool:
    return (
        isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    )


def _is_all_assignment(node: ast.stmt) -> bool:
    if not isinstance(node, ast.Assign) or len(node.targets) != 1:
        return False
    target = node.targets[0]
    return isinstance(target, ast.Name) and target.id == "__all__"


def _describe_statement(node: ast.stmt) -> str:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return f"'{node.name}'"
    if isinstance(node, ast.Assign):
        return "assignment"
    if isinstance(node, ast.AnnAssign):
        return "annotated assignment"
    return "statement"


if __name__ == "__main__":
    raise SystemExit(main())
