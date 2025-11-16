#!/usr/bin/env python3
"""
CI/CD Integration Script for Signature Validation
=================================================

Implements automated signature consistency checking as part of the CI/CD pipeline.
This script should be run as a pre-commit hook or CI step to detect signature drift.

Features:
- Automated signature regression diffing
- Breaking change detection
- Integration with signature registry
- Exit codes for CI/CD integration

Usage:
    python signature_ci_check.py [--project-root PATH] [--fail-on-changes]

Author: CI/CD Integration Team
Version: 1.0.0
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path
from saaaaaa.utils.signature_validator import (
    FunctionSignature,
    SignatureMismatch,
    SignatureRegistry,
    audit_project_signatures,
)

logger = logging.getLogger(__name__)

class SignatureCIChecker:
    """
    CI/CD integration for signature validation
    Implements regression diffing as described in the mitigation plan
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.registry = SignatureRegistry(project_root / "data" / "signature_registry.json")
        self.changed_signatures: list[tuple[str, FunctionSignature, FunctionSignature]] = []
        self.new_signatures: list[FunctionSignature] = []
        self.mismatches: list[SignatureMismatch] = []

    def check_signature_changes(self) -> tuple[int, int, int]:
        """
        Check for signature changes in the project

        Returns:
            Tuple of (changed_count, new_count, total_count)
        """
        logger.info("Auditing repository for signature mismatches")
        self.mismatches = audit_project_signatures(
            self.project_root,
            output_path=self.project_root / "data" / "signature_audit_report.json",
        )

        changed_count = len(self.mismatches)
        new_count = len(self.new_signatures)
        total_count = len(self.registry.signatures)

        return changed_count, new_count, total_count

    def generate_diff_report(self) -> dict[str, Any]:
        """Generate a detailed diff report of signature changes"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "summary": {
                "total_signatures": len(self.registry.signatures),
                "changed_signatures": len(self.changed_signatures),
                "new_signatures": len(self.new_signatures),
                "mismatches_detected": len(self.mismatches),
            },
            "changed_signatures": [
                {
                    "function": key,
                    "old_signature": old.to_dict(),
                    "new_signature": new.to_dict(),
                    "breaking_change": self._is_breaking_change(old, new)
                }
                for key, old, new in self.changed_signatures
            ],
            "new_signatures": [sig.to_dict() for sig in self.new_signatures],
            "mismatches": [m.__dict__ for m in self.mismatches],
        }

        return report

    def _is_breaking_change(self, old: FunctionSignature, new: FunctionSignature) -> bool:
        """
        Determine if a signature change is a breaking change

        Breaking changes include:
        - Removed required parameters
        - Changed parameter order
        - Changed return type (in strict mode)
        """
        # Check if required parameters were removed
        old_params = set(old.parameters)
        new_params = set(new.parameters)

        removed_params = old_params - new_params
        if removed_params:
            return True

        # Check if parameter order changed (for positional arguments)
        return old.parameters != new.parameters

    def export_diff_report(self, output_path: Path):
        """Export diff report to JSON"""
        report = self.generate_diff_report()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Exported signature diff report to {output_path}")

    def print_summary(self):
        """Print a summary of signature changes to console"""
        print("\n" + "=" * 70)
        print("SIGNATURE VALIDATION SUMMARY")
        print("=" * 70)

        changed = len(self.changed_signatures)
        new = len(self.new_signatures)
        total = len(self.registry.signatures)

        print(f"Total registered signatures: {total}")
        print(f"Changed signatures: {changed}")
        print(f"New signatures: {new}")
        print(f"Mismatches detected: {len(self.mismatches)}")

        if self.changed_signatures:
            print("\nChanged Signatures:")
            for key, old, new in self.changed_signatures[:10]:  # Show first 10
                breaking = " [BREAKING]" if self._is_breaking_change(old, new) else ""
                print(f"  - {key}{breaking}")
                print(f"    Old: {old.parameters}")
                print(f"    New: {new.parameters}")

        if len(self.changed_signatures) > 10:
            print(f"  ... and {len(self.changed_signatures) - 10} more")

        if self.mismatches:
            print("\nSignature Mismatches:")
            for mismatch in self.mismatches[:10]:
                print(f"  - {mismatch.caller_module}:{mismatch.caller_line} → {mismatch.callee_module}.{mismatch.callee_function}")
                print(f"    Expected: {mismatch.expected_signature}")
                print(f"    Actual:   {mismatch.actual_call}")
                print(f"    Severity: {mismatch.severity}")
            if len(self.mismatches) > 10:
                print(f"  ... and {len(self.mismatches) - 10} more")

        print("=" * 70 + "\n")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CI/CD Signature Validation Check"
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path("."),
        help="Project root directory (default: current directory)"
    )
    parser.add_argument(
        "--fail-on-changes",
        action="store_true",
        help="Exit with non-zero code if signature changes detected"
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with non-zero code only if breaking changes detected"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/signature_diff_report.json"),
        help="Output path for diff report"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Run signature check
    checker = SignatureCIChecker(args.project_root)
    changed, new, total = checker.check_signature_changes()

    # Export report
    checker.export_diff_report(args.output)

    # Print summary
    checker.print_summary()

    # Determine exit code
    exit_code = 0

    if args.fail_on_breaking:
        # Check if any changes are breaking
        breaking_changes = [
            key for key, old, new in checker.changed_signatures
            if checker._is_breaking_change(old, new)
        ]
        if breaking_changes:
            print(f"ERROR: {len(breaking_changes)} breaking signature changes detected!")
            print("Breaking changes require manual review and approval.")
            exit_code = 1
    elif args.fail_on_changes:
        if changed > 0:
            print(f"ERROR: {changed} signature changes detected!")
            print("Signature changes require manual review and approval.")
            exit_code = 1

    # Also run audit for mismatches
    logger.info("Running signature audit for mismatches...")
    mismatches = audit_project_signatures(
        args.project_root,
        output_path=args.output.parent / "signature_audit_report.json"
    )

    if mismatches:
        print(f"\nWARNING: {len(mismatches)} signature mismatches detected in code!")
        print("See signature_audit_report.json for details.")
        if args.fail_on_changes:
            exit_code = 1

    sys.exit(exit_code)

if __name__ == "__main__":
    main()
