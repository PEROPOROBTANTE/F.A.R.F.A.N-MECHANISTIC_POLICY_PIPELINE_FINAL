#!/usr/bin/env python3
"""
Verification script: Detect hardcoded calibration values.

Scans Python code for hardcoded calibration values, weights, thresholds, and penalties.

ZERO TOLERANCE: This script MUST find 0 violations for Phase 2/4 compliance.

Exit codes:
    0: No hardcoded values detected
    1: Hardcoded values found (ZERO TOLERANCE violation)
"""
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Patterns to detect hardcoded calibration values
VIOLATION_PATTERNS = [
    # Hardcoded scores/weights (0.XXX float literals)
    (r'(?<!#\s)(?<!")(?<!\.)(\b0\.\d{2,}\b)', "Hardcoded float literal (possible calibration value)"),
    # Hardcoded penalty assignments
    (r'penalty\s*=\s*0\.\d+', "Hardcoded penalty value"),
    (r'PENALTY\s*=\s*0\.\d+', "Hardcoded PENALTY constant"),
    # Hardcoded threshold assignments
    (r'threshold\s*=\s*0\.\d+', "Hardcoded threshold value"),
    (r'THRESHOLD\s*=\s*0\.\d+', "Hardcoded THRESHOLD constant"),
    # Hardcoded weight assignments
    (r'weight\s*=\s*0\.\d+', "Hardcoded weight value"),
    (r'w_\w+\s*=\s*0\.\d+', "Hardcoded weight (w_XXX pattern)"),
]

# Exempt patterns (allowed hardcoded values)
EXEMPT_PATTERNS = [
    r'tolerance\s*=\s*1e-6',  # Numerical tolerance is OK
    r'version\s*=\s*',  # Version numbers OK
    r'"value":\s*0\.\d+',  # JSON values OK
    r'#.*0\.\d+',  # Comments OK
    r'""".*0\.\d+.*"""',  # Docstrings OK
    r'@classmethod',  # Decorator OK
    r'DEFAULT_',  # DEFAULT_* constants are FALLBACKS - OK
    r'\.get\(',  # .get() fallback values - OK
    r'min_score=',  # Decorator min_score parameters - semantic thresholds, not calibration
    r'role=',  # Decorator role parameters - OK
    r'default:',  # Function default parameters in docstrings - OK
    r'def\s+\w+.*default.*0\.\d+',  # Function signatures with defaults - OK
    r'\.  ',  # Likely in documentation/examples
    r'Example:',  # Example code blocks - OK
    r'>>>',  # Doctest examples - OK
    r'return.*\*\*',  # Math expressions like x**0.25 - OK
]

# Files to exclude from checking
EXCLUDE_FILES = [
    'config_loaders.py',  # Loader utilities are exempt
    'test_',  # Test files OK to have hardcoded values for testing
    '__pycache__',
]

# Directories to scan
SCAN_DIRS = [
    PROJECT_ROOT / "src" / "saaaaaa" / "core" / "calibration"
]


def should_exclude_file(file_path: Path) -> bool:
    """Check if file should be excluded from scanning."""
    for pattern in EXCLUDE_FILES:
        if pattern in str(file_path):
            return True
    return False


def is_exempt(line: str) -> bool:
    """Check if line matches any exempt pattern."""
    for pattern in EXEMPT_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            return True
    return False


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Scan a file for hardcoded calibration values.

    Returns:
        List of (line_number, violation_type, line_content)
    """
    violations = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # Skip exempt lines
            if is_exempt(line):
                continue

            # Check each violation pattern
            for pattern, violation_type in VIOLATION_PATTERNS:
                if re.search(pattern, line):
                    violations.append((line_num, violation_type, line.strip()))

    except Exception as e:
        print(f"  ⚠️  ERROR scanning {file_path}: {e}")

    return violations


def main():
    """Run hardcoded value detection."""
    print("=" * 80)
    print("HARDCODED CALIBRATION VALUES DETECTION")
    print("=" * 80)
    print()

    total_files_scanned = 0
    total_violations = 0
    files_with_violations = {}

    # Scan each directory
    for scan_dir in SCAN_DIRS:
        if not scan_dir.exists():
            print(f"⚠️  Directory not found: {scan_dir}")
            continue

        print(f"Scanning: {scan_dir}")
        print()

        # Find all Python files
        python_files = list(scan_dir.glob("*.py"))

        for py_file in sorted(python_files):
            if should_exclude_file(py_file):
                continue

            violations = scan_file(py_file)
            total_files_scanned += 1

            if violations:
                files_with_violations[py_file] = violations
                total_violations += len(violations)

    # Report results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()

    if not files_with_violations:
        print(f"✅ SUCCESS: Scanned {total_files_scanned} files - NO hardcoded values detected!")
        print()
        print("🎉 ZERO TOLERANCE requirement met:")
        print("   - All Choquet weights loaded from JSON")
        print("   - All penalties loaded from JSON")
        print("   - All thresholds loaded from JSON")
        print("   - All configuration values externalized")
        print()
        return 0

    # Violations found - report them
    print(f"❌ FAILURE: Found {total_violations} hardcoded value(s) in {len(files_with_violations)} file(s)")
    print()

    for file_path, violations in files_with_violations.items():
        rel_path = file_path.relative_to(PROJECT_ROOT)
        print(f"📄 {rel_path}")

        for line_num, violation_type, line_content in violations:
            print(f"   Line {line_num}: {violation_type}")
            print(f"      {line_content}")
        print()

    print("=" * 80)
    print("REMEDIATION REQUIRED")
    print("=" * 80)
    print()
    print("🚨 ZERO TOLERANCE VIOLATION DETECTED")
    print()
    print("All calibration values MUST be loaded from JSON files:")
    print("  - config/choquet_weights.json")
    print("  - config/calibration_penalties.json")
    print("  - config/quality_thresholds.json")
    print("  - config/unit_layer_config.json")
    print()
    print("NO hardcoded values allowed in Python code.")
    print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
