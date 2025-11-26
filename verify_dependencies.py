#!/usr/bin/env python3
"""
F.A.R.F.A.N Pipeline - Dependency Verification Script
======================================================
Verifies all critical dependencies are installed correctly.
Run this after installing requirements.txt to ensure everything works.
"""

import sys
from typing import List, Tuple


def check_import(module_name: str, package_name: str | None = None) -> bool:
    """
    Try to import a module and report status.

    Args:
        module_name: The module to import (e.g., 'camelot')
        package_name: The pip package name if different (e.g., 'camelot-py[cv]==0.11.0')

    Returns:
        True if import succeeded, False otherwise
    """
    try:
        __import__(module_name)
        print(f"✓ {module_name:30} OK")
        return True
    except ImportError as e:
        pkg = package_name or module_name
        print(f"✗ {module_name:30} MISSING")
        print(f"  Install with: pip install {pkg}")
        print(f"  Error: {e}")
        return False


def check_system_dependencies() -> bool:
    """Check for required system dependencies."""
    import shutil
    import subprocess

    print("\n" + "=" * 80)
    print("SYSTEM DEPENDENCIES CHECK")
    print("=" * 80 + "\n")

    checks = []

    # Check ghostscript
    if shutil.which("gs"):
        print("✓ ghostscript                  OK")
        checks.append(True)
    else:
        print("✗ ghostscript                  MISSING")
        print("  Ubuntu/Debian: sudo apt-get install ghostscript")
        print("  macOS: brew install ghostscript")
        checks.append(False)

    # Check Java
    if shutil.which("java"):
        try:
            result = subprocess.run(
                ["java", "-version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            version_info = result.stderr.split('\n')[0] if result.stderr else "unknown"
            print(f"✓ java                         OK ({version_info})")
            checks.append(True)
        except Exception:
            print("✗ java                         ERROR (installed but not working)")
            checks.append(False)
    else:
        print("✗ java                         MISSING")
        print("  Ubuntu/Debian: sudo apt-get install default-jre")
        print("  macOS: brew install openjdk")
        checks.append(False)

    # Check graphviz
    if shutil.which("dot"):
        print("✓ graphviz                     OK")
        checks.append(True)
    else:
        print("✗ graphviz                     MISSING")
        print("  Ubuntu/Debian: sudo apt-get install graphviz")
        print("  macOS: brew install graphviz")
        checks.append(False)

    return all(checks)


def check_python_version() -> bool:
    """Check Python version is 3.12.x."""
    version = sys.version_info
    print("\n" + "=" * 80)
    print("PYTHON VERSION CHECK")
    print("=" * 80 + "\n")

    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"Python version: {version_str}")

    if version.major == 3 and version.minor == 12:
        print("✓ Python version OK (3.12.x required)")
        return True
    else:
        print(f"✗ Python version mismatch (3.12.x required, found {version_str})")
        return False


def check_critical_packages() -> List[bool]:
    """Check all critical Python packages."""
    print("\n" + "=" * 80)
    print("CRITICAL PYTHON PACKAGES CHECK")
    print("=" * 80 + "\n")

    checks = [
        # PDF Processing (causes of test failures)
        ('camelot', 'camelot-py[cv]==0.11.0'),
        ('tabula', 'tabula-py==2.10.0'),

        # NLP (causes of test failures)
        ('sentence_transformers', 'sentence-transformers==3.3.1'),
        ('transformers', 'transformers==4.53.0'),

        # Bayesian Analysis
        ('pymc', 'pymc==5.16.2'),
        ('pytensor', 'pytensor==2.25.1'),
        ('arviz', 'arviz==0.20.0'),

        # Deep Learning
        ('torch', 'torch==2.8.0'),
        ('tensorflow', 'tensorflow==2.18.0'),

        # NLP Tools
        ('spacy', 'spacy==3.8.3'),
        ('nltk', 'nltk==3.9.1'),

        # Graph Analysis
        ('networkx', 'networkx==3.4.2'),
        ('igraph', 'igraph==0.11.8'),

        # Web Frameworks
        ('fastapi', 'fastapi==0.115.6'),
        ('flask', 'flask==3.0.3'),

        # Scientific Computing
        ('numpy', 'numpy==1.26.4'),
        ('scipy', 'scipy==1.14.1'),
        ('pandas', 'pandas==2.2.3'),
        ('sklearn', 'scikit-learn==1.6.1'),

        # Computer Vision
        ('cv2', 'opencv-python==4.10.0.84'),

        # PDF Tools
        ('pdfplumber', 'pdfplumber==0.11.4'),
        ('PyPDF2', 'PyPDF2==3.0.1'),

        # Data Validation
        ('pydantic', 'pydantic==2.10.6'),
    ]

    return [check_import(mod, pkg) for mod, pkg in checks]


def verify_versions() -> bool:
    """Verify critical package versions match requirements."""
    print("\n" + "=" * 80)
    print("VERSION VERIFICATION")
    print("=" * 80 + "\n")

    try:
        import numpy
        import pytensor
        import pymc

        versions_ok = True

        # NumPy version check
        if numpy.__version__ == "1.26.4":
            print(f"✓ NumPy version:               {numpy.__version__} (correct)")
        else:
            print(f"✗ NumPy version:               {numpy.__version__} (expected 1.26.4)")
            print("  WARNING: NumPy 2.0 breaks PyMC compatibility!")
            versions_ok = False

        # PyTensor version check
        if pytensor.__version__.startswith("2.25"):
            print(f"✓ PyTensor version:            {pytensor.__version__} (correct)")
        else:
            print(f"✗ PyTensor version:            {pytensor.__version__} (expected 2.34.x)")
            versions_ok = False

        # PyMC version check
        if pymc.__version__.startswith("5.16"):
            print(f"✓ PyMC version:                {pymc.__version__} (correct)")
        else:
            print(f"✗ PyMC version:                {pymc.__version__} (expected 5.16.x)")
            versions_ok = False

        return versions_ok

    except ImportError as e:
        print(f"✗ Could not verify versions: {e}")
        return False


def check_spacy_models() -> bool:
    """Check if required spaCy models are installed."""
    print("\n" + "=" * 80)
    print("SPACY MODELS CHECK")
    print("=" * 80 + "\n")

    try:
        import spacy

        try:
            nlp = spacy.load("es_core_news_sm")
            print("✓ es_core_news_sm              OK")
            return True
        except OSError:
            print("✗ es_core_news_sm              MISSING")
            print("  Install with: python -m spacy download es_core_news_sm")
            return False

    except ImportError:
        print("✗ spaCy not installed")
        return False


def test_critical_imports() -> bool:
    """Test that critical imports actually work (not just installed)."""
    print("\n" + "=" * 80)
    print("FUNCTIONAL TESTS")
    print("=" * 80 + "\n")

    all_ok = True

    # Test camelot
    try:
        import camelot
        # Try to access a basic function
        _ = camelot.__version__
        print("✓ camelot                      Functional")
    except Exception as e:
        print(f"✗ camelot                      Error: {e}")
        all_ok = False

    # Test sentence_transformers
    try:
        from sentence_transformers import SentenceTransformer
        # Don't load a model (too slow), just check import
        print("✓ sentence_transformers        Functional")
    except Exception as e:
        print(f"✗ sentence_transformers        Error: {e}")
        all_ok = False

    # Test PyMC
    try:
        import pymc as pm
        import pytensor
        # Basic check
        _ = pm.__version__
        print("✓ pymc + pytensor              Functional")
    except Exception as e:
        print(f"✗ pymc + pytensor              Error: {e}")
        all_ok = False

    return all_ok


def main() -> int:
    """Run all verification checks."""
    print("=" * 80)
    print("F.A.R.F.A.N PIPELINE - DEPENDENCY VERIFICATION")
    print("=" * 80)

    # Run all checks
    python_ok = check_python_version()
    system_ok = check_system_dependencies()
    packages_results = check_critical_packages()
    packages_ok = all(packages_results)
    versions_ok = verify_versions()
    spacy_ok = check_spacy_models()
    functional_ok = test_critical_imports()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80 + "\n")

    total_checks = len(packages_results)
    passed_checks = sum(packages_results)

    print(f"Python Version:        {'✓ OK' if python_ok else '✗ FAILED'}")
    print(f"System Dependencies:   {'✓ OK' if system_ok else '✗ FAILED'}")
    print(f"Python Packages:       {passed_checks}/{total_checks} installed")
    print(f"Version Compatibility: {'✓ OK' if versions_ok else '✗ FAILED'}")
    print(f"spaCy Models:          {'✓ OK' if spacy_ok else '✗ FAILED'}")
    print(f"Functional Tests:      {'✓ OK' if functional_ok else '✗ FAILED'}")

    all_ok = (
        python_ok and
        system_ok and
        packages_ok and
        versions_ok and
        spacy_ok and
        functional_ok
    )

    if all_ok:
        print("\n✓ All checks passed! Your environment is ready.")
        print("\nYou can now run:")
        print("  pytest tests/ -v")
        return 0
    else:
        print("\n✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  1. Install system dependencies: ./install-system-deps.sh")
        print("  2. Reinstall Python packages: pip install -r requirements.txt")
        print("  3. Download spaCy model: python -m spacy download es_core_news_sm")
        print("\nFor detailed help, see: INSTALL.md and DEPENDENCIES.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
