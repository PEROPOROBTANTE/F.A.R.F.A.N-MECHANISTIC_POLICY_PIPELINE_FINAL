#!/usr/bin/env python3.12
"""
Core Purity Scanner - AST-based anti-I/O and anti-__main__ checker

Enforces architectural purity in core modules by detecting:
1. I/O operations (file access, network calls, print statements)
2. __main__ blocks (core modules should be pure libraries)

Exit codes:
    0: All checks passed
    1: Violations found
"""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

# I/O operations to detect
IO_OPERATIONS = {
    # File I/O
    "open", "read", "write", "close",
    # Print operations
    "print",
    # Network I/O
    "urlopen", "requests", "httpx",
    # System I/O
    "input",
}

class CorePurityChecker(ast.NodeVisitor):
    """AST visitor to detect I/O operations and __main__ blocks."""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.violations: List[Tuple[int, str]] = []
        self.has_main_block = False

    def visit_Call(self, node: ast.Call) -> None:
        """Check for I/O function calls."""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in IO_OPERATIONS:
                self.violations.append(
                    (node.lineno, f"I/O operation detected: {func_name}()")
                )

        # Check for file operations like Path().open()
        if isinstance(node.func, ast.Attribute):
            if node.func.attr in IO_OPERATIONS:
                self.violations.append(
                    (node.lineno, f"I/O method detected: .{node.func.attr}()")
                )

        self.generic_visit(node)

    def visit_If(self, node: ast.If) -> None:
        """Check for if __name__ == '__main__' blocks."""
        if isinstance(node.test, ast.Compare):
            left = node.test.left
            if isinstance(left, ast.Name) and left.id == "__name__":
                for comparator in node.test.comparators:
                    if isinstance(comparator, ast.Constant):
                        if comparator.value == "__main__":
                            self.has_main_block = True
                            self.violations.append(
                                (node.lineno, "__main__ block detected in core module")
                            )

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Check for with statements (often used for file I/O)."""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                if isinstance(item.context_expr.func, ast.Name):
                    func_name = item.context_expr.func.id
                    if func_name == "open":
                        self.violations.append(
                            (node.lineno, "File I/O detected: with open(...)")
                        )

        self.generic_visit(node)


def scan_file(filepath: Path) -> List[Tuple[int, str]]:
    """Scan a single Python file for purity violations."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(filepath))
        checker = CorePurityChecker(filepath)
        checker.visit(tree)

        return checker.violations

    except SyntaxError as e:
        print(f"⚠️  Syntax error in {filepath}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"⚠️  Error scanning {filepath}: {e}", file=sys.stderr)
        return []


def scan_core_modules(src_dir: Path) -> int:
    """
    Scan all core modules for purity violations.

    Returns:
        0 if all checks pass, 1 if violations found
    """
    core_dirs = [
        src_dir / "saaaaaa" / "core",
        src_dir / "saaaaaa" / "processing",
        src_dir / "saaaaaa" / "analysis",
    ]

    all_violations: List[Tuple[Path, int, str]] = []

    for core_dir in core_dirs:
        if not core_dir.exists():
            continue

        # Scan all Python files in the core directory
        for pyfile in core_dir.rglob("*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" in str(pyfile) or pyfile.name.startswith("test_"):
                continue

            violations = scan_file(pyfile)
            for lineno, msg in violations:
                all_violations.append((pyfile, lineno, msg))

    # Report violations
    if all_violations:
        print("❌ Core purity violations detected:\n")
        for filepath, lineno, msg in all_violations:
            rel_path = filepath.relative_to(src_dir.parent)
            print(f"  {rel_path}:{lineno} - {msg}")
        print(f"\n❌ Total violations: {len(all_violations)}")
        return 1

    print("✓ Core purity check passed - no I/O or __main__ blocks detected")
    return 0


def main() -> int:
    """Main entry point."""
    # Determine project root and src directory
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}", file=sys.stderr)
        return 1

    return scan_core_modules(src_dir)


if __name__ == "__main__":
    sys.exit(main())
