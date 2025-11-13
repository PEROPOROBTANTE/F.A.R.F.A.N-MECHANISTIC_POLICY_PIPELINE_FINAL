#!/usr/bin/env python3
"""Validate Canonical Method Catalog

This script validates that the canonical method catalog complies with
all directive requirements:

1. Universal coverage - no filters or exceptions
2. Machine-readable calibration flags
3. Complete calibration tracking
4. Transitional cases explicitly managed
5. Single source of truth

Exit codes:
  0 - All validation passed
  1 - Validation failures found
"""

import json
import sys
from pathlib import Path
from typing import List


class CatalogValidator:
    """Validator for canonical method catalog."""
    
    def __init__(self, catalog_path: Path):
        """Initialize validator."""
        with open(catalog_path) as f:
            self.catalog = json.load(f)
        
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.repo_root = catalog_path.parent.parent
    
    def validate_all(self) -> bool:
        """Run all validations."""
        print("=" * 80)
        print("CANONICAL METHOD CATALOG VALIDATION")
        print("=" * 80)
        print()
        
        # Run all validation checks
        self.validate_metadata()
        self.validate_universal_coverage()
        self.validate_unique_ids()
        self.validate_calibration_flags()
        self.validate_calibration_tracking()
        self.validate_migration_backlog()
        self.validate_layer_classification()
        
        # Print results
        print("\n" + "=" * 80)
        print("VALIDATION RESULTS")
        print("=" * 80)
        
        if self.errors:
            print(f"\n❌ FAILED: {len(self.errors)} errors found\n")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        else:
            print("\n✅ PASSED: All validations successful")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS: {len(self.warnings)} warnings\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print()
        return len(self.errors) == 0
    
    def validate_metadata(self):
        """Validate catalog metadata."""
        print("Validating metadata...")
        
        metadata = self.catalog.get('metadata', {})
        
        # Check required fields
        required = ['generated_at', 'version', 'total_methods', 'directive_compliance']
        for field in required:
            if field not in metadata:
                self.errors.append(f"Missing metadata field: {field}")
        
        # Check directive compliance flags
        compliance = metadata.get('directive_compliance', {})
        required_flags = [
            'universal_coverage',
            'machine_readable_flags',
            'no_filters_applied',
            'single_canonical_source'
        ]
        
        for flag in required_flags:
            if not compliance.get(flag):
                self.errors.append(f"Directive compliance flag not set: {flag}")
        
        print(f"  ✓ Metadata validated")
    
    def validate_universal_coverage(self):
        """Validate universal coverage requirement."""
        print("Validating universal coverage...")
        
        total_methods = len(self.catalog.get('methods', []))
        
        if total_methods == 0:
            self.errors.append("Catalog is empty - no methods found")
            return
        
        # Check that summary matches actual count
        summary_total = self.catalog['summary']['total_methods']
        if total_methods != summary_total:
            self.errors.append(
                f"Method count mismatch: summary={summary_total}, actual={total_methods}"
            )
        
        # Validate no filters were applied (check metadata flag)
        if not self.catalog['metadata']['directive_compliance']['no_filters_applied']:
            self.errors.append("Filters were applied - universal coverage violated")
        
        print(f"  ✓ Universal coverage: {total_methods} methods tracked")
    
    def validate_unique_ids(self):
        """Validate all methods have unique IDs."""
        print("Validating unique identifiers...")
        
        methods = self.catalog.get('methods', [])
        
        # Check unique_id uniqueness
        unique_ids = set()
        duplicates = []
        
        for method in methods:
            uid = method.get('unique_id')
            if not uid:
                self.errors.append(f"Method missing unique_id: {method.get('canonical_name', 'unknown')}")
            elif uid in unique_ids:
                duplicates.append(uid)
            else:
                unique_ids.add(uid)
        
        if duplicates:
            self.errors.append(f"Duplicate unique_ids found: {len(duplicates)} duplicates")
        
        # Check canonical_name uniqueness
        canonical_names = set()
        name_duplicates = []
        
        for method in methods:
            name = method.get('canonical_name')
            if not name:
                self.errors.append(f"Method missing canonical_name: {method.get('unique_id', 'unknown')}")
            elif name in canonical_names:
                name_duplicates.append(name)
            else:
                canonical_names.add(name)
        
        if name_duplicates:
            self.warnings.append(
                f"Duplicate canonical_names found: {len(name_duplicates)} duplicates"
            )
        
        print(f"  ✓ Unique IDs validated: {len(unique_ids)} unique methods")
    
    def validate_calibration_flags(self):
        """Validate machine-readable calibration flags."""
        print("Validating calibration flags...")
        
        methods = self.catalog.get('methods', [])
        
        valid_statuses = {'centralized', 'embedded', 'none', 'unknown'}
        
        invalid_count = 0
        missing_flag_count = 0
        
        for method in methods:
            # Check requires_calibration flag exists
            if 'requires_calibration' not in method:
                missing_flag_count += 1
                continue
            
            requires = method['requires_calibration']
            status = method.get('calibration_status')
            
            # Validate status is valid
            if status not in valid_statuses:
                invalid_count += 1
                continue
            
            # Validate consistency
            if requires and status == 'none':
                self.errors.append(
                    f"Inconsistent calibration: {method['canonical_name']} "
                    f"requires_calibration=True but status='none'"
                )
            
            if not requires and status in ['centralized', 'embedded']:
                self.errors.append(
                    f"Inconsistent calibration: {method['canonical_name']} "
                    f"requires_calibration=False but status='{status}'"
                )
        
        if missing_flag_count > 0:
            self.errors.append(f"{missing_flag_count} methods missing requires_calibration flag")
        
        if invalid_count > 0:
            self.errors.append(f"{invalid_count} methods have invalid calibration_status")
        
        print(f"  ✓ Calibration flags validated")
    
    def validate_calibration_tracking(self):
        """Validate complete calibration tracking."""
        print("Validating calibration tracking...")
        
        summary = self.catalog['summary']['by_calibration_status']
        tracking = self.catalog['calibration_tracking']
        
        # Verify counts match
        for status in ['centralized', 'embedded', 'none', 'unknown']:
            summary_count = summary.get(status, 0)
            tracking_count = len(tracking.get(status, []))
            
            if summary_count != tracking_count:
                self.errors.append(
                    f"Calibration count mismatch for '{status}': "
                    f"summary={summary_count}, tracking={tracking_count}"
                )
        
        # Check centralized calibrations reference registry
        centralized = tracking.get('centralized', [])
        for method in centralized:
            location = method.get('calibration_location', '')
            if 'calibration_registry.py' not in location:
                self.errors.append(
                    f"Centralized calibration {method['canonical_name']} "
                    f"does not reference calibration_registry.py"
                )
        
        # Check embedded calibrations have location
        embedded = tracking.get('embedded', [])
        for method in embedded:
            if not method.get('calibration_location'):
                self.errors.append(
                    f"Embedded calibration {method['canonical_name']} "
                    f"missing calibration_location"
                )
        
        print(f"  ✓ Calibration tracking: {summary['centralized']} centralized, "
              f"{summary['embedded']} embedded, {summary['unknown']} unknown")
    
    def validate_migration_backlog(self):
        """Validate migration backlog for embedded calibrations."""
        print("Validating migration backlog...")
        
        embedded_count = self.catalog['summary']['by_calibration_status']['embedded']
        
        # Check if appendix exists
        appendix_path = self.repo_root / 'config' / 'embedded_calibration_appendix.json'
        
        if embedded_count > 0 and not appendix_path.exists():
            self.errors.append(
                f"Migration backlog missing: {embedded_count} embedded calibrations "
                f"but no appendix found at {appendix_path}"
            )
            return
        
        if embedded_count > 0:
            # Validate appendix
            with open(appendix_path) as f:
                appendix = json.load(f)
            
            appendix_count = appendix['metadata']['total_embedded']
            
            if embedded_count != appendix_count:
                self.errors.append(
                    f"Migration backlog count mismatch: catalog={embedded_count}, "
                    f"appendix={appendix_count}"
                )
            
            # Check priority distribution
            by_priority = appendix['metadata']['by_priority']
            critical = by_priority.get('critical', 0)
            high = by_priority.get('high', 0)
            
            if critical > 0:
                self.warnings.append(
                    f"CRITICAL priority migrations needed: {critical} methods"
                )
            
            if high > 0:
                self.warnings.append(
                    f"HIGH priority migrations needed: {high} methods"
                )
            
            print(f"  ✓ Migration backlog: {embedded_count} methods tracked")
        else:
            print(f"  ✓ No migration backlog needed (0 embedded calibrations)")
    
    def validate_layer_classification(self):
        """Validate layer classification."""
        print("Validating layer classification...")
        
        by_layer = self.catalog['summary']['by_layer']
        
        # Check for unknown layer count
        unknown_count = by_layer.get('unknown', 0)
        total = sum(by_layer.values())
        
        if unknown_count > total * 0.15:  # More than 15% unknown
            self.warnings.append(
                f"High proportion of unknown layers: {unknown_count}/{total} "
                f"({100*unknown_count/total:.1f}%)"
            )
        
        # Validate layer values
        valid_layers = {
            'orchestrator', 'executor', 'analyzer', 'processor',
            'ingestion', 'utility', 'validation', 'contracts', 'unknown'
        }
        
        for layer in by_layer.keys():
            if layer not in valid_layers:
                self.warnings.append(f"Unexpected layer name: {layer}")
        
        print(f"  ✓ Layer classification: {len(by_layer)} layers, "
              f"{unknown_count} unknown ({100*unknown_count/total:.1f}%)")


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    catalog_path = repo_root / "config" / "canonical_method_catalog.json"
    
    if not catalog_path.exists():
        print(f"Error: Catalog not found at {catalog_path}")
        print("Run build_canonical_method_catalog.py first.")
        return 1
    
    validator = CatalogValidator(catalog_path)
    success = validator.validate_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
