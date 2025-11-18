#!/usr/bin/env python3
"""
Diagnostic Script - Shows REAL import errors (not just "NOT INSTALLED")

This script helps diagnose dependency issues by showing the actual error
instead of simplifying it as "NOT INSTALLED".
"""

import subprocess
from importlib import import_module


def check_package_with_traceback(package_name, description):
    """Check if a package can be imported and show full error if not."""
    print(f"\n{'='*70}")
    print(f"Checking: {package_name} ({description})")
    print('='*70)

    # 1. Check if installed with pip
    result = subprocess.run(
        ['pip', 'show', package_name],
        capture_output=True,
        text=True,
        check=False
    )

    if result.returncode != 0:
        print(f"✗ NOT installed via pip")
        return False
    else:
        for line in result.stdout.split('\n'):
            if 'Version:' in line:
                print(f"✓ Installed: {line.strip()}")
                break

    # 2. Try to import and capture real error
    print("\nAttempting import...")
    try:
        import_module(package_name)
        print(f"✓ Import successful!")
        return True
    except ImportError as e:
        print(f"✗ ImportError (NOT 'not installed', but IMPORT FAILED):")
        print(f"\nError message: {e}")
        print("\n" + "="*70)
        print("FULL TRACEBACK:")
        print("="*70)
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run diagnostics on critical packages."""
    print("\n" + "="*70)
    print("DEPENDENCY IMPORT DIAGNOSTICS")
    print("="*70)
    print("\nThis script shows REAL errors, not just 'NOT INSTALLED'")

    packages_to_check = [
        ("transformers", "Hugging Face Transformers"),
        ("sentence_transformers", "Sentence Transformers"),
        ("accelerate", "Hugging Face Accelerate"),
    ]

    results = []
    for package, description in packages_to_check:
        success = check_package_with_traceback(package, description)
        results.append((package, success))

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    for package, success in results:
        status = "✓ OK" if success else "✗ FAILED"
        print(f"{package:30} {status}")

    print("\n" + "="*70)
    print("INTERPRETATION:")
    print("="*70)
    print("""
If you see 'NOT installed via pip': Install the package
If you see 'Import successful': Everything is working
If you see 'ImportError' with installed package: VERSION INCOMPATIBILITY

Common issue:
- transformers 4.42+ tries to import TorchTensorParallelPlugin
- This class was removed from accelerate 1.0+
- Solution: Downgrade transformers to 4.41.2

  pip install transformers==4.41.2 sentence-transformers==3.1.0
    """)


if __name__ == "__main__":
    main()
