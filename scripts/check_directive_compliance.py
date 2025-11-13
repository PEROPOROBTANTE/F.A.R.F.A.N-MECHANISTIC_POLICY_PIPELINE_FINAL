#!/usr/bin/env python3
"""Directive Compliance Checker

This script validates that the repository complies with ALL directive requirements
from the problem statement:

1. Universal method coverage - no filters, no exceptions
2. Single canonical catalog - no conceptual splits
3. Machine-readable calibration requirements
4. Complete calibration tracking (centralized vs embedded)
5. Transitional cases explicitly managed
6. Stage-based implementation tracking

Exit codes:
  0 - Full compliance
  1 - Compliance violations found
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class ComplianceViolation:
    """A directive compliance violation."""
    severity: str  # "critical", "high", "medium", "low"
    requirement: str  # Which directive requirement
    description: str
    remediation: str


class DirectiveComplianceChecker:
    """Checker for directive compliance."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.violations: List[ComplianceViolation] = []
        
        # Load artifacts
        self.catalog = self._load_catalog()
        self.appendix = self._load_appendix()
        self.calibration_registry = self._load_calibration_registry()
    
    def _load_catalog(self) -> Dict[str, Any]:
        """Load canonical method catalog."""
        catalog_path = self.repo_root / "config" / "canonical_method_catalog.json"
        if not catalog_path.exists():
            raise FileNotFoundError(f"Canonical catalog not found: {catalog_path}")
        
        with open(catalog_path) as f:
            return json.load(f)
    
    def _load_appendix(self) -> Dict[str, Any]:
        """Load embedded calibration appendix."""
        appendix_path = self.repo_root / "config" / "embedded_calibration_appendix.json"
        if not appendix_path.exists():
            return {'metadata': {'total_embedded': 0}, 'embedded_calibrations': []}
        
        with open(appendix_path) as f:
            return json.load(f)
    
    def _load_calibration_registry(self) -> str:
        """Load calibration registry source code."""
        registry_path = self.repo_root / "src" / "saaaaaa" / "core" / "orchestrator" / "calibration_registry.py"
        if not registry_path.exists():
            return ""
        
        with open(registry_path) as f:
            return f.read()
    
    def check_all(self) -> bool:
        """Run all compliance checks."""
        print("=" * 80)
        print("DIRECTIVE COMPLIANCE CHECKER")
        print("=" * 80)
        print()
        
        # Check each requirement
        self.check_requirement_1_universal_coverage()
        self.check_requirement_2_mechanical_decidability()
        self.check_requirement_3_calibration_implementation()
        self.check_requirement_4_transitional_cases()
        self.check_requirement_5_stage_enforcement()
        
        # Report results
        self._report_results()
        
        return len([v for v in self.violations if v.severity in ["critical", "high"]]) == 0
    
    def check_requirement_1_universal_coverage(self):
        """Requirement 1: Universal method coverage, no filters."""
        print("Checking Requirement 1: Universal Coverage...")
        
        # Check directive compliance flags
        compliance = self.catalog['metadata']['directive_compliance']
        
        if not compliance.get('universal_coverage'):
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 1 - Universal Coverage",
                description="universal_coverage flag not set to true",
                remediation="Rebuild catalog with universal coverage enabled"
            ))
        
        if not compliance.get('no_filters_applied'):
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 1 - Universal Coverage",
                description="no_filters_applied flag not set to true",
                remediation="Rebuild catalog without any filters"
            ))
        
        # Check for suspicious exclusions
        total_methods = self.catalog['summary']['total_methods']
        if total_methods < 1000:
            self.violations.append(ComplianceViolation(
                severity="high",
                requirement="Requirement 1 - Universal Coverage",
                description=f"Suspiciously low method count: {total_methods}",
                remediation="Verify all Python files are being scanned"
            ))
        
        # Check for fabricated splits
        if 'subset_catalog' in self.catalog or 'filtered_methods' in self.catalog:
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 1 - Universal Coverage",
                description="Fabricated catalog split detected",
                remediation="Remove conceptual splits - maintain single canonical catalog"
            ))
        
        print(f"  ✓ Total methods tracked: {total_methods}")
    
    def check_requirement_2_mechanical_decidability(self):
        """Requirement 2: Calibration requirements mechanically decidable."""
        print("Checking Requirement 2: Mechanical Decidability...")
        
        methods = self.catalog['methods']
        compliance = self.catalog['metadata']['directive_compliance']
        
        # Check all methods have requires_calibration flag
        missing_flag = 0
        for method in methods:
            if 'requires_calibration' not in method:
                missing_flag += 1
        
        if missing_flag > 0:
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 2 - Mechanical Decidability",
                description=f"{missing_flag} methods missing requires_calibration flag",
                remediation="Rebuild catalog to add calibration flags to all methods"
            ))
        
        # Check for undocumented heuristics
        if not compliance.get('machine_readable_flags'):
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 2 - Mechanical Decidability",
                description="machine_readable_flags not set to true",
                remediation="Ensure all calibration decisions are machine-readable"
            ))
        
        # Check for improvised eligibility criteria
        methods_requiring = len([m for m in methods if m.get('requires_calibration')])
        print(f"  ✓ Methods requiring calibration: {methods_requiring}/{len(methods)}")
    
    def check_requirement_3_calibration_implementation(self):
        """Requirement 3: Calibration implementation status tracking."""
        print("Checking Requirement 3: Calibration Implementation Tracking...")
        
        by_status = self.catalog['summary']['by_calibration_status']
        
        # Check all status categories exist
        required_statuses = {'centralized', 'embedded', 'none', 'unknown'}
        for status in required_statuses:
            if status not in by_status:
                self.violations.append(ComplianceViolation(
                    severity="critical",
                    requirement="Requirement 3 - Calibration Tracking",
                    description=f"Missing calibration status category: {status}",
                    remediation="Rebuild catalog with all calibration status categories"
                ))
        
        # Check embedded calibrations are tracked
        embedded_count = by_status.get('embedded', 0)
        appendix_count = self.appendix['metadata']['total_embedded']
        
        if embedded_count != appendix_count:
            self.violations.append(ComplianceViolation(
                severity="high",
                requirement="Requirement 3 - Calibration Tracking",
                description=f"Embedded count mismatch: catalog={embedded_count}, appendix={appendix_count}",
                remediation="Rebuild embedded calibration appendix"
            ))
        
        # Check centralized calibrations reference registry
        centralized = self.catalog['calibration_tracking'].get('centralized', [])
        for method in centralized[:10]:  # Sample
            if 'calibration_registry.py' not in method.get('calibration_location', ''):
                self.violations.append(ComplianceViolation(
                    severity="medium",
                    requirement="Requirement 3 - Calibration Tracking",
                    description=f"Centralized method {method['canonical_name']} doesn't reference registry",
                    remediation="Update calibration_location to reference calibration_registry.py"
                ))
                break
        
        print(f"  ✓ Centralized: {by_status.get('centralized', 0)}")
        print(f"  ✓ Embedded: {embedded_count}")
        print(f"  ✓ Unknown: {by_status.get('unknown', 0)}")
    
    def check_requirement_4_transitional_cases(self):
        """Requirement 4: Transitional cases explicitly managed."""
        print("Checking Requirement 4: Transitional Cases...")
        
        embedded_count = self.catalog['summary']['by_calibration_status'].get('embedded', 0)
        
        if embedded_count > 0:
            # Check appendix exists
            appendix_path = self.repo_root / "config" / "embedded_calibration_appendix.json"
            if not appendix_path.exists():
                self.violations.append(ComplianceViolation(
                    severity="critical",
                    requirement="Requirement 4 - Transitional Cases",
                    description=f"{embedded_count} embedded calibrations but no appendix found",
                    remediation="Run detect_embedded_calibrations.py to create appendix"
                ))
            
            # Check markdown documentation exists
            md_path = self.repo_root / "config" / "embedded_calibration_appendix.md"
            if not md_path.exists():
                self.violations.append(ComplianceViolation(
                    severity="medium",
                    requirement="Requirement 4 - Transitional Cases",
                    description="Migration appendix markdown documentation missing",
                    remediation="Generate embedded_calibration_appendix.md"
                ))
            
            # Check all embedded have migration metadata
            embedded = self.catalog['calibration_tracking'].get('embedded', [])
            for method in embedded:
                if 'embedded_calibration' not in method:
                    self.violations.append(ComplianceViolation(
                        severity="high",
                        requirement="Requirement 4 - Transitional Cases",
                        description=f"Embedded method {method['canonical_name']} missing migration metadata",
                        remediation="Run detect_embedded_calibrations.py and update catalog"
                    ))
                    break
        
        print(f"  ✓ Transitional cases tracked: {embedded_count}")
        
        # Check for critical priority items
        if embedded_count > 0:
            by_priority = self.appendix['metadata'].get('by_priority', {})
            critical = by_priority.get('critical', 0)
            high = by_priority.get('high', 0)
            
            if critical > 0:
                self.violations.append(ComplianceViolation(
                    severity="high",
                    requirement="Requirement 4 - Transitional Cases",
                    description=f"{critical} CRITICAL priority embedded calibrations need immediate migration",
                    remediation="Migrate critical priority methods to calibration_registry.py"
                ))
            
            if high > 5:
                self.violations.append(ComplianceViolation(
                    severity="medium",
                    requirement="Requirement 4 - Transitional Cases",
                    description=f"{high} HIGH priority embedded calibrations need migration",
                    remediation="Plan migration for high priority methods"
                ))
    
    def check_requirement_5_stage_enforcement(self):
        """Requirement 5: Stage-based implementation enforcement."""
        print("Checking Requirement 5: Stage Enforcement...")
        
        # Check stage documentation exists
        stages_doc = self.repo_root / "IMPLEMENTATION_STAGES.md"
        if not stages_doc.exists():
            self.violations.append(ComplianceViolation(
                severity="high",
                requirement="Requirement 5 - Stage Enforcement",
                description="Implementation stages documentation missing",
                remediation="Create IMPLEMENTATION_STAGES.md with stage tracking"
            ))
        
        # Check canonical catalog is single source of truth
        if not self.catalog['metadata']['directive_compliance'].get('single_canonical_source'):
            self.violations.append(ComplianceViolation(
                severity="critical",
                requirement="Requirement 5 - Stage Enforcement",
                description="Single canonical source flag not set",
                remediation="Ensure catalog is sole source of truth for methods"
            ))
        
        # Check for parallel math or hidden defaults
        unknown_count = self.catalog['summary']['by_calibration_status'].get('unknown', 0)
        total_requiring = len([m for m in self.catalog['methods'] if m.get('requires_calibration')])
        
        if unknown_count > total_requiring * 0.3:  # More than 30% unknown
            self.violations.append(ComplianceViolation(
                severity="high",
                requirement="Requirement 5 - Stage Enforcement",
                description=f"High unknown calibration status: {unknown_count}/{total_requiring} ({100*unknown_count/total_requiring:.1f}%)",
                remediation="Investigate unknown status methods to ensure no hidden defaults"
            ))
        
        print(f"  ✓ Stage tracking: {stages_doc.exists()}")
        print(f"  ✓ Unknown status: {unknown_count} ({100*unknown_count/len(self.catalog['methods']):.1f}%)")
    
    def _report_results(self):
        """Report compliance results."""
        print()
        print("=" * 80)
        print("COMPLIANCE REPORT")
        print("=" * 80)
        print()
        
        if not self.violations:
            print("✅ FULL COMPLIANCE")
            print()
            print("All directive requirements met:")
            print("  ✓ Universal coverage - no filters or exceptions")
            print("  ✓ Mechanical decidability - all flags present")
            print("  ✓ Complete tracking - all calibrations visible")
            print("  ✓ Transitional cases - explicitly managed")
            print("  ✓ Stage enforcement - documented and tracked")
            return
        
        # Group violations by severity
        by_severity = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for violation in self.violations:
            by_severity[violation.severity].append(violation)
        
        # Report critical and high first
        critical_count = len(by_severity['critical'])
        high_count = len(by_severity['high'])
        
        if critical_count > 0 or high_count > 0:
            print(f"❌ COMPLIANCE VIOLATIONS: {critical_count} critical, {high_count} high")
        else:
            print(f"⚠️  MINOR ISSUES: {len(self.violations)} warnings")
        
        print()
        
        # Detail each severity level
        for severity in ['critical', 'high', 'medium', 'low']:
            violations = by_severity[severity]
            if not violations:
                continue
            
            icon = "❌" if severity in ['critical', 'high'] else "⚠️"
            print(f"{icon} {severity.upper()} ({len(violations)}):")
            print()
            
            for i, violation in enumerate(violations, 1):
                print(f"  {i}. {violation.requirement}")
                print(f"     Issue: {violation.description}")
                print(f"     Fix: {violation.remediation}")
                print()


def main():
    """Main entry point."""
    repo_root = Path(__file__).parent.parent
    
    try:
        checker = DirectiveComplianceChecker(repo_root)
        compliant = checker.check_all()
        
        return 0 if compliant else 1
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun these commands first:")
        print("  python3 scripts/build_canonical_method_catalog.py")
        print("  python3 scripts/detect_embedded_calibrations.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
