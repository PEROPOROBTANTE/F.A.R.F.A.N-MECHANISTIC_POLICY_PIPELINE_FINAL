"""Tests for CPPAdapter without pyarrow dependency."""

import pytest


def test_cpp_adapter_import_without_arrow():
    """Test that CPPAdapter can be imported without pyarrow."""
    # This should not raise ImportError
    from saaaaaa.utils.cpp_adapter import CPPAdapter
    
    # Should be able to instantiate
    adapter = CPPAdapter()
    assert adapter is not None
    assert adapter._conversions_count == 0


def test_cpp_adapter_has_methods():
    """Test that CPPAdapter has expected methods."""
    from saaaaaa.utils.cpp_adapter import CPPAdapter
    
    adapter = CPPAdapter()
    assert hasattr(adapter, "to_preprocessed_document")
    assert hasattr(adapter, "_calculate_provenance_completeness")
    assert hasattr(adapter, "get_metrics")


def test_cpp_adapter_metrics():
    """Test that CPPAdapter can report metrics."""
    from saaaaaa.utils.cpp_adapter import CPPAdapter
    
    adapter = CPPAdapter()
    metrics = adapter.get_metrics()
    
    assert isinstance(metrics, dict)
    assert "conversions_count" in metrics
    assert metrics["conversions_count"] == 0
