#!/usr/bin/env python3
"""
Catalog-Registry-Usage Alignment Audit

Comprehensive audit to verify alignment between:
1. canonical_method_catalog.json (canonical method universe - 1,996 methods)
2. calibration_registry.py (calibration metadata)
3. Actual codebase usage

Outputs:
- Methods catalogued vs used vs calibrated
- Defects found
- Alignment verification results
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
repo_root = Path(__file__).parent.parent

from saaaaaa.core.orchestrator.calibration_registry import CALIBRATIONS


def main():
    print("="*80)
    print("CATALOG-REGISTRY-USAGE ALIGNMENT AUDIT")
    print("="*80)
    
    # Load canonical method catalog
    catalog_path = repo_root / "config" / "canonical_method_catalog.json"
    with open(catalog_path) as f:
        catalog_data = json.load(f)
    
    print(f"\nCanonical catalog: {catalog_data['summary']['total_methods']} methods (v{catalog_data['metadata']['version']})")
    
    # Load usage intelligence
    usage_path = repo_root / "config" / "method_usage_intelligence.json"
    with open(usage_path, 'r') as f:
        usage_data = json.load(f)
    
    # Load calibration decisions
    decisions_path = repo_root / "config" / "calibration_decisions.json"
    with open(decisions_path, 'r') as f:
        decisions_data = json.load(f)
    
    # Build method sets
    catalog_methods = {
        (m['class_name'], m['method_name']) 
        for m in catalog_data['methods'] 
        if m['class_name']
    }
    registry_methods = set(CALIBRATIONS.keys())
    used_methods = set()
    
    for fqn, usage in usage_data.get('methods', {}).items():
        if isinstance(usage, dict):
            class_name = usage.get('class_name', '')
            method_name = usage.get('method_name', '')
            if class_name and method_name and usage.get('total_usages', 0) > 0:
                used_methods.add((class_name, method_name))
    
    print(f"\n[INVENTORY]")
    print(f"  Catalog methods: {len(catalog_methods)}")
    print(f"  Registry methods: {len(registry_methods)}")
    print(f"  Used methods (in codebase): {len(used_methods)}")
    
    # Analyze overlaps
    print(f"\n[ALIGNMENT ANALYSIS]")
    
    # 1. Methods in catalog AND registry
    catalog_and_registry = catalog_methods & registry_methods
    print(f"  ✓ In both catalog AND registry: {len(catalog_and_registry)}")
    
    # 2. Methods in catalog but NOT in registry
    catalog_not_registry = catalog_methods - registry_methods
    print(f"  ⚠ In catalog but NOT in registry: {len(catalog_not_registry)}")
    
    # 3. Methods in registry but NOT in catalog (DEFECT)
    registry_not_catalog = registry_methods - catalog_methods
    print(f"  ❌ In registry but NOT in catalog (DEFECT): {len(registry_not_catalog)}")
    
    # 4. Methods used but NOT in catalog (DEFECT)
    used_not_catalog = used_methods - catalog_methods
    print(f"  ❌ Used but NOT in catalog (DEFECT): {len(used_not_catalog)}")
    
    # 5. Methods in catalog but NEVER used
    catalog_not_used = catalog_methods - used_methods
    print(f"  ⚠ In catalog but NEVER used: {len(catalog_not_used)}")
    
    # 6. Methods used but NOT in registry
    used_not_registry = used_methods - registry_methods
    print(f"  ⚠ Used but NOT in registry: {len(used_not_registry)}")
    
    # Build defect report
    defects = []
    acceptable_divergence = []
    
    # Check 1: Registry methods not in catalog
    # Per CATALOG_REGISTRY_ALIGNMENT_POLICY.md, this is ACCEPTABLE if methods are unused
    for class_name, method_name in sorted(registry_not_catalog):
        fqn = f"{class_name}.{method_name}"
        
        # Check if this method is actually used
        usage = usage_data.get('methods', {}).get(fqn, {})
        usage_count = usage.get('total_usages', 0) if isinstance(usage, dict) else 0
        
        if usage_count > 0:
            # Used but not in catalog - this is a DEFECT
            defects.append({
                "type": "REGISTRY_NOT_IN_CATALOG_USED",
                "severity": "HIGH",
                "method": fqn,
                "description": f"Method has calibration, is USED ({usage_count} times), but not in canonical catalog",
                "action": "Add to catalog - this method is actively used"
            })
        else:
            # Unused and not in catalog - this is ACCEPTABLE per policy
            acceptable_divergence.append({
                "type": "REGISTRY_NOT_IN_CATALOG_UNUSED",
                "severity": "INFO",
                "method": fqn,
                "description": "Method has calibration but is not in catalog (unused - acceptable per policy)",
                "action": "No action required (different scopes) - see CATALOG_REGISTRY_ALIGNMENT_POLICY.md"
            })
    
    # Check 2: Used method not in catalog - ALWAYS A DEFECT
    for class_name, method_name in sorted(used_not_catalog):
        defects.append({
            "type": "USED_NOT_IN_CATALOG",
            "severity": "CRITICAL",
            "method": f"{class_name}.{method_name}",
            "description": "Method is used in codebase but not in canonical catalog",
            "action": "Add to catalog immediately"
        })
    
    # Warnings
    warnings = []
    
    # Warning Type 1: Catalog method never used
    for class_name, method_name in sorted(list(catalog_not_used)[:20]):  # Top 20
        warnings.append({
            "type": "CATALOGUED_NOT_USED",
            "severity": "LOW",
            "method": f"{class_name}.{method_name}",
            "description": "Method in catalog but never used in codebase",
            "action": "Consider if method is obsolete"
        })
    
    # Warning Type 2: Used but not calibrated
    for class_name, method_name in sorted(list(used_not_registry)[:20]):  # Top 20
        # Check calibration decision
        fqn = f"{class_name}.{method_name}"
        
        # Decisions are now method-keyed, not category-keyed
        decision_data = decisions_data.get('decisions', {}).get(fqn)
        
        if decision_data and decision_data.get('decision') == "REQUIRES_CALIBRATION":
            warnings.append({
                "type": "USED_NOT_CALIBRATED",
                "severity": "MEDIUM",
                "method": fqn,
                "description": "Method is used and requires calibration but not in registry",
                "action": f"Add calibration entry (auto-decision: {decision_data.get('decision')})"
            })
    
    # Generate report
    report = {
        "metadata": {
            "generated_at": "2025-11-08",
            "audit_version": "1.0.0"
        },
        "inventory": {
            "catalog_methods": len(catalog_methods),
            "registry_methods": len(registry_methods),
            "used_methods": len(used_methods),
        },
        "alignment": {
            "catalog_and_registry": len(catalog_and_registry),
            "catalog_not_registry": len(catalog_not_registry),
            "registry_not_catalog": len(registry_not_catalog),
            "used_not_catalog": len(used_not_catalog),
            "catalog_not_used": len(catalog_not_used),
            "used_not_registry": len(used_not_registry),
        },
        "defects": defects,
        "acceptable_divergence": acceptable_divergence,
        "warnings": warnings[:50],  # Limit warnings
        "alignment_score": {
            "catalog_registry_alignment": round(len(catalog_and_registry) / max(len(catalog_methods), 1) * 100, 2),
            "catalog_usage_alignment": round(len(catalog_methods - catalog_not_used) / max(len(catalog_methods), 1) * 100, 2),
            "overall_integrity": "PASS" if len(defects) == 0 else "FAIL"
        }
    }
    
    # Write report
    output_path = repo_root / "config" / "alignment_audit_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n\n[DEFECT REPORT]")
    print(f"  Total CRITICAL defects: {len(defects)}")
    
    if defects:
        print(f"\n  CRITICAL defects (require action):")
        for defect in defects[:10]:
            print(f"    {defect['type']}: {defect['method']}")
            print(f"      → {defect['description']}")
            print(f"      Action: {defect['action']}")
    
    print(f"\n\n[ACCEPTABLE DIVERGENCE]")
    print(f"  Total acceptable divergences: {len(acceptable_divergence)}")
    print(f"  (Registry methods not in catalog but unused - per CATALOG_REGISTRY_ALIGNMENT_POLICY.md)")
    
    if acceptable_divergence and len(acceptable_divergence) <= 10:
        print(f"\n  All {len(acceptable_divergence)} acceptable divergences:")
        for item in acceptable_divergence:
            print(f"    {item['method']}")
    elif acceptable_divergence:
        print(f"\n  Sample acceptable divergences (first 5 of {len(acceptable_divergence)}):")
        for item in acceptable_divergence[:5]:
            print(f"    {item['method']}")
        print(f"  See CATALOG_REGISTRY_ALIGNMENT_POLICY.md for full policy")
    
    print(f"\n\n[WARNING REPORT]")
    print(f"  Total warnings: {len(warnings)}")
    
    if warnings:
        print(f"\n  Sample warnings (first 5):")
        for warning in warnings[:5]:
            print(f"    {warning['type']}: {warning['method']}")
            print(f"      → {warning['description']}")
    
    print(f"\n\n[ALIGNMENT SCORES]")
    print(f"  Catalog-Registry alignment: {report['alignment_score']['catalog_registry_alignment']}%")
    print(f"  Catalog-Usage alignment: {report['alignment_score']['catalog_usage_alignment']}%")
    print(f"  Overall integrity: {report['alignment_score']['overall_integrity']}")
    
    print(f"\n✓ Audit report written to: {output_path}")
    
    # Policy-aware exit
    if len(defects) > 0:
        print(f"\n❌ AUDIT FAILED: {len(defects)} CRITICAL defects found")
        print("   Fix critical defects before proceeding")
        print(f"\n   Note: {len(acceptable_divergence)} acceptable divergences documented")
        print("   See CATALOG_REGISTRY_ALIGNMENT_POLICY.md for alignment policy")
        return 1
    else:
        print(f"\n✅ AUDIT PASSED: No critical defects found")
        print(f"   ({len(acceptable_divergence)} acceptable divergences per policy)")
        return 0


if __name__ == "__main__":
    sys.exit(main())
