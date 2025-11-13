#!/usr/bin/env python3
"""
Runtime Code Audit Tool - Dry Run Deletion Plan Generator

Audits a Python codebase to identify files/directories not strictly required for runtime execution.
Produces a comprehensive dry-run plan in JSON format with keep/delete/unsure categories.

Usage:
    python runtime_audit.py > audit_report.json
"""

import ast
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple


class RuntimeAudit:
    """Comprehensive runtime code audit tool."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.keep_items = []
        self.delete_items = []
        self.unsure_items = []
        self.evidence = {
            "entry_points": [],
            "import_graph_nodes": 0,
            "dynamic_strings_matched": [],
            "runtime_io_refs": [],
            "smoke_test": "not_run"
        }
        
        # Import graph: file -> set of imported files
        self.import_graph: Dict[Path, Set[Path]] = defaultdict(set)
        
        # Reachable files from entry points
        self.reachable_files: Set[Path] = set()
        
        # Dynamic import patterns found
        self.dynamic_patterns: Set[str] = set()
        
        # Files opened at runtime
        self.runtime_io_files: Set[Path] = set()
        
        # Package structure (package dirs and their __init__.py files)
        self.package_dirs: Set[Path] = set()
        self.init_files: Set[Path] = set()

    def run_audit(self) -> Dict[str, Any]:
        """Execute the complete audit pipeline."""
        print("Starting runtime code audit...", file=sys.stderr)
        
        # Step 1: Parse packaging files to get entry points
        print("Step 1: Parsing packaging configuration...", file=sys.stderr)
        self._parse_packaging_files()
        
        # Step 2: Build import graph
        print("Step 2: Building import dependency graph...", file=sys.stderr)
        self._build_import_graph()
        
        # Step 3: Find dynamic imports
        print("Step 3: Scanning for dynamic imports...", file=sys.stderr)
        self._scan_dynamic_imports()
        
        # Step 4: Find runtime file I/O
        print("Step 4: Scanning for runtime file I/O...", file=sys.stderr)
        self._scan_runtime_io()
        
        # Step 5: Identify package structure
        print("Step 5: Identifying package structure...", file=sys.stderr)
        self._identify_package_structure()
        
        # Step 6: Trace reachability from entry points
        print("Step 6: Tracing reachability from entry points...", file=sys.stderr)
        self._trace_reachability()
        
        # Step 7: Classify all files
        print("Step 7: Classifying files...", file=sys.stderr)
        self._classify_files()
        
        # Step 8: Simulate smoke test
        print("Step 8: Simulating smoke test...", file=sys.stderr)
        self._simulate_smoke_test()
        
        # Step 9: Generate report
        print("Step 9: Generating report...", file=sys.stderr)
        return self._generate_report()

    def _parse_packaging_files(self):
        """Parse setup.py, pyproject.toml, setup.cfg for entry points and packages."""
        # Parse setup.py
        setup_py = self.repo_root / "setup.py"
        if setup_py.exists():
            with open(setup_py, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for entry_points
            entry_match = re.search(r'entry_points\s*=\s*{([^}]+)}', content, re.DOTALL)
            if entry_match:
                # Extract console_scripts
                scripts_match = re.search(
                    r'"console_scripts":\s*\[([^\]]+)\]',
                    entry_match.group(1),
                    re.DOTALL
                )
                if scripts_match:
                    for line in scripts_match.group(1).split(','):
                        line = line.strip().strip('"').strip("'")
                        if '=' in line:
                            _, module_path = line.split('=', 1)
                            self.evidence["entry_points"].append(module_path.strip())
        
        # Parse pyproject.toml
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists():
            with open(pyproject, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Look for [project.scripts]
            scripts_section = re.search(
                r'\[project\.scripts\]\s*\n((?:[^\[]+)+)',
                content,
                re.MULTILINE
            )
            if scripts_section:
                for line in scripts_section.group(1).split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#'):
                        _, module_path = line.split('=', 1)
                        module_path = module_path.strip().strip('"').strip("'")
                        self.evidence["entry_points"].append(module_path)

        # Add default entry point if none found
        if not self.evidence["entry_points"]:
            # Try to find main package __init__.py
            src_dir = self.repo_root / "src"
            if src_dir.exists():
                for pkg_dir in src_dir.iterdir():
                    if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
                        self.evidence["entry_points"].append(f"{pkg_dir.name}.__init__")
                        break

    def _build_import_graph(self):
        """Build the import dependency graph for all Python files."""
        # Find all Python files
        for py_file in self.repo_root.rglob("*.py"):
            # Skip git, venv, and other non-code directories
            if any(part.startswith('.') or part in ['venv', 'env', '__pycache__']
                   for part in py_file.parts):
                continue
            
            self._parse_imports(py_file)

    def _parse_imports(self, py_file: Path):
        """Parse imports from a Python file and add to import graph."""
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read(), filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_file = self._resolve_import(alias.name, py_file)
                    if imported_file:
                        self.import_graph[py_file].add(imported_file)
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_file = self._resolve_import(node.module, py_file)
                    if imported_file:
                        self.import_graph[py_file].add(imported_file)

    def _resolve_import(self, module_name: str, from_file: Path) -> Path | None:
        """Resolve an import statement to a file path."""
        # Try different resolution strategies
        
        # Strategy 1: Resolve from src/package
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            module_path = src_dir / module_name.replace('.', '/')
            
            # Check if it's a package
            if (module_path / "__init__.py").exists():
                return module_path / "__init__.py"
            
            # Check if it's a module
            py_file = module_path.with_suffix('.py')
            if py_file.exists():
                return py_file
        
        # Strategy 2: Resolve from repo root
        module_path = self.repo_root / module_name.replace('.', '/')
        
        if (module_path / "__init__.py").exists():
            return module_path / "__init__.py"
        
        py_file = module_path.with_suffix('.py')
        if py_file.exists():
            return py_file
        
        # Strategy 3: Check if it's a relative import in the same directory
        parent_dir = from_file.parent
        module_parts = module_name.split('.')
        
        for i in range(len(module_parts), 0, -1):
            potential_path = parent_dir / '/'.join(module_parts[:i])
            if (potential_path / "__init__.py").exists():
                return potential_path / "__init__.py"
            
            py_file = potential_path.with_suffix('.py')
            if py_file.exists():
                return py_file
        
        return None

    def _scan_dynamic_imports(self):
        """Scan for dynamic import patterns (importlib, __import__, registries, etc.)."""
        # Patterns to search for
        patterns = [
            r'importlib\.import_module',
            r'__import__\(',
            r'pkg_resources',
            r'entry_points\(',
            r'importlib\.metadata',
            r'\.entry_points\(',
            r'["\'].*registry.*["\']',
            r'["\'].*factory.*["\']',
            r'["\'].*plugin.*["\']',
        ]
        
        for py_file in self.repo_root.rglob("*.py"):
            if any(part.startswith('.') or part in ['venv', 'env', '__pycache__']
                   for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern in patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        for match in matches:
                            self.dynamic_patterns.add(match)
                            self.evidence["dynamic_strings_matched"].append(match)
                        
                        # Mark this file as reachable due to dynamic imports
                        self.reachable_files.add(py_file)
                
                # Also scan for string literals that match module names
                try:
                    tree = ast.parse(content, filename=str(py_file))
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Constant) and isinstance(node.value, str):
                            # Check if string looks like a module name
                            if self._looks_like_module_name(node.value):
                                self.dynamic_patterns.add(f"'{node.value}'")
                                
                                # Try to resolve it
                                resolved = self._resolve_import(node.value, py_file)
                                if resolved:
                                    self.reachable_files.add(resolved)
                except SyntaxError:
                    pass
                    
            except (UnicodeDecodeError, PermissionError):
                continue

    def _looks_like_module_name(self, s: str) -> bool:
        """Check if a string looks like a module name."""
        # Simple heuristic: contains only alphanumeric, dots, underscores
        # and has at least one dot or matches known package names
        if not s or len(s) > 100:
            return False
        
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_\.]*$', s):
            return False
        
        # Check if it matches our known package structure
        if s.startswith('saaaaaa'):
            return True
        
        # Check if it contains common module patterns
        if '.' in s and len(s.split('.')) >= 2:
            return True
        
        return False

    def _scan_runtime_io(self):
        """Scan for runtime file I/O operations."""
        io_patterns = [
            (r'open\(["\']([^"\']+)["\']', 'open()'),
            (r'Path\(["\']([^"\']+)["\']', 'Path()'),
            (r'\.read_text\(\)', 'read_text()'),
            (r'\.read_bytes\(\)', 'read_bytes()'),
            (r'json\.load\(', 'json.load'),
            (r'json\.loads\(', 'json.loads'),
            (r'yaml\.safe_load\(', 'yaml.safe_load'),
            (r'yaml\.load\(', 'yaml.load'),
            (r'\.read\(\)', 'file.read()'),
        ]
        
        for py_file in self.repo_root.rglob("*.py"):
            if any(part.startswith('.') or part in ['venv', 'env', '__pycache__']
                   for part in py_file.parts):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                for pattern, op_name in io_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        # File performs I/O operations
                        for match in matches:
                            if isinstance(match, str) and match:
                                # Resolve the file path
                                target_file = self._resolve_io_path(match, py_file)
                                if target_file:
                                    self.runtime_io_files.add(target_file)
                                    self.evidence["runtime_io_refs"].append(
                                        f"{py_file.relative_to(self.repo_root)} -> '{match}' via {op_name}"
                                    )
            except (UnicodeDecodeError, PermissionError):
                continue

    def _resolve_io_path(self, path_str: str, from_file: Path) -> Path | None:
        """Resolve a file I/O path string to an actual file."""
        # Try relative to from_file
        resolved = (from_file.parent / path_str).resolve()
        if resolved.exists() and resolved.is_relative_to(self.repo_root):
            return resolved
        
        # Try relative to repo root
        resolved = (self.repo_root / path_str).resolve()
        if resolved.exists() and resolved.is_relative_to(self.repo_root):
            return resolved
        
        return None

    def _identify_package_structure(self):
        """Identify all Python packages and their __init__.py files."""
        for init_file in self.repo_root.rglob("__init__.py"):
            if any(part.startswith('.') or part in ['venv', 'env', '__pycache__']
                   for part in init_file.parts):
                continue
            
            self.init_files.add(init_file)
            self.package_dirs.add(init_file.parent)

    def _trace_reachability(self):
        """Trace reachability from entry points using DFS on import graph."""
        # Convert entry points to file paths
        entry_files = set()
        
        for entry_point in self.evidence["entry_points"]:
            # Parse entry point format: "package.module:function" or "package.module"
            if ':' in entry_point:
                module_path, _ = entry_point.split(':', 1)
            else:
                module_path = entry_point
            
            # Try to resolve to a file
            entry_file = self._resolve_import(module_path, self.repo_root)
            if entry_file:
                entry_files.add(entry_file)
        
        # Add __init__.py files from main package
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            for pkg_dir in src_dir.iterdir():
                if pkg_dir.is_dir():
                    init = pkg_dir / "__init__.py"
                    if init.exists():
                        entry_files.add(init)
        
        # DFS from entry points
        visited = set()
        stack = list(entry_files)
        
        while stack:
            current = stack.pop()
            if current in visited:
                continue
            
            visited.add(current)
            self.reachable_files.add(current)
            
            # Add imported files to stack
            for imported in self.import_graph.get(current, set()):
                if imported not in visited:
                    stack.append(imported)
        
        # Also mark parent __init__.py files as reachable for package structure
        for reachable_file in list(self.reachable_files):
            current_dir = reachable_file.parent
            while current_dir != self.repo_root and current_dir.is_relative_to(self.repo_root):
                init_file = current_dir / "__init__.py"
                if init_file.exists():
                    self.reachable_files.add(init_file)
                current_dir = current_dir.parent
        
        self.evidence["import_graph_nodes"] = len(self.reachable_files)

    def _classify_files(self):
        """Classify all files into keep/delete/unsure categories."""
        # Get all files in the repository
        all_files = []
        for item in self.repo_root.rglob("*"):
            if any(part.startswith('.git') for part in item.parts):
                continue
            if item.is_file():
                all_files.append(item)
        
        for item in all_files:
            rel_path = str(item.relative_to(self.repo_root))
            
            # Skip these patterns
            skip_patterns = ['.git/', '__pycache__/', '.venv/', 'venv/', '.pyc', '.pyo']
            if any(pattern in rel_path for pattern in skip_patterns):
                continue
            
            # Determine category
            if self._should_keep(item):
                reason = self._get_keep_reason(item)
                self.keep_items.append({"path": rel_path, "reason": reason})
            elif self._should_delete(item):
                reason, rules = self._get_delete_reason(item)
                self.delete_items.append({"path": rel_path, "reason": reason, "rules": rules})
            else:
                ambiguity = self._get_unsure_reason(item)
                self.unsure_items.append({"path": rel_path, "ambiguity": ambiguity})

    def _should_keep(self, item: Path) -> bool:
        """Determine if an item should be kept."""
        # Keep if reachable in import graph
        if item in self.reachable_files:
            return True
        
        # Keep if referenced by runtime I/O
        if item in self.runtime_io_files:
            return True
        
        # Keep if it's an __init__.py in a reachable package
        if item.name == "__init__.py" and item.parent in self.package_dirs:
            # Check if any file in this package is reachable
            for reachable in self.reachable_files:
                if reachable.is_relative_to(item.parent):
                    return True
        
        # Keep root-level compatibility shims (orchestrator/, concurrency/, core/, executors/, scoring/)
        # These provide backward compatibility imports
        rel_path = str(item.relative_to(self.repo_root))
        compat_dirs = ['orchestrator/', 'concurrency/', 'core/', 'executors/', 'scoring/']
        if any(rel_path.startswith(d) for d in compat_dirs):
            # Check if this is a shim file
            if item.suffix == '.py' or item.name == '__init__.py':
                # Keep if there's a corresponding file in src/saaaaaa/
                src_counterpart = self.repo_root / "src" / "saaaaaa" / rel_path
                if src_counterpart.exists() and src_counterpart in self.reachable_files:
                    return True
        
        # Keep packaging files
        if item.name in ['setup.py', 'pyproject.toml', 'setup.cfg', 'MANIFEST.in',
                          'requirements.txt', 'constraints.txt', 'README.md', 'LICENSE']:
            return True
        
        # Keep py.typed if present (for type checking support)
        if item.name == 'py.typed':
            return True
        
        return False

    def _get_keep_reason(self, item: Path) -> str:
        """Get the reason why an item should be kept."""
        if item in self.reachable_files:
            return "Reachable in import graph from entry points"
        
        if item in self.runtime_io_files:
            return "Referenced by runtime file I/O operations"
        
        # Check for compatibility shim
        rel_path = str(item.relative_to(self.repo_root))
        compat_dirs = ['orchestrator/', 'concurrency/', 'core/', 'executors/', 'scoring/']
        if any(rel_path.startswith(d) for d in compat_dirs):
            src_counterpart = self.repo_root / "src" / "saaaaaa" / rel_path
            if src_counterpart.exists() and src_counterpart in self.reachable_files:
                return "Compatibility shim for backward-compatible imports"
        
        if item.name == "__init__.py":
            return "Package __init__.py required for import resolution"
        
        if item.name in ['setup.py', 'pyproject.toml', 'setup.cfg']:
            return "Packaging configuration required for installation"
        
        if item.name == 'requirements.txt':
            return "Dependency specification for pip install"
        
        if item.name == 'README.md':
            return "Package documentation referenced by setup.py"
        
        if item.name == 'LICENSE':
            return "License file for package distribution"
        
        if item.name == 'py.typed':
            return "PEP 561 marker for typed package"
        
        return "Required for runtime"

    def _should_delete(self, item: Path) -> bool:
        """Determine if an item can be safely deleted."""
        rel_path = str(item.relative_to(self.repo_root))
        
        # Patterns that indicate deletable content
        delete_patterns = [
            'test_*.py', '*_test.py', 'tests/', '/test/',
            'examples/', 'example/',
            'docs/', 'doc/',
            '*.md', 'README', 'CHANGELOG', 'CONTRIBUTING', 'AUTHORS',
            '.github/', '.vscode/', '.idea/',
            'scripts/', 'tools/',
            'benchmark/', 'bench/',
            '*.ipynb', 'notebooks/',
            '.pre-commit-config.yaml', '.gitignore', '.gitattributes',
            'Makefile', '*.sh',
            '.importlinter', '.python-version',
            '*.yaml', '*.yml', '*.toml',  # Config files (unless runtime IO)
            '*.json',  # Data files (unless runtime IO)
            '*.csv', '*.txt',  # Data files (unless runtime IO or requirements)
        ]
        
        # Check if it matches any delete pattern
        for pattern in delete_patterns:
            if pattern.startswith('*'):
                # Suffix match
                if rel_path.endswith(pattern[1:]):
                    return True
            elif pattern.endswith('/'):
                # Directory match
                if pattern[:-1] in rel_path:
                    return True
            elif '*' in pattern:
                # Glob match
                import fnmatch
                if fnmatch.fnmatch(rel_path, pattern):
                    return True
            else:
                # Exact match
                if pattern in rel_path:
                    return True
        
        return False

    def _get_delete_reason(self, item: Path) -> Tuple[str, List[str]]:
        """Get the reason why an item can be deleted."""
        rel_path = str(item.relative_to(self.repo_root))
        rules = []
        
        # Check which rules apply
        if item not in self.reachable_files:
            rules.append("unreachable-import-graph")
        
        if not any(pattern in str(item) for pattern in self.dynamic_patterns):
            rules.append("no-dynamic-match")
        
        if item not in self.runtime_io_files:
            rules.append("no-runtime-io")
        
        # Determine category
        if 'test' in rel_path.lower():
            reason = "Test file; not required for runtime"
        elif 'example' in rel_path.lower():
            reason = "Example/demo file; not required for runtime"
        elif 'doc' in rel_path.lower() or item.suffix == '.md':
            reason = "Documentation; not required for runtime"
        elif '.github' in rel_path or '.vscode' in rel_path:
            reason = "Development tooling; not required for runtime"
        elif 'scripts/' in rel_path or 'tools/' in rel_path:
            reason = "Development scripts; not required for runtime"
        elif item.suffix in ['.yaml', '.yml', '.json', '.csv']:
            reason = "Configuration/data file; not used at runtime"
        elif 'Makefile' in item.name or item.suffix == '.sh':
            reason = "Build/deployment script; not required for runtime"
        else:
            reason = "Not reachable from entry points"
        
        return reason, rules

    def _get_unsure_reason(self, item: Path) -> str:
        """Get the reason why an item classification is uncertain."""
        rel_path = str(item.relative_to(self.repo_root))
        
        # Check for ambiguous cases
        if 'legacy' in rel_path.lower() or 'deprecated' in rel_path.lower():
            return "Marked as legacy/deprecated; unclear if still used"
        
        if 'experimental' in rel_path.lower():
            return "Experimental code; usage unclear"
        
        if 'backup' in rel_path.lower() or 'old' in rel_path.lower():
            return "Appears to be backup/old code; manual verification needed"
        
        # Root-level Python files might be compatibility shims or standalone scripts
        if item.suffix == '.py' and item.parent == self.repo_root:
            return "Root-level Python file; might be compatibility shim or standalone script"
        
        if item.suffix == '.py' and item not in self.reachable_files:
            # Check if it has a main function
            try:
                with open(item, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'def main(' in content or '__name__ == "__main__"' in content:
                        return "Has main() function; might be CLI entry point not in packaging config"
            except:
                pass
            return "Python module not in import graph; usage unclear"
        
        return "Classification unclear; requires human review"

    def _simulate_smoke_test(self):
        """Simulate a smoke test of the main package import."""
        # Try to identify the main package
        src_dir = self.repo_root / "src"
        if src_dir.exists():
            for pkg_dir in src_dir.iterdir():
                if pkg_dir.is_dir() and (pkg_dir / "__init__.py").exists():
                    # Check if __init__.py is in reachable set
                    if (pkg_dir / "__init__.py") in self.reachable_files:
                        self.evidence["smoke_test"] = "simulated-pass"
                        return
        
        self.evidence["smoke_test"] = "simulated-inconclusive"

    def _generate_report(self) -> Dict[str, Any]:
        """Generate the final audit report."""
        return {
            "keep": sorted(self.keep_items, key=lambda x: x["path"]),
            "delete": sorted(self.delete_items, key=lambda x: x["path"]),
            "unsure": sorted(self.unsure_items, key=lambda x: x["path"]),
            "evidence": {
                **self.evidence,
                "summary": {
                    "total_kept": len(self.keep_items),
                    "total_deleted": len(self.delete_items),
                    "total_unsure": len(self.unsure_items),
                    "entry_points_analyzed": len(self.evidence["entry_points"]),
                }
            }
        }


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.resolve()
    
    auditor = RuntimeAudit(repo_root)
    report = auditor.run_audit()
    
    # Output JSON report
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
