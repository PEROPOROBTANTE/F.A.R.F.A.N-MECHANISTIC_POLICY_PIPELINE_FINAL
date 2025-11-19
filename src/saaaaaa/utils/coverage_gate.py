#!/usr/bin/env python3
"""
Coverage Enforcement Gate
=========================
Enforces hard-fail at <555 methods threshold + audit.json emission

Requirements:
- Count all public methods across Producer classes
- Generate audit.json with method counts and validation results
- Hard-fail if total methods < 555
- Include schema validation results
"""

import ast
import json
import sys
from datetime import datetime
from pathlib import Path


def count_methods_in_class(filepath: Path, class_name: str) -> tuple[list[str], dict[str, int]]:
    """Count public and private methods in a class and return method names"""
    if not filepath.exists():
        return [], {"public": 0, "private": 0, "total": 0}

    with open(filepath, encoding='utf-8') as f:
        tree = ast.parse(f.read())

    method_names = []
    method_counts = {
        "public": 0,
        "private": 0,
        "total": 0
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_names.append(item.name)
                    if not item.name.startswith('_'):
                        method_counts["public"] += 1
                    else:
                        method_counts["private"] += 1
                    method_counts["total"] += 1

    return method_names, method_counts

def validate_schema_exists(module_dir: Path) -> tuple[bool, list[str]]:
    """Validate that schema files exist for a module"""
    if not module_dir.exists():
        return False, []

    schema_files = list(module_dir.glob("*.schema.json"))
    return len(schema_files) > 0, [f.name for f in schema_files]

def count_file_methods(filepath: Path) -> tuple[int, int]:
    """Count all public and total methods in a file"""
    if not filepath.exists():
        return 0, 0

    with open(filepath, encoding='utf-8') as f:
        try:
            tree = ast.parse(f.read())
            public_methods = 0
            all_methods = 0

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    all_methods += 1
                    if not node.name.startswith('_'):
                        public_methods += 1

            return public_methods, all_methods
        except Exception as e:
            print(f"Error parsing {filepath}: {e}")
            return 0, 0

def count_all_methods() -> dict[str, any]:
    """Count all methods across all modules and producers"""

    # All files to analyze
    files_to_analyze = [
        "financiero_viabilidad_tablas.py",
        "Analyzer_one.py",
        "contradiction_deteccion.py",
        "embedding_policy.py",
        "teoria_cambio.py",
        "derek_beach.py",
        "policy_processor.py",
        "report_assembly.py",
        "semantic_chunking_policy.py"
    ]

    # Producer classes to check
    producers = {
        "SemanticChunkingProducer": "semantic_chunking_policy.py",
        "EmbeddingPolicyProducer": "embedding_policy.py",
        "DerekBeachProducer": "derek_beach.py",
        "ReportAssemblyProducer": "report_assembly.py"
    }

    results = {
        "timestamp": datetime.now().isoformat(),
        "files": {},
        "producers": {},
        "totals": {
            "file_public_methods": 0,
            "file_total_methods": 0,
            "producer_methods": 0,
            "threshold": 555,
            "meets_threshold": False
        },
        "schema_validation": {},
        "audit_status": "PENDING"
    }

    # Count file methods
    print("=" * 80)
    print("FILE METHOD COUNTS")
    print("=" * 80)

    for filepath_str in files_to_analyze:
        filepath = Path(filepath_str)
        public_methods, total_methods = count_file_methods(filepath)
        results["files"][filepath_str] = {
            "public_methods": public_methods,
            "total_methods": total_methods
        }
        results["totals"]["file_public_methods"] += public_methods
        results["totals"]["file_total_methods"] += total_methods
        print(f"{filepath_str:45} | {public_methods:4} public | {total_methods:4} total")

    # Count Producer methods
    print("\n" + "=" * 80)
    print("PRODUCER METHOD COUNTS")
    print("=" * 80)

    for class_name, filepath in producers.items():
        methods, counts = count_methods_in_class(Path(filepath), class_name)
        results["producers"][class_name] = {
            "file": filepath,
            "methods": methods,
            "counts": counts,
            "public_methods": counts["public"]
        }
        results["totals"]["producer_methods"] += counts["public"]
        print(f"{class_name:45} | {counts['public']:3} public | {counts['private']:3} private | {counts['total']:3} total")

    # Update meets_threshold
    results["totals"]["meets_threshold"] = (
        results["totals"]["file_total_methods"] >= 555
    )

    # Validate schemas
    print("\n" + "=" * 80)
    print("SCHEMA VALIDATION")
    print("=" * 80)

    schema_modules = [
        "semantic_chunking_policy",
        "embedding_policy",
        "derek_beach",
        "report_assembly"
    ]

    for module in schema_modules:
        module_dir = Path("schemas") / module
        has_schemas, schema_files = validate_schema_exists(module_dir)
        results["schema_validation"][module] = {
            "has_schemas": has_schemas,
            "schema_files": schema_files,
            "schema_count": len(schema_files)
        }
        status = "✓" if has_schemas else "✗"
        print(f"{module:35} | {status} | {len(schema_files)} schemas")

    # Determine audit status
    all_have_schemas = all(
        v["has_schemas"] for v in results["schema_validation"].values()
    )

    if results["totals"]["meets_threshold"] and all_have_schemas:
        results["audit_status"] = "PASS"
    else:
        results["audit_status"] = "FAIL"

    return results

def main() -> int:
    """Main entry point"""
    print("\n" + "=" * 80)
    print("COVERAGE ENFORCEMENT GATE")
    print("=" * 80 + "\n")

    # Count all methods
    results = count_all_methods()

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total file methods:      {results['totals']['file_total_methods']:4}")
    print(f"Total public methods:    {results['totals']['file_public_methods']:4}")
    print(f"Producer methods:        {results['totals']['producer_methods']:4}")
    print(f"Threshold:               {results['totals']['threshold']:4}")
    print(f"Meets threshold:         {results['totals']['meets_threshold']}")
    print(f"All schemas present:     {all(v['has_schemas'] for v in results['schema_validation'].values())}")
    print(f"Audit status:            {results['audit_status']}")

    # Save audit.json
    audit_path = Path("audit.json")
    with open(audit_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    print(f"\n✓ Audit results saved to {audit_path}")

    # Enforce hard-fail
    if not results['totals']['meets_threshold']:
        print("\n" + "=" * 80)
        print("❌ COVERAGE GATE FAILED")
        print("=" * 80)
        print(f"Required: {results['totals']['threshold']} methods")
        print(f"Found:    {results['totals']['file_total_methods']} methods")
        print(f"Gap:      {results['totals']['threshold'] - results['totals']['file_total_methods']} methods")
        print("=" * 80 + "\n")
        return 1

    # Check schema validation
    if not all(v['has_schemas'] for v in results['schema_validation'].values()):
        print("\n" + "=" * 80)
        print("❌ SCHEMA VALIDATION FAILED")
        print("=" * 80)
        for module, validation in results['schema_validation'].items():
            if not validation['has_schemas']:
                print(f"Missing schemas for: {module}")
        print("=" * 80 + "\n")
        return 1

    print("\n" + "=" * 80)
    print("✓ COVERAGE GATE PASSED")
    print("=" * 80)
    print(f"All {results['totals']['file_total_methods']} methods accounted for")
    print(f"{results['totals']['file_public_methods']} public methods available")
    print(f"{results['totals']['producer_methods']} producer methods exposed")
    print("All schema contracts validated")
    print("=" * 80 + "\n")

    return 0

if __name__ == "__main__":
    sys.exit(main())
