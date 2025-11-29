#!/usr/bin/env python3
"""
SIN_CARRETA Calibration Coverage Validator

This script enforces calibration coverage requirements:
- Minimum 25% coverage of methods requiring calibration
- Fail loudly if coverage is below threshold
- Compute coverage from canonical_method_catalog.json against calibration_registry.py

Exit codes:
- 0: Coverage meets or exceeds 25% threshold
- 1: Coverage below 25% threshold (FAIL)
- 2: Script error (misconfiguration, missing files, etc.)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Set, Tuple


class CalibrationCoverageError(Exception):
    """Raised when calibration coverage is below threshold"""
    pass


def load_canonical_catalog(catalog_path: Path) -> Dict:
    """Load canonical method catalog"""
    try:
        with open(catalog_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Canonical catalog not found: {catalog_path}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in catalog: {e}")
        sys.exit(2)


def extract_all_methods_from_catalog(catalog: Dict) -> Set[str]:
    """
    Extract ALL methods from canonical catalog (not just those requiring calibration).
    
    Per canonic_calibration_methods.md: Every method must be either calibrated or excluded.
    
    Returns:
        Set of canonical_name strings for all methods in catalog
    """
    all_methods = set()
    
    # Iterate through all layers
    for layer_name, methods in catalog.get("layers", {}).items():
        for method_info in methods:
            canonical_name = method_info.get("canonical_name", "")
            if canonical_name:
                all_methods.add(canonical_name)
    
    return all_methods


def load_intrinsic_calibrations() -> Tuple[Set[str], Set[str]]:
    """
    Load calibrations from intrinsic_calibration.json.
    
    Per canonic_calibration_methods.md: This is Pillar 1, the authoritative source.
    
    Returns:
        (calibrated_methods, excluded_methods) - both as sets of canonical_name strings
    """
    repo_root = Path(__file__).parent.parent
    intrinsic_path = repo_root / "config" / "intrinsic_calibration.json"
    
    try:
        with open(intrinsic_path, 'r') as f:
            intrinsic_data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: intrinsic_calibration.json not found: {intrinsic_path}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in intrinsic_calibration.json: {e}")
        sys.exit(2)
    
    methods_dict = intrinsic_data.get("methods", {})
    
    calibrated_methods = set()
    excluded_methods = set()
    
    for method_id, profile in methods_dict.items():
        # Skip template entries
        if method_id.startswith("_"):
            continue
            
        # Check if method is excluded
        calibration_status = profile.get("calibration_status", "calibrated")
        
        if calibration_status == "excluded":
            excluded_methods.add(method_id)
        else:
            # Has a calibration profile (b_theory, b_impl, b_deploy)
            calibrated_methods.add(method_id)
    
    return calibrated_methods, excluded_methods


def compute_coverage(
    all_catalog_methods: Set[str],
    calibrated_methods: Set[str],
    excluded_methods: Set[str]
) -> Tuple[float, int, int, int, Set[str]]:
    """
    Compute calibration coverage per canonic_calibration_methods.md specification.
    
    Every method must be either calibrated OR excluded. Missing methods are errors.
    
    Returns:
        (coverage_percentage, calibrated_count, excluded_count, total_count, missing_methods)
    """
    total_count = len(all_catalog_methods)
    if total_count == 0:
        return 100.0, 0, 0, 0, set()
    
    # Find methods that are neither calibrated nor excluded
    accounted_for = calibrated_methods.union(excluded_methods)
    missing_methods = all_catalog_methods - accounted_for
    
    calibrated_count = len(calibrated_methods)
    excluded_count = len(excluded_methods)
    
    # Coverage is calibrated / total (excluded methods don't count toward coverage)
    coverage = (calibrated_count / total_count) * 100.0
    
    return coverage, calibrated_count, excluded_count, total_count, missing_methods


def print_coverage_report(
    coverage: float,
    calibrated_count: int,
    excluded_count: int,
    total_count: int,
    missing_methods: Set[str],
    threshold: float
):
    """Print detailed coverage report per canonic_calibration_methods.md"""
    print("=" * 80)
    print("THREE-PILLAR CALIBRATION COVERAGE REPORT")
    print("Per canonic_calibration_methods.md specification")
    print("=" * 80)
    print(f"\nTotal methods in canonical_method_catalog.json: {total_count}")
    print(f"Methods in intrinsic_calibration.json (calibrated): {calibrated_count}")
    print(f"Methods in intrinsic_calibration.json (excluded): {excluded_count}")
    print(f"Methods MISSING from intrinsic_calibration.json: {len(missing_methods)}")
    print(f"\nCoverage: {coverage:.2f}% ({calibrated_count}/{total_count})")
    print(f"Threshold: {threshold}%")
    print()
    
    # Check for missing methods (BLOCKER)
    if missing_methods:
        print(f"✗ BLOCKER: {len(missing_methods)} methods are MISSING from intrinsic_calibration.json")
        print("Per spec: Every method must be either calibrated OR excluded with reason.")
        print("\nMissing methods (first 20):")
        for i, method_id in enumerate(sorted(missing_methods)[:20]):
            print(f"  {i+1}. {method_id}")
        if len(missing_methods) > 20:
            print(f"  ... and {len(missing_methods) - 20} more")
        print()
    
    # Check coverage threshold
    if coverage >= threshold:
        if missing_methods:
            print(f"⚠ Coverage {coverage:.2f}% >= {threshold}%, but MISSING methods block merge")
        else:
            print(f"✓ PASS: Coverage meets threshold ({coverage:.2f}% >= {threshold}%)")
            print(f"✓ All methods accounted for (calibrated or excluded)")
    else:
        print(f"✗ FAIL: Coverage below threshold ({coverage:.2f}% < {threshold}%)")
        deficit = threshold - coverage
        methods_needed = int((deficit / 100.0) * total_count) + 1
        print(f"\nDeficit: {deficit:.2f}%")
        print(f"Additional calibrations needed: ~{methods_needed}")
    
    print("\n" + "=" * 80)


def validate_coverage(threshold: float = 25.0) -> int:
    """
    Main validation function per canonic_calibration_methods.md.
    
    Enforces:
    1. Every method in catalog must be in intrinsic_calibration.json (calibrated OR excluded)
    2. Coverage (calibrated/total) must meet threshold
    
    Args:
        threshold: Minimum coverage percentage required
        
    Returns:
        0 if all checks pass
        1 if coverage below threshold or methods missing (BLOCKER)
    """
    # Paths
    repo_root = Path(__file__).parent.parent
    catalog_path = repo_root / "config" / "canonical_method_catalog.json"
    
    print(f"Repository root: {repo_root}")
    print(f"Catalog path: {catalog_path}")
    print(f"Intrinsic calibration: config/intrinsic_calibration.json")
    print()
    
    # Load data
    catalog = load_canonical_catalog(catalog_path)
    all_catalog_methods = extract_all_methods_from_catalog(catalog)
    calibrated_methods, excluded_methods = load_intrinsic_calibrations()
    
    # Compute coverage
    coverage, calibrated_count, excluded_count, total_count, missing_methods = compute_coverage(
        all_catalog_methods, calibrated_methods, excluded_methods
    )
    
    # Print report
    print_coverage_report(
        coverage, calibrated_count, excluded_count, total_count, missing_methods, threshold
    )
    
    # Determine pass/fail
    # BLOCKER: Missing methods
    if missing_methods:
        print("\n❌ VALIDATION FAILED: Methods missing from intrinsic_calibration.json")
        print("Action required: Add all missing methods with either:")
        print("  - Full calibration profile (b_theory, b_impl, b_deploy)")
        print("  - Exclusion with 'calibration_status': 'excluded' and 'reason'")
        return 1
    
    # Check coverage threshold
    if coverage < threshold:
        print(f"\n❌ VALIDATION FAILED: Coverage {coverage:.2f}% < {threshold}%")
        return 1
    
    print(f"\n✅ VALIDATION PASSED: All checks OK")
    return 0


def main():
    """CLI entry point"""
    # Parse arguments (simple threshold override)
    threshold = 25.0
    if len(sys.argv) > 1:
        try:
            threshold = float(sys.argv[1])
        except ValueError:
            print(f"ERROR: Invalid threshold: {sys.argv[1]}")
            print("Usage: validate_calibration_coverage.py [threshold_percentage]")
            sys.exit(2)
    
    # Run validation
    exit_code = validate_coverage(threshold)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
