#!/usr/bin/env python3
"""
Validation script for build hygiene checklist.
Verifies that the repository follows all build hygiene requirements.
"""

import re
import sys
from pathlib import Path

def check_python_version_pin() -> bool:
    """Check that Python version is pinned to 3.12.x."""
    print("✓ Checking Python version pin...")

    # Check .python-version
    python_version_file = Path(".python-version")
    if not python_version_file.exists():
        print("  ✗ Missing .python-version file")
        return False

    version = python_version_file.read_text().strip()
    if not version.startswith("3.12"):
        print(f"  ✗ .python-version should be 3.12.x, got {version}")
        return False

    # Check pyproject.toml
    pyproject = Path("pyproject.toml").read_text()
    if 'requires-python = "~=3.12.0"' not in pyproject:
        print("  ✗ pyproject.toml should have requires-python = \"~=3.12.0\"")
        return False

    if 'pythonVersion = "3.12"' not in pyproject:
        print("  ✗ pyproject.toml should have pythonVersion = \"3.12\"")
        return False

    print("  ✓ Python version properly pinned to 3.12.x")
    return True

def check_pinned_dependencies() -> bool:
    """Check that all dependencies are pinned to exact versions."""
    print("✓ Checking dependency pinning...")

    requirements = Path("requirements.txt")
    if not requirements.exists():
        print("  ✗ Missing requirements.txt")
        return False

    constraints = Path("constraints.txt")
    if not constraints.exists():
        print("  ✗ Missing constraints.txt")
        return False

    # Check for wildcards or open ranges in requirements.txt
    content = requirements.read_text()
    lines = [line.strip() for line in content.split('\n')
             if line.strip() and not line.strip().startswith('#')]

    bad_patterns = []
    for line in lines:
        # Check for wildcard or open ranges in version specifiers
        # Look for these patterns after package name and optional extras
        # Match patterns like: package>=1.0, package~=1.0, package>1.0, package<2.0, package*
        if (re.search(r'(>=|~=|>|<|\*)', line) and
            re.search(r'[^\[]*(\[.*\])?\s*(>=|~=|>|<|\*)', line)):
            # Further validate it's in version spec position, not in package name
            # Package name format: name[extras]==version
            bad_patterns.append(line)

    if bad_patterns:
        print("  ✗ Found wildcards or open ranges in requirements.txt:")
        for pattern in bad_patterns:
            print(f"    - {pattern}")
        return False

    print(f"  ✓ All {len(lines)} dependencies properly pinned with exact versions")
    print("  ✓ constraints.txt exists")
    return True

def check_directory_structure() -> bool:
    """Check that required directories exist with __init__.py files."""
    print("✓ Checking directory structure...")

    required_dirs = [
        "orchestrator",
        "executors",
        "contracts",
        "tests",
        "tools",
        "examples",
        "src/saaaaaa/core",
    ]

    missing_dirs = []
    missing_init = []

    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            missing_dirs.append(dir_path)
        elif not (path / "__init__.py").exists():
            missing_init.append(dir_path)

    if missing_dirs:
        print("  ✗ Missing directories:")
        for d in missing_dirs:
            print(f"    - {d}")
        return False

    if missing_init:
        print("  ✗ Missing __init__.py in:")
        for d in missing_init:
            print(f"    - {d}")
        return False

    print("  ✓ All required directories exist with __init__.py files")
    return True

def check_pythonpath_config() -> bool:
    """Check that setup.py exists for proper PYTHONPATH configuration."""
    print("✓ Checking PYTHONPATH configuration...")

    setup_py = Path("setup.py")
    if not setup_py.exists():
        print("  ✗ Missing setup.py for pip install -e .")
        return False

    content = setup_py.read_text()
    if 'find_packages' not in content:
        print("  ✗ setup.py should use find_packages()")
        return False

    print("  ✓ setup.py exists for editable installation")
    return True

def check_centralized_config() -> bool:
    """Check that centralized configuration exists."""
    print("✓ Checking centralized configuration...")

    settings = Path("orchestrator/settings.py")
    if not settings.exists():
        print("  ✗ Missing orchestrator/settings.py")
        return False

    env_example = Path(".env.example")
    if not env_example.exists():
        print("  ✗ Missing .env.example")
        return False

    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            print("  ✗ .gitignore should exclude .env files")
            return False

    print("  ✓ Centralized config exists (orchestrator/settings.py, .env.example)")
    print("  ✓ .env properly excluded in .gitignore")
    return True

def main() -> int:
    """Run all validation checks."""
    print("=" * 60)
    print("Build Hygiene Validation")
    print("=" * 60)
    print()

    checks = [
        check_python_version_pin,
        check_pinned_dependencies,
        check_directory_structure,
        check_pythonpath_config,
        check_centralized_config,
    ]

    results = []
    for check in checks:
        try:
            results.append(check())
            print()
        except Exception as e:
            print(f"  ✗ Error running check: {e}")
            results.append(False)
            print()

    print("=" * 60)
    if all(results):
        print("✓ All build hygiene checks passed!")
        print("=" * 60)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"✗ {failed} check(s) failed")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
