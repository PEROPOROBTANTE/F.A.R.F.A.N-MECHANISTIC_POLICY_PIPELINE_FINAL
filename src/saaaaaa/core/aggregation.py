"""Aggregation module re-exports from processing package.

This module provides backward compatibility for code that imports
aggregation classes from saaaaaa.core.aggregation instead of
saaaaaa.processing.aggregation.
"""

from saaaaaa.processing.aggregation import (
    AreaPolicyAggregator,
    AreaScore,
    ClusterAggregator,
    ClusterScore,
    DimensionAggregator,
    DimensionScore,
    MacroAggregator,
    ScoredResult,
)

__all__ = [
    "AreaPolicyAggregator",
    "AreaScore",
    "ClusterAggregator",
    "ClusterScore",
    "DimensionAggregator",
    "DimensionScore",
    "MacroAggregator",
    "ScoredResult",
]
