#!/usr/bin/env python3
"""
Verify Critical Import Test

This script verifies that all critical dependencies can be imported.
Run this after installing requirements to ensure the environment is properly configured.

Usage:
    python scripts/verify_critical_imports.py

Exit codes:
    0 - All imports successful
    1 - Some imports failed
"""
import sys

# Critical packages that were missing and causing system failures
CRITICAL_IMPORTS = [
    ('cv2', 'opencv-python', 'Computer vision - Required for image processing'),
    ('huggingface_hub', 'huggingface-hub', 'Model hub - Required for NLP models'),
]

# Important transitive dependencies that are imported directly
IMPORTANT_IMPORTS = [
    ('safetensors', 'safetensors', 'Safe model serialization'),
    ('tokenizers', 'tokenizers', 'Fast tokenization'),
    ('filelock', 'filelock', 'File locking'),
    ('regex', 'regex', 'Advanced regex'),
    ('requests', 'requests', 'HTTP requests'),
    ('urllib3', 'urllib3', 'HTTP client'),
    ('certifi', 'certifi', 'SSL certificates'),
    ('charset_normalizer', 'charset-normalizer', 'Character encoding'),
    ('idna', 'idna', 'Domain names'),
    ('tqdm', 'tqdm', 'Progress bars'),
    ('packaging', 'packaging', 'Version parsing'),
    ('click', 'click', 'CLI framework'),
    ('joblib', 'joblib', 'Pipeline caching'),
    ('six', 'six', 'Python 2/3 compat'),
    ('dateutil', 'python-dateutil', 'Date utilities'),
    ('pytz', 'pytz', 'Timezone support'),
]

# Core packages
CORE_IMPORTS = [
    ('numpy', 'numpy', 'Numerical computing'),
    ('pandas', 'pandas', 'Data analysis'),
    ('scipy', 'scipy', 'Scientific computing'),
    ('sklearn', 'scikit-learn', 'Machine learning'),
    ('transformers', 'transformers', 'NLP transformers'),
    ('sentence_transformers', 'sentence-transformers', 'Sentence embeddings'),
    ('spacy', 'spacy', 'NLP processing'),
    ('torch', 'torch', 'Deep learning'),
    ('pydantic', 'pydantic', 'Data validation'),
    ('fastapi', 'fastapi', 'Web framework'),
    ('flask', 'flask', 'Web framework'),
    ('networkx', 'networkx', 'Graph analysis'),
    ('pymc', 'pymc', 'Bayesian modeling'),
]


def test_import(module_name: str, package_name: str) -> tuple[bool, str | None]:
    """
    Test if a module can be imported.
    
    Args:
        module_name: The module to import
        package_name: The package name for error messages
        
    Returns:
        (success, error_message)
    """
    try:
        __import__(module_name)
        return True, None
    except Exception as e:
        return False, str(e)


def main() -> int:
    """Run the import verification test."""
    print("=" * 80)
    print("CRITICAL IMPORT VERIFICATION TEST")
    print("=" * 80)
    print()
    print("This test verifies that all dependencies from requirements.txt")
    print("can be imported successfully.")
    print()
    
    all_passed = True
    
    # Test critical imports
    print("CRITICAL IMPORTS (these were missing and causing failures):")
    critical_failed = []
    for module, package, description in CRITICAL_IMPORTS:
        success, error = test_import(module, package)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {module:25} ({package})")
        if not success:
            print(f"       {description}")
            print(f"       Error: {error}")
            critical_failed.append((module, package))
            all_passed = False
    print()
    
    # Test important imports
    print("IMPORTANT TRANSITIVE DEPENDENCIES:")
    important_failed = []
    for module, package, description in IMPORTANT_IMPORTS:
        success, error = test_import(module, package)
        if not success:
            important_failed.append((module, package, error))
    
    if important_failed:
        print(f"  ❌ {len(important_failed)}/{len(IMPORTANT_IMPORTS)} packages failed:")
        for module, package, error in important_failed:
            print(f"     - {module} ({package})")
        all_passed = False
    else:
        print(f"  ✅ All {len(IMPORTANT_IMPORTS)} packages can be imported")
    print()
    
    # Test core imports
    print("CORE PACKAGES:")
    core_failed = []
    for module, package, description in CORE_IMPORTS:
        success, error = test_import(module, package)
        if not success:
            core_failed.append((module, package, error))
    
    if core_failed:
        print(f"  ❌ {len(core_failed)}/{len(CORE_IMPORTS)} packages failed:")
        for module, package, error in core_failed:
            print(f"     - {module} ({package})")
        all_passed = False
    else:
        print(f"  ✅ All {len(CORE_IMPORTS)} packages can be imported")
    print()
    
    print("=" * 80)
    if all_passed:
        print("✅ ALL IMPORTS SUCCESSFUL")
        print()
        print("The environment is properly configured.")
        return 0
    else:
        print("❌ SOME IMPORTS FAILED")
        print()
        if critical_failed:
            print("CRITICAL packages are missing! The system will not work properly.")
            print()
        print("To fix:")
        print("  1. Create/activate a virtual environment:")
        print("     python3 -m venv venv")
        print("     source venv/bin/activate")
        print()
        print("  2. Install requirements:")
        print("     pip install -r requirements.txt")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())
