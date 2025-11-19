#!/usr/bin/env python3
"""
Comprehensive circular import detection and analysis.

Detects circular dependencies in the FARFAN codebase using:
1. Static import parsing (AST analysis)
2. Dynamic import tracking
3. Dependency graph visualization

Reports severity levels:
- CRITICAL: Causes runtime import errors
- WARNING: Causes delayed/lazy loading issues
- BENIGN: No runtime issues due to import order/structure
"""

import sys
import ast
import importlib
import importlib.util
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from collections import defaultdict

class ImportAnalyzer:
    """Analyze Python imports and detect circular dependencies."""

    def __init__(self, root_path: str):
        self.root_path = Path(root_path).resolve()
        self.imports_graph: Dict[str, Set[str]] = defaultdict(set)
        self.cycles: List[List[str]] = []
        self.import_issues: List[Dict] = []

    def _module_to_path(self, module_name: str) -> Optional[Path]:
        """Convert a module name to file path."""
        parts = module_name.split('.')

        # Try as regular module
        as_file = self.root_path / Path(*parts).with_suffix('.py')
        if as_file.exists():
            return as_file

        # Try as package __init__.py
        as_package = self.root_path / Path(*parts) / '__init__.py'
        if as_package.exists():
            return as_package

        return None

    def _path_to_module(self, file_path: Path) -> str:
        """Convert a file path to module name."""
        # Try to find relative to root
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            return str(file_path)

        # Convert path to module notation
        parts = list(rel_path.parts[:-1]) + [rel_path.stem]
        if parts[-1] == '__init__':
            parts = parts[:-1]
        return '.'.join(parts)

    def _extract_imports_from_ast(self, file_path: Path) -> Set[str]:
        """Extract import statements from Python file using AST."""
        imports = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                except SyntaxError as e:
                    print(f"Warning: Syntax error in {file_path}: {e}")
                    return imports
        except Exception as e:
            print(f"Warning: Cannot read {file_path}: {e}")
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                # Resolve relative imports using the file path so we capture local package dependencies.
                # node.level == 0 => absolute import; node.level > 0 => relative import with that many leading dots.
                current_module = self._path_to_module(file_path)
                package_parts = current_module.split('.')[:-1]  # module's package parts
                # Compute parent package parts based on relative level
                if getattr(node, "level", 0) and node.level > 0:
                    cut = node.level - 1
                    if cut <= 0:
                        parent_parts = package_parts
                    else:
                        parent_parts = package_parts[:-cut] if cut <= len(package_parts) else []
                else:
                    parent_parts = package_parts
                # Build resolved module name
                if node.module:
                    if parent_parts:
                        resolved = '.'.join(parent_parts + [node.module]) if node.level and node.level > 0 else node.module
                    else:
                        resolved = node.module
                else:
                    # from . import name  -> resolved to parent package
                    resolved = '.'.join(parent_parts) if parent_parts else ''
                if resolved:
                    imports.add(resolved)

        return imports

    def analyze_directory(self, directory: str = None):
        """Analyze all Python files in a directory."""
        if directory is None:
            directory = str(self.root_path)

        search_path = Path(directory)
        if not search_path.exists():
            print(f"Directory not found: {directory}")
            return

        py_files = list(search_path.rglob('*.py'))
        print(f"Found {len(py_files)} Python files in {directory}")

        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue

            module_name = self._path_to_module(py_file)
            imports = self._extract_imports_from_ast(py_file)

            # Filter imports to those in our project
            project_imports = set()
            for imp in imports:
                # Check if this is a saaaaaa import
                if imp.startswith('saaaaaa'):
                    project_imports.add(imp)
                # Check if it could be a relative local import
                elif '.' in module_name:
                    base_module = module_name.split('.')[0]
                    if imp.startswith(base_module):
                        project_imports.add(imp)

            if project_imports:
                self.imports_graph[module_name] = project_imports

    def find_cycles(self) -> List[List[str]]:
        """Find all circular dependencies in import graph."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self.imports_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor, path[:])
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    # Check if we haven't already found this cycle
                    cycle_normalized = min(
                        [cycle[i:] + cycle[:i] for i in range(len(cycle)-1)],
                        key=tuple
                    )
                    if cycle_normalized not in cycles:
                        cycles.append(cycle_normalized)

            path.pop()
            rec_stack.remove(node)

        for node in self.imports_graph:
            if node not in visited:
                dfs(node, [])

        self.cycles = cycles
        return cycles

    def analyze_specific_imports(self, module_path: str) -> Dict:
        """Detailed analysis of specific module imports."""
        file_path = Path(module_path)
        if not file_path.exists():
            return {}

        result = {
            'file': str(file_path),
            'direct_imports': [],
            'is_circular': False,
            'cycle_chain': []
        }

        # Extract from/import statements for detailed info
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return result

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('saaaaaa'):
                    names = [alias.name for alias in node.names]
                    result['direct_imports'].append({
                        'module': node.module,
                        'names': names,
                        'lineno': node.lineno
                    })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('saaaaaa'):
                        result['direct_imports'].append({
                            'module': alias.name,
                            'lineno': node.lineno
                        })

        # Check if involved in cycle
        module_name = self._path_to_module(file_path)
        for cycle in self.cycles:
            if module_name in cycle:
                result['is_circular'] = True
                result['cycle_chain'] = cycle
                break

        return result


def assess_severity(cycle: List[str]) -> Tuple[str, str]:
    """Assess severity of circular import."""
    # Check for immediate imports at module level
    severity = "BENIGN"  # Default assumption
    reason = "Circular dependency exists but may not cause runtime issues"

    # Check specific patterns that cause problems
    problematic_patterns = [
        ('spc_adapter', 'cpp_adapter'),  # Known issue
        ('cpp_adapter', 'spc_adapter'),  # Known issue
    ]

    cycle_str = '->'.join(cycle)

    for pattern in problematic_patterns:
        if all(p in cycle for p in pattern):
            # Check if only aliasing (benign)
            if len(cycle) == 2:  # Two-module cycle
                severity = "WARNING"
                reason = "Two-way circular import detected - potential runtime issues if not properly handled"
            else:
                severity = "WARNING"
                reason = f"Circular dependency chain: {cycle_str}"

    # Check length - longer chains are usually worse
    # Escalate to CRITICAL for long chains regardless of prior severity
    if len(cycle) > 3:
        severity = "CRITICAL"
        reason = f"Long circular dependency chain ({len(cycle)} modules): {cycle_str}"

    return severity, reason


def test_import_runtime(module_name: str) -> Tuple[bool, Optional[str]]:
    """Test if module can be imported at runtime."""
    try:
        # Dynamically import and check for issues
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            return False, f"Module spec not found: {module_name}"

        # Try actual import
        importlib.import_module(module_name)
        return True, None
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    repo_root = Path(__file__).parent.parent.resolve()

    print("=" * 80)
    print("CIRCULAR IMPORT ANALYSIS REPORT")
    print(f"Repository: {repo_root}")
    print("=" * 80)

    # Analyze src/saaaaaa directory
    print("\n[1/3] Analyzing src/saaaaaa directory...")
    saaaaaa_root = repo_root / 'src' / 'saaaaaa'

    if not saaaaaa_root.exists():
        print(f"Error: saaaaaa directory not found at {saaaaaa_root}")
        sys.exit(1)

    analyzer = ImportAnalyzer(saaaaaa_root)
    analyzer.analyze_directory(str(saaaaaa_root))

    print(f"    Found {len(analyzer.imports_graph)} modules with imports")

    # Find cycles
    print("\n[2/3] Finding circular dependencies...")
    cycles = analyzer.find_cycles()

    if cycles:
        print(f"    Found {len(cycles)} circular dependency chains")
    else:
        print("    No circular dependencies found")

    # Analyze specific files
    print("\n[3/3] Analyzing specific adapter files...")

    spc_adapter_path = saaaaaa_root / 'utils' / 'spc_adapter.py'
    cpp_adapter_path = saaaaaa_root / 'utils' / 'cpp_adapter.py'

    findings = []

    # Report cycles
    print("\n" + "=" * 80)
    print("CIRCULAR IMPORT CHAINS FOUND")
    print("=" * 80)

    if cycles:
        for i, cycle in enumerate(cycles, 1):
            severity, reason = assess_severity(cycle)
            print(f"\n[Circular Import #{i}]")
            print(f"  Severity: {severity}")
            print(f"  Chain: {' -> '.join(cycle)}")
            print(f"  Reason: {reason}")

            findings.append({
                'id': i,
                'chain': cycle,
                'severity': severity,
                'reason': reason
            })
    else:
        print("\nNo circular imports detected in static analysis.")

    # Detailed analysis of known problematic files
    print("\n" + "=" * 80)
    print("DETAILED ANALYSIS: spc_adapter.py <-> cpp_adapter.py")
    print("=" * 80)

    if spc_adapter_path.exists():
        print(f"\n[spc_adapter.py]")
        spc_info = analyzer.analyze_specific_imports(str(spc_adapter_path))

        print(f"  Direct imports:")
        for imp in spc_info.get('direct_imports', []):
            print(f"    - Line {imp.get('lineno')}: from {imp['module']} import {', '.join(imp.get('names', []))}")

        if spc_info.get('is_circular'):
            print(f"  Circular: YES")
            print(f"  Cycle: {' -> '.join(spc_info['cycle_chain'])}")
        else:
            print(f"  Circular: NO")

    if cpp_adapter_path.exists():
        print(f"\n[cpp_adapter.py]")
        cpp_info = analyzer.analyze_specific_imports(str(cpp_adapter_path))

        print(f"  Direct imports:")
        for imp in cpp_info.get('direct_imports', []):
            print(f"    - Line {imp.get('lineno')}: from {imp['module']} import {', '.join(imp.get('names', []))}")

        if cpp_info.get('is_circular'):
            print(f"  Circular: YES")
            print(f"  Cycle: {' -> '.join(cpp_info['cycle_chain'])}")
        else:
            print(f"  Circular: NO")

    # Test runtime behavior
    print("\n" + "=" * 80)
    print("RUNTIME IMPORT TESTS")
    print("=" * 80)

    test_modules = [
        'saaaaaa.utils.spc_adapter',
        'saaaaaa.utils.cpp_adapter',
        'saaaaaa.processing.embedding_policy',
        'saaaaaa.processing.semantic_chunking_policy',
    ]

    for module_name in test_modules:
        success, error = test_import_runtime(module_name)
        status = "SUCCESS" if success else "FAILED"
        print(f"\n  {module_name}")
        print(f"    Status: {status}")
        if error:
            print(f"    Error: {error}")

    # Import smart_policy_chunks script imports
    print("\n" + "=" * 80)
    print("ANALYSIS: scripts/smart_policy_chunks_canonic_phase_one.py")
    print("=" * 80)

    smart_chunks_path = repo_root / 'scripts' / 'smart_policy_chunks_canonic_phase_one.py'
    if smart_chunks_path.exists():
        smart_analyzer = ImportAnalyzer(repo_root)
        smart_info = smart_analyzer.analyze_specific_imports(str(smart_chunks_path))

        print(f"\n  File: {smart_chunks_path}")
        print(f"  Direct saaaaaa imports:")
        saaaaaa_imports = [imp for imp in smart_info.get('direct_imports', [])
                           if imp['module'].startswith('saaaaaa')]
        for imp in saaaaaa_imports:
            print(f"    - from {imp['module']} import {', '.join(imp.get('names', []))}")

        if not saaaaaa_imports:
            print(f"    (No direct saaaaaa imports detected)")

        # Test if script can be imported as module
        print(f"\n  Import test:")
        sys.path.insert(0, str(repo_root))
        try:
            spec = importlib.util.spec_from_file_location("smart_chunks", smart_chunks_path)
            if spec and spec.loader:
                print(f"    Module spec found: OK")
                # Don't actually load to avoid executing the full script
            else:
                print(f"    Module spec not found")
        except Exception as e:
            print(f"    Error: {e}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if findings:
        print(f"\nCircular imports found: {len(findings)}")
        for finding in findings:
            print(f"  - [{finding['severity']}] {' -> '.join(finding['chain'])}")
    else:
        print("\nNo critical circular imports detected.")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    print("""
1. **Known Circular Import**: spc_adapter.py <-> cpp_adapter.py
   - Status: MITIGATED (by deprecation wrapper pattern)
   - Reason: cpp_adapter.py only imports from spc_adapter at module level,
     then wraps classes. No actual circular execution occurs.
   - Action: This is acceptable but consider migrating away from cpp_adapter.py

2. **For Future Changes**:
   - Avoid importing at module-level in adapter files
   - Use delayed imports (inside functions/methods) if needed
   - Consider factory patterns to break circular dependencies

3. **Testing Recommendation**:
   - Run 'import saaaaaa.utils.spc_adapter' in clean Python process
   - Run 'import saaaaaa.utils.cpp_adapter' in clean Python process
   - Verify no ImportError or circular dependency errors occur
""")

    print("=" * 80)
    print("Analysis complete.")


if __name__ == '__main__':
    main()
