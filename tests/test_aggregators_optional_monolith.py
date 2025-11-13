"""Tests for aggregators with optional monolith parameter."""

import pytest


def test_dimension_aggregator_without_monolith():
    """Test DimensionAggregator can be instantiated without monolith."""
    from saaaaaa.processing.aggregation import DimensionAggregator
    
    # Should not raise error
    aggregator = DimensionAggregator(monolith=None)
    assert aggregator is not None
    assert aggregator.monolith is None


def test_area_policy_aggregator_without_monolith():
    """Test AreaPolicyAggregator can be instantiated without monolith."""
    from saaaaaa.processing.aggregation import AreaPolicyAggregator
    
    # Should not raise error
    aggregator = AreaPolicyAggregator(monolith=None)
    assert aggregator is not None
    assert aggregator.monolith is None


def test_cluster_aggregator_without_monolith():
    """Test ClusterAggregator can be instantiated without monolith."""
    from saaaaaa.processing.aggregation import ClusterAggregator
    
    # Should not raise error
    aggregator = ClusterAggregator(monolith=None)
    assert aggregator is not None
    assert aggregator.monolith is None


def test_macro_aggregator_without_monolith():
    """Test MacroAggregator can be instantiated without monolith."""
    from saaaaaa.processing.aggregation import MacroAggregator
    
    # Should not raise error
    aggregator = MacroAggregator(monolith=None)
    assert aggregator is not None
    assert aggregator.monolith is None


def test_aggregators_with_monolith():
    """Test aggregators work with monolith provided."""
    from saaaaaa.processing.aggregation import DimensionAggregator
    
    # Minimal monolith structure
    monolith = {
        "blocks": {
            "scoring": {"thresholds": {}},
            "niveles_abstraccion": {
                "policy_areas": [],
                "dimensions": []
            }
        }
    }
    
    aggregator = DimensionAggregator(monolith=monolith)
    assert aggregator.monolith is not None
    assert aggregator.scoring_config == {"thresholds": {}}
