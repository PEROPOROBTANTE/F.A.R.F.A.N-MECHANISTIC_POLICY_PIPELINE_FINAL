#!/usr/bin/env python3
"""
Verification script for canonical_method_inventory.json

This script validates the canonical method inventory against required criteria:
1. Total methods >= 1995
2. All 30 D1Q1-D6Q5 executors present with is_executor=true
3. No duplicate canonical IDs
4. Every method has non-empty role

Exits with error code if any check fails and provides detailed diagnostic output.
"""

import json
import sys
from pathlib import Path
from typing import Any

MIN_REQUIRED_METHODS = 1995
MAX_DISPLAY_ITEMS = 10


def load_inventory(inventory_path: Path) -> dict[str, Any]:  # type: ignore[misc]
    """Load and parse the canonical method inventory JSON file."""
    if not inventory_path.exists():
        print(f"❌ ERROR: Inventory file not found: {inventory_path}")
        sys.exit(1)

    try:
        with open(inventory_path, encoding="utf-8") as f:
            return json.load(f)  # type: ignore[no-any-return]
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: Failed to parse JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: Failed to read file: {e}")
        sys.exit(1)


def check_total_methods(inventory: dict[str, Any]) -> tuple[bool, int]:  # type: ignore[misc]
    """Check if total_methods >= 1995."""
    metadata = inventory.get("metadata", {})
    total_methods = metadata.get("total_methods", 0)

    if isinstance(total_methods, str):
        try:
            total_methods = int(total_methods)
        except ValueError:
            total_methods = 0

    methods_dict = inventory.get("methods", {})
    actual_count = (
        len(methods_dict) if isinstance(methods_dict, dict) else len(methods_dict)
    )

    total_methods = max(total_methods, actual_count)

    passed = total_methods >= MIN_REQUIRED_METHODS
    return passed, total_methods


def generate_expected_executors() -> set[str]:
    """Generate the set of 30 expected executor identifiers (D1Q1-D6Q5)."""
    executors = set()
    for dim in range(1, 7):
        for question in range(1, 6):
            executors.add(f"D{dim}Q{question}")
    return executors


def check_executors(  # type: ignore[misc] # noqa: PLR0912
    inventory: dict[str, Any],
) -> tuple[bool, set[str], set[str]]:
    """Check if all 30 D1Q1-D6Q5 executors are present with is_executor=true."""
    expected_executors = generate_expected_executors()
    found_executors = set()

    methods = inventory.get("methods", {})

    if isinstance(methods, dict):
        for method_id, method_data in methods.items():
            if not isinstance(method_data, dict):
                continue

            is_executor = method_data.get("is_executor", False)
            if is_executor is True or str(is_executor).lower() == "true":
                search_fields = [
                    method_data.get("canonical_name", ""),
                    method_data.get("method_name", ""),
                    method_data.get("class_name", ""),
                    method_id,
                ]

                for executor_id in expected_executors:
                    patterns = [
                        executor_id,
                        executor_id.replace("Q", "_Q_"),
                        executor_id.replace("Q", "-Q"),
                        f"D{executor_id[1]}_Q{executor_id[3]}",
                    ]

                    for field in search_fields:
                        if field:
                            for pattern in patterns:
                                if pattern in field:
                                    found_executors.add(executor_id)
                                    break
    elif isinstance(methods, list):
        for method_data in methods:
            if not isinstance(method_data, dict):
                continue

            is_executor = method_data.get("is_executor", False)
            if is_executor is True or str(is_executor).lower() == "true":
                search_fields = [
                    method_data.get("canonical_name", ""),
                    method_data.get("method_name", ""),
                    method_data.get("class_name", ""),
                    method_data.get("method_id", ""),
                ]

                for executor_id in expected_executors:
                    patterns = [
                        executor_id,
                        executor_id.replace("Q", "_Q_"),
                        executor_id.replace("Q", "-Q"),
                        f"D{executor_id[1]}_Q{executor_id[3]}",
                    ]

                    for field in search_fields:
                        if field:
                            for pattern in patterns:
                                if pattern in field:
                                    found_executors.add(executor_id)
                                    break

    missing_executors = expected_executors - found_executors
    passed = len(missing_executors) == 0

    return passed, found_executors, missing_executors


def check_duplicate_ids(  # type: ignore[misc]
    inventory: dict[str, Any],
) -> tuple[bool, list[str]]:
    """Check for duplicate canonical identifiers."""
    methods = inventory.get("methods", {})

    seen_ids: set[str] = set()
    duplicates: list[str] = []

    if isinstance(methods, dict):
        for method_id, method_data in methods.items():
            if not isinstance(method_data, dict):
                continue

            canonical_id = method_data.get(
                "canonical_identifier",
                method_data.get("unique_id", method_data.get("method_id", method_id)),
            )

            if canonical_id in seen_ids:
                duplicates.append(canonical_id)
            else:
                seen_ids.add(canonical_id)
    elif isinstance(methods, list):
        for method_data in methods:
            if not isinstance(method_data, dict):
                continue

            canonical_id = method_data.get(
                "canonical_identifier",
                method_data.get("unique_id", method_data.get("method_id", "")),
            )

            if canonical_id in seen_ids:
                duplicates.append(canonical_id)
            else:
                seen_ids.add(canonical_id)

    passed = len(duplicates) == 0
    return passed, duplicates


def check_roles(inventory: dict[str, Any]) -> tuple[bool, list[str]]:  # type: ignore[misc]
    """Check that every method has a non-empty role."""
    methods = inventory.get("methods", {})
    methods_without_role: list[str] = []

    if isinstance(methods, dict):
        for method_id, method_data in methods.items():
            if not isinstance(method_data, dict):
                continue

            role = method_data.get("role", "")
            if not role or (isinstance(role, str) and role.strip() == ""):
                methods_without_role.append(method_id)
    elif isinstance(methods, list):
        for method_data in methods:
            if not isinstance(method_data, dict):
                continue

            method_id = method_data.get(
                "method_id",
                method_data.get(
                    "canonical_name", method_data.get("canonical_identifier", "UNKNOWN")
                ),
            )
            role = method_data.get("role", "")
            if not role or (isinstance(role, str) and role.strip() == ""):
                methods_without_role.append(method_id)

    passed = len(methods_without_role) == 0
    return passed, methods_without_role


def main() -> None:  # noqa: PLR0912, PLR0915
    """Main verification routine."""
    repo_root = Path(__file__).parent.parent.parent
    inventory_path = (
        repo_root / "scripts" / "inventory" / "canonical_method_inventory.json"
    )

    print("=" * 80)
    print("CANONICAL METHOD INVENTORY VERIFICATION")
    print("=" * 80)
    print(f"\nInventory path: {inventory_path}")
    print()

    inventory = load_inventory(inventory_path)

    all_checks_passed = True

    print("Running verification checks...\n")

    # Check 1: Total methods >= 1995
    print("[1/4] Checking total methods count...")
    methods_check_passed, total_methods = check_total_methods(inventory)
    if methods_check_passed:
        print(f"✅ PASS: Total methods = {total_methods} (>= {MIN_REQUIRED_METHODS})")
    else:
        print(
            f"❌ FAIL: Total methods = {total_methods} (expected >= {MIN_REQUIRED_METHODS})"
        )
        print(f"   Deficit: {MIN_REQUIRED_METHODS - total_methods} methods")
        all_checks_passed = False
    print()

    # Check 2: All 30 executors present
    print("[2/4] Checking for D1Q1-D6Q5 executors...")
    executors_check_passed, found_executors, missing_executors = check_executors(
        inventory
    )
    if executors_check_passed:
        print("✅ PASS: All 30 executors present (D1Q1-D6Q5)")
        print(f"   Found executors: {sorted(found_executors)}")
    else:
        print(f"❌ FAIL: Missing {len(missing_executors)} executor(s)")
        print(f"   Found: {len(found_executors)}/30 executors")
        print(f"   Found executors: {sorted(found_executors)}")
        print(f"   Missing executors: {sorted(missing_executors)}")
        all_checks_passed = False
    print()

    # Check 3: No duplicate canonical IDs
    print("[3/4] Checking for duplicate canonical identifiers...")
    duplicates_check_passed, duplicates = check_duplicate_ids(inventory)
    if duplicates_check_passed:
        print("✅ PASS: No duplicate canonical identifiers")
    else:
        print(f"❌ FAIL: Found {len(duplicates)} duplicate identifier(s)")
        if len(duplicates) <= MAX_DISPLAY_ITEMS:
            for dup_id in duplicates:
                print(f"   - {dup_id}")
        else:
            for dup_id in duplicates[:MAX_DISPLAY_ITEMS]:
                print(f"   - {dup_id}")
            print(f"   ... and {len(duplicates) - MAX_DISPLAY_ITEMS} more")
        all_checks_passed = False
    print()

    # Check 4: All methods have non-empty roles
    print("[4/4] Checking that all methods have non-empty roles...")
    roles_check_passed, methods_without_role = check_roles(inventory)
    if roles_check_passed:
        print("✅ PASS: All methods have non-empty roles")
    else:
        print(f"❌ FAIL: Found {len(methods_without_role)} method(s) without role")
        if len(methods_without_role) <= MAX_DISPLAY_ITEMS:
            for method_id in methods_without_role:
                print(f"   - {method_id}")
        else:
            for method_id in methods_without_role[:MAX_DISPLAY_ITEMS]:
                print(f"   - {method_id}")
            print(f"   ... and {len(methods_without_role) - MAX_DISPLAY_ITEMS} more")
        all_checks_passed = False
    print()

    # Summary
    print("=" * 80)
    if all_checks_passed:
        print("✅ ALL CHECKS PASSED")
        print("=" * 80)
        sys.exit(0)
    else:
        print("❌ VERIFICATION FAILED")
        print("=" * 80)
        sys.exit(1)


if __name__ == "__main__":
    main()
