#!/usr/bin/env python3
"""
Native Dependencies Equipment Script

Verifies system libraries and native extensions for:
- C-extensions (pyarrow, polars, blake3)
- System libraries (zstd, icu, omp)
- Platform compatibility
- CPU features

Exit codes:
- 0: All native dependencies OK (or warnings only)
- 1: Critical native dependencies missing
"""

from __future__ import annotations

import sys
from pathlib import Path

from saaaaaa.compat.native_check import (
    check_cpu_features,
    check_fips_mode,
    check_system_library,
    verify_native_dependencies,
)


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("NATIVE DEPENDENCIES EQUIPMENT CHECK")
    print("=" * 60)
    print()
    
    # Use the comprehensive report from native_check
    from saaaaaa.compat.native_check import print_native_report
    print_native_report()
    
    print("=" * 60)
    print("RECOMMENDATION")
    print("=" * 60)
    
    # Check critical packages
    critical = ["pyarrow", "blake3"]
    results = verify_native_dependencies(critical)
    
    missing_critical = [
        name for name, result in results.items()
        if not result.available and ":" not in name
    ]
    
    if missing_critical:
        print(f"✗ Missing critical native packages: {', '.join(missing_critical)}")
        print("Install with: pip install -r requirements.txt")
        return 1
    else:
        print("✓ All critical native dependencies available")
        print("\nNote: Some system libraries may be missing but are not critical")
        print("      for basic functionality. See warnings above.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
