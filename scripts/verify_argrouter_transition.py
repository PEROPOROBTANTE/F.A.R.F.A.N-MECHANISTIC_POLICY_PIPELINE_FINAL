#!/usr/bin/env python
"""Verification script for ArgRouter → ExtendedArgRouter transition.

This script verifies that the transition has been implemented correctly.
Run this after merging the PR to confirm everything is working.

Usage:
    python scripts/verify_argrouter_transition.py
"""

import sys
from pathlib import Path

# Add src to path
repo_root = Path(__file__).parent.parent


def check_imports() -> tuple[bool, str]:
    """Verify ExtendedArgRouter can be imported."""
    try:
        from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
        return True, "ExtendedArgRouter import successful"
    except ImportError as e:
        return False, f"Failed to import ExtendedArgRouter: {e}"


def check_phase4_complete() -> tuple[bool, str]:
    """Verify Phase 4 completion - consolidated arg_router.py exists."""
    try:
        from saaaaaa.core.orchestrator.arg_router import ArgRouter, ExtendedArgRouter
        
        # Check that both classes are available from the single module
        assert ArgRouter is not None
        assert ExtendedArgRouter is not None
        
        # Verify ArgRouter base class doesn't emit deprecation warnings (Phase 4 complete)
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            router = ArgRouter({})
            
            # Should have NO deprecation warnings in Phase 4
            deprecation_warnings = [x for x in w if issubclass(x.category, DeprecationWarning)]
            if deprecation_warnings:
                return False, f"Unexpected deprecation warnings found (Phase 4 should remove these)"
        
        return True, "Phase 4 complete - consolidated arg_router.py"
    except Exception as e:
        return False, f"Error checking Phase 4 completion: {e}"


def check_special_routes() -> tuple[bool, str]:
    """Verify special routes are defined."""
    try:
        from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
        
        router = ExtendedArgRouter({})
        coverage = router.get_special_route_coverage()
        
        if coverage < 30:
            return False, f"Expected ≥30 special routes, got {coverage}"
        
        return True, f"Special routes verified ({coverage} routes)"
    except Exception as e:
        return False, f"Error checking special routes: {e}"


def check_metrics() -> tuple[bool, str]:
    """Verify metrics are available."""
    try:
        from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
        
        router = ExtendedArgRouter({})
        metrics = router.get_metrics()
        
        required_keys = [
            'total_routes',
            'special_routes_hit',
            'validation_errors',
            'silent_drops_prevented',
        ]
        
        missing = [k for k in required_keys if k not in metrics]
        if missing:
            return False, f"Missing metrics keys: {missing}"
        
        return True, "Metrics structure verified"
    except Exception as e:
        return False, f"Error checking metrics: {e}"


def check_files() -> tuple[bool, str]:
    """Verify required files exist."""
    required_files = [
        'scripts/report_routing_metrics.py',
        'tests/test_routing_metrics_integration.py',
        '.github/workflows/routing-metrics.yml',
        'docs/ARGROUTER_MIGRATION_GUIDE.md',
        'ARGROUTER_TRANSITION_SUMMARY.md',
    ]
    
    missing = []
    for file_path in required_files:
        if not (repo_root / file_path).exists():
            missing.append(file_path)
    
    if missing:
        return False, f"Missing files: {missing}"
    
    return True, "All required files present"


def main() -> int:
    """Run all verification checks."""
    print("="*70)
    print("ArgRouter → ExtendedArgRouter Transition Verification")
    print("="*70)
    print()
    
    checks = [
        ("Import ExtendedArgRouter", check_imports),
        ("Phase 4 Complete", check_phase4_complete),
        ("Special Routes", check_special_routes),
        ("Metrics Structure", check_metrics),
        ("Required Files", check_files),
    ]
    
    results = []
    for name, check_fn in checks:
        print(f"Checking: {name}...", end=" ")
        success, message = check_fn()
        results.append(success)
        
        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    
    print()
    print("="*70)
    
    if all(results):
        print("🎉 All verification checks passed!")
        print()
        print("The ArgRouter → ExtendedArgRouter transition is complete.")
        print("See docs/ARGROUTER_MIGRATION_GUIDE.md for usage information.")
        return 0
    else:
        failed = sum(1 for r in results if not r)
        print(f"❌ {failed}/{len(results)} checks failed")
        print()
        print("Please review the errors above and ensure all changes were applied.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
