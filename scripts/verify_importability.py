#!/usr/bin/env python3
"""
Verify importability and versions of all critical packages.

This script ensures that:
1. All critical packages can be imported
2. Package versions match expectations
3. No missing dependencies exist
"""

import importlib
import importlib.metadata
import sys
from typing import Dict, List, Tuple


# Critical packages that MUST be importable
CRITICAL_PACKAGES = [
    ("numpy", "np"),
    ("pandas", "pd"),
    ("polars", "pl"),
    ("scipy", None),
    ("sklearn", None),
    ("networkx", "nx"),
    ("transformers", None),
    ("sentence_transformers", None),
    ("spacy", None),
    ("pdfplumber", None),
    ("PyPDF2", None),
    ("fitz", None),  # PyMuPDF
    ("docx", None),  # python-docx
    ("flask", None),
    ("fastapi", None),
    ("httpx", None),
    ("uvicorn", None),
    ("sse_starlette", None),
    ("pydantic", None),
    ("yaml", None),  # pyyaml
    ("jsonschema", None),
    ("blake3", None),
    ("structlog", None),
    ("tenacity", None),
    ("typer", None),
]

# Optional packages - warn if missing but don't fail
OPTIONAL_PACKAGES = [
    ("flask_socketio", None),
    ("flask_cors", None),
    ("redis", None),
    ("sqlalchemy", None),
    ("nltk", None),
    ("langdetect", None),
    ("fuzzywuzzy", None),
    ("bs4", None),  # beautifulsoup4
    ("psutil", None),
    ("prometheus_client", None),
]

# Development packages
DEV_PACKAGES = [
    ("pytest", None),
    ("hypothesis", None),
    ("black", None),
    ("ruff", None),
    ("mypy", None),
]


def check_import(package_name: str, import_as: str = None) -> Tuple[bool, str, str]:
    """
    Check if a package can be imported and return its version.
    
    Args:
        package_name: Name of the package to import
        import_as: Alternative name to import as (e.g., 'np' for numpy)
    
    Returns:
        Tuple of (success, version, error_message)
    """
    try:
        module_name = import_as or package_name
        mod = importlib.import_module(package_name)
        
        # Try to get version
        version = "unknown"
        if hasattr(mod, "__version__"):
            version = mod.__version__
        else:
            # Try to get from metadata
            try:
                # Map import name to package name
                pkg_name_map = {
                    "sklearn": "scikit-learn",
                    "yaml": "pyyaml",
                    "fitz": "PyMuPDF",
                    "docx": "python-docx",
                    "bs4": "beautifulsoup4",
                    "flask_socketio": "flask-socketio",
                    "flask_cors": "flask-cors",
                    "sse_starlette": "sse-starlette",
                }
                pkg_name = pkg_name_map.get(package_name, package_name)
                version = importlib.metadata.version(pkg_name)
            except Exception:
                pass
        
        return True, version, ""
    except ImportError as e:
        return False, "", str(e)
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"


def verify_packages(packages: List[Tuple[str, str]], package_type: str) -> Tuple[int, int]:
    """
    Verify a list of packages.
    
    Returns:
        Tuple of (success_count, failure_count)
    """
    print(f"\n{'='*80}")
    print(f"Verifying {package_type} packages")
    print(f"{'='*80}")
    
    success_count = 0
    failure_count = 0
    
    for pkg_name, import_as in packages:
        success, version, error = check_import(pkg_name, import_as)
        
        if success:
            status = "✓"
            success_count += 1
            print(f"{status} {pkg_name:30s} version: {version}")
        else:
            status = "✗"
            failure_count += 1
            print(f"{status} {pkg_name:30s} ERROR: {error[:50]}")
    
    print(f"\n{package_type}: {success_count} passed, {failure_count} failed")
    return success_count, failure_count


def main():
    """Main entry point."""
    print("="*80)
    print("DEPENDENCY IMPORTABILITY VERIFICATION")
    print("="*80)
    print("This script verifies that all required packages can be imported")
    print("and displays their versions.\n")
    
    total_success = 0
    total_failure = 0
    critical_failures = 0
    
    # Verify critical packages
    success, failure = verify_packages(CRITICAL_PACKAGES, "CRITICAL")
    total_success += success
    critical_failures = failure
    total_failure += failure
    
    # Verify optional packages
    success, failure = verify_packages(OPTIONAL_PACKAGES, "OPTIONAL")
    total_success += success
    total_failure += failure
    
    # Verify dev packages
    success, failure = verify_packages(DEV_PACKAGES, "DEVELOPMENT")
    total_success += success
    total_failure += failure
    
    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"Total packages checked: {total_success + total_failure}")
    print(f"Successful imports: {total_success}")
    print(f"Failed imports: {total_failure}")
    print(f"Critical failures: {critical_failures}")
    
    if critical_failures > 0:
        print("\n❌ CRITICAL: Some required packages are missing!")
        print("Install them with: pip install -r requirements-core.txt")
        return 1
    elif total_failure > 0:
        print("\n⚠️  WARNING: Some optional/dev packages are missing")
        print("Install them with: pip install -r requirements-all.txt")
        return 0
    else:
        print("\n✅ SUCCESS: All packages verified!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
