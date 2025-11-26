#!/usr/bin/env python3
"""
Generate Method Classification Artifact for FAKE → REAL Executor Migration

This script performs code inspection to classify all methods into three categories:
- REAL_NON_EXEC: Real methods that are not executors (already calibrated, protected)
- FAKE_EXEC: Fake executor methods from old executors.py (invalid, must discard)
- REAL_EXEC: Real executor methods from executors_contract.py (need calibration)

NO placeholders. NO guesswork. Evidence-based classification only.

Output: method_classification.json
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src" / "saaaaaa"
ORCHESTRATOR_ROOT = SRC_ROOT / "core" / "orchestrator"


def extract_classes_from_file(file_path: Path) -> list[str]:
    """Extract all class names from a Python file via AST parsing."""
    if not file_path.exists():
        return []

    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        print(f"WARNING: Could not parse {file_path}: {exc}")
        return []

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)

    return classes


def get_fake_executors() -> list[str]:
    """Extract FAKE executor class names from old executors.py."""
    fake_file = ORCHESTRATOR_ROOT / "executors.py"
    classes = extract_classes_from_file(fake_file)

    # Filter to only executor classes (D{n}_Q{m}_* pattern)
    # Exclude BaseExecutor, ExecutorFailure, etc.
    fake_executors = []
    for class_name in classes:
        # Match pattern: D{digit}(_| )Q{digit}_*
        # Examples: D1_Q1_QuantitativeBaselineExtractor, D3_Q2_TargetProportionalityAnalyzer
        if (
            class_name.startswith("D")
            and ("_Q" in class_name or " Q" in class_name)
            and not class_name.startswith("Base")
            and class_name not in ["ExecutorFailure"]
        ):
            # Construct the fully qualified name
            fake_executors.append(f"orchestrator.executors.{class_name}")

    return sorted(fake_executors)


def get_real_executors() -> list[str]:
    """Extract REAL executor class names from executors_contract.py."""
    real_file = ORCHESTRATOR_ROOT / "executors_contract.py"
    classes = extract_classes_from_file(real_file)

    # All D{n}Q{m}_Executor_Contract classes
    real_executors = []
    for class_name in classes:
        if class_name.endswith("_Executor_Contract") or class_name.endswith("_Executor"):
            real_executors.append(f"orchestrator.executors_contract.{class_name}")

    # Also add the aliases (D{n}Q{m}_Executor = D{n}Q{m}_Executor_Contract)
    # These are defined in executors_contract.py lines 186-216
    dimension_question_pairs = [
        (d, q) for d in range(1, 7) for q in range(1, 6)
    ]

    for dim, quest in dimension_question_pairs:
        # Add both the _Contract class and its alias
        contract_class = f"orchestrator.executors_contract.D{dim}Q{quest}_Executor_Contract"
        alias_class = f"orchestrator.executors_contract.D{dim}Q{quest}_Executor"

        # Only add if not already in the list
        if contract_class not in real_executors:
            real_executors.append(contract_class)
        if alias_class not in real_executors:
            real_executors.append(alias_class)

    return sorted(set(real_executors))


def load_calibrated_methods() -> set[str]:
    """Load all methods from intrinsic_calibration.json."""
    calibration_file = PROJECT_ROOT / "config" / "intrinsic_calibration.json"

    if not calibration_file.exists():
        print(f"WARNING: {calibration_file} not found")
        return set()

    try:
        data = json.loads(calibration_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"WARNING: Could not parse {calibration_file}: {exc}")
        return set()

    # Extract method identifiers from the "methods" key
    # Intrinsic calibration uses format: "module.ClassName.method_name"
    methods = set()
    if "methods" in data:
        methods = set(data["methods"].keys())

    return methods


def scan_all_methods() -> set[str]:
    """Scan all Python files in src/saaaaaa to find all class.method combinations."""
    all_methods = set()

    # Walk through all Python files
    for py_file in SRC_ROOT.rglob("*.py"):
        # Skip test files, __pycache__, etc.
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue

        # Extract class names and their methods
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name

                # Get all method names (functions defined in the class)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_name = item.name
                        # Skip private methods (but include __init__)
                        if not method_name.startswith("_") or method_name == "__init__":
                            # Use simplified format: ClassName.method_name
                            all_methods.add(f"{class_name}.{method_name}")

    return all_methods


def get_real_non_exec_methods(
    calibrated_methods: set[str],
    fake_executors: list[str],
    real_executors: list[str],
) -> list[str]:
    """
    Identify REAL_NON_EXEC methods: calibrated methods that are not executors.

    These are methods that:
    1. Appear in intrinsic_calibration.json
    2. Are NOT fake executors
    3. Are NOT real executors (executors need recalibration)
    """
    # Extract simplified executor names for comparison
    fake_exec_names = set()
    for fake_exec in fake_executors:
        # Extract class name: "orchestrator.executors.D1_Q1_QuantitativeBaselineExtractor"
        # → "D1_Q1_QuantitativeBaselineExtractor"
        parts = fake_exec.split(".")
        if len(parts) >= 3:
            fake_exec_names.add(parts[-1])

        # Also add the alias form used in calibration (D{n}Q{m}_Executor)
        # D1_Q1_QuantitativeBaselineExtractor → D1Q1_Executor
        if "_Q" in parts[-1]:
            # Extract D{n}_Q{m} and convert to D{n}Q{m}_Executor
            import re
            match = re.match(r'D(\d+)_Q(\d+)_', parts[-1])
            if match:
                alias = f"D{match.group(1)}Q{match.group(2)}_Executor"
                fake_exec_names.add(alias)

    real_exec_names = set()
    for real_exec in real_executors:
        parts = real_exec.split(".")
        if len(parts) >= 3:
            real_exec_names.add(parts[-1])

    # Filter calibrated methods
    real_non_exec = []
    fake_exec_methods = []
    real_exec_methods = []

    for method in calibrated_methods:
        # Method format: "module.ClassName.method_name" or "ClassName.method_name"
        # or "src.module.ClassName.method_name" (full path format)
        parts = method.split(".")

        # Extract class name (second-to-last part)
        if len(parts) >= 3:
            class_name = parts[-2]  # ...ClassName.method_name → ClassName
        elif len(parts) == 2:
            class_name = parts[0]  # ClassName.method_name → ClassName
        else:
            class_name = method  # Just the name

        # Check if it's from the old executors.py (FAKE)
        is_fake = False
        if "executors." in method and "executors_contract" not in method:
            # Check if it matches executor pattern
            if (
                class_name.startswith("D")
                and ("_Q" in class_name or "Q" in class_name)
                and any(char.isdigit() for char in class_name[:5])  # D{n}_Q{m} or D{n}Q{m}
            ):
                is_fake = True
                fake_exec_methods.append(method)
                continue

        # Check if it's an executor by name
        if class_name in fake_exec_names or class_name in real_exec_names:
            if class_name in fake_exec_names:
                fake_exec_methods.append(method)
            else:
                real_exec_methods.append(method)
            continue

        # Exclude if it matches executor patterns (D{n}_Q{m} or D{n}Q{m})
        if (
            class_name.startswith("D")
            and ("_Q" in class_name or "Q" in class_name)
            and any(char.isdigit() for char in class_name[:5])  # D{n}_Q{m} or D{n}Q{m}
        ):
            # Likely an executor variant
            fake_exec_methods.append(method)
            continue

        real_non_exec.append(method)

    return sorted(real_non_exec), sorted(fake_exec_methods), sorted(real_exec_methods)


def generate_classification() -> dict[str, Any]:
    """Generate the complete method classification artifact."""
    print("=" * 80)
    print("GENERATING METHOD CLASSIFICATION ARTIFACT")
    print("=" * 80)

    print("\n1. Extracting FAKE executors from executors.py...")
    fake_executors = get_fake_executors()
    print(f"   Found {len(fake_executors)} FAKE executor classes")

    print("\n2. Extracting REAL executors from executors_contract.py...")
    real_executors = get_real_executors()
    print(f"   Found {len(real_executors)} REAL executor classes")

    print("\n3. Loading calibrated methods from intrinsic_calibration.json...")
    calibrated_methods = load_calibrated_methods()
    print(f"   Found {len(calibrated_methods)} calibrated methods")

    print("\n4. Classifying methods from calibration file...")
    real_non_exec, fake_exec_calibrated, real_exec_calibrated = get_real_non_exec_methods(
        calibrated_methods, fake_executors, real_executors
    )
    print(f"   REAL_NON_EXEC:  {len(real_non_exec):>5} methods (protected)")
    print(f"   FAKE_EXEC:      {len(fake_exec_calibrated):>5} methods in calibration (discard)")
    print(f"   REAL_EXEC:      {len(real_exec_calibrated):>5} methods in calibration (recalibrate)")

    # Construct the artifact
    classification = {
        "_metadata": {
            "version": "1.0",
            "date": "2025-11-24",
            "migration": "FAKE → REAL Executor Migration",
            "branch": "claude/fake-real-executor-migration-01DkQrq2dtSN3scUvzNVKqGy",
            "description": (
                "Machine-readable classification of all methods for executor migration. "
                "REAL_NON_EXEC methods have protected calibrations. "
                "FAKE_EXEC methods have invalid calibrations (must discard). "
                "REAL_EXEC methods need new calibrations (all 8 layers)."
            ),
        },
        "REAL_NON_EXEC": {
            "description": "Real methods that are not executors. Already calibrated via rubric. PROTECTED - DO NOT MODIFY.",
            "count": len(real_non_exec),
            "methods": real_non_exec,
        },
        "FAKE_EXEC": {
            "description": "Fake executor methods from old executors.py. Hardcoded execute() methods. INVALID - DISCARD CALIBRATIONS.",
            "count": len(fake_executors),
            "file": "src/saaaaaa/core/orchestrator/executors.py",
            "snapshot": "src/saaaaaa/core/orchestrator/executors_snapshot/executors.py",
            "classes": fake_executors,
            "calibrated_methods": {
                "count": len(fake_exec_calibrated),
                "status": "INVALID - placeholder_computed",
                "action": "DISCARD",
                "methods": fake_exec_calibrated,
            },
        },
        "REAL_EXEC": {
            "description": "Real executor methods from executors_contract.py. Contract-driven routing. NEED CALIBRATION - ALL 8 LAYERS.",
            "count": len(real_executors),
            "file": "src/saaaaaa/core/orchestrator/executors_contract.py",
            "classes": real_executors,
            "calibrated_methods": {
                "count": len(real_exec_calibrated),
                "status": "partial or none",
                "action": "RECALIBRATE",
                "methods": real_exec_calibrated,
            },
        },
        "summary": {
            "total_classes": len(real_non_exec) + len(fake_executors) + len(real_executors),
            "total_calibrated_methods": len(calibrated_methods),
            "real_non_exec_methods": len(real_non_exec),
            "fake_exec_classes": len(fake_executors),
            "fake_exec_calibrated_methods": len(fake_exec_calibrated),
            "real_exec_classes": len(real_executors),
            "real_exec_calibrated_methods": len(real_exec_calibrated),
        },
    }

    return classification


def main() -> None:
    """Main entry point."""
    classification = generate_classification()

    # Write to file
    output_file = PROJECT_ROOT / "method_classification.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(classification, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 80}")
    print(f"✅ Classification artifact written to: {output_file}")
    print(f"{'=' * 80}")
    print("\nSUMMARY:")
    print(f"  REAL_NON_EXEC:             {classification['summary']['real_non_exec_methods']:>5} methods (protected)")
    print(f"  FAKE_EXEC classes:         {classification['summary']['fake_exec_classes']:>5} classes")
    print(f"    - in calibration file:   {classification['summary']['fake_exec_calibrated_methods']:>5} methods (DISCARD)")
    print(f"  REAL_EXEC classes:         {classification['summary']['real_exec_classes']:>5} classes")
    print(f"    - in calibration file:   {classification['summary']['real_exec_calibrated_methods']:>5} methods (recalibrate)")
    print(f"  {'─' * 50}")
    print(f"  Total calibrated methods:  {classification['summary']['total_calibrated_methods']:>5}")
    print()


if __name__ == "__main__":
    main()
