#!/usr/bin/env python3
"""Read-only Python 3.9+ AST checks for explicit files or directories.

Print a JSON array of {file, line, code, message}. Exit 0 means clean, 1 means
structural findings, and 2 means invalid input or an incomplete source check.
This checks recognizable syntax, not semantic architecture or lifecycle design.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
import tokenize
from typing import Optional


DATACLASSES = {
    "dataclasses.dataclass", "pydantic.dataclasses.dataclass",
    "pydantic.v1.dataclasses.dataclass",
}
MODEL_FACTORIES = {
    "{}.{}".format(module, name)
    for module, names in (
        ("enum", ("Enum", "IntEnum", "StrEnum", "Flag", "IntFlag")),
        ("typing", ("NamedTuple", "TypedDict")),
        ("typing_extensions", ("NamedTuple", "TypedDict")),
        ("collections", ("namedtuple",)),
    )
    for name in names
}
MODEL_BASES = MODEL_FACTORIES | {
    "pydantic.BaseModel", "pydantic.RootModel", "pydantic.BaseSettings", "pydantic.v1.BaseModel",
    "pydantic.v1.BaseSettings", "pydantic_settings.BaseSettings", "@model",
}
SQL_FACTORIES = {"create_engine", "create_async_engine", "sessionmaker", "async_sessionmaker", "Session", "AsyncSession"}


def finding(file: str, line: int, code: str, message: str) -> dict:
    return {"file": file, "line": line, "code": code, "message": message}


class StructureVisitor(ast.NodeVisitor):
    """Resolve local import aliases without importing or executing source."""

    def __init__(self, path: Path):
        self.file = path.as_posix()
        self.symbols: dict[str, str] = {}
        self.findings: list[dict] = []
        self.check_models = "models" not in path.parent.parts and not (
            "tests" in path.parent.parts or path.name.startswith("test_") or path.name == "tests.py"
        )
        self.check_dependencies = "dependencies" not in path.parent.parts and (
            "routers" in path.parent.parts
            or path.name in {"app.py", "main.py", "router.py", "routers.py"}
        )

    def report(self, node: ast.AST, code: str, message: str) -> None:
        self.findings.append(finding(self.file, node.lineno, code, message))

    def qualified(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return self.symbols.get(node.id, "")
        if isinstance(node, ast.Attribute):
            owner = self.qualified(node.value)
            return owner + "." + node.attr if owner else ""
        if isinstance(node, ast.Subscript):
            return self.qualified(node.value)
        return ""

    def bind(self, node: ast.AST, value: str = "") -> None:
        if isinstance(node, ast.Name):
            self.symbols[node.id] = value
        elif isinstance(node, (ast.Tuple, ast.List)):
            for item in node.elts:
                self.bind(item)

    def model(self, node: ast.AST, name: str) -> None:
        if self.check_models:
            self.report(node, "STRUCT003", "Move model '{}' into a models/ directory.".format(name))

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            name = alias.asname or alias.name.split(".")[0]
            self.symbols[name] = alias.name if alias.asname else name

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.report(node, "STRUCT001", "Replace wildcard import with explicit imports.")
            else:
                module = node.module or ""
                self.symbols[alias.asname or alias.name] = (
                    module + "." + alias.name if not node.level and module
                    else "@relative." + module + "." + alias.name
                )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_model = any(self.qualified(base) in MODEL_BASES for base in node.bases)
        for decorator in node.decorator_list:
            target = decorator.func if isinstance(decorator, ast.Call) else decorator
            is_model = is_model or self.qualified(target) in DATACLASSES
        if is_model:
            self.model(node, node.name)
        for expression in [*node.bases, *node.decorator_list, *node.keywords]:
            self.visit(expression)
        self.symbols[node.name] = "@model" if is_model else ""
        self.scoped_body(node.body)

    def scoped_body(self, body: list[ast.AST], shadows: tuple[str, ...] = ()) -> None:
        previous = self.symbols
        self.symbols = dict(previous)
        self.symbols.update((name, "") for name in shadows)
        for statement in body:
            self.visit(statement)
        self.symbols = previous

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for expression in [*node.decorator_list, node.args, node.returns]:
            if expression is not None:
                self.visit(expression)
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        arguments.extend(arg for arg in (node.args.vararg, node.args.kwarg) if arg)
        self.symbols[node.name] = ""
        self.scoped_body(node.body, tuple(arg.arg for arg in arguments))

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        self.visit(node.args)
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        arguments.extend(arg for arg in (node.args.vararg, node.args.kwarg) if arg)
        self.scoped_body([node.body], tuple(arg.arg for arg in arguments))

    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self.bind(node.target)
        for statement in [*node.body, *node.orelse]:
            self.visit(statement)

    visit_AsyncFor = visit_For

    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self.bind(item.optional_vars)
        for statement in node.body:
            self.visit(statement)

    visit_AsyncWith = visit_With

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is not None:
            self.visit(node.type)
        if node.name:
            self.symbols[node.name] = ""
        for statement in node.body:
            self.visit(statement)

    def visit_ListComp(self, node: ast.ListComp) -> None:
        previous = self.symbols
        self.symbols = dict(previous)
        for generator in node.generators:
            self.visit(generator.iter)
            self.bind(generator.target)
            for condition in generator.ifs:
                self.visit(condition)
        expressions = [node.key, node.value] if isinstance(node, ast.DictComp) else [node.elt]
        for expression in expressions:
            self.visit(expression)
        self.symbols = previous

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        is_model = isinstance(node.value, ast.Call) and self.qualified(node.value.func) in MODEL_FACTORIES
        for target in node.targets:
            if is_model and isinstance(target, ast.Name):
                self.model(node, target.id)
            self.bind(target, "@model" if is_model else "")

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value is not None:
            self.visit_Assign(ast.copy_location(ast.Assign(targets=[node.target], value=node.value), node))

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.visit(node.value)
        self.bind(node.target)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.generic_visit(node)
        self.bind(node.target)

    def visit_Call(self, node: ast.Call) -> None:
        name = self.qualified(node.func)
        leaf = name.rsplit(".", 1)[-1]
        constructor = bool(leaf) and leaf[0].isupper() and leaf.endswith(("Service", "Repository", "Client"))
        sql_factory = name.startswith("sqlalchemy.") and leaf in SQL_FACTORIES
        if self.check_dependencies and (constructor or sql_factory):
            self.report(node, "STRUCT004", "Move construction of '{}' into a dependencies/ concern module.".format(leaf))
        self.generic_visit(node)


def check_file(path: Path, relative: Path) -> list[dict]:
    """Read a source file using its declared encoding and inspect its AST."""
    file = relative.as_posix()
    try:
        with tokenize.open(path) as source:
            text = source.read()
    except (OSError, UnicodeError, SyntaxError) as error:
        return [finding(file, 0, "READ_ERROR", str(error))]
    try:
        tree = ast.parse(text, filename=file)
    except RecursionError:
        return [finding(file, 0, "CHECK_ERROR", "AST nesting exceeds the parser's recursion limit; source check incomplete.")]
    except (SyntaxError, ValueError) as error:
        return [finding(file, getattr(error, "lineno", 0) or 0, "SYNTAX_ERROR", str(error))]
    visitor = StructureVisitor(relative)
    if path.name == "__init__.py":
        body = tree.body
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        for statement in body:
            visitor.report(statement, "STRUCT002", "Keep __init__.py limited to a module docstring and comments.")
    try:
        visitor.visit(tree)
    except RecursionError:
        visitor.findings.append(finding(file, 0, "CHECK_ERROR", "AST nesting exceeds the checker's recursion limit; source check incomplete."))
    return visitor.findings


def display(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)


def validate_path(path: Path, root: Path, findings: list[dict]) -> Optional[Path]:
    """Reject escapes and directory symlinks before source enumeration or reads."""
    file = display(path, root)
    try:
        if not path.is_relative_to(root) or not path.resolve(strict=True).is_relative_to(root):
            findings.append(finding(file, 0, "OUTSIDE_ROOT", "Path must stay within --repo-root."))
            return None
        for parent in (path, *path.parents):
            if parent == root:
                break
            if parent.is_symlink() and parent.is_dir():
                findings.append(finding(file, 0, "INPUT_ERROR", "Directory symlinks are not traversed."))
                return None
        return path
    except (OSError, RuntimeError, ValueError) as error:
        findings.append(finding(file, 0, "INPUT_ERROR", str(error)))
        return None


def collect_files(root: Path, targets: list[str], findings: list[dict]) -> list[Path]:
    files: dict[Path, Path] = {}

    def add_file(path: Path) -> None:
        if validate_path(path, root, findings) is not None:
            if path.is_file() and path.suffix == ".py":
                resolved = path.resolve()
                files.setdefault(resolved, resolved)
            else:
                findings.append(finding(display(path, root), 0, "INPUT_ERROR", "Expected a Python file or directory."))

    def walk_error(error: OSError) -> None:
        findings.append(finding(str(error.filename), 0, "READ_ERROR", str(error)))

    for target in targets:
        path = Path(os.path.abspath(root / target))
        if validate_path(path, root, findings) is None:
            continue
        if not path.is_dir():
            add_file(path)
            continue
        for current, directories, names in os.walk(path, followlinks=False, onerror=walk_error):
            directory = Path(current)
            for name in list(directories):
                child = directory / name
                if child.is_symlink():
                    validate_path(child, root, findings)
                    directories.remove(name)
            directories.sort()
            for name in sorted(names):
                if name.endswith(".py"):
                    add_file(directory / name)
    return sorted(files.values())


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValueError(message)


def main(argv: Optional[list[str]] = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Source boundary; relative targets start here.")
    parser.add_argument("paths", nargs="+", help="Explicit Python files or directories to inspect.")
    findings: list[dict] = []
    try:
        arguments = parser.parse_args(argv)
        root = Path(arguments.repo_root).resolve(strict=True)
        if not root.is_dir():
            raise ValueError("--repo-root must name an existing directory.")
    except (OSError, RuntimeError, ValueError) as error:
        findings.append(finding("", 0, "INPUT_ERROR", str(error)))
    else:
        for path in collect_files(root, arguments.paths, findings):
            findings.extend(check_file(path, path.relative_to(root)))
    findings.sort(key=lambda item: (item["file"], item["line"], item["code"], item["message"]))
    print(json.dumps(findings, indent=2))
    if any(not item["code"].startswith("STRUCT") for item in findings):
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
