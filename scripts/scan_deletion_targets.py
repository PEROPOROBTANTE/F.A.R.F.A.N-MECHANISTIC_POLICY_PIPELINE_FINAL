#!/usr/bin/env python3
"""
PHASE 1: MASSIVE DELETION SCRIPT
Identifies and deletes contaminated and unnecessary files for calibration system.

ZERO TOLERANCE policy for:
- Old documentation versions
- Contaminated calibration files
- Duplicate/parallel systems
- Legacy reports and audits
"""

from pathlib import Path
import json

PROJECT_ROOT = Path(".")

# Files to DELETE - organized by category
FILES_TO_DELETE = {
    "OLD_CANONIC_METHODS": [
        # Old versions of canonic methods (keep only the one in MIGRATION_ARTIFACTS)
        "canonic_calibration_methods.md",  # Will be replaced with new version
    ],

    "LEGACY_DOCUMENTATION": [
        # Old architecture/audit docs (redundant with migration artifacts)
        "ACTUAL_INTEGRATION_EVIDENCE.md",
        "ADVANCED_TESTING_STRATEGY.md",
        "AGGREGATION_AUDIT_FINDINGS.md",
        "AGGREGATION_DESIGN_RATIONALE.md",
        "ALIGNMENT_AUDIT_RESPONSE.md",
        "ALIGNMENT_CERTIFICATION_PR330.md",
        "ANALYSIS.md",
        "ARCHITECTURAL_VIOLATIONS_FOUND.md",
        "ARCHITECTURE_ENFORCEMENT_SUMMARY.md",
        "ARCHITECTURE_UNDERSTANDING.md",
        "ARGROUTER_TRANSITION_SUMMARY.md",
        "ASSESSMENT_REAL_ISSUES.md",
        "ATROZ_IMPLEMENTATION_GUIDE.md",
        "AUDIT_COMPLIANCE_REPORT.md",
        "AUDIT_FIX_PLAN.md",
        "AUDIT_PHASE2_CRITICAL_FINDINGS.md",
        "AUDIT_PHASE2_FIXES_SUMMARY.md",
        "AUDIT_README.md",
        "AUDIT_REPORT.md",
        "BUILD_HYGIENE.md",
        "CANONICAL_FLUX.md",
        "CANONICAL_INTEGRATION_PLAN.md",
        "FLUX_CANONICAL.md",
        "IMPLEMENTATION_SUMMARY_CANONICAL_SYSTEMS.md",
        "CANONICAL_SYSTEMS_ENGINEERING.md",
    ],

    "REDUNDANT_CALIBRATION_DOCS": [
        # Redundant with MIGRATION_ARTIFACTS/08_FORMAL_SPEC/
        "CALIBRATION_IMPLEMENTATION_REPORT.md",  # Exists in migration artifacts
        "CALIBRATION_IMPLEMENTATION_SUMMARY.md",  # Exists in migration artifacts
        "CALIBRATION_SYSTEM_AUDIT.md",  # Exists in migration artifacts
        "CANONICAL_METHOD_CATALOG.md",  # Exists in migration artifacts
        "CANONICAL_METHOD_CATALOG_QUICKSTART.md",  # Exists in migration artifacts
        "METHOD_REGISTRATION_POLICY.md",  # Exists in migration artifacts
    ],

    "TEMPORARY_ANALYSIS_FILES": [
        "analyze_executor_methods.py",
        "audit_signal_packs.py",
        "class_usage_report.txt",
        "executor_dependencies.csv",
        "executor_methods_mapping.json",
        "executor_methods_summary.md",
        "update_monolith_methods.py",
        "verify_hash.py",
    ],

    "OLD_METHOD_CATALOGS": [
        # Keep only the ones in MIGRATION_ARTIFACTS
        "canonical_method_catalogue_v2_OLD_BACKUP.json",
        "method_parameters_draft.json",  # Draft, not final
        "catalogue_v1_to_v2_diff.json",  # Historical, not needed
    ],

    "AUDIT_SUMMARY_CLEANUP": [
        "AUDIT_SUMMARY.md",  # Superseded by JOBFRONT_1_2_AUDIT_REPORT.md
    ],
}

# Files to KEEP (explicitly protected)
PROTECTED_FILES = [
    "CALIBRATION_MIGRATION_CONTRACT.md",  # Keep in root (will be moved to proper location)
    "JOBFRONT_1_2_AUDIT_REPORT.md",  # Keep in root (will be moved)
    "method_classification.json",  # Keep in root (will be moved)
    "ARCHITECTURE.md",  # Main architecture doc
    "README.md",  # Project readme
    "requirements.txt",
    ".gitignore",
    "setup.py",
    "pyproject.toml",
]

# Directories to KEEP (protected)
PROTECTED_DIRS = [
    "MIGRATION_ARTIFACTS_FAKE_TO_REAL",  # Our organized collection
    "src",
    "tests",
    "config",
    "data",
    "scripts",
    "docs",
    ".git",
    ".github",
    "venv",
    "node_modules",
]


def scan_files_to_delete():
    """Scan and report files that will be deleted."""

    to_delete = []

    for category, files in FILES_TO_DELETE.items():
        print(f"\n{category}:")
        for filename in files:
            filepath = PROJECT_ROOT / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"  ✓ {filename} ({size:,} bytes)")
                to_delete.append((category, filepath))
            else:
                print(f"  ✗ {filename} (not found)")

    return to_delete


def create_deletion_report(to_delete):
    """Create detailed deletion report before executing."""

    report = {
        "total_files": len(to_delete),
        "total_size_bytes": sum(f[1].stat().st_size for f in to_delete),
        "categories": {},
        "files": []
    }

    for category, filepath in to_delete:
        if category not in report["categories"]:
            report["categories"][category] = {
                "count": 0,
                "size_bytes": 0,
                "files": []
            }

        size = filepath.stat().st_size
        report["categories"][category]["count"] += 1
        report["categories"][category]["size_bytes"] += size
        report["categories"][category]["files"].append(str(filepath))

        report["files"].append({
            "category": category,
            "path": str(filepath),
            "size_bytes": size
        })

    return report


def main():
    print("="*80)
    print("PHASE 1: MASSIVE DELETION - FILE IDENTIFICATION")
    print("="*80)

    # Scan
    to_delete = scan_files_to_delete()

    # Create report
    report = create_deletion_report(to_delete)

    # Summary
    print("\n" + "="*80)
    print("DELETION SUMMARY")
    print("="*80)
    print(f"\nTotal files to delete: {report['total_files']}")
    print(f"Total size: {report['total_size_bytes']:,} bytes ({report['total_size_bytes'] / 1024 / 1024:.2f} MB)")

    print("\nBy category:")
    for category, info in report["categories"].items():
        print(f"  {category}:")
        print(f"    Files: {info['count']}")
        print(f"    Size: {info['size_bytes']:,} bytes ({info['size_bytes'] / 1024 / 1024:.2f} MB)")

    # Save report
    report_file = PROJECT_ROOT / "DELETION_REPORT.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n✅ Deletion report saved to: {report_file}")
    print("\nTo execute deletion, run:")
    print("  python3 scripts/execute_deletion.py")

    return report


if __name__ == "__main__":
    main()
