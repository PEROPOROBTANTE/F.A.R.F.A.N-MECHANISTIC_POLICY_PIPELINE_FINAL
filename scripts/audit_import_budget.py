#!/usr/bin/env python3
"""
Import Time Budget Checker

Measures import time for critical modules and ensures they meet budget requirements.
Import time affects startup performance and user experience.

Budget: ≤ 300 ms per critical module (as specified in problem statement)

Exit codes:
- 0: All imports within budget
- 1: Some imports exceed budget
"""

from __future__ import annotations

import importlib
import sys
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportTiming:
    """Result of import timing measurement."""
    
    module: str
    time_ms: float
    success: bool
    error: str = ""


def measure_import_time(module_name: str) -> ImportTiming:
    """
    Measure the time to import a module.
    
    Note: This measures import time with the module potentially already
    in sys.modules cache. For accurate first-import timing, run in a
    fresh Python process.
    
    Parameters
    ----------
    module_name : str
        Fully qualified module name
    
    Returns
    -------
    ImportTiming
        Timing result with success status
    """
    try:
        start = time.perf_counter()
        importlib.import_module(module_name)
        end = time.perf_counter()
        
        elapsed_ms = (end - start) * 1000
        return ImportTiming(module_name, elapsed_ms, True)
    
    except Exception as e:
        return ImportTiming(module_name, 0.0, False, str(e))


def check_import_budget(budget_ms: float = 300.0) -> list[ImportTiming]:
    """
    Check import times for critical modules against budget.
    
    Parameters
    ----------
    budget_ms : float, default=300.0
        Maximum allowed import time in milliseconds
    
    Returns
    -------
    list[ImportTiming]
        Results for all tested modules
    """
    # Critical modules to test (from pyproject.toml and known heavy imports)
    critical_modules = [
        "saaaaaa",
        "saaaaaa.core",
        "saaaaaa.core.orchestrator",
        "saaaaaa.processing",
        "saaaaaa.processing.document_ingestion",
        "saaaaaa.analysis",
        "saaaaaa.concurrency",
        "saaaaaa.utils",
        "saaaaaa.compat",
    ]
    
    # Heavy optional dependencies to measure separately
    optional_modules = [
        "numpy",
        "pandas",
        "polars",
        "pyarrow",
        "torch",
        "tensorflow",
        "transformers",
        "spacy",
    ]
    
    results = []
    
    print("=== Import Budget Check ===")
    print(f"Budget: {budget_ms} ms per module\n")
    
    print("Critical Modules:")
    for module in critical_modules:
        result = measure_import_time(module)
        results.append(result)
        
        if result.success:
            status = "✓" if result.time_ms <= budget_ms else "✗"
            print(f"  {status} {module}: {result.time_ms:.1f} ms")
        else:
            print(f"  ✗ {module}: FAILED ({result.error})")
    
    print("\nOptional Dependencies (informational):")
    for module in optional_modules:
        result = measure_import_time(module)
        
        if result.success:
            print(f"    {module}: {result.time_ms:.1f} ms")
        else:
            print(f"    {module}: not installed or failed")
    
    return results


def main() -> int:
    """Main entry point."""
    results = check_import_budget()
    
    # Check for budget violations
    budget_ms = 300.0
    violations = [
        r for r in results 
        if r.success and r.time_ms > budget_ms
    ]
    
    failures = [r for r in results if not r.success]
    
    print("\n=== Summary ===")
    print(f"Tested: {len(results)} modules")
    print(f"Budget violations: {len(violations)}")
    print(f"Import failures: {len(failures)}")
    
    if violations:
        print("\nModules exceeding budget:")
        for r in violations:
            print(f"  {r.module}: {r.time_ms:.1f} ms (over by {r.time_ms - budget_ms:.1f} ms)")
        print("\nRecommendation: Apply lazy imports to reduce startup time")
    
    if failures:
        print("\nImport failures:")
        for r in failures:
            print(f"  {r.module}: {r.error}")
    
    if violations or failures:
        return 1
    
    print("\n✓ All imports within budget")
    return 0


if __name__ == "__main__":
    sys.exit(main())
