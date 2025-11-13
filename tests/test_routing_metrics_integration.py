"""Integration tests for ExtendedArgRouter metrics collection and reporting."""

import json
import tempfile
from pathlib import Path

import pytest

from saaaaaa.core.orchestrator.arg_router import ExtendedArgRouter
from scripts.report_routing_metrics import format_metrics_report, report_metrics


class DummyClass:
    """Dummy class for testing routing."""
    
    def simple_method(self, arg1: str) -> str:
        return arg1
    
    def kwargs_method(self, arg1: str, **kwargs: object) -> str:
        return arg1


@pytest.fixture
def router():
    """Create an ExtendedArgRouter for testing."""
    return ExtendedArgRouter({"DummyClass": DummyClass})


def test_metrics_collection(router):
    """Test that metrics are properly collected during routing."""
    # Initial state
    metrics = router.get_metrics()
    assert metrics['total_routes'] == 0
    assert metrics['special_routes_hit'] == 0
    assert metrics['validation_errors'] == 0
    
    # Route a call
    router.route("DummyClass", "simple_method", {"arg1": "test"})
    
    # Check metrics updated
    metrics = router.get_metrics()
    assert metrics['total_routes'] == 1
    assert metrics['default_routes_hit'] == 1


def test_metrics_silent_drop_prevention(router):
    """Test that silent drops are properly tracked."""
    # Try to route with unexpected argument to a method without **kwargs
    with pytest.raises(Exception):  # Should raise ArgumentValidationError
        router.route("DummyClass", "simple_method", {"arg1": "test", "unexpected": "value"})
    
    # Check that silent drop was prevented
    metrics = router.get_metrics()
    assert metrics['validation_errors'] > 0
    assert metrics['silent_drops_prevented'] > 0


def test_metrics_report_formatting():
    """Test that metrics report is properly formatted."""
    sample_metrics = {
        'total_routes': 100,
        'special_routes_hit': 25,
        'default_routes_hit': 75,
        'special_routes_coverage': 30,
        'validation_errors': 5,
        'silent_drops_prevented': 3,
        'special_route_hit_rate': 0.25,
        'error_rate': 0.05,
    }
    
    report = format_metrics_report(sample_metrics)
    
    # Verify key information is in report
    assert 'Total Routes:' in report
    assert '100' in report
    assert 'Special Routes Hit:' in report
    assert '25' in report
    assert 'Silent Drops Prevented:' in report
    assert '3' in report


def test_metrics_report_no_silent_drops():
    """Test that report_metrics succeeds when no silent drops."""
    metrics = {
        'total_routes': 10,
        'silent_drops_prevented': 0,
    }
    
    result = report_metrics(metrics, fail_on_silent_drops=True)
    assert result == 0  # Should succeed


def test_metrics_report_with_silent_drops_no_fail():
    """Test that report_metrics warns but succeeds when silent drops present (without fail flag)."""
    metrics = {
        'total_routes': 10,
        'silent_drops_prevented': 2,
    }
    
    result = report_metrics(metrics, fail_on_silent_drops=False)
    assert result == 0  # Should succeed with warning


def test_metrics_report_with_silent_drops_fail():
    """Test that report_metrics fails when silent drops present (with fail flag)."""
    metrics = {
        'total_routes': 10,
        'silent_drops_prevented': 2,
    }
    
    result = report_metrics(metrics, fail_on_silent_drops=True)
    assert result == 1  # Should fail


def test_metrics_json_roundtrip():
    """Test that metrics can be serialized to JSON and back."""
    sample_metrics = {
        'total_routes': 100,
        'special_routes_hit': 25,
        'validation_errors': 5,
    }
    
    # Write to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(sample_metrics, f)
        temp_path = Path(f.name)
    
    try:
        # Read back
        with open(temp_path) as f:
            loaded_metrics = json.load(f)
        
        assert loaded_metrics == sample_metrics
    finally:
        temp_path.unlink()


def test_method_executor_metrics_integration():
    """Test that MethodExecutor exposes metrics from ExtendedArgRouter."""
    try:
        from saaaaaa.core.orchestrator.core import MethodExecutor
    except (ImportError, SystemExit) as e:
        pytest.skip(f"MethodExecutor import failed (missing dependencies): {e}")
    
    # This will create a MethodExecutor with ExtendedArgRouter
    try:
        executor = MethodExecutor()
        
        # Verify metrics method exists
        assert hasattr(executor, 'get_routing_metrics')
        
        # Get initial metrics
        metrics = executor.get_routing_metrics()
        
        # Should return a dict (even if empty initially)
        assert isinstance(metrics, dict)
        
    except (SystemExit, ImportError, ModuleNotFoundError) as e:
        # If instantiation fails due to missing dependencies, that's okay for this test
        # We're just verifying the interface exists
        pytest.skip(f"MethodExecutor instantiation failed (expected in minimal test env): {e}")
