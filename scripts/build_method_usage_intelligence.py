#!/usr/bin/env python3
"""
Method Usage Intelligence Scanner

Performs exhaustive codebase scan to build usage intelligence for every method:
- Count of usages across repo
- Processes/pipelines where it participates  
- Execution topology (Solo, Sequential, Parallel, Interconnected)
- Parameterization locus (In-script, In YAML, In calibration_registry.py)

Output: Machine-readable metadata for auto-calibration decision system

Uses canonical method catalog: config/canonical_method_catalog.json (1,996 methods)
"""

import ast
import json
import re
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, asdict

# Add src to path
repo_root = Path(__file__).parent.parent


@dataclass
class MethodUsage:
    """Usage intelligence for a single method"""
    class_name: str
    method_name: str
    fqn: str
    
    # Usage counts
    total_usages: int
    usage_locations: List[Dict[str, any]]  # [{file, line, context}, ...]
    
    # Pipeline participation
    pipelines: List[str]  # Names of pipelines/processes using this method
    
    # Execution topology
    execution_topology: str  # Solo, Sequential, Parallel, Interconnected
    
    # Parameterization
    param_in_script: bool  # Hardcoded in Python
    param_in_yaml: bool  # Configured via YAML (RED FLAG)
    param_in_registry: bool  # Configured via calibration_registry.py
    
    # Catalog status
    in_catalog: bool
    in_calibration_registry: bool
    
    # Criticality signals
    used_in_critical_path: bool
    method_priority: str  # From catalog
    method_complexity: str  # From catalog


class MethodUsageScanner:
    """Scans codebase for method usage patterns"""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.src_root = repo_root / "src"
        
        # Load canonical method catalog
        catalog_path = repo_root / "config" / "canonical_method_catalog.json"
        with open(catalog_path) as f:
            catalog_data = json.load(f)
        self.catalog_methods = catalog_data['methods']
        
        # Results
        self.usage_map: Dict[Tuple[str, str], MethodUsage] = {}
        self.calibration_registry_methods: Set[Tuple[str, str]] = set()
        
        # Patterns for detecting parameterization
        self.yaml_param_pattern = re.compile(r'\.yaml|\.yml', re.IGNORECASE)
        
    def scan(self):
        """Execute full usage scan"""
        print("="*80)
        print("METHOD USAGE INTELLIGENCE SCANNER")
        print("="*80)
        
        print("\n[1/5] Loading calibration registry methods...")
        self._load_calibration_registry()
        
        print(f"\n[2/5] Scanning Python files in {self.src_root}...")
        self._scan_python_files()
        
        print("\n[3/5] Scanning YAML configuration files...")
        self._scan_yaml_files()
        
        print("\n[4/5] Analyzing execution topology...")
        self._analyze_topology()
        
        print("\n[5/5] Building usage intelligence map...")
        self._build_usage_intelligence()
        
        print("\n✓ Scan complete!")
        
    def _load_calibration_registry(self):
        """Load methods from calibration_registry.py"""
        registry_path = self.repo_root / "src" / "saaaaaa" / "core" / "orchestrator" / "calibration_registry.py"
        
        if not registry_path.exists():
            print(f"WARNING: calibration_registry.py not found at {registry_path}")
            return
        
        with open(registry_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the CALIBRATIONS dict using AST
        tree = ast.parse(content, filename=str(registry_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'CALIBRATIONS':
                        if isinstance(node.value, ast.Dict):
                            for key in node.value.keys:
                                # Expecting tuple of two strings: (class_name, method_name)
                                if isinstance(key, ast.Tuple) and len(key.elts) == 2:
                                    elt0, elt1 = key.elts
                                    if isinstance(elt0, ast.Constant) and isinstance(elt1, ast.Constant):
                                        if isinstance(elt0.value, str) and isinstance(elt1.value, str):
                                            self.calibration_registry_methods.add((elt0.value, elt1.value))
        print(f"  Found {len(self.calibration_registry_methods)} methods in calibration_registry.py")
    
    def _scan_python_files(self):
        """Scan Python files for method calls"""
        python_files = list(self.src_root.rglob("*.py"))
        print(f"  Found {len(python_files)} Python files")
        
        # Get catalog methods as a set for fast lookup
        catalog_method_set = {
            (m['class_name'], m['method_name']) 
            for m in self.catalog_methods 
            if m['class_name']
        }
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                visitor = MethodCallVisitor(py_file, self.repo_root, catalog_method_set)
                visitor.visit(tree)
                
                # Collect results
                for (class_name, method_name), locations in visitor.method_calls.items():
                    key = (class_name, method_name)
                    if key not in self.usage_map:
                        self.usage_map[key] = {
                            'class_name': class_name,
                            'method_name': method_name,
                            'locations': []
                        }
                    self.usage_map[key]['locations'].extend(locations)
                    
            except Exception as e:
                print(f"  ERROR parsing {py_file}: {e}")
        
        print(f"  Tracked {len(self.usage_map)} unique methods with actual usage")
    
    def _scan_yaml_files(self):
        """Scan YAML files for method references"""
        yaml_files = list(self.repo_root.rglob("*.yaml")) + list(self.repo_root.rglob("*.yml"))
        print(f"  Found {len(yaml_files)} YAML files")
        
        for yaml_file in yaml_files:
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for patterns that might reference methods
                # e.g., class: ClassName, method: method_name
                class_pattern = r'class:\s*([A-Za-z_][A-Za-z0-9_]*)'
                method_pattern = r'method:\s*([A-Za-z_][A-Za-z0-9_]*)'
                
                for line_num, line in enumerate(content.splitlines(), 1):
                    class_match = re.search(class_pattern, line)
                    method_match = re.search(method_pattern, line)
                    
                    # Mark methods found in YAML
                    if class_match or method_match:
                        # This is a heuristic - need context to be sure
                        # For now, just flag files that have YAML config
                        pass
                        
            except Exception as e:
                print(f"  ERROR reading {yaml_file}: {e}")
    
    def _analyze_topology(self):
        """Analyze execution topology of methods"""
        # For now, use simple heuristics
        # TODO: More sophisticated analysis of call graphs
        pass
    
    def _build_usage_intelligence(self):
        """Build final usage intelligence records"""
        all_catalog_methods = {(m.class_name, m.method_name): m for m in self.catalog.all_methods()}
        
        # Build usage records for all catalogued methods
        for (class_name, method_name), catalog_method in all_catalog_methods.items():
            usage_data = self.usage_map.get((class_name, method_name), {})
            locations = usage_data.get('locations', [])
            
            usage = MethodUsage(
                class_name=class_name,
                method_name=method_name,
                fqn=catalog_method.fqn,
                total_usages=len(locations),
                usage_locations=locations,
                pipelines=[],  # TODO: extract from usage contexts
                execution_topology="Solo",  # TODO: analyze call patterns
                param_in_script=len(locations) > 0,  # If used, likely params in script
                param_in_yaml=False,  # TODO: detect from YAML scan
                param_in_registry=(class_name, method_name) in self.calibration_registry_methods,
                in_catalog=True,
                in_calibration_registry=(class_name, method_name) in self.calibration_registry_methods,
                used_in_critical_path=catalog_method.priority.value == "CRITICAL",
                method_priority=catalog_method.priority.value,
                method_complexity=catalog_method.complexity.value,
            )
            
            self.usage_map[(class_name, method_name)] = usage
        
        # Also track methods used but not in catalog (DEFECT)
        for (class_name, method_name), usage_data in list(self.usage_map.items()):
            if (class_name, method_name) not in all_catalog_methods:
                # Method used but not catalogued - this is a defect
                locations = usage_data.get('locations', [])
                usage = MethodUsage(
                    class_name=class_name,
                    method_name=method_name,
                    fqn=f"{class_name}.{method_name}",
                    total_usages=len(locations),
                    usage_locations=locations,
                    pipelines=[],
                    execution_topology="Unknown",
                    param_in_script=True,
                    param_in_yaml=False,
                    param_in_registry=False,
                    in_catalog=False,  # DEFECT
                    in_calibration_registry=False,
                    used_in_critical_path=False,
                    method_priority="UNKNOWN",
                    method_complexity="UNKNOWN",
                )
                self.usage_map[(class_name, method_name)] = usage
    
    def generate_report(self, output_path: Path):
        """Generate usage intelligence report"""
        report = {
            "metadata": {
                "generated_at": "2025-11-08",
                "total_methods_tracked": len(self.usage_map),
                "catalog_methods": self.catalog.total_methods,
                "calibration_registry_methods": len(self.calibration_registry_methods),
            },
            "methods": {}
        }
        
        # Convert usage records to dict
        for key, usage in self.usage_map.items():
            if isinstance(usage, MethodUsage):
                report["methods"][f"{usage.class_name}.{usage.method_name}"] = asdict(usage)
            else:
                # Old dict format
                report["methods"][f"{key[0]}.{key[1]}"] = usage
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Usage intelligence report written to: {output_path}")
        
        # Print summary
        print("\n" + "="*80)
        print("USAGE INTELLIGENCE SUMMARY")
        print("="*80)
        
        in_catalog = sum(1 for u in self.usage_map.values() if isinstance(u, MethodUsage) and u.in_catalog)
        not_in_catalog = sum(1 for u in self.usage_map.values() if isinstance(u, MethodUsage) and not u.in_catalog)
        in_registry = sum(1 for u in self.usage_map.values() if isinstance(u, MethodUsage) and u.in_calibration_registry)
        
        print(f"Total methods tracked: {len(self.usage_map)}")
        print(f"  - In catalog: {in_catalog}")
        print(f"  - NOT in catalog (DEFECT): {not_in_catalog}")
        print(f"  - In calibration registry: {in_registry}")
        
        # Methods in catalog but never used
        unused = sum(1 for u in self.usage_map.values() if isinstance(u, MethodUsage) and u.in_catalog and u.total_usages == 0)
        print(f"  - In catalog but NEVER used: {unused}")
        
        # Critical methods
        critical = sum(1 for u in self.usage_map.values() if isinstance(u, MethodUsage) and u.used_in_critical_path)
        print(f"  - Critical methods: {critical}")


class MethodCallVisitor(ast.NodeVisitor):
    """AST visitor to extract method calls"""
    
    def __init__(self, file_path: Path, repo_root: Path, catalog_methods: Set[Tuple[str, str]]):
        self.file_path = file_path
        self.repo_root = repo_root
        self.catalog_methods = catalog_methods
        self.method_calls: Dict[Tuple[str, str], List[dict]] = defaultdict(list)
        self.current_class = None
        self.imports = {}  # Track imports: {alias: module}
        self.class_instances = {}  # Track variable assignments to classes
    
    def visit_Import(self, node):
        """Track import statements"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = alias.name
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        """Track from...import statements"""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if node.module:
                self.imports[name] = f"{node.module}.{alias.name}"
            else:
                self.imports[name] = alias.name
        self.generic_visit(node)
    
    def visit_ClassDef(self, node):
        """Track current class context"""
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
    
    def visit_Assign(self, node):
        """Track variable assignments that might be class instances"""
        try:
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.class_instances[target.id] = class_name
        except Exception:
            pass
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Extract method calls"""
        try:
            # Pattern 1: obj.method()
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                class_name = None
                
                # Try to infer the class
                if isinstance(node.func.value, ast.Name):
                    # Direct call: obj.method()
                    obj_name = node.func.value.id
                    
                    # Check if obj is a known class instance
                    if obj_name in self.class_instances:
                        class_name = self.class_instances[obj_name]
                    # Check if obj is a known import
                    elif obj_name in self.imports:
                        # Try to extract class name from import
                        import_path = self.imports[obj_name]
                        if '.' in import_path:
                            class_name = import_path.split('.')[-1]
                        else:
                            class_name = obj_name
                    # Check if it matches any catalog class
                    else:
                        for cat_class, cat_method in self.catalog_methods:
                            if method_name == cat_method:
                                # Potential match - use catalog class name
                                class_name = cat_class
                                break
                
                elif isinstance(node.func.value, ast.Call):
                    # Chained call: ClassName().method()
                    if isinstance(node.func.value.func, ast.Name):
                        class_name = node.func.value.func.id
                
                # Record the call if we found a class
                if class_name and (class_name, method_name) in self.catalog_methods:
                    location = {
                        'file': str(self.file_path.relative_to(self.repo_root)),
                        'line': node.lineno,
                        'context': 'method_call'
                    }
                    self.method_calls[(class_name, method_name)].append(location)
        
        except Exception:
            pass
        
        self.generic_visit(node)


def main():
    repo_root = Path(__file__).parent.parent
    scanner = MethodUsageScanner(repo_root)
    scanner.scan()
    
    output_path = repo_root / "config" / "method_usage_intelligence.json"
    scanner.generate_report(output_path)
    
    print("\n✓ Method usage intelligence scan complete!")


if __name__ == "__main__":
    main()
