#!/usr/bin/env python3
"""
Verify that the SAAAAAA repository structure is findable by Python.

This script checks:
1. All __init__.py files exist where needed
2. Python can import from all major modules
3. Package structure is correct
4. No circular import issues
"""

import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent

def check_init_files():
    """Verify all Python packages have __init__.py files."""
    print("=" * 70)
    print("CHECKING __init__.py FILES")
    print("=" * 70)
    
    src_dir = repo_root / "src" / "saaaaaa"
    
    # Find all directories that should be packages
    package_dirs = []
    for path in src_dir.rglob("*.py"):
        if path.name != "__init__.py":
            package_dirs.append(path.parent)
    
    # Remove duplicates and check for __init__.py
    package_dirs = sorted(set(package_dirs))
    missing = []
    
    for pkg_dir in package_dirs:
        init_file = pkg_dir / "__init__.py"
        if not init_file.exists():
            missing.append(pkg_dir.relative_to(repo_root))
            print(f"✗ MISSING: {pkg_dir.relative_to(repo_root)}/__init__.py")
        else:
            print(f"✓ {pkg_dir.relative_to(repo_root)}/__init__.py")
    
    if missing:
        print(f"\n⚠️  {len(missing)} package(s) missing __init__.py")
        return False
    else:
        print("\n✓ All packages have __init__.py")
        return True

def check_major_imports():
    """Test importing from all major modules."""
    print("\n" + "=" * 70)
    print("CHECKING MAJOR MODULE IMPORTS")
    print("=" * 70)
    
    imports_to_test = [
        # Core modules
        ("saaaaaa.core.orchestrator", "Orchestrator"),
        ("saaaaaa.core.orchestrator.core", "Evidence"),
        ("saaaaaa.core.orchestrator.evidence_registry", "EvidenceRegistry"),
        
        # Analysis modules
        ("saaaaaa.analysis.scoring.scoring", "apply_scoring"),
        ("saaaaaa.analysis.bayesian_multilevel_system", "MultiLevelBayesianOrchestrator"),
        
        # Processing modules
        ("saaaaaa.processing.document_ingestion", "RawDocument"),
        ("saaaaaa.processing.aggregation", "AreaPolicyAggregator"),
        
        # Utilities
        ("saaaaaa.utils.contracts", "validate_contract"),
        ("saaaaaa.concurrency.concurrency", "WorkerPool"),
        
        # Compatibility wrappers
        ("orchestrator", "Orchestrator"),
        ("scoring.scoring", "apply_scoring"),
        ("contracts", "validate_contract"),
    ]
    
    failed = []
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            item = getattr(module, item_name)
            print(f"✓ from {module_name} import {item_name}")
        except Exception as e:
            print(f"✗ FAILED: from {module_name} import {item_name}")
            print(f"  Error: {e}")
            failed.append((module_name, item_name, str(e)))
    
    if failed:
        print(f"\n⚠️  {len(failed)} import(s) failed")
        return False
    else:
        print("\n✓ All major imports successful")
        return True

def check_package_structure():
    """Verify the package structure is correct."""
    print("\n" + "=" * 70)
    print("CHECKING PACKAGE STRUCTURE")
    print("=" * 70)
    
    required_dirs = [
        "src/saaaaaa",
        "src/saaaaaa/core",
        "src/saaaaaa/core/orchestrator",
        "src/saaaaaa/analysis",
        "src/saaaaaa/analysis/scoring",
        "src/saaaaaa/processing",
        "src/saaaaaa/utils",
        "src/saaaaaa/concurrency",
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        full_path = repo_root / dir_path
        if full_path.is_dir():
            print(f"✓ {dir_path}/")
        else:
            print(f"✗ MISSING: {dir_path}/")
            all_ok = False
    
    if all_ok:
        print("\n✓ Package structure is correct")
    else:
        print("\n⚠️  Some directories are missing")
    
    return all_ok

def check_compatibility_wrappers():
    """Verify compatibility wrappers exist and work."""
    print("\n" + "=" * 70)
    print("CHECKING COMPATIBILITY WRAPPERS")
    print("=" * 70)
    
    wrapper_files = [
        "orchestrator.py",
        "scoring.py",
        "contracts.py",
        "aggregation.py",
        "bayesian_multilevel_system.py",
        "derek_beach.py",
        "document_ingestion.py",
        "macro_prompts.py",
        "micro_prompts.py",
        "meso_cluster_analysis.py",
    ]
    
    wrapper_dirs = [
        "orchestrator/",
        "scoring/",
        "concurrency/",
        "contracts/",
        "core/",
        "executors/",
    ]
    
    all_ok = True
    
    # Check wrapper files
    for wrapper in wrapper_files:
        path = repo_root / wrapper
        if path.exists():
            print(f"✓ {wrapper}")
        else:
            print(f"✗ MISSING: {wrapper}")
            all_ok = False
    
    # Check wrapper directories
    for wrapper in wrapper_dirs:
        path = repo_root / wrapper
        if path.is_dir() and (path / "__init__.py").exists():
            print(f"✓ {wrapper}__init__.py")
        else:
            print(f"✗ MISSING: {wrapper}__init__.py")
            all_ok = False
    
    if all_ok:
        print("\n✓ All compatibility wrappers present")
    else:
        print("\n⚠️  Some wrappers are missing")
    
    return all_ok

def main():
    """Run all verification checks."""
    print("SAAAAAA REPOSITORY STRUCTURE VERIFICATION")
    print("=" * 70)
    print(f"Repository: {repo_root}")
    print()
    
    checks = [
        ("Package Structure", check_package_structure),
        ("__init__.py Files", check_init_files),
        ("Compatibility Wrappers", check_compatibility_wrappers),
        ("Major Imports", check_major_imports),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"\n✗ {name} check FAILED with exception: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Repository structure is correct!")
        return 0
    else:
        print("❌ SOME CHECKS FAILED - See details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
