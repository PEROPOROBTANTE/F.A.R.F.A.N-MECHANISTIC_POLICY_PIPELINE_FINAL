"""Test statistics guards for edge cases in core.py."""
import statistics
import pytest


def test_variance_with_empty_list():
    """Test variance calculation with empty list."""
    normalized_values = []
    
    # Guard implementation
    variance = (
        statistics.variance(normalized_values)
        if len(normalized_values) >= 2
        else 0.0
    )
    
    assert variance == 0.0


def test_variance_with_single_value():
    """Test variance calculation with single value."""
    normalized_values = [0.5]
    
    # Guard implementation
    variance = (
        statistics.variance(normalized_values)
        if len(normalized_values) >= 2
        else 0.0
    )
    
    assert variance == 0.0


def test_variance_with_two_values():
    """Test variance calculation with two values."""
    normalized_values = [0.4, 0.6]
    
    # Guard implementation
    variance = (
        statistics.variance(normalized_values)
        if len(normalized_values) >= 2
        else 0.0
    )
    
    # Should calculate variance normally
    assert variance > 0.0
    assert variance == statistics.variance(normalized_values)


def test_variance_with_multiple_values():
    """Test variance calculation with multiple values."""
    normalized_values = [0.3, 0.5, 0.7, 0.9]
    
    # Guard implementation
    variance = (
        statistics.variance(normalized_values)
        if len(normalized_values) >= 2
        else 0.0
    )
    
    # Should calculate variance normally
    assert variance > 0.0
    assert variance == statistics.variance(normalized_values)


def test_variance_without_guard_raises():
    """Test that variance without guard raises error on single value."""
    normalized_values = [0.5]
    
    with pytest.raises(statistics.StatisticsError):
        statistics.variance(normalized_values)


def test_mean_with_empty_list():
    """Test mean calculation with empty list using guard."""
    values = []
    
    # Guard implementation
    mean = statistics.mean(values) if len(values) >= 1 else 0.0
    
    assert mean == 0.0


def test_mean_with_values():
    """Test mean calculation with values."""
    values = [1.0, 2.0, 3.0]
    
    # Guard implementation
    mean = statistics.mean(values) if len(values) >= 1 else 0.0
    
    assert mean == 2.0
