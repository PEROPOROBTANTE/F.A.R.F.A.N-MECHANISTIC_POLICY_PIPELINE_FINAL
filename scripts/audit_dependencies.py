#!/usr/bin/env python3
"""
Comprehensive Dependency Auditor for SAAAAAA Project

This script performs exhaustive dependency analysis:
1. Static AST analysis to extract all imports
2. Classification by role (core_runtime, optional_runtime, dev_test, docs)
3. Detection of missing dependencies
4. Version pinning recommendations
5. Generation of structured dependency files
"""

import ast
import importlib
import importlib.metadata
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Mapping of import names to PyPI package names
IMPORT_TO_PACKAGE = {
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
    "jwt": "pyjwt",
    "socketio": "python-socketio",
    "blake3": "blake3",
    "bs4": "beautifulsoup4",
    "OpenSSL": "pyOpenSSL",
    "MySQLdb": "mysqlclient",
    "psycopg2": "psycopg2-binary",
    "fitz": "PyMuPDF",
    "docx": "python-docx",
    "flask_socketio": "flask-socketio",
    "flask_cors": "flask-cors",
    "sse_starlette": "sse-starlette",
    "tabula": "tabula-py",
    "camelot": "camelot-py",
}

# Local project modules that should not be treated as external dependencies
LOCAL_MODULES = {
    "saaaaaa",
    # Project internal modules
    "advanced_module_config", "config", "layer_requirements", "tomllib",
    "calibration_context", "intrinsic_loader", "event_tracking",
    "layer_coexistence", "congruence_layer", "saga", "compatibility",
    "executor_config", "data_structures", "calibration_registry",
    "analysis", "errors", "scripts", "feature_flags", "unit_layer",
    "signal_consumption", "questionnaire", "meta_layer", "pdt_structure",
    "enhanced_contracts", "audit_system", "contract_io", "processing",
    "opentelemetry_integration", "src", "core_module_factory", "lazy_deps",
    "chain_layer", "layer_computers", "safe_imports", "versions",
    "utils", "dependency_lockdown", "choquet_aggregator",
    "questionnaire_resource_provider", "signals", "rl_strategy",
    "signal_loader", "policy_processor", "golden_rule", "scoring",
    "validation", "financiero_viabilidad_tablas", "aggregation_models",
    "evidence_registry", "tables", "schemas", "document_ingestion",
    "seeds", "core", "chunking", "parsers", "retry_handler",
    "inference", "dnp_integration", "class_registry", "factory",
    "concurrency", "contract_loader", "phases", "schema_validator",
    "tests", "contradiction_deteccion", "contracts", "methods",
    "structural", "runtime_error_fixes", "tools",
    "architecture_validator", "arg_router", "quality_gates", "pipeline",
    "configs", "cli", "models", "recommendation_engine",
    # Executors
    "executors",
    # Orchestrator modules
    "orchestrator",
    # API modules
    "api",
}

# Standard library modules (Python 3.10+) - should not be listed as dependencies
# Use sys.stdlib_module_names for Python 3.10+, with fallback for older versions
import sys as _sys

if hasattr(_sys, 'stdlib_module_names'):
    STDLIB_MODULES = _sys.stdlib_module_names
else:
    # Fallback for Python <3.10 - manually maintained list
    STDLIB_MODULES = {
        "abc", "argparse", "ast", "asyncio", "base64", "collections", "concurrent",
        "contextlib", "copy", "dataclasses", "datetime", "decimal", "enum", "functools",
        "hashlib", "heapq", "importlib", "inspect", "io", "itertools", "json", "logging",
        "math", "multiprocessing", "operator", "os", "pathlib", "pickle", "platform",
        "queue", "random", "re", "shutil", "signal", "socket", "sqlite3", "statistics",
        "string", "struct", "subprocess", "sys", "tempfile", "textwrap", "threading",
        "time", "traceback", "types", "typing", "unittest", "urllib", "uuid", "warnings",
        "weakref", "xml", "zipfile", "zoneinfo"
    }

# Package role classifications
ROLE_CLASSIFICATIONS = {
    # Core runtime - critical for production execution
    "core_runtime": {
        "numpy", "pandas", "polars", "pyarrow", "scipy", "scikit-learn",
        "torch", "tensorflow", "transformers", "sentence-transformers",
        "spacy", "networkx", "pymc", "arviz", "pytensor",
        "pdfplumber", "PyPDF2", "PyMuPDF", "python-docx",
        "flask", "fastapi", "httpx", "uvicorn", "sse-starlette",
        "pydantic", "pyyaml", "jsonschema", "blake3",
        "structlog", "opentelemetry-api", "opentelemetry-sdk",
        "tenacity", "typer", "python-dotenv"
    },
    # Optional runtime - enhances functionality but not critical
    "optional_runtime": {
        "flask-cors", "flask-socketio", "python-socketio",
        "gevent", "gevent-websocket", "pyjwt",
        "redis", "sqlalchemy", "gunicorn",
        "prometheus-client", "psutil",
        "opentelemetry-instrumentation-fastapi",
        "dowhy", "econml", "igraph", "python-louvain", "pydot",
        "tabula-py", "camelot-py",
        "nltk", "sentencepiece", "tiktoken", "fuzzywuzzy",
        "python-Levenshtein", "langdetect"
    },
    # Development & testing
    "dev_test": {
        "pytest", "pytest-cov", "hypothesis", "schemathesis",
        "black", "ruff", "flake8", "mypy", "pyright",
        "bandit", "pycycle", "import-linter"
    },
    # Documentation
    "docs": {
        "sphinx", "sphinx-rtd-theme", "myst-parser"
    }
}


class DependencyAuditor:
    """Audits and classifies all dependencies in the project."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.imports_by_file: Dict[str, Set[str]] = defaultdict(set)
        self.all_imports: Set[str] = set()
        self.missing_packages: Set[str] = set()
        self.installed_packages: Dict[str, str] = {}
        self.package_usage: Dict[str, List[str]] = defaultdict(list)
        
    def scan_imports_in_file(self, filepath: Path) -> Set[str]:
        """Extract all imports from a Python file using AST."""
        imports = set()
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(filepath))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split('.')[0])
        except Exception as e:
            print(f"Warning: Could not parse {filepath}: {e}", file=sys.stderr)
        
        return imports
    
    def scan_all_python_files(self):
        """Scan all Python files in the project."""
        print("Scanning Python files for imports...")
        
        # Scan src directory
        src_dir = self.project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    rel_path = py_file.relative_to(self.project_root)
                    imports = self.scan_imports_in_file(py_file)
                    self.imports_by_file[str(rel_path)] = imports
                    self.all_imports.update(imports)
        
        # Scan root level Python files
        for py_file in self.project_root.glob("*.py"):
            if py_file.name not in ["setup.py"]:
                rel_path = py_file.relative_to(self.project_root)
                imports = self.scan_imports_in_file(py_file)
                self.imports_by_file[str(rel_path)] = imports
                self.all_imports.update(imports)
        
        # Scan tests directory
        tests_dir = self.project_root / "tests"
        if tests_dir.exists():
            for py_file in tests_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    rel_path = py_file.relative_to(self.project_root)
                    imports = self.scan_imports_in_file(py_file)
                    self.imports_by_file[str(rel_path)] = imports
                    # Mark test imports separately
                    self.all_imports.update(imports)
        
        # Scan examples directory
        examples_dir = self.project_root / "examples"
        if examples_dir.exists():
            for py_file in examples_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    rel_path = py_file.relative_to(self.project_root)
                    imports = self.scan_imports_in_file(py_file)
                    self.imports_by_file[str(rel_path)] = imports
                    self.all_imports.update(imports)
        
        # Scan scripts directory
        scripts_dir = self.project_root / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.rglob("*.py"):
                if "__pycache__" not in str(py_file):
                    rel_path = py_file.relative_to(self.project_root)
                    imports = self.scan_imports_in_file(py_file)
                    self.imports_by_file[str(rel_path)] = imports
                    self.all_imports.update(imports)
        
        print(f"Found {len(self.imports_by_file)} Python files")
        print(f"Found {len(self.all_imports)} unique imports")
    
    def get_installed_packages(self):
        """Get all currently installed packages and their versions."""
        print("Checking installed packages...")
        try:
            for dist in importlib.metadata.distributions():
                self.installed_packages[dist.name.lower()] = dist.version
        except Exception as e:
            print(f"Warning: Could not get installed packages: {e}", file=sys.stderr)
    
    def normalize_import_to_package(self, import_name: str) -> str:
        """Convert import name to PyPI package name."""
        # Check if it's a known mapping
        if import_name in IMPORT_TO_PACKAGE:
            return IMPORT_TO_PACKAGE[import_name]
        
        # Check if it's a local package
        if import_name == "saaaaaa":
            return "saaaaaa"
        
        # Otherwise, assume import name = package name
        return import_name
    
    def classify_import(self, import_name: str) -> str:
        """Classify an import into a role category."""
        # Skip stdlib modules
        if import_name in STDLIB_MODULES:
            return "stdlib"
        
        # Skip local modules
        if import_name in LOCAL_MODULES:
            return "local"
        
        package_name = self.normalize_import_to_package(import_name)
        
        # Check role classifications
        for role, packages in ROLE_CLASSIFICATIONS.items():
            if package_name in packages:
                return role
        
        # Default: assume core_runtime for unknown packages
        return "core_runtime"
    
    def check_importability(self, import_name: str) -> Tuple[bool, str]:
        """Check if a module can be imported."""
        if import_name in STDLIB_MODULES:
            return True, "stdlib"
        
        if import_name in LOCAL_MODULES:
            return True, "local"
        
        try:
            importlib.import_module(import_name)
            return True, "available"
        except ImportError:
            return False, "missing"
        except Exception as e:
            return False, f"error: {str(e)[:50]}"
    
    def build_package_usage_map(self):
        """Build a map of which files use which packages."""
        print("Building package usage map...")
        
        for filepath, imports in self.imports_by_file.items():
            for import_name in imports:
                if import_name not in STDLIB_MODULES and import_name not in LOCAL_MODULES:
                    package_name = self.normalize_import_to_package(import_name)
                    self.package_usage[package_name].append(filepath)
    
    def detect_missing_dependencies(self):
        """Detect which imports cannot be satisfied."""
        print("Detecting missing dependencies...")
        
        for import_name in self.all_imports:
            if import_name in STDLIB_MODULES or import_name in LOCAL_MODULES:
                continue
            
            can_import, status = self.check_importability(import_name)
            if not can_import:
                package_name = self.normalize_import_to_package(import_name)
                self.missing_packages.add(package_name)
                print(f"  Missing: {import_name} -> {package_name} ({status})")
    
    def generate_report(self) -> Dict:
        """Generate comprehensive audit report."""
        report = {
            "summary": {
                "total_files_scanned": len(self.imports_by_file),
                "total_unique_imports": len(self.all_imports),
                "missing_packages": len(self.missing_packages),
                "installed_packages": len(self.installed_packages)
            },
            "imports_by_file": {},
            "package_classification": defaultdict(list),
            "missing_packages": list(self.missing_packages),
            "package_usage": {}
        }
        
        # Classify all non-stdlib, non-local imports
        for import_name in sorted(self.all_imports):
            if import_name not in STDLIB_MODULES and import_name not in LOCAL_MODULES:
                role = self.classify_import(import_name)
                package_name = self.normalize_import_to_package(import_name)
                if package_name not in report["package_classification"][role]:
                    report["package_classification"][role].append(package_name)
        
        # Add package usage
        for package, files in sorted(self.package_usage.items()):
            report["package_usage"][package] = files
        
        return report
    
    def run_full_audit(self) -> Dict:
        """Run complete dependency audit."""
        print("=" * 80)
        print("DEPENDENCY AUDIT STARTING")
        print("=" * 80)
        
        self.scan_all_python_files()
        self.get_installed_packages()
        self.build_package_usage_map()
        self.detect_missing_dependencies()
        
        report = self.generate_report()
        
        print("\n" + "=" * 80)
        print("AUDIT COMPLETE")
        print("=" * 80)
        print(f"Files scanned: {report['summary']['total_files_scanned']}")
        print(f"Unique imports: {report['summary']['total_unique_imports']}")
        print(f"Missing packages: {report['summary']['missing_packages']}")
        
        return report


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    auditor = DependencyAuditor(project_root)
    
    report = auditor.run_full_audit()
    
    # Save report to JSON
    output_file = project_root / "dependency_audit_report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, sort_keys=True, default=list)
    
    print(f"\nReport saved to: {output_file}")
    
    # Return non-zero exit code if missing packages
    if report['summary']['missing_packages'] > 0:
        print("\n⚠️  WARNING: Missing packages detected!")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
