"""Aggregation module re-exports from processing package.

This module provides backward compatibility for code that imports
aggregation classes from farfan_core.core.aggregation instead of
farfan_core.processing.aggregation.
"""

from farfan_pipeline.processing.aggregation import (
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
