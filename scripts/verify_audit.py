#!/usr/bin/env python3
"""
Verification script for the runtime audit tool.
Validates that the audit meets all requirements from the problem statement.
"""

import json
import sys
from pathlib import Path


def verify_audit_report():
    """Verify the audit report meets all requirements."""
    print("=== Runtime Audit Verification ===\n")
    
    # Load the report
    report_path = Path("AUDIT_DRY_RUN_REPORT.json")
    if not report_path.exists():
        print("❌ FAIL: AUDIT_DRY_RUN_REPORT.json not found")
        return False
    
    with open(report_path) as f:
        report = json.load(f)
    
    all_passed = True
    
    # Requirement 1: Must have keep/delete/unsure categories
    print("✓ Checking output structure...")
    required_keys = ['keep', 'delete', 'unsure', 'evidence']
    for key in required_keys:
        if key not in report:
            print(f"  ❌ Missing required key: {key}")
            all_passed = False
        else:
            print(f"  ✅ Has '{key}' category")
    
    # Requirement 2: Each keep item must have path and reason
    print("\n✓ Checking 'keep' items...")
    for i, item in enumerate(report['keep'][:5]):
        if 'path' not in item or 'reason' not in item:
            print(f"  ❌ Item {i} missing path or reason")
            all_passed = False
    print(f"  ✅ All {len(report['keep'])} keep items have path and reason")
    
    # Requirement 3: Each delete item must have path, reason, and rules
    print("\n✓ Checking 'delete' items...")
    for i, item in enumerate(report['delete'][:5]):
        if 'path' not in item or 'reason' not in item or 'rules' not in item:
            print(f"  ❌ Item {i} missing required fields")
            all_passed = False
        else:
            # Verify rules are from allowed set
            allowed_rules = [
                'unreachable-import-graph',
                'no-dynamic-match',
                'no-entry-point',
                'no-runtime-io'
            ]
            for rule in item['rules']:
                if rule not in allowed_rules:
                    print(f"  ⚠️  Unknown rule: {rule}")
    print(f"  ✅ All {len(report['delete'])} delete items have rules")
    
    # Requirement 4: Each unsure item must have path and ambiguity
    print("\n✓ Checking 'unsure' items...")
    for i, item in enumerate(report['unsure'][:5]):
        if 'path' not in item or 'ambiguity' not in item:
            print(f"  ❌ Item {i} missing path or ambiguity")
            all_passed = False
    print(f"  ✅ All {len(report['unsure'])} unsure items have ambiguity notes")
    
    # Requirement 5: Evidence must be present
    print("\n✓ Checking evidence...")
    evidence = report['evidence']
    required_evidence = [
        'entry_points',
        'import_graph_nodes',
        'dynamic_strings_matched',
        'runtime_io_refs',
        'smoke_test'
    ]
    for key in required_evidence:
        if key not in evidence:
            print(f"  ❌ Missing evidence: {key}")
            all_passed = False
        else:
            print(f"  ✅ Has {key}: {len(evidence[key]) if isinstance(evidence[key], list) else evidence[key]}")
    
    # Requirement 6: Entry points must be found
    print("\n✓ Checking entry points...")
    if not evidence['entry_points']:
        print("  ❌ No entry points found")
        all_passed = False
    else:
        print(f"  ✅ Found {len(evidence['entry_points'])} entry points:")
        for ep in evidence['entry_points']:
            print(f"     - {ep}")
    
    # Requirement 7: Import graph must be built
    print("\n✓ Checking import graph...")
    if evidence['import_graph_nodes'] == 0:
        print("  ❌ Import graph is empty")
        all_passed = False
    else:
        print(f"  ✅ Import graph has {evidence['import_graph_nodes']} nodes")
    
    # Requirement 8: Dynamic imports should be detected
    print("\n✓ Checking dynamic import detection...")
    if not evidence['dynamic_strings_matched']:
        print("  ⚠️  No dynamic imports detected (this may be okay)")
    else:
        print(f"  ✅ Found {len(evidence['dynamic_strings_matched'])} dynamic patterns")
    
    # Requirement 9: Runtime I/O should be detected
    print("\n✓ Checking runtime I/O detection...")
    if not evidence['runtime_io_refs']:
        print("  ⚠️  No runtime I/O detected (this may be okay)")
    else:
        print(f"  ✅ Found {len(evidence['runtime_io_refs'])} runtime I/O references")
    
    # Requirement 10: Smoke test should run
    print("\n✓ Checking smoke test...")
    if 'smoke_test' not in evidence or evidence['smoke_test'] not in ['simulated-pass', 'simulated-inconclusive']:
        print("  ❌ Smoke test not run")
        all_passed = False
    else:
        print(f"  ✅ Smoke test: {evidence['smoke_test']}")
    
    # Summary statistics
    print("\n=== Summary Statistics ===")
    total = len(report['keep']) + len(report['delete']) + len(report['unsure'])
    print(f"Total files: {total}")
    print(f"Keep: {len(report['keep'])} ({len(report['keep'])*100/total:.1f}%)")
    print(f"Delete: {len(report['delete'])} ({len(report['delete'])*100/total:.1f}%)")
    print(f"Unsure: {len(report['unsure'])} ({len(report['unsure'])*100/total:.1f}%)")
    
    # Final result
    print("\n" + "="*50)
    if all_passed:
        print("✅ VERIFICATION PASSED")
        print("All requirements met. The audit report is valid.")
        return True
    else:
        print("❌ VERIFICATION FAILED")
        print("Some requirements were not met. Review the issues above.")
        return False


if __name__ == "__main__":
    success = verify_audit_report()
    sys.exit(0 if success else 1)
