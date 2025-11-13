#!/usr/bin/env python3
"""
Python Environment Equipment Script

Verifies Python environment readiness including:
- Python version requirements
- Package dependencies
- C-extensions compilation
- Import availability for critical packages

Exit codes:
- 0: Environment ready
- 1: Environment has issues
"""

from __future__ import annotations

import importlib
import subprocess
import sys
from pathlib import Path


def check_python_version() -> bool:
    """Check Python version meets minimum requirements."""
    print("=== Python Version Check ===")
    min_version = (3, 10)
    current = sys.version_info[:2]
    
    print(f"Current: Python {current[0]}.{current[1]}")
    print(f"Required: Python {min_version[0]}.{min_version[1]}+")
    
    if current >= min_version:
        print("✓ Version OK\n")
        return True
    else:
        print(f"✗ Python {min_version[0]}.{min_version[1]}+ required\n")
        return False


def check_critical_imports() -> bool:
    """Check that critical packages can be imported."""
    print("=== Critical Package Imports ===")
    
    critical_packages = [
        ("numpy", "Core scientific computing"),
        ("pandas", "Data manipulation"),
        ("pydantic", "Data validation"),
        ("blake3", "Cryptographic hashing"),
        ("structlog", "Structured logging"),
    ]
    
    all_ok = True
    for package, description in critical_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}: {description}")
        except ImportError as e:
            print(f"✗ {package}: NOT INSTALLED ({description})")
            all_ok = False
    
    print()
    return all_ok


def check_optional_imports() -> None:
    """Check optional packages (informational only)."""
    print("=== Optional Package Imports (Informational) ===")
    
    optional_packages = [
        ("polars", "Fast DataFrame library"),
        ("pyarrow", "Arrow format support"),
        ("torch", "Deep learning"),
        ("tensorflow", "Machine learning"),
        ("transformers", "NLP models"),
        ("spacy", "NLP processing"),
    ]
    
    for package, description in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package}: {description}")
        except ImportError:
            print(f"  {package}: not installed ({description})")
    
    print()


def test_package_import() -> bool:
    """Test that the saaaaaa package can be imported."""
    print("=== SAAAAAA Package Import ===")
    
    try:
        import saaaaaa
        print(f"✓ Package imported successfully")
        
        # Test compat layer
        from saaaaaa.compat import try_import
        print(f"✓ Compat layer available")
        
        print()
        return True
    except Exception as e:
        print(f"✗ Failed to import package: {e}\n")
        return False


def compile_bytecode() -> bool:
    """Compile Python bytecode to check for syntax errors."""
    print("=== Bytecode Compilation ===")
    
    root = Path(__file__).parent.parent
    src_path = root / "src" / "saaaaaa"
    
    try:
        result = subprocess.run(
            ["python", "-m", "compileall", "-q", str(src_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        
        if result.returncode == 0:
            print("✓ All files compile successfully\n")
            return True
        else:
            print(f"✗ Compilation errors:\n{result.stderr}\n")
            return False
    except Exception as e:
        print(f"✗ Compilation check failed: {e}\n")
        return False


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("PYTHON ENVIRONMENT EQUIPMENT CHECK")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version()),
        ("Critical Imports", check_critical_imports()),
        ("Package Import", test_package_import()),
        ("Bytecode Compilation", compile_bytecode()),
    ]
    
    # Run optional checks (don't affect exit code)
    check_optional_imports()
    
    # Summary
    print("=" * 60)
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
        print("Please resolve these issues before proceeding.")
        return 1
    else:
        print("✓ Environment is ready!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
