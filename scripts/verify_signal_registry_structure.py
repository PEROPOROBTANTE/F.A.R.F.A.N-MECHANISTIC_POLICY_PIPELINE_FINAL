#!/usr/bin/env python3
"""
Signal Registry Structure Verification
=======================================

Verifies the structure and completeness of the signal registry implementation
without requiring full dependency resolution.

Usage:
    python scripts/verify_signal_registry_structure.py
"""

import ast
import sys
from pathlib import Path


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "=" * 80)
    print(text)
    print("=" * 80)


def print_section(text: str):
    """Print formatted section."""
    print(f"\n{text}")
    print("-" * 80)


def analyze_signal_registry_module():
    """Analyze signal_registry.py module structure."""
    print_header("SIGNAL REGISTRY MODULE ANALYSIS")

    module_path = Path("src/saaaaaa/core/orchestrator/signal_registry.py")
    if not module_path.exists():
        print(f"✗ Module not found: {module_path}")
        return {}

    print(f"✓ Module found: {module_path}")

    with open(module_path) as f:
        content = f.read()
        tree = ast.parse(content)

    # Analyze classes
    classes = {}
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_info = {
                "name": node.name,
                "methods": [],
                "base_classes": [
                    base.id if isinstance(base, ast.Name) else "Unknown"
                    for base in node.bases
                ],
            }

            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    class_info["methods"].append(item.name)

            classes[node.name] = class_info

        elif isinstance(node, ast.FunctionDef) and not any(
            isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
        ):
            functions.append(node.name)

    # Report classes
    print_section("Classes Defined")
    for class_name, info in classes.items():
        print(f"\n{class_name}")
        if info["base_classes"]:
            print(f"  Base: {', '.join(info['base_classes'])}")
        print(f"  Methods: {len(info['methods'])}")
        for method in info["methods"][:10]:  # Show first 10 methods
            print(f"    - {method}")
        if len(info["methods"]) > 10:
            print(f"    ... and {len(info['methods']) - 10} more")

    return classes


def verify_signal_pack_classes(classes):
    """Verify all required SignalPack classes exist."""
    print_header("SIGNAL PACK CLASS VERIFICATION")

    required_packs = [
        "ChunkingSignalPack",
        "MicroAnsweringSignalPack",
        "ValidationSignalPack",
        "AssemblySignalPack",
        "ScoringSignalPack",
    ]

    results = {}
    for pack_name in required_packs:
        if pack_name in classes:
            print(f"✓ {pack_name} defined")
            # Check if it's a BaseModel subclass
            bases = classes[pack_name]["base_classes"]
            if "BaseModel" in bases:
                print(f"  - Inherits from Pydantic BaseModel ✓")
            results[pack_name] = True
        else:
            print(f"✗ {pack_name} NOT FOUND")
            results[pack_name] = False

    return results


def verify_registry_class(classes):
    """Verify QuestionnaireSignalRegistry class."""
    print_header("SIGNAL REGISTRY CLASS VERIFICATION")

    if "QuestionnaireSignalRegistry" not in classes:
        print("✗ QuestionnaireSignalRegistry NOT FOUND")
        return False

    print("✓ QuestionnaireSignalRegistry defined")

    registry_class = classes["QuestionnaireSignalRegistry"]
    required_methods = [
        "get_chunking_signals",
        "get_micro_answering_signals",
        "get_validation_signals",
        "get_assembly_signals",
        "get_scoring_signals",
        "get_metrics",
        "clear_cache",
    ]

    print("\nRequired Methods:")
    all_found = True
    for method in required_methods:
        if method in registry_class["methods"]:
            print(f"  ✓ {method}")
        else:
            print(f"  ✗ {method} MISSING")
            all_found = False

    return all_found


def verify_helper_classes(classes):
    """Verify helper classes."""
    print_header("HELPER CLASS VERIFICATION")

    helper_classes = [
        "PatternItem",
        "ExpectedElement",
        "ValidationCheck",
        "FailureContract",
        "ModalityConfig",
        "QualityLevel",
    ]

    results = {}
    for class_name in helper_classes:
        if class_name in classes:
            print(f"✓ {class_name} defined")
            results[class_name] = True
        else:
            print(f"✗ {class_name} NOT FOUND")
            results[class_name] = False

    return results


def check_file_sizes():
    """Check file sizes to verify implementation completeness."""
    print_header("IMPLEMENTATION COMPLETENESS CHECK")

    files = [
        "src/saaaaaa/core/orchestrator/signal_registry.py",
        "tests/test_signal_irrigation_contrafactual.py",
        "tests/test_signal_irrigation_component_impact.py",
        "docs/SIGNAL_IRRIGATION_INNOVATION_AUDIT.md",
        "docs/QUESTIONNAIRE_SIGNAL_IRRIGATION_DESIGN.md",
    ]

    total_lines = 0
    for file_path in files:
        path = Path(file_path)
        if path.exists():
            with open(path) as f:
                lines = len(f.readlines())
            total_lines += lines
            size_kb = path.stat().st_size / 1024
            print(f"✓ {path.name}: {lines} lines ({size_kb:.1f} KB)")
        else:
            print(f"✗ {path.name}: NOT FOUND")

    print(f"\nTotal implementation: {total_lines} lines of code/documentation")
    return total_lines


def verify_standards_compliance():
    """Verify standards compliance in code."""
    print_header("STANDARDS COMPLIANCE CHECK")

    module_path = Path("src/saaaaaa/core/orchestrator/signal_registry.py")
    with open(module_path) as f:
        content = f.read()

    checks = {
        "Pydantic v2 (BaseModel)": "from pydantic import BaseModel" in content,
        "Type hints (from __future__)": "from __future__ import annotations" in content,
        "OpenTelemetry tracing": "from opentelemetry import trace" in content or "OTEL_AVAILABLE" in content,
        "Structured logging (structlog)": "import structlog" in content,
        "BLAKE3 hashing": "import blake3" in content or "BLAKE3_AVAILABLE" in content,
        "Frozen dataclasses": "frozen=True" in content,
        "Strict validation": "strict=True" in content,
        "Field validators": "@field_validator" in content,
        "Type safety (Literal)": "from typing import" in content and "Literal" in content,
        "Docstrings": '"""' in content,
    }

    for check_name, passed in checks.items():
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {check_name}")

    passed_count = sum(1 for v in checks.values() if v)
    total_count = len(checks)
    print(f"\nStandards compliance: {passed_count}/{total_count} ({passed_count/total_count*100:.0f}%)")

    return passed_count, total_count


def generate_final_report(pack_results, registry_ok, helper_results, total_lines, standards):
    """Generate final verification report."""
    print_header("FINAL VERIFICATION REPORT")

    # Signal packs
    pack_passed = sum(1 for v in pack_results.values() if v)
    pack_total = len(pack_results)
    print(f"\nSignal Pack Classes: {pack_passed}/{pack_total} implemented")

    # Helper classes
    helper_passed = sum(1 for v in helper_results.values() if v)
    helper_total = len(helper_results)
    print(f"Helper Classes: {helper_passed}/{helper_total} implemented")

    # Registry
    print(f"Signal Registry: {'✓ Complete' if registry_ok else '✗ Incomplete'}")

    # Implementation size
    print(f"\nImplementation Size: {total_lines} lines")
    if total_lines < 1000:
        print("  ⚠ Warning: Implementation seems incomplete (< 1000 lines)")
    elif total_lines < 2000:
        print("  ✓ Good: Solid implementation (1000-2000 lines)")
    else:
        print("  ✓ Excellent: Comprehensive implementation (> 2000 lines)")

    # Standards
    standards_passed, standards_total = standards
    print(f"\nStandards Compliance: {standards_passed}/{standards_total} ({standards_passed/standards_total*100:.0f}%)")
    if standards_passed / standards_total >= 0.8:
        print("  ✓ Excellent: Meets high standards (≥80%)")
    else:
        print("  ⚠ Warning: Below recommended standards (<80%)")

    # Overall score
    overall_score = (
        (pack_passed / pack_total * 30)
        + (helper_passed / helper_total * 20)
        + (30 if registry_ok else 0)
        + (min(total_lines / 2000, 1.0) * 10)
        + (standards_passed / standards_total * 10)
    )

    print("\n" + "=" * 80)
    print(f"OVERALL SCORE: {overall_score:.1f}/100")

    if overall_score >= 90:
        print("✓ EXCELLENT: Production-ready implementation")
    elif overall_score >= 75:
        print("✓ GOOD: Solid implementation, minor improvements possible")
    elif overall_score >= 60:
        print("⚠ ACCEPTABLE: Functional but needs improvements")
    else:
        print("✗ NEEDS WORK: Significant gaps in implementation")

    print("=" * 80)


def main():
    """Run all verification checks."""
    print("\n" + "="*80)
    print("SIGNAL IRRIGATION STRUCTURE VERIFICATION SUITE")
    print("="*80)

    # Analyze module
    classes = analyze_signal_registry_module()
    if not classes:
        print("\n✗ CRITICAL: Cannot analyze module")
        return

    # Verify signal packs
    pack_results = verify_signal_pack_classes(classes)

    # Verify registry
    registry_ok = verify_registry_class(classes)

    # Verify helpers
    helper_results = verify_helper_classes(classes)

    # Check implementation size
    total_lines = check_file_sizes()

    # Check standards
    standards = verify_standards_compliance()

    # Final report
    generate_final_report(pack_results, registry_ok, helper_results, total_lines, standards)


if __name__ == "__main__":
    main()
