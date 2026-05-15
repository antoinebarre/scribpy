"""Enforce Scribpy's strict public API docstring contract."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

SOURCE_ROOT = Path("src/scribpy")


@dataclass(frozen=True)
class DocstringIssue:
    """One strict docstring contract violation.

    Attributes:
        path: Source file containing the violation.
        line: One-based line number of the public declaration.
        name: Public declaration name.
        missing_sections: Required Google-style sections that are absent.
    """

    path: Path
    line: int
    name: str
    missing_sections: tuple[str, ...]


def main() -> int:
    """Check public declarations and print strict docstring violations.

    Returns:
        Process exit code. ``0`` means the strict contract is satisfied and
        ``1`` means at least one public declaration is missing required
        Google-style sections.
    """
    issues = collect_issues(SOURCE_ROOT)
    if not issues:
        print("Strict Google docstring check passed.")
        return 0

    print("Strict Google docstring check failed:\n")
    for issue in issues:
        sections = ", ".join(issue.missing_sections)
        print(f"{issue.path}:{issue.line}: {issue.name} missing {sections}")
    return 1


def collect_issues(root: Path) -> tuple[DocstringIssue, ...]:
    """Collect strict docstring violations below a source root.

    Args:
        root: Directory containing Python source files to inspect.

    Returns:
        Public declaration violations sorted by path and line.
    """
    issues: list[DocstringIssue] = []
    for path in sorted(root.rglob("*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"))
        issues.extend(_module_issues(path, module))
    return tuple(issues)


def _module_issues(path: Path, module: ast.Module) -> tuple[DocstringIssue, ...]:
    issues: list[DocstringIssue] = []
    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef) and _is_public(node.name):
            missing = _missing_class_sections(node)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _is_public(
            node.name
        ):
            missing = _missing_function_sections(node)
        else:
            continue

        if missing:
            issues.append(
                DocstringIssue(
                    path=path,
                    line=node.lineno,
                    name=node.name,
                    missing_sections=missing,
                )
            )
    return tuple(issues)


def _missing_function_sections(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, ...]:
    docstring = ast.get_docstring(node) or ""
    missing: list[str] = []
    if _documented_parameters(node) and "Args:" not in docstring:
        missing.append("Args")
    if _returns_value(node) and "Returns:" not in docstring:
        missing.append("Returns")
    return tuple(missing)


def _missing_class_sections(node: ast.ClassDef) -> tuple[str, ...]:
    docstring = ast.get_docstring(node) or ""
    if _annotated_public_fields(node) and "Attributes:" not in docstring:
        return ("Attributes",)
    return ()


def _documented_parameters(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> tuple[str, ...]:
    positional = [
        argument.arg
        for argument in (*node.args.posonlyargs, *node.args.args)
        if argument.arg not in {"self", "cls"}
    ]
    keyword_only = [argument.arg for argument in node.args.kwonlyargs]
    variadic = []
    if node.args.vararg is not None:
        variadic.append(node.args.vararg.arg)
    if node.args.kwarg is not None:
        variadic.append(node.args.kwarg.arg)
    return tuple((*positional, *keyword_only, *variadic))


def _returns_value(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    annotation = node.returns
    return annotation is not None and not (
        isinstance(annotation, ast.Constant) and annotation.value is None
    )


def _annotated_public_fields(node: ast.ClassDef) -> tuple[str, ...]:
    return tuple(
        child.target.id
        for child in node.body
        if isinstance(child, ast.AnnAssign)
        and isinstance(child.target, ast.Name)
        and _is_public(child.target.id)
    )


def _is_public(name: str) -> bool:
    return not name.startswith("_")


if __name__ == "__main__":
    raise SystemExit(main())
