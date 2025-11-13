"""
Tests for aggregation weight validation using Pydantic models.

Tests zero-tolerance enforcement of validation constraints.
"""

import pytest
from pydantic import ValidationError

from saaaaaa.utils.validation.aggregation_models import (
    AggregationWeights,
    AreaAggregationConfig,
    ClusterAggregationConfig,
    DimensionAggregationConfig,
    MacroAggregationConfig,
    validate_dimension_config,
    validate_weights,
)

class TestAggregationWeights:
    """Test AggregationWeights validation model."""

    def test_valid_equal_weights(self):
        """Test valid equal weights."""
        weights = AggregationWeights(weights=[0.25, 0.25, 0.25, 0.25])
        assert len(weights.weights) == 4
        assert sum(weights.weights) == pytest.approx(1.0)

    def test_valid_unequal_weights(self):
        """Test valid unequal weights."""
        weights = AggregationWeights(weights=[0.1, 0.2, 0.3, 0.4])
        assert sum(weights.weights) == pytest.approx(1.0)

    def test_negative_weight_rejected(self):
        """Test that negative weights are rejected."""
        with pytest.raises(ValidationError, match="non-negative"):
            AggregationWeights(weights=[0.5, -0.1, 0.6])

    def test_weight_greater_than_one_rejected(self):
        """Test that weights > 1.0 are rejected."""
        with pytest.raises(ValidationError, match="<= 1.0"):
            AggregationWeights(weights=[1.5, 0.0, 0.0])

    def test_weights_not_summing_to_one_rejected(self):
        """Test that weights not summing to 1.0 are rejected."""
        with pytest.raises(ValidationError, match="Weight sum validation failed"):
            AggregationWeights(weights=[0.3, 0.3, 0.3])

    def test_empty_weights_rejected(self):
        """Test that empty weight list is rejected."""
        with pytest.raises(ValidationError):
            AggregationWeights(weights=[])

    def test_single_weight_of_one(self):
        """Test single weight of 1.0."""
        weights = AggregationWeights(weights=[1.0])
        assert weights.weights == [1.0]

    def test_tolerance_parameter(self):
        """Test custom tolerance parameter."""
        # This should pass with default tolerance
        weights = AggregationWeights(weights=[0.333333, 0.333333, 0.333334])
        assert sum(weights.weights) == pytest.approx(1.0, abs=1e-6)

        # This should fail with very strict tolerance - weights that are farther from 1.0
        with pytest.raises(ValidationError, match="exceeds tolerance"):
            AggregationWeights(
                weights=[0.3, 0.3, 0.3],  # Sum is 0.9, not 1.0
                tolerance=1e-9
            )

    def test_immutability(self):
        """Test that AggregationWeights is immutable."""
        weights = AggregationWeights(weights=[0.5, 0.5])
        with pytest.raises(ValidationError):
            weights.weights = [0.3, 0.7]

    def test_extra_fields_rejected(self):
        """Test that extra fields are rejected."""
        with pytest.raises(ValidationError):
            AggregationWeights(weights=[0.5, 0.5], extra_field="invalid")

    def test_multiple_negative_weights(self):
        """Test rejection of multiple negative weights."""
        with pytest.raises(ValidationError, match="non-negative"):
            AggregationWeights(weights=[-0.1, -0.2, 1.3])

    def test_zero_weights_valid(self):
        """Test that zero weights are valid."""
        weights = AggregationWeights(weights=[0.0, 0.0, 1.0])
        assert weights.weights[0] == 0.0
        assert weights.weights[1] == 0.0

class TestDimensionAggregationConfig:
    """Test DimensionAggregationConfig validation."""

    def test_valid_config(self):
        """Test valid dimension configuration."""
        config = DimensionAggregationConfig(
            dimension_id="DIM01",
            area_id="PA01"
        )
        assert config.dimension_id == "DIM01"
        assert config.area_id == "PA01"

    def test_invalid_dimension_id_format(self):
        """Test invalid dimension ID format."""
        with pytest.raises(ValidationError, match="DIM"):
            DimensionAggregationConfig(
                dimension_id="INVALID",
                area_id="PA01"
            )

    def test_invalid_area_id_format(self):
        """Test invalid area ID format."""
        with pytest.raises(ValidationError, match="PA"):
            DimensionAggregationConfig(
                dimension_id="DIM01",
                area_id="INVALID"
            )

    def test_with_weights(self):
        """Test dimension config with weights."""
        weights = AggregationWeights(weights=[0.2, 0.2, 0.2, 0.2, 0.2])
        config = DimensionAggregationConfig(
            dimension_id="DIM01",
            area_id="PA01",
            weights=weights,
            expected_question_count=5
        )
        assert config.weights == weights

class TestAreaAggregationConfig:
    """Test AreaAggregationConfig validation."""

    def test_valid_config(self):
        """Test valid area configuration."""
        config = AreaAggregationConfig(area_id="PA05")
        assert config.area_id == "PA05"
        assert config.expected_dimension_count == 6

    def test_invalid_area_id(self):
        """Test invalid area ID."""
        with pytest.raises(ValidationError):
            AreaAggregationConfig(area_id="INVALID")

class TestClusterAggregationConfig:
    """Test ClusterAggregationConfig validation."""

    def test_valid_config(self):
        """Test valid cluster configuration."""
        config = ClusterAggregationConfig(
            cluster_id="CL01",
            policy_area_ids=["PA01", "PA02", "PA03"]
        )
        assert config.cluster_id == "CL01"
        assert len(config.policy_area_ids) == 3

    def test_invalid_cluster_id(self):
        """Test invalid cluster ID."""
        with pytest.raises(ValidationError):
            ClusterAggregationConfig(
                cluster_id="INVALID",
                policy_area_ids=["PA01"]
            )

    def test_invalid_policy_area_id(self):
        """Test invalid policy area ID in list."""
        with pytest.raises(ValidationError, match="Invalid policy area ID"):
            ClusterAggregationConfig(
                cluster_id="CL01",
                policy_area_ids=["PA01", "INVALID", "PA03"]
            )

    def test_empty_policy_areas_rejected(self):
        """Test that empty policy area list is rejected."""
        with pytest.raises(ValidationError):
            ClusterAggregationConfig(
                cluster_id="CL01",
                policy_area_ids=[]
            )

    def test_short_policy_area_id_rejected(self):
        """Test that policy area IDs shorter than 3 characters are rejected."""
        with pytest.raises(ValidationError, match="Invalid policy area ID"):
            ClusterAggregationConfig(
                cluster_id="CL01",
                policy_area_ids=["PA"]  # Too short
            )

class TestMacroAggregationConfig:
    """Test MacroAggregationConfig validation."""

    def test_valid_config(self):
        """Test valid macro configuration."""
        config = MacroAggregationConfig(
            cluster_ids=["CL01", "CL02", "CL03", "CL04"]
        )
        assert len(config.cluster_ids) == 4

    def test_invalid_cluster_id(self):
        """Test invalid cluster ID."""
        with pytest.raises(ValidationError, match="Invalid cluster ID"):
            MacroAggregationConfig(
                cluster_ids=["CL01", "INVALID"]
            )

    def test_short_cluster_id_rejected(self):
        """Test that cluster IDs shorter than 3 characters are rejected."""
        with pytest.raises(ValidationError, match="Invalid cluster ID"):
            MacroAggregationConfig(
                cluster_ids=["CL"]  # Too short
            )

class TestValidationHelpers:
    """Test validation helper functions."""

    def test_validate_weights_helper(self):
        """Test validate_weights convenience function."""
        weights = validate_weights([0.3, 0.3, 0.4])
        assert isinstance(weights, AggregationWeights)
        assert sum(weights.weights) == pytest.approx(1.0)

    def test_validate_weights_helper_with_negative(self):
        """Test validate_weights rejects negative weights."""
        with pytest.raises(ValidationError):
            validate_weights([0.5, -0.1, 0.6])

    def test_validate_dimension_config_helper(self):
        """Test validate_dimension_config helper."""
        config = validate_dimension_config(
            dimension_id="DIM02",
            area_id="PA03",
            weights=[0.2, 0.2, 0.2, 0.2, 0.2]
        )
        assert isinstance(config, DimensionAggregationConfig)
        assert config.dimension_id == "DIM02"
        assert config.weights is not None

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_small_weights(self):
        """Test very small but valid weights."""
        weights = AggregationWeights(
            weights=[0.001, 0.001, 0.998]
        )
        assert sum(weights.weights) == pytest.approx(1.0)

    def test_precision_edge_case(self):
        """Test floating point precision edge case."""
        # Weights that sum to exactly 1.0 due to representation
        weights = AggregationWeights(
            weights=[1/3, 1/3, 1/3]
        )
        # Should pass with default tolerance
        assert weights is not None

    def test_many_weights(self):
        """Test with many weights."""
        n = 100
        weight_list = [1.0 / n] * n
        weights = AggregationWeights(weights=weight_list)
        assert len(weights.weights) == n
        assert sum(weights.weights) == pytest.approx(1.0, abs=1e-6)

class TestStrictValidationBehavior:
    """Test strict validation behavior for the problem statement requirements."""

    def test_zero_tolerance_for_negative_weights(self):
        """
        REQUIREMENT: Zero-tolerance for invalid weights.
        Negative weights must be rejected immediately.
        """
        test_cases = [
            [-1.0],
            [-0.5, 1.5],
            [0.3, -0.2, 0.9],
            [-0.001, 0.501, 0.5],
        ]

        for weights in test_cases:
            with pytest.raises(ValidationError, match="non-negative"):
                AggregationWeights(weights=weights)

    def test_validation_at_ingestion(self):
        """
        REQUIREMENT: Validation at ingestion, not downstream.
        Models should validate immediately upon creation.
        """
        # This should fail immediately at object creation
        with pytest.raises(ValidationError) as exc_info:
            AggregationWeights(weights=[0.6, -0.1, 0.5])

        # Ensure the error is raised during initialization
        assert "non-negative" in str(exc_info.value)

    def test_auditable_diagnostics(self):
        """
        REQUIREMENT: Violations should halt pipeline with auditable diagnostic.
        Error messages should be clear and actionable.
        """
        try:
            AggregationWeights(weights=[-0.5, 1.5])
            pytest.fail("Should have raised ValidationError")
        except ValidationError as e:
            error_msg = str(e)
            # Verify error message contains useful diagnostic information
            assert "non-negative" in error_msg.lower()
            # Verify it indicates which weight is invalid
            assert "-0.5" in error_msg or "index" in error_msg.lower()
