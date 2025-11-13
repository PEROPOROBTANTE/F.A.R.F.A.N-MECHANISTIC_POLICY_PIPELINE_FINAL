#!/usr/bin/env python3
"""
Simple circular dependency detector
Alternative to pycycle for detecting import cycles.
"""
import ast
import sys
from collections import defaultdict
from pathlib import Path

def extract_imports(file_path: Path) -> set[str]:
    """Extract import statements from a Python file."""
    imports = set()

    try:
        with open(file_path, encoding='utf-8') as f:
            tree = ast.parse(f.read(), str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split('.')[0])
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)

    return imports

def build_dependency_graph(root_path: Path, package_name: str) -> dict[str, set[str]]:
    """Build a dependency graph for the package."""
    graph = defaultdict(set)

    for py_file in root_path.rglob('*.py'):
        if py_file.name == '__init__.py':
            continue

        # Convert file path to module name
        try:
            rel_path = py_file.relative_to(root_path.parent)
            module = str(rel_path.with_suffix('')).replace('/', '.')
        except ValueError:
            continue

        # Extract imports from this module
        imports = extract_imports(py_file)

        # Track all imports (internal and external) for dependency analysis
        for imp in imports:
            # Add to graph if it's an internal module or starts with package name
            graph[module].add(imp)

            # Also track sub-package relationships
            if '.' in imp and imp.startswith(package_name):
                parts = imp.split('.')
                for i in range(1, len(parts)):
                    sub_pkg = '.'.join(parts[:i+1])
                    graph[module].add(sub_pkg)

    return graph

def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find cycles in the dependency graph using DFS."""
    cycles = []
    visited = set()
    rec_stack = set()
    path = []

    def dfs(node: str) -> bool:
        """DFS to detect cycles."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                # Found a cycle
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
                return True

        path.pop()
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            dfs(node)

    return cycles

def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python detect_cycles.py <package_path>")
        sys.exit(1)

    root_path = Path(sys.argv[1])
    if not root_path.exists():
        print(f"Error: Path {root_path} does not exist")
        sys.exit(1)

    # Get package name from path
    package_name = root_path.name

    print(f"Analyzing package: {package_name}")
    print(f"Path: {root_path}")

    # Build dependency graph
    graph = build_dependency_graph(root_path, package_name)

    print(f"\nFound {len(graph)} modules")

    # Find cycles
    cycles = find_cycles(graph)

    if cycles:
        print(f"\n❌ Found {len(cycles)} circular dependencies:")
        for i, cycle in enumerate(cycles, 1):
            print(f"\n  Cycle {i}:")
            for j, module in enumerate(cycle):
                if j < len(cycle) - 1:
                    print(f"    {module} →")
                else:
                    print(f"    {module}")
        sys.exit(1)
    else:
        print("\n✅ No circular dependencies found")
        sys.exit(0)

if __name__ == '__main__':
    main()
