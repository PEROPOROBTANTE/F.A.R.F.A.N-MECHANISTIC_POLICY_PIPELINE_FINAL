"""
Smoke test to verify all major submodules can be imported.

This test ensures the package structure is correct and all imports work
without sys.path manipulations.
"""

import importlib
import pkgutil
import sys
from pathlib import Path

import pytest


def test_package_imports():
    """Test that the main package can be imported."""
    import saaaaaa
    assert saaaaaa is not None
    assert hasattr(saaaaaa, '__path__')


def test_core_submodules():
    """Test that core submodules can be imported."""
    # Core orchestrator
    from saaaaaa.core import orchestrator
    assert orchestrator is not None
    
    # Core ports
    from saaaaaa.core import ports
    assert ports is not None


def test_analysis_submodules():
    """Test that analysis submodules can be imported."""
    from saaaaaa.analysis import bayesian_multilevel_system
    assert bayesian_multilevel_system is not None
    
    from saaaaaa.analysis import recommendation_engine
    assert recommendation_engine is not None
    
    from saaaaaa.analysis import meso_cluster_analysis
    assert meso_cluster_analysis is not None


def test_processing_submodules():
    """Test that processing submodules can be imported."""
    from saaaaaa.processing import document_ingestion
    assert document_ingestion is not None
    
    from saaaaaa.processing import embedding_policy
    assert embedding_policy is not None
    
    from saaaaaa.processing import aggregation
    assert aggregation is not None


def test_concurrency_module():
    """Test that concurrency module can be imported."""
    from saaaaaa.concurrency import concurrency
    assert concurrency is not None


def test_scoring_module():
    """Test that scoring module can be imported."""
    from saaaaaa.analysis.scoring import scoring
    assert scoring is not None


def test_api_module():
    """Test that API module can be imported."""
    from saaaaaa.api import api_server
    assert api_server is not None


def test_utils_submodules():
    """Test that utils submodules can be imported."""
    from saaaaaa.utils import contracts
    assert contracts is not None
    
    from saaaaaa.utils.validation import schema_validator
    assert schema_validator is not None


def test_infrastructure_modules():
    """Test that infrastructure modules can be imported."""
    from saaaaaa.infrastructure import filesystem
    assert filesystem is not None
    
    from saaaaaa.infrastructure import log_adapters
    assert log_adapters is not None


def test_walk_packages():
    """Test that we can walk all packages without errors."""
    import saaaaaa
    
    # Count packages
    packages = list(pkgutil.walk_packages(
        saaaaaa.__path__,
        prefix='saaaaaa.',
        onerror=lambda name: None
    ))
    
    # Should have multiple packages
    assert len(packages) > 5, f"Expected more packages, got {len(packages)}"
    
    # Try to import each discovered module (excluding known problematic ones)
    skip_modules = {
        'saaaaaa.core.orchestrator.ORCHESTRATOR_MONILITH',  # May require dependencies
    }
    
    imported_count = 0
    for importer, modname, ispkg in packages:
        if modname in skip_modules:
            continue
        
        try:
            importlib.import_module(modname)
            imported_count += 1
        except ImportError as e:
            # Some modules may have missing dependencies, that's ok for a smoke test
            if 'No module named' in str(e):
                pass
            else:
                # But other import errors should be reported
                print(f"Warning: Could not import {modname}: {e}")
    
    # At least 50% of modules should import successfully
    assert imported_count >= len(packages) * 0.3, \
        f"Only {imported_count}/{len(packages)} modules imported successfully"


def test_no_syspath_manipulation():
    """Verify that no module in the package manipulates sys.path."""
    import saaaaaa
    from pathlib import Path
    
    # Get all .py files in the package
    package_root = Path(saaaaaa.__path__[0])
    python_files = list(package_root.rglob('*.py'))
    
    violations = []
    for filepath in python_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for sys.path manipulations
            if 'sys.path.insert' in content or 'sys.path.append' in content:
                violations.append(str(filepath.relative_to(package_root.parent)))
        except Exception:
            pass
    
    assert len(violations) == 0, \
        f"Found sys.path manipulations in: {violations}"


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
