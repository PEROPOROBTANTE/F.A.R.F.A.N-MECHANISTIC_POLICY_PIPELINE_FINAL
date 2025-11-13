"""Compatibility shim for aggregation validation models."""
from saaaaaa.utils.validation.aggregation_models import (  # noqa: F401
    AggregationWeights,
    AreaAggregationConfig,
    ClusterAggregationConfig,
    DimensionAggregationConfig,
    MacroAggregationConfig,
    validate_dimension_config,
    validate_weights,
)

__all__ = [
    "AggregationWeights",
    "AreaAggregationConfig",
    "ClusterAggregationConfig",
    "DimensionAggregationConfig",
    "MacroAggregationConfig",
    "validate_dimension_config",
    "validate_weights",
]
