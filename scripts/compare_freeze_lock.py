#!/usr/bin/env python3
"""
Compare pip freeze output with expected constraints/lock file.

This script is used in CI to ensure that installed packages match expected versions.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple


def parse_requirements_file(filepath: Path) -> Dict[str, str]:
    """Parse a requirements file and return package->version mapping."""
    packages = {}
    
    if not filepath.exists():
        return packages
    
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Skip -r includes
            if line.startswith('-r '):
                continue
            
            # Parse package==version
            if '==' in line:
                pkg, version = line.split('==', 1)
                packages[pkg.lower().strip()] = version.strip()
            elif '>=' in line or '~=' in line or '<=' in line:
                # For now, skip range specifications
                continue
    
    return packages


def compare_packages(freeze: Dict[str, str], lock: Dict[str, str]) -> Tuple[Set[str], Set[str], Dict[str, Tuple[str, str]]]:
    """
    Compare freeze and lock dictionaries.
    
    Returns:
        - missing_in_freeze: packages in lock but not in freeze
        - extra_in_freeze: packages in freeze but not in lock
        - version_mismatches: packages with different versions
    """
    freeze_keys = set(freeze.keys())
    lock_keys = set(lock.keys())
    
    missing_in_freeze = lock_keys - freeze_keys
    extra_in_freeze = freeze_keys - lock_keys
    
    version_mismatches = {}
    for pkg in freeze_keys & lock_keys:
        if freeze[pkg] != lock[pkg]:
            version_mismatches[pkg] = (freeze[pkg], lock[pkg])
    
    return missing_in_freeze, extra_in_freeze, version_mismatches


def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: compare_freeze_lock.py <freeze-file> <lock-file>")
        print("  freeze-file: Output from 'pip freeze'")
        print("  lock-file: Expected constraints file")
        return 1
    
    freeze_file = Path(sys.argv[1])
    lock_file = Path(sys.argv[2])
    
    if not freeze_file.exists():
        print(f"Error: Freeze file not found: {freeze_file}")
        return 1
    
    if not lock_file.exists():
        print(f"Error: Lock file not found: {lock_file}")
        return 1
    
    print("="*80)
    print("FREEZE vs LOCK COMPARISON")
    print("="*80)
    print(f"Freeze file: {freeze_file}")
    print(f"Lock file: {lock_file}")
    print()
    
    freeze = parse_requirements_file(freeze_file)
    lock = parse_requirements_file(lock_file)
    
    print(f"Packages in freeze: {len(freeze)}")
    print(f"Packages in lock: {len(lock)}")
    print()
    
    missing, extra, mismatches = compare_packages(freeze, lock)
    
    has_errors = False
    
    # Report missing packages
    if missing:
        has_errors = True
        print("❌ MISSING IN FREEZE (in lock but not installed):")
        for pkg in sorted(missing):
            print(f"  - {pkg}=={lock[pkg]}")
        print()
    
    # Report extra packages (informational only)
    if extra:
        print("⚠️  EXTRA IN FREEZE (installed but not in lock):")
        for pkg in sorted(extra):
            print(f"  - {pkg}=={freeze[pkg]}")
        print("  (This may be OK if they are transitive dependencies)")
        print()
    
    # Report version mismatches
    if mismatches:
        has_errors = True
        print("❌ VERSION MISMATCHES:")
        for pkg, (freeze_ver, lock_ver) in sorted(mismatches.items()):
            print(f"  - {pkg}:")
            print(f"      Installed: {freeze_ver}")
            print(f"      Expected:  {lock_ver}")
        print()
    
    # Summary
    print("="*80)
    if not has_errors:
        print("✅ SUCCESS: Freeze matches lock file")
        return 0
    else:
        print("❌ FAILURE: Discrepancies detected")
        print()
        print("To fix:")
        print("  1. Install exact versions: pip install -c constraints-new.txt -r requirements-core.txt")
        print("  2. Or regenerate lock: pip freeze > constraints-new.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
