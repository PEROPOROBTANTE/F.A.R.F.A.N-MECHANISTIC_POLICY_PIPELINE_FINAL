"""
Pydantic models for aggregation weight validation.

This module provides strict type-safe validation for aggregation weights,
ensuring zero-tolerance for invalid values at ingestion time.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self

class AggregationWeights(BaseModel):
    """
    Validation model for aggregation weights.

    Enforces:
    - All weights must be non-negative (>= 0)
    - All weights must be <= 1.0
    - Weights must sum to 1.0 (within tolerance)
    """

    model_config = ConfigDict(frozen=True, extra='forbid')

    weights: list[float] = Field(..., min_length=1, description="List of aggregation weights")
    tolerance: float = Field(default=1e-6, ge=0, description="Tolerance for sum validation")

    @field_validator('weights')
    @classmethod
    def validate_non_negative(cls, v: list[float]) -> list[float]:
        """Ensure all weights are non-negative."""
        for i, weight in enumerate(v):
            if weight < 0:
                raise ValueError(
                    f"Invalid aggregation weight at index {i}: {weight}. "
                    f"All weights must be non-negative (>= 0)."
                )
            if weight > 1.0:
                raise ValueError(
                    f"Invalid aggregation weight at index {i}: {weight}. "
                    f"All weights must be <= 1.0."
                )
        return v

    @model_validator(mode='after')
    def validate_sum(self) -> Self:
        """Ensure weights sum to 1.0 within tolerance."""
        weight_sum = sum(self.weights)
        if abs(weight_sum - 1.0) > self.tolerance:
            raise ValueError(
                f"Weight sum validation failed: sum={weight_sum:.6f}, expected=1.0. "
                f"Difference {abs(weight_sum - 1.0):.6f} exceeds tolerance {self.tolerance:.6f}."
            )
        return self

class DimensionAggregationConfig(BaseModel):
    """Configuration for dimension-level aggregation."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    dimension_id: str = Field(..., pattern=r'^DIM\d{2}$')
    area_id: str = Field(..., pattern=r'^PA\d{2}$')
    weights: AggregationWeights | None = None
    expected_question_count: int = Field(default=5, ge=1, le=10)
    group_by_keys: list[str] = Field(default=['dimension', 'policy_area'], min_length=1)


class AreaAggregationConfig(BaseModel):
    """Configuration for area-level aggregation."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    area_id: str = Field(..., pattern=r'^PA\d{2}$')
    expected_dimension_count: int = Field(default=6, ge=1, le=10)
    weights: AggregationWeights | None = None
    group_by_keys: list[str] = Field(default=['area_id'], min_length=1)


class ClusterAggregationConfig(BaseModel):
    """Configuration for cluster-level aggregation."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    cluster_id: str = Field(..., pattern=r'^CL\d{2}$')
    policy_area_ids: list[str] = Field(..., min_length=1)
    weights: AggregationWeights | None = None
    group_by_keys: list[str] = Field(default=['cluster_id'], min_length=1)

    @field_validator('policy_area_ids')
    @classmethod
    def validate_policy_areas(cls, v: list[str]) -> list[str]:
        """Ensure all policy area IDs follow the correct pattern."""
        for pa_id in v:
            if len(pa_id) < 3 or not pa_id.startswith('PA') or not pa_id[2:].isdigit():
                raise ValueError(f"Invalid policy area ID: {pa_id}. Expected format: PA##")
        return v

class MacroAggregationConfig(BaseModel):
    """Configuration for macro-level aggregation."""

    model_config = ConfigDict(frozen=True, extra='forbid')

    cluster_ids: list[str] = Field(..., min_length=1)
    weights: AggregationWeights | None = None

    @field_validator('cluster_ids')
    @classmethod
    def validate_clusters(cls, v: list[str]) -> list[str]:
        """Ensure all cluster IDs follow the correct pattern."""
        for cl_id in v:
            if len(cl_id) < 3 or not cl_id.startswith('CL') or not cl_id[2:].isdigit():
                raise ValueError(f"Invalid cluster ID: {cl_id}. Expected format: CL##")
        return v

def validate_weights(weights: list[float], tolerance: float = 1e-6) -> AggregationWeights:
    """
    Convenience function to validate a list of weights.

    Args:
        weights: List of weights to validate
        tolerance: Tolerance for sum validation

    Returns:
        Validated AggregationWeights instance

    Raises:
        ValueError: If validation fails
    """
    return AggregationWeights(weights=weights, tolerance=tolerance)

def validate_dimension_config(
    dimension_id: str,
    area_id: str,
    weights: list[float] | None = None,
    expected_question_count: int = 5
) -> DimensionAggregationConfig:
    """
    Validate dimension aggregation configuration.

    Args:
        dimension_id: Dimension ID (e.g., "DIM01")
        area_id: Area ID (e.g., "PA01")
        weights: Optional list of weights
        expected_question_count: Expected number of questions

    Returns:
        Validated configuration

    Raises:
        ValueError: If validation fails
    """
    weight_model = None
    if weights is not None:
        weight_model = validate_weights(weights)

    return DimensionAggregationConfig(
        dimension_id=dimension_id,
        area_id=area_id,
        weights=weight_model,
        expected_question_count=expected_question_count
    )
