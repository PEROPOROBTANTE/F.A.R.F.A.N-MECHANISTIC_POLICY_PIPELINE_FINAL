#!/usr/bin/env python3
"""
Comprehensive import consistency test.

Tests that all import paths work correctly from different locations:
1. Root-level compatibility shims (orchestrator/, scoring/, etc.)
2. Direct saaaaaa.* imports
3. Root-level .py file imports
"""

import sys
from pathlib import Path

# Add parent directory to path for root-level imports

def test_root_level_module_imports():
    """Test that root-level .py files can be imported."""
    # These should all work via compatibility wrappers
    from saaaaaa.scoring import apply_scoring
    from saaaaaa.core.orchestrator import Orchestrator
    from saaaaaa.contracts import SeedFactory
    from saaaaaa.core.aggregation import AreaPolicyAggregator
    
    assert callable(apply_scoring)
    assert Orchestrator is not None
    assert SeedFactory is not None
    assert AreaPolicyAggregator is not None
    print("✓ Root-level module imports work")

def test_root_level_package_imports():
    """Test that root-level compatibility packages can be imported."""
    # Import from packages (directories with __init__.py)
    from saaaaaa.scoring.scoring import QualityLevel
    from saaaaaa.core.orchestrator.core import Evidence
    from saaaaaa.concurrency.concurrency import WorkerPool
    from saaaaaa.contracts import validate_contract
    
    assert QualityLevel is not None
    assert Evidence is not None
    assert WorkerPool is not None
    assert callable(validate_contract)
    print("✓ Root-level package imports work")

def test_saaaaaa_direct_imports():
    """Test that direct saaaaaa.* imports work."""
    # Ensure src is in path
    src_path = Path(__file__).parent.parent / "src"
    from saaaaaa.analysis.scoring.scoring import apply_scoring as apply_scoring_direct
    from saaaaaa.core.orchestrator import Orchestrator as OrchestratorDirect
    from saaaaaa.utils.contracts import validate_contract as validate_contract_direct
    from saaaaaa.processing.aggregation import AreaPolicyAggregator as AggregatorDirect
    
    assert callable(apply_scoring_direct)
    assert OrchestratorDirect is not None
    assert callable(validate_contract_direct)
    assert AggregatorDirect is not None
    print("✓ Direct saaaaaa.* imports work")

def test_import_equivalence():
    """Test that both import paths lead to the same objects."""
    src_path = Path(__file__).parent.parent / "src"
    # Import same thing via different paths
    from saaaaaa.scoring import apply_scoring as apply_scoring_compat
    from saaaaaa.analysis.scoring.scoring import apply_scoring as apply_scoring_direct
    
    # They should be the same function
    assert apply_scoring_compat is apply_scoring_direct, \
        "Compatibility wrapper and direct import should reference the same object"
    print("✓ Import paths are equivalent (reference same objects)")

def test_executors_lazy_loading():
    """Test that executors module can be imported (lazy loading)."""
    from saaaaaa.core.orchestrator import executors
    
    assert executors is not None
    print("✓ Executors module lazy loading works")

def test_all_compatibility_shims():
    """Test all compatibility shim directories and modules."""
    compatibility_packages = [
        'orchestrator',
        'scoring',
        'concurrency',
        'contracts',
        'core',
        'executors',
    ]
    
    compatibility_modules = [
        'aggregation',
        'bayesian_multilevel_system',
        # 'derek_beach',  # Skip - has spacy dependency
        'document_ingestion',
        # 'embedding_policy',  # Skip - has sentence_transformers dependency
        'macro_prompts',
        'micro_prompts',
        # 'policy_processor',  # Skip - may have dependencies
        # 'recommendation_engine',  # Skip - may have dependencies
        'scoring',
        'meso_cluster_analysis',
    ]
    
    for package in compatibility_packages:
        try:
            __import__(package)
            print(f"✓ {package} compatibility shim works")
        except ImportError as e:
            print(f"✗ {package} compatibility shim FAILED: {e}")
            raise
    
    for module in compatibility_modules:
        try:
            __import__(module)
            print(f"✓ {module} compatibility wrapper works")
        except ImportError as e:
            print(f"✗ {module} compatibility wrapper FAILED: {e}")
            raise

def main():
    """Run all import tests."""
    print("=" * 70)
    print("IMPORT CONSISTENCY TEST SUITE")
    print("=" * 70)
    print()
    
    tests = [
        test_all_compatibility_shims,
        test_root_level_module_imports,
        test_root_level_package_imports,
        test_saaaaaa_direct_imports,
        test_import_equivalence,
        test_executors_lazy_loading,
    ]
    
    failed = []
    for test_func in tests:
        try:
            print(f"\nRunning: {test_func.__name__}")
            test_func()
        except Exception as e:
            print(f"✗ FAILED: {test_func.__name__}")
            print(f"  Error: {e}")
            failed.append((test_func.__name__, e))
    
    print("\n" + "=" * 70)
    if failed:
        print(f"FAILED: {len(failed)} test(s) failed")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return 1
    else:
        print("SUCCESS: All import consistency tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
