#!/usr/bin/env python3
"""
Compatibility Layer Equipment Script

Verifies the compat layer functionality including:
- safe_imports module
- native_check module
- Version compatibility shims
- Platform detection

Exit codes:
- 0: Compat layer OK
- 1: Compat layer has issues
"""

from __future__ import annotations

import sys
from pathlib import Path


def test_compat_imports() -> bool:
    """Test that compat module can be imported."""
    print("=== Compat Module Imports ===")
    
    try:
        from saaaaaa.compat import (
            ImportErrorDetailed,
            check_import_available,
            get_import_version,
            lazy_import,
            tomllib,
            try_import,
        )
        print("✓ All compat exports available")
        return True
    except ImportError as e:
        print(f"✗ Failed to import compat: {e}")
        return False


def test_safe_imports_functionality() -> bool:
    """Test safe_imports functions."""
    print("\n=== Safe Imports Functionality ===")
    
    from saaaaaa.compat import check_import_available, try_import
    
    all_ok = True
    
    # Test checking for existing module
    if check_import_available("sys"):
        print("✓ check_import_available works for stdlib")
    else:
        print("✗ check_import_available failed for sys")
        all_ok = False
    
    # Test importing existing module
    result = try_import("os", required=False)
    if result is not None:
        print("✓ try_import works for stdlib")
    else:
        print("✗ try_import failed for os")
        all_ok = False
    
    # Test importing nonexistent optional module (should not raise)
    result = try_import("nonexistent_test_module", required=False)
    if result is None:
        print("✓ try_import handles missing optional correctly")
    else:
        print("✗ try_import should return None for missing optional")
        all_ok = False
    
    return all_ok


def test_native_check() -> bool:
    """Test native_check module."""
    print("\n=== Native Check Functionality ===")
    
    try:
        from saaaaaa.compat.native_check import (
            check_cpu_features,
            check_system_library,
        )
        
        # Test CPU features
        cpu_result = check_cpu_features()
        print(f"✓ CPU features check: {cpu_result.message}")
        
        # Test system library check (informational)
        lib_result = check_system_library("zstd")
        status = "available" if lib_result.available else "not found"
        print(f"  System library zstd: {status}")
        
        return True
    except Exception as e:
        print(f"✗ Native check failed: {e}")
        return False


def test_version_shims() -> bool:
    """Test version compatibility shims."""
    print("\n=== Version Compatibility Shims ===")
    
    from saaaaaa.compat import tomllib
    
    all_ok = True
    
    # Test tomllib
    if tomllib is not None:
        print("✓ TOML support available (tomllib or tomli)")
    else:
        print("✗ TOML support not available")
        all_ok = False
    
    # Test typing extensions
    try:
        from saaaaaa.compat import (
            Annotated,
            Final,
            Literal,
            Protocol,
            TypeAlias,
            TypedDict,
        )
        print("✓ Typing extensions available")
    except ImportError as e:
        print(f"✗ Typing extensions failed: {e}")
        all_ok = False
    
    return all_ok


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("COMPATIBILITY LAYER EQUIPMENT CHECK")
    print("=" * 60)
    print()
    
    checks = [
        ("Compat Imports", test_compat_imports()),
        ("Safe Imports", test_safe_imports_functionality()),
        ("Native Check", test_native_check()),
        ("Version Shims", test_version_shims()),
    ]
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    failed = []
    for name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"{status} {name}")
        if not passed:
            failed.append(name)
    
    print()
    
    if failed:
        print(f"Failed checks: {', '.join(failed)}")
        return 1
    else:
        print("✓ Compat layer is ready!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
