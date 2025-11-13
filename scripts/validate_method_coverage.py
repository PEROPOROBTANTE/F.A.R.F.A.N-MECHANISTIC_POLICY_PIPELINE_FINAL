#!/usr/bin/env python3
"""
Validate Method Catalog Coverage

This script ensures 100% coverage of methods from canonical_method_catalog.json
in intrinsic_calibration.json (either calibrated or explicitly excluded).

Spec compliance: Section 8 (Validation & Governance) + Hard-mode enforcement
"""

import sys
import json
from pathlib import Path

# Add parent directory to path


def load_json(path: Path) -> dict:
    """Load JSON file"""
    with open(path, 'r') as f:
        return json.load(f)


def main():
    """Validate method catalog coverage"""
    print("=" * 70)
    print("Method Catalog Coverage Validation")
    print("=" * 70)
    print()
    
    repo_root = Path(__file__).parent.parent
    
    # Load canonical catalog
    catalog_path = repo_root / "config" / "canonical_method_catalog.json"
    if not catalog_path.exists():
        print(f"❌ Canonical catalog not found: {catalog_path}")
        return 1
    
    catalog = load_json(catalog_path)
    
    # Load intrinsic calibration
    intrinsic_path = repo_root / "config" / "intrinsic_calibration.json"
    if not intrinsic_path.exists():
        print(f"❌ Intrinsic calibration not found: {intrinsic_path}")
        return 1
    
    intrinsic = load_json(intrinsic_path)
    
    # Extract all method IDs from catalog
    all_methods = set()
    
    if "layers" in catalog:
        for layer_name, methods in catalog["layers"].items():
            for method in methods:
                if method.get("requires_calibration", False):
                    all_methods.add(method["canonical_name"])
    
    print(f"Found {len(all_methods)} methods requiring calibration in catalog")
    
    # Extract calibrated and excluded methods from intrinsic config
    calibrated = set()
    excluded = set()
    
    methods_section = intrinsic.get("methods", {})
    for method_id, method_data in methods_section.items():
        if method_id.startswith("_"):
            continue  # Skip metadata
        
        if isinstance(method_data, dict):
            if method_data.get("calibration_status") == "excluded":
                excluded.add(method_id)
            elif all(k in method_data for k in ["b_theory", "b_impl", "b_deploy"]):
                calibrated.add(method_id)
    
    print(f"Found {len(calibrated)} calibrated methods")
    print(f"Found {len(excluded)} explicitly excluded methods")
    print()
    
    # Calculate coverage
    accounted = calibrated | excluded
    missing = all_methods - accounted
    
    coverage_percent = (len(accounted) / len(all_methods) * 100) if all_methods else 0
    
    print(f"Coverage: {coverage_percent:.1f}% ({len(accounted)}/{len(all_methods)})")
    print()
    
    if missing:
        print(f"❌ VALIDATION FAILED")
        print()
        print(f"{len(missing)} methods are not accounted for:")
        print()
        for i, method_id in enumerate(sorted(missing)[:20], 1):
            print(f"  {i}. {method_id}")
        
        if len(missing) > 20:
            print(f"  ... and {len(missing) - 20} more")
        
        print()
        print("Each method MUST either:")
        print("  1. Have intrinsic calibration (b_theory, b_impl, b_deploy), OR")
        print("  2. Be explicitly excluded with calibration_status='excluded' and reason")
        print()
        return 1
    
    print("✅ ALL METHODS ACCOUNTED FOR")
    print()
    print("Coverage requirements:")
    print("  ✓ All methods either calibrated or explicitly excluded")
    print("  ✓ No silent fallbacks or missing entries")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
