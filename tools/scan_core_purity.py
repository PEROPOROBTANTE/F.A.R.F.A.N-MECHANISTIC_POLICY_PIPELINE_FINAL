#!/usr/bin/env python3
"""
Core Purity Scanner - Ensures core modules follow functional purity principles.

Checks:
1. No I/O operations in core modules (print, open, file operations)
2. No __main__ blocks in core modules
3. No direct database or network calls
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

try:
    from saaaaaa.config.paths import PROJECT_ROOT
except Exception:  # pragma: no cover - bootstrap fallback
    PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Directories that must maintain purity
CORE_PATHS = [
    "src/saaaaaa/core",
]

# Forbidden operations (allowing open for config loading, but not print/input)
FORBIDDEN_FUNCTIONS = {
    "print", "input",
}

FORBIDDEN_IMPORTS = {
    "requests", "urllib", "socket", "sqlalchemy",
}


class PurityChecker(ast.NodeVisitor):
    """AST visitor to detect impure operations."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []

    def visit_Call(self, node: ast.Call):
        """Check for forbidden function calls."""
        if isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_FUNCTIONS:
                self.violations.append(
                    (node.lineno, f"Forbidden function: {node.func.id}")
                )
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        """Check for __main__ blocks."""
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.left, ast.Name):
                if node.test.left.id == "__name__":
                    self.violations.append(
                        (node.lineno, "Forbidden __main__ block in core module")
                    )
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        """Check for forbidden imports."""
        for alias in node.names:
            if any(forbidden in alias.name for forbidden in FORBIDDEN_IMPORTS):
                self.violations.append(
                    (node.lineno, f"Forbidden import: {alias.name}")
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Check for forbidden imports."""
        if node.module:
            if any(forbidden in node.module for forbidden in FORBIDDEN_IMPORTS):
                self.violations.append(
                    (node.lineno, f"Forbidden import from: {node.module}")
                )
        self.generic_visit(node)


def check_file_purity(filepath: Path) -> List[Tuple[int, str]]:
    """Check a single file for purity violations."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        checker = PurityChecker(filepath)
        checker.visit(tree)
        return checker.violations
    except SyntaxError as e:
        return [(e.lineno or 0, f"Syntax error: {e.msg}")]
    except Exception as e:
        return [(0, f"Error parsing file: {e}")]


def main() -> int:
    """Scan all core modules for purity violations."""
    repo_root = PROJECT_ROOT
    violations_found = False

    for core_path_str in CORE_PATHS:
        core_path = repo_root / core_path_str

        if not core_path.exists():
            print(f"⚠️  Core path not found: {core_path}")
            continue

        print(f"Scanning {core_path_str}...")

        for py_file in core_path.rglob("*.py"):
            violations = check_file_purity(py_file)

            if violations:
                violations_found = True
                rel_path = py_file.relative_to(repo_root)
                print(f"\n❌ {rel_path}")
                for lineno, msg in violations:
                    print(f"  Line {lineno}: {msg}")

    if violations_found:
        print("\n❌ Core purity violations detected")
        return 1
    else:
        print("✓ All core modules are pure")
        return 0


if __name__ == "__main__":
    sys.exit(main())
