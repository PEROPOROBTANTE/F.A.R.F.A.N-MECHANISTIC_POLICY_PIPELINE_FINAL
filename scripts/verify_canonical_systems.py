#!/usr/bin/env python3
"""
Canonical Systems Verification Script

Quick verification that all canonical systems components are operational.

Run this after making changes to ensure system integrity.
"""

import json
import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent


def check_catalog():
    """Verify canonical method catalog loads"""
    try:
        catalog_path = repo_root / "config" / "canonical_method_catalog.json"
        with open(catalog_path) as f:
            catalog = json.load(f)
        total = catalog['summary']['total_methods']
        print(f"✅ Canonical catalog loaded: {total} methods (v{catalog['metadata']['version']})")
        return True
    except Exception as e:
        print(f"❌ Canonical catalog failed to load: {e}")
        return False


def check_registry():
    """Verify calibration registry loads"""
    try:
        from saaaaaa.core.orchestrator.calibration_registry import CALIBRATIONS
        print(f"✅ Calibration registry loaded: {len(CALIBRATIONS)} calibrations")
        return True
    except Exception as e:
        print(f"❌ Calibration registry failed to load: {e}")
        return False


def check_ontology():
    """Verify canonical ontology file exists"""
    ontology_path = repo_root / "config" / "canonical_ontologies" / "policy_areas_and_dimensions.json"
    if ontology_path.exists():
        print(f"✅ Canonical ontology exists")
        return True
    else:
        print(f"❌ Canonical ontology not found at {ontology_path}")
        return False


def check_artifacts():
    """Verify all required artifacts exist and have valid structure"""
    artifacts = {
        "config/method_usage_intelligence.json": {
            "size_check": True,
            "structure_check": "usage_intelligence"
        },
        "config/calibration_decisions.json": {
            "size_check": True,
            "structure_check": "calibration_decisions"
        },
        "config/alignment_audit_report.json": {
            "size_check": True,
            "structure_check": None
        },
    }
    
    all_valid = True
    for artifact, checks in artifacts.items():
        path = repo_root / artifact
        if not path.exists():
            print(f"❌ {artifact} missing")
            all_valid = False
            continue
        
        size_kb = path.stat().st_size / 1024
        
        # Load and validate structure if needed
        if checks.get("structure_check"):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                
                if checks["structure_check"] == "usage_intelligence":
                    # Validate usage intelligence structure
                    methods = data.get("methods", {})
                    total = len(methods)
                    used = sum(1 for m in methods.values() if isinstance(m, dict) and m.get("total_usages", 0) > 0)
                    catalog_used = sum(1 for m in methods.values() 
                                     if isinstance(m, dict) and m.get("in_catalog", False) and m.get("total_usages", 0) > 0)
                    
                    if catalog_used == 0:
                        print(f"❌ {artifact} ({size_kb:.1f} KB) - ZERO catalog methods have usage data")
                        all_valid = False
                    elif catalog_used < 10:
                        print(f"⚠️  {artifact} ({size_kb:.1f} KB) - Only {catalog_used} catalog methods have usage data")
                    else:
                        print(f"✅ {artifact} ({size_kb:.1f} KB) - {catalog_used} catalog methods tracked")
                
                elif checks["structure_check"] == "calibration_decisions":
                    # Validate calibration decisions structure
                    decisions = data.get("decisions", {})
                    
                    # Check if it's category-keyed (WRONG) or method-keyed (CORRECT)
                    if "REQUIRES_CALIBRATION" in decisions:
                        print(f"❌ {artifact} ({size_kb:.1f} KB) - WRONG STRUCTURE (category-keyed, should be method-keyed)")
                        all_valid = False
                    elif len(decisions) < 100:
                        print(f"⚠️  {artifact} ({size_kb:.1f} KB) - Only {len(decisions)} decisions (expected 590+)")
                    else:
                        # Validate a sample entry
                        sample_key = list(decisions.keys())[0]
                        sample_val = decisions[sample_key]
                        if not isinstance(sample_val, dict) or "decision" not in sample_val:
                            print(f"❌ {artifact} ({size_kb:.1f} KB) - Invalid entry structure")
                            all_valid = False
                        else:
                            print(f"✅ {artifact} ({size_kb:.1f} KB) - {len(decisions)} method-keyed decisions")
            
            except Exception as e:
                print(f"❌ {artifact} - Failed to validate: {e}")
                all_valid = False
        else:
            print(f"✅ {artifact} ({size_kb:.1f} KB)")
    
    return all_valid


def check_scripts():
    """Verify scripts are executable"""
    scripts = [
        "scripts/build_method_usage_intelligence.py",
        "scripts/build_calibration_decisions.py",
        "scripts/audit_catalog_registry_alignment.py",
    ]
    
    all_exec = True
    for script in scripts:
        path = repo_root / script
        if path.exists() and path.stat().st_mode & 0o111:
            print(f"✅ {script} is executable")
        else:
            print(f"❌ {script} not executable or missing")
            all_exec = False
    
    return all_exec


def main():
    print("="*80)
    print("CANONICAL SYSTEMS VERIFICATION")
    print("="*80)
    
    results = []
    
    print("\n[1/5] Checking catalog module...")
    results.append(check_catalog())
    
    print("\n[2/5] Checking calibration registry...")
    results.append(check_registry())
    
    print("\n[3/5] Checking canonical ontology...")
    results.append(check_ontology())
    
    print("\n[4/5] Checking artifacts...")
    results.append(check_artifacts())
    
    print("\n[5/5] Checking scripts...")
    results.append(check_scripts())
    
    print("\n" + "="*80)
    if all(results):
        print("✅ ALL CHECKS PASSED")
        print("="*80)
        print("\nCanonical systems infrastructure is operational.")
        print("\nNext steps:")
        print("  1. Run alignment audit: python scripts/audit_catalog_registry_alignment.py")
        print("  2. Review defects in config/alignment_audit_report.json")
        print("  3. Resolve defects to achieve system integrity")
        return 0
    else:
        print("❌ SOME CHECKS FAILED")
        print("="*80)
        print("\nFix errors above before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
