#!/usr/bin/env python3
"""
Import System Forensic Audit Tool
Comprehensive import analysis and pathology detection
"""

import ast
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
import re

class ImportAuditor:
    def __init__(self, root_path: Path):
        self.root = root_path
        self.results = {
            "total_files": 0,
            "total_imports": 0,
            "imports_by_type": defaultdict(int),
            "imports_by_file": {},
            "pathologies": {
                "CRITICAL": [],
                "HIGH": [],
                "MEDIUM": [],
                "LOW": []
            },
            "metrics": {
                "circular_dependency_count": 0,
                "phantom_import_count": 0,
                "star_import_count": 0,
                "unused_import_count": 0
            }
        }
        self.import_graph = defaultdict(set)
        self.module_to_file = {}
        
    def scan_file(self, file_path: Path) -> Dict:
        """Extract all imports from a Python file using AST"""
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content, filename=str(file_path))
        except Exception as e:
            return {"error": str(e), "imports": []}
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "absolute",
                        "module": alias.name,
                        "names": [alias.asname or alias.name],
                        "line": node.lineno,
                        "is_star": False
                    })
                    self.results["imports_by_type"]["absolute"] += 1
                    
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                is_star = any(alias.name == '*' for alias in node.names)
                names = [alias.name for alias in node.names]
                
                import_type = "relative" if node.level > 0 else "absolute"
                if is_star:
                    self.results["pathologies"]["HIGH"].append({
                        "type": "star_import",
                        "file": str(file_path.relative_to(self.root)),
                        "line": node.lineno,
                        "module": module,
                        "severity": 7
                    })
                    self.results["metrics"]["star_import_count"] += 1
                
                imports.append({
                    "type": import_type,
                    "module": module,
                    "names": names,
                    "line": node.lineno,
                    "level": node.level,
                    "is_star": is_star
                })
                self.results["imports_by_type"][import_type] += 1
        
        return {"imports": imports, "error": None}
    
    def scan_all_files(self):
        """Scan all Python files in the repository"""
        py_files = list(self.root.rglob("*.py"))
        self.results["total_files"] = len(py_files)
        
        for py_file in py_files:
            rel_path = str(py_file.relative_to(self.root))
            scan_result = self.scan_file(py_file)
            
            if scan_result["error"]:
                self.results["pathologies"]["MEDIUM"].append({
                    "type": "parse_error",
                    "file": rel_path,
                    "error": scan_result["error"],
                    "severity": 5
                })
                continue
            
            imports = scan_result["imports"]
            self.results["total_imports"] += len(imports)
            self.results["imports_by_file"][rel_path] = imports
            
            # Build import graph
            module_name = self._file_to_module(py_file)
            self.module_to_file[module_name] = rel_path
            
            for imp in imports:
                target_module = imp["module"]
                if target_module:
                    self.import_graph[module_name].add(target_module)
    
    def _file_to_module(self, file_path: Path) -> str:
        """Convert file path to Python module name"""
        try:
            rel_path = file_path.relative_to(self.root)
            parts = list(rel_path.parts)
            
            # Remove src/ if present
            if parts and parts[0] == 'src':
                parts = parts[1:]
            
            # Remove .py extension
            if parts[-1].endswith('.py'):
                parts[-1] = parts[-1][:-3]
            
            # Remove __init__
            if parts[-1] == '__init__':
                parts = parts[:-1]
            
            return '.'.join(parts) if parts else ''
        except:
            return str(file_path)
    
    def detect_circular_dependencies(self):
        """Detect circular import dependencies using DFS"""
        def dfs(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.import_graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, visited, rec_stack, path[:])
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]
            
            rec_stack.remove(node)
            return None
        
        visited = set()
        cycles = []
        
        for node in self.import_graph:
            if node not in visited:
                cycle = dfs(node, visited, set(), [])
                if cycle and cycle not in cycles:
                    cycles.append(cycle)
                    self.results["pathologies"]["CRITICAL"].append({
                        "type": "circular_dependency",
                        "cycle": cycle,
                        "severity": 10
                    })
        
        self.results["metrics"]["circular_dependency_count"] = len(cycles)
        return cycles
    
    def detect_phantom_imports(self):
        """Detect imports that don't resolve to actual modules"""
        phantom_count = 0
        
        for file_path, imports in self.results["imports_by_file"].items():
            for imp in imports:
                module = imp["module"]
                if not module:
                    continue
                
                # Check if it's a standard library module
                if self._is_stdlib_module(module):
                    continue
                
                # Check if it's an installed package
                if self._is_installed_package(module.split('.')[0]):
                    continue
                
                # Check if it's a local module
                if not self._is_local_module(module):
                    self.results["pathologies"]["CRITICAL"].append({
                        "type": "phantom_import",
                        "file": file_path,
                        "line": imp["line"],
                        "module": module,
                        "severity": 10
                    })
                    phantom_count += 1
        
        self.results["metrics"]["phantom_import_count"] = phantom_count
    
    def _is_stdlib_module(self, module: str) -> bool:
        """Check if module is from standard library"""
        stdlib_modules = {
            'os', 'sys', 'json', 're', 'ast', 'pathlib', 'typing', 'collections',
            'itertools', 'functools', 'datetime', 'time', 'math', 'random',
            'subprocess', 'threading', 'multiprocessing', 'asyncio', 'logging',
            'unittest', 'pytest', 'dataclasses', 'enum', 'abc', 'copy', 'io'
        }
        return module.split('.')[0] in stdlib_modules
    
    def _is_installed_package(self, package: str) -> bool:
        """Check if package is installed using find_spec (no import side effects)"""
        try:
            import importlib.util
            spec = importlib.util.find_spec(package)
            return spec is not None
        except (ImportError, ValueError, AttributeError):
            return False
    
    def _is_local_module(self, module: str) -> bool:
        """Check if module exists locally"""
        # Check in module_to_file mapping
        if module in self.module_to_file:
            return True
        
        # Check for partial matches (parent packages)
        for known_module in self.module_to_file:
            if known_module.startswith(module + '.'):
                return True
        
        return False
    
    def generate_report(self) -> Dict:
        """Generate final audit report"""
        # Sort pathologies by severity
        for severity in self.results["pathologies"]:
            self.results["pathologies"][severity].sort(
                key=lambda x: x.get("severity", 0), 
                reverse=True
            )
        
        self.results["imports_by_type"] = dict(self.results["imports_by_type"])
        
        return self.results
    
    def save_report(self, output_path: Path):
        """Save audit report to JSON file"""
        report = self.generate_report()
        
        # Convert summary for readability
        summary = {
            "audit_timestamp": "2025-11-28T15:03:00Z",
            "total_files_scanned": report["total_files"],
            "total_imports": report["total_imports"],
            "imports_by_type": report["imports_by_type"],
            "pathology_counts": {
                severity: len(items) 
                for severity, items in report["pathologies"].items()
            },
            "metrics": report["metrics"]
        }
        
        full_report = {
            "summary": summary,
            "pathologies": report["pathologies"],
            "detailed_imports": report["imports_by_file"]
        }
        
        output_path.write_text(json.dumps(full_report, indent=2))
        return full_report


def main():
    repo_root = Path("/home/recovered/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/src/saaaaaa")
    
    print("Starting Import System Forensic Audit...")
    print(f"Scanning: {repo_root}")
    print("=" * 80)
    
    auditor = ImportAuditor(repo_root)
    
    # Phase 1.1: Complete Import Inventory
    print("\n[Phase 1.1] Scanning all Python files...")
    auditor.scan_all_files()
    print(f"✓ Files scanned: {auditor.results['total_files']}")
    print(f"✓ Total imports found: {auditor.results['total_imports']}")
    
    # Phase 1.2: Pathology Detection
    print("\n[Phase 1.2] Detecting import pathologies...")
    
    print("  → Detecting circular dependencies...")
    cycles = auditor.detect_circular_dependencies()
    print(f"    Found {len(cycles)} circular dependency chains")
    
    print("  → Detecting phantom imports...")
    auditor.detect_phantom_imports()
    print(f"    Found {auditor.results['metrics']['phantom_import_count']} phantom imports")
    
    print(f"  → Found {auditor.results['metrics']['star_import_count']} star imports")
    
    # Generate and save report
    output_path = Path("/home/recovered/F.A.R.F.A.N-MECHANISTIC_POLICY_PIPELINE_FINAL/import_audit_report.json")
    report = auditor.save_report(output_path)
    
    print(f"\n✓ Audit report saved to: {output_path}")
    print("\n" + "=" * 80)
    print("PATHOLOGY SUMMARY:")
    print("=" * 80)
    
    for severity, pathologies in report["pathologies"].items():
        if pathologies:
            print(f"\n{severity}: {len(pathologies)} issues")
            for i, p in enumerate(pathologies[:5], 1):  # Show first 5
                print(f"  {i}. {p['type']}: {p.get('file', p.get('cycle', 'N/A'))}")
            if len(pathologies) > 5:
                print(f"  ... and {len(pathologies) - 5} more")
    
    print("\n" + "=" * 80)
    print(f"Total pathologies found: {sum(len(p) for p in report['pathologies'].values())}")
    
    return 0 if sum(len(p) for p in report["pathologies"]["CRITICAL"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
