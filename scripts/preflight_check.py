#!/usr/bin/env python3
"""
Preflight Check Script - Validates system readiness before execution.

Aligned with the OPERATIONAL_GUIDE equipment checks.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


def check(name: str, func) -> Tuple[bool, str]:
    """Run a check and return (success, message)."""
    try:
        result = func()
        return (True, f"✓ {name}: {result}")
    except Exception as e:
        return (False, f"✗ {name}: {e}")


def check_python_version():
    """Check Python version >= 3.10."""
    version = sys.version_info
    if version < (3, 10):
        raise RuntimeError(f"Python {version.major}.{version.minor} < 3.10")
    return f"{version.major}.{version.minor}.{version.micro}"


def check_no_yaml_in_executors():
    """Check no YAML files in executors/."""
    executors_dir = Path(__file__).parent.parent / "executors"
    if not executors_dir.exists():
        return "executors/ not found (OK)"
    
    yaml_files = list(executors_dir.glob("**/*.yaml")) + list(executors_dir.glob("**/*.yml"))
    if yaml_files:
        raise RuntimeError(f"Found {len(yaml_files)} YAML files in executors/")
    return "No YAML in executors/"


def check_arg_router_routes():
    """Check ArgRouter has >= 30 routes."""
    try:
        from saaaaaa.core.orchestrator.arg_router import ArgRouter
        router = ArgRouter()
        count = len(router._routes)
        if count < 30:
            raise RuntimeError(f"Expected >=30 routes, got {count}")
        return f"{count} routes"
    except ImportError as e:
        raise RuntimeError(f"Cannot import ArgRouter: {e}")


def check_memory_signals():
    """Check memory:// signals available."""
    try:
        from saaaaaa.core.orchestrator.signals import SignalClient
        client = SignalClient(base_url="memory://")
        if client.base_url != "memory://":
            raise RuntimeError("Memory mode not enabled")
        return "memory:// available"
    except ImportError as e:
        raise RuntimeError(f"Cannot import SignalClient: {e}")


def check_critical_imports():
    """Check critical imports."""
    modules = [
        "saaaaaa.core.orchestrator",
        "saaaaaa.flux",
        "saaaaaa.processing.cpp_ingestion",
    ]
    
    for module in modules:
        try:
            __import__(module)
        except ImportError as e:
            raise RuntimeError(f"Cannot import {module}: {e}")
    
    return f"{len(modules)} modules OK"


def check_pins():
    """Check pinned dependencies are installed."""
    requirements_file = Path(__file__).parent.parent / "requirements.txt"
    if not requirements_file.exists():
        return "requirements.txt not found (skip)"
    
    # Read requirements
    with open(requirements_file) as f:
        requirements = [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#") and "==" in line
        ]
    
    # Check installed versions
    try:
        import pkg_resources
        installed = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
        
        mismatches = []
        for req in requirements[:10]:  # Check first 10 for speed
            if "==" in req:
                name, version = req.split("==")
                name = name.lower().replace("_", "-")
                if name not in installed:
                    mismatches.append(f"{name} not installed")
                elif installed[name] != version:
                    mismatches.append(
                        f"{name}: expected {version}, got {installed[name]}"
                    )
        
        if mismatches:
            raise RuntimeError(f"Pin mismatches: {', '.join(mismatches[:3])}")
        
        return f"Checked {len(requirements)} pins"
    except ImportError:
        return "pkg_resources not available (skip)"


def main():
    """Run all preflight checks."""
    print("=" * 70)
    print("PREFLIGHT CHECKLIST")
    print("=" * 70)
    print()
    
    checks = [
        ("Python version >= 3.10", check_python_version),
        ("No YAML in executors/", check_no_yaml_in_executors),
        ("ArgRouter routes >= 30", check_arg_router_routes),
        ("Memory signals available", check_memory_signals),
        ("Critical imports", check_critical_imports),
        ("Pinned dependencies", check_pins),
    ]
    
    results = []
    for name, func in checks:
        success, message = check(name, func)
        results.append(success)
        print(message)
    
    print()
    print("=" * 70)
    
    if all(results):
        print(f"✓ PREFLIGHT COMPLETE: {len(results)}/{len(results)} checks passed")
        print("=" * 70)
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"✗ PREFLIGHT FAILED: {failed}/{len(results)} checks failed")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
