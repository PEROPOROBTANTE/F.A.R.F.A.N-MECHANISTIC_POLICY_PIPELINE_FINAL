#!/usr/bin/env python3
"""
Import Shadowing Detector

Detects local files that shadow standard library or third-party packages.
This is a critical security and correctness issue.

Examples of problems:
- json.py in the project shadows stdlib json
- typing.py shadows stdlib typing
- requests.py shadows third-party requests

Exit codes:
- 0: No shadowing detected
- 1: Shadowing detected (with details)
"""

from __future__ import annotations

import sys
from pathlib import Path


# Standard library modules that must not be shadowed
STDLIB_MODULES = {
    "abc", "ast", "asyncio", "base64", "collections", "concurrent",
    "contextlib", "copy", "csv", "dataclasses", "datetime", "decimal",
    "enum", "functools", "hashlib", "heapq", "http", "importlib",
    "inspect", "io", "itertools", "json", "logging", "math", "multiprocessing",
    "operator", "os", "pathlib", "pickle", "platform", "queue", "random",
    "re", "shutil", "signal", "socket", "sqlite3", "ssl", "string",
    "struct", "subprocess", "sys", "tempfile", "threading", "time",
    "traceback", "typing", "unittest", "urllib", "uuid", "warnings",
    "weakref", "xml", "zipfile", "zlib",
}

# Common third-party packages that must not be shadowed
THIRDPARTY_MODULES = {
    "numpy", "pandas", "scipy", "sklearn", "torch", "tensorflow",
    "requests", "httpx", "flask", "fastapi", "pydantic", "click",
    "pytest", "hypothesis", "black", "ruff", "mypy", "pyyaml",
    "polars", "pyarrow", "blake3", "networkx", "spacy", "transformers",
}


def find_python_files(root: Path) -> list[Path]:
    """Find all Python files in the project, excluding known safe directories."""
    exclude_patterns = {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        ".mypy_cache", ".ruff_cache", "node_modules", "minipdm",
        "dist", "build", "*.egg-info",
    }
    
    python_files = []
    for py_file in root.rglob("*.py"):
        # Check if any excluded pattern is in the path
        if any(pattern in py_file.parts for pattern in exclude_patterns):
            continue
        python_files.append(py_file)
    
    return python_files


def check_shadowing(root: Path) -> list[tuple[Path, str, str]]:
    """
    Check for files that shadow stdlib or third-party modules.
    
    Returns
    -------
    list[tuple[Path, str, str]]
        List of (file_path, shadowed_module, category)
    """
    issues = []
    python_files = find_python_files(root)
    
    for py_file in python_files:
        # Get module name from filename
        stem = py_file.stem
        
        # Check against stdlib
        if stem in STDLIB_MODULES:
            issues.append((py_file, stem, "stdlib"))
        
        # Check against third-party
        elif stem in THIRDPARTY_MODULES:
            issues.append((py_file, stem, "third-party"))
    
    return issues


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent
    
    print("=== Import Shadowing Detection ===")
    print(f"Scanning: {root}")
    print()
    
    issues = check_shadowing(root)
    
    if not issues:
        print("✓ No shadowing issues detected")
        return 0
    
    print(f"✗ Found {len(issues)} shadowing issue(s):\n")
    
    for file_path, module_name, category in sorted(issues):
        rel_path = file_path.relative_to(root)
        print(f"  {rel_path}")
        print(f"    Shadows {category} module: {module_name}")
        print(f"    Fix: Rename file to avoid import hijacking")
        print()
    
    print(f"Total issues: {len(issues)}")
    print("\nShadowing is a critical security and correctness issue.")
    print("Files must be renamed before they can be safely imported.")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
