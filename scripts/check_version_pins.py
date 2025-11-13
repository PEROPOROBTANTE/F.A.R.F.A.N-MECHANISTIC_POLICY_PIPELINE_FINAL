#!/usr/bin/env python3
"""
Check if dependencies have appropriate version constraints.

This script verifies that requirement files use exact pins (==) or properly
constrained ranges (>=X,<Y) for packages that need flexible dependency resolution.
Used in CI to enforce reproducible yet resolvable builds.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# Packages allowed to use constrained ranges due to complex dependency chains
ALLOWED_CONSTRAINED_RANGES = {
    'fastapi', 'huggingface-hub', 'numpy', 'pandas', 'pydantic',
    'safetensors', 'scikit-learn', 'scipy', 'sentence-transformers',
    'tokenizers', 'transformers'
}


def check_file_for_version_constraints(filepath: Path) -> Tuple[bool, List[str]]:
    """
    Check a requirements file for appropriate version constraints.
    
    Returns:
        Tuple of (has_violations, list_of_violations)
    """
    if not filepath.exists():
        return False, []
    
    violations = []
    # Match version specifiers more precisely: package_name OPERATOR version
    # Package names can contain letters, numbers, underscores, hyphens, and dots
    # NOTE: This regex parses Python package version specifiers (PEP 440), NOT HTML tags
    # CodeQL alert py/bad-tag-filter is a FALSE POSITIVE - we are not parsing HTML
    version_specifier_pattern = re.compile(r'^([a-zA-Z0-9_.-]+)\s*(>=|~=|<=|<|>|==|\*)')  # noqa: DUO138
    
    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            original_line = line
            line = line.strip()
            
            # Skip empty lines, comments, and -r includes
            if not line or line.startswith('#') or line.startswith('-r '):
                continue
            
            # Check for version constraints
            match = version_specifier_pattern.match(line)
            if match:
                pkg_name = match.group(1).lower()
                operator = match.group(2)
                
                # Exact pins are always OK
                if operator == '==':
                    continue
                
                # Check for constrained ranges (>=X,<Y)
                if operator == '>=' and '<' in line:
                    # This is a constrained range
                    if pkg_name not in ALLOWED_CONSTRAINED_RANGES:
                        violations.append(
                            f"Line {line_num}: {original_line.strip()}\n"
                            f"    Package '{pkg_name}' not allowed to use constrained ranges.\n"
                            f"    Use exact pin (==) or add to ALLOWED_CONSTRAINED_RANGES if needed."
                        )
                    # Otherwise, it's allowed
                else:
                    # Unconstrained or unusual operator
                    violations.append(
                        f"Line {line_num}: {original_line.strip()}\n"
                        f"    Use exact pin (==) or constrained range (>=X,<Y)"
                    )
    
    return len(violations) > 0, violations


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: check_version_pins.py <requirement-file> [<requirement-file> ...]")
        return 1
    
    print("="*80)
    print("VERSION CONSTRAINT VALIDATOR")
    print("="*80)
    print("Checking for appropriate version constraints")
    print("Allowed: exact pins (==) or constrained ranges (>=X,<Y) for approved packages")
    print()
    
    total_violations = 0
    files_with_violations = []
    
    for filepath_str in sys.argv[1:]:
        filepath = Path(filepath_str)
        print(f"Checking {filepath}...")
        
        has_violations, violations = check_file_for_version_constraints(filepath)
        
        if has_violations:
            total_violations += len(violations)
            files_with_violations.append(filepath)
            print(f"  ❌ Found {len(violations)} violation(s):")
            for violation in violations:
                print(f"    {violation}")
        else:
            print(f"  ✅ All version constraints are appropriate")
        print()
    
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Files checked: {len(sys.argv) - 1}")
    print(f"Files with violations: {len(files_with_violations)}")
    print(f"Total violations: {total_violations}")
    
    if total_violations > 0:
        print("\n❌ FAILED: Inappropriate version constraints detected!")
        print("\nFor reproducible builds, use exact pins (==) or constrained ranges (>=X,<Y)")
        print("Example: numpy==2.2.1 or transformers>=4.40.0,<5.0.0")
        return 1
    else:
        print("\n✅ SUCCESS: All version constraints are appropriate")
        return 0


if __name__ == "__main__":
    sys.exit(main())
