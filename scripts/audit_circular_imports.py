#!/usr/bin/env python3
"""
Circular Import Detector

Detects circular import patterns in the codebase using AST analysis.
Circular imports can cause import failures and are difficult to debug.

This script builds an import graph and detects cycles.

Exit codes:
- 0: No circular imports detected
- 1: Circular imports detected (with details)
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path
from typing import Set


def extract_imports(file_path: Path) -> set[str]:
    """
    Extract all imported modules from a Python file.
    
    Returns
    -------
    set[str]
        Set of imported module names (absolute imports only)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    
    imports = set()
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                # Keep full module path for better cycle detection
                imports.add(alias.name)
        
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.level == 0:  # Absolute import
                # Keep full module path for better cycle detection
                imports.add(node.module)
    
    return imports


def build_import_graph(root: Path, package_name: str = "saaaaaa") -> dict[str, set[str]]:
    """
    Build import graph for the package.
    
    Parameters
    ----------
    root : Path
        Root directory of the project
    package_name : str
        Name of the package to analyze
    
    Returns
    -------
    dict[str, set[str]]
        Adjacency list representing import dependencies
    """
    graph = defaultdict(set)
    src_root = root / "src" / package_name
    
    if not src_root.exists():
        print(f"Warning: Package directory not found: {src_root}", file=sys.stderr)
        return dict(graph)
    
    # Find all Python files in the package
    python_files = list(src_root.rglob("*.py"))
    
    # Build module name to file path mapping
    file_to_module = {}
    for py_file in python_files:
        rel_path = py_file.relative_to(src_root)
        parts = list(rel_path.parts)
        
        # Convert to module name
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].replace(".py", "")
        
        if parts:
            module_name = ".".join(parts)
            file_to_module[py_file] = f"{package_name}.{module_name}"
        else:
            file_to_module[py_file] = package_name
    
    # Build dependency graph
    for py_file, module_name in file_to_module.items():
        imports = extract_imports(py_file)
        
        # Filter to only imports within our package
        for imp in imports:
            if imp == package_name or imp.startswith(f"{package_name}."):
                graph[module_name].add(imp)
    
    return dict(graph)


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """
    Find all cycles in the import graph using DFS.
    
    Parameters
    ----------
    graph : dict[str, set[str]]
        Import dependency graph
    
    Returns
    -------
    list[list[str]]
        List of cycles (each cycle is a list of module names)
    """
    cycles = []
    visited = set()
    rec_stack = set()
    path = []
    
    def dfs(node: str) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
        
        path.pop()
        rec_stack.remove(node)
    
    for node in graph:
        if node not in visited:
            dfs(node)
    
    return cycles


def main() -> int:
    """Main entry point."""
    root = Path(__file__).parent.parent
    
    print("=== Circular Import Detection ===")
    print(f"Scanning: {root}")
    print()
    
    # Build import graph
    print("Building import graph...")
    graph = build_import_graph(root)
    print(f"Found {len(graph)} modules with imports")
    print()
    
    # Detect cycles
    print("Detecting circular imports...")
    cycles = find_cycles(graph)
    
    if not cycles:
        print("✓ No circular imports detected")
        return 0
    
    print(f"✗ Found {len(cycles)} circular import(s):\n")
    
    for i, cycle in enumerate(cycles, 1):
        print(f"Cycle {i}:")
        for j, module in enumerate(cycle[:-1]):
            print(f"  {module}")
            if j < len(cycle) - 2:
                print(f"    ↓ imports")
        print()
    
    print(f"Total cycles: {len(cycles)}")
    print("\nCircular imports can cause import failures and runtime errors.")
    print("Fixes:")
    print("  1. Move import inside function (deferred import)")
    print("  2. Refactor to break dependency")
    print("  3. Introduce intermediate module")
    
    return 1


if __name__ == "__main__":
    sys.exit(main())
