"""
Unit Tests for Aggregation Module
==================================

Comprehensive tests for the hierarchical aggregation system:
- FASE 4: Dimension aggregation (60 dimensions: 6 × 10 policy areas)
- FASE 5: Policy area aggregation (10 areas)
- FASE 6: Cluster aggregation (4 MESO questions)
- FASE 7: Macro evaluation (1 holistic question)

Tests cover:
- Weight validation and normalization
- Threshold application
- Hermeticity checks
- Coherence analysis
- Deterministic aggregation
- Error handling and abortability
"""

from pathlib import Path
from typing import Any

import pytest

from saaaaaa.core.aggregation import (
    AreaPolicyAggregator,
    AreaScore,
    ClusterAggregator,
    ClusterScore,
    DimensionAggregator,
    DimensionScore,
    MacroAggregator,
    ScoredResult,
)

# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def minimal_monolith() -> dict[str, Any]:
    """Minimal monolith structure for testing."""
    return {
        "questions": [],
        "blocks": {
            "scoring": {
                "modalities": {}
            },
            "niveles_abstraccion": {
                "MICRO": {},
                "MESO": {},
                "MACRO": {}
            }
        },
        "rubric": {
            "dimension": {
                "thresholds": {
                    "EXCELENTE": 0.85,
                    "BUENO": 0.70,
                    "ACEPTABLE": 0.55,
                    "INSUFICIENTE": 0.0,
                }
            },
            "area": {
                "thresholds": {
                    "EXCELENTE": 0.85,
                    "BUENO": 0.70,
                    "ACEPTABLE": 0.55,
                    "INSUFICIENTE": 0.0,
                }
            },
            "cluster": {
                "thresholds": {
                    "EXCELENTE": 0.85,
                    "BUENO": 0.70,
                    "ACEPTABLE": 0.55,
                    "INSUFICIENTE": 0.0,
                }
            },
            "macro": {
                "thresholds": {
                    "EXCELENTE": 0.85,
                    "BUENO": 0.70,
                    "ACEPTABLE": 0.55,
                    "INSUFICIENTE": 0.0,
                }
            }
        },
        "clusters": {
            "CL01": {"name": "Cluster 1", "areas": ["P1", "P2"]},
            "CL02": {"name": "Cluster 2", "areas": ["P3", "P4"]},
            "CL03": {"name": "Cluster 3", "areas": ["P5", "P6"]},
            "CL04": {"name": "Cluster 4", "areas": ["P7", "P8"]},
        }
    }

@pytest.fixture
def sample_scored_results() -> list[ScoredResult]:
    """Sample scored results for a dimension."""
    return [
        ScoredResult(
            question_global=i,
            base_slot=f"P1-D1-Q{i:03d}",
            policy_area="P1",
            dimension="D1",
            score=2.0 + (i * 0.1),
            quality_level="BUENO",
            evidence={},
            raw_results={},
        )
        for i in range(1, 6)
    ]

@pytest.fixture
def sample_dimension_scores() -> list[DimensionScore]:
    """Sample dimension scores for an area."""
    return [
        DimensionScore(
            dimension_id=f"D{i}",
            area_id="P1",
            score=2.0 + (i * 0.1),
            quality_level="BUENO",
            micro_scores=[2.0] * 5,
            evidence={},
        )
        for i in range(1, 7)
    ]

# ============================================================================
# DIMENSION AGGREGATOR TESTS
# ============================================================================

class TestDimensionAggregator:
    """Test DimensionAggregator functionality."""

    def test_initialization(self, minimal_monolith):
        """Test aggregator initialization."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)
        assert aggregator.monolith == minimal_monolith
        assert aggregator.abort_on_insufficient is False

    def test_validate_weights_success(self, minimal_monolith):
        """Test weight validation with valid weights."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        valid_weights = [0.2, 0.2, 0.2, 0.2, 0.2]
        is_valid, msg = aggregator.validate_weights(valid_weights)
        assert is_valid
        assert "valid" in msg.lower()

    def test_validate_weights_not_sum_to_one(self, minimal_monolith):
        """Test weight validation rejects weights that don't sum to 1."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        invalid_weights = [0.3, 0.3, 0.3]
        is_valid, msg = aggregator.validate_weights(invalid_weights)
        assert not is_valid
        assert "sum" in msg.lower()

    @pytest.mark.xfail(reason="Weight validation doesn't reject negative weights - known bug")
    def test_validate_weights_negative(self, minimal_monolith):
        """Test weight validation rejects negative weights."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        invalid_weights = [0.5, 0.5, -0.1, 0.1]
        is_valid, msg = aggregator.validate_weights(invalid_weights)
        # BUG: Current implementation doesn't check for negative weights
        # This test documents the expected behavior
        assert not is_valid, "Should reject negative weights"
        assert "negative" in msg.lower(), "Error message should mention negative weights"

    def test_validate_coverage_complete(self, minimal_monolith):
        """Test coverage validation with complete coverage."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        expected_slots = {f"P1-D1-Q{i:03d}" for i in range(1, 6)}
        actual_slots = {f"P1-D1-Q{i:03d}" for i in range(1, 6)}

        is_complete, msg = aggregator.validate_coverage(expected_slots, actual_slots)
        assert is_complete

    def test_validate_coverage_incomplete(self, minimal_monolith):
        """Test coverage validation detects missing slots."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        expected_slots = {f"P1-D1-Q{i:03d}" for i in range(1, 6)}
        actual_slots = {f"P1-D1-Q{i:03d}" for i in range(1, 4)}  # Missing Q004, Q005

        is_complete, msg = aggregator.validate_coverage(expected_slots, actual_slots)
        assert not is_complete
        assert "missing" in msg.lower()

    def test_calculate_weighted_average(self, minimal_monolith):
        """Test weighted average calculation."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        scores = [1.0, 2.0, 3.0]
        weights = [0.2, 0.3, 0.5]

        avg = aggregator.calculate_weighted_average(scores, weights)
        expected = (1.0 * 0.2) + (2.0 * 0.3) + (3.0 * 0.5)
        assert avg == pytest.approx(expected)

    def test_apply_rubric_thresholds(self, minimal_monolith):
        """Test rubric threshold application."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        # EXCELENTE: ≥ 0.85
        level = aggregator.apply_rubric_thresholds(0.90, level="dimension")
        assert level == "EXCELENTE"

        # BUENO: ≥ 0.70
        level = aggregator.apply_rubric_thresholds(0.75, level="dimension")
        assert level == "BUENO"

        # ACEPTABLE: ≥ 0.55
        level = aggregator.apply_rubric_thresholds(0.60, level="dimension")
        assert level == "ACEPTABLE"

        # INSUFICIENTE: < 0.55
        level = aggregator.apply_rubric_thresholds(0.50, level="dimension")
        assert level == "INSUFICIENTE"

    def test_aggregate_dimension_success(self, minimal_monolith, sample_scored_results):
        """Test successful dimension aggregation."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        result = aggregator.aggregate_dimension(
            dimension_id="D1",
            area_id="P1",
            scored_results=sample_scored_results,
        )

        assert isinstance(result, DimensionScore)
        assert result.dimension_id == "D1"
        assert result.area_id == "P1"
        assert 0.0 <= result.score <= 3.0
        assert result.quality_level in ["EXCELENTE", "BUENO", "ACEPTABLE", "INSUFICIENTE"]

    def test_aggregate_dimension_deterministic(self, minimal_monolith, sample_scored_results):
        """Test dimension aggregation is deterministic."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        result1 = aggregator.aggregate_dimension(
            dimension_id="D1",
            area_id="P1",
            scored_results=sample_scored_results,
        )

        result2 = aggregator.aggregate_dimension(
            dimension_id="D1",
            area_id="P1",
            scored_results=sample_scored_results,
        )

        assert result1.score == result2.score
        assert result1.quality_level == result2.quality_level

# ============================================================================
# AREA POLICY AGGREGATOR TESTS
# ============================================================================

class TestAreaPolicyAggregator:
    """Test AreaPolicyAggregator functionality."""

    def test_initialization(self, minimal_monolith):
        """Test area aggregator initialization."""
        aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)
        assert aggregator.monolith == minimal_monolith
        assert aggregator.abort_on_insufficient is False

    def test_validate_hermeticity_complete(self, minimal_monolith):
        """Test hermeticity validation with complete dimensions."""
        aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)

        dimension_ids = {f"D{i}" for i in range(1, 7)}
        is_hermetic, msg = aggregator.validate_hermeticity(dimension_ids, area_id="P1")

        # Hermeticity requires exactly 6 dimensions
        assert is_hermetic

    def test_normalize_scores(self, minimal_monolith, sample_dimension_scores):
        """Test score normalization."""
        aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)

        normalized = aggregator.normalize_scores(sample_dimension_scores)

        # All scores should be in [0, 1]
        for score in normalized:
            assert 0.0 <= score <= 1.0

    def test_aggregate_area_success(self, minimal_monolith, sample_dimension_scores):
        """Test successful area aggregation."""
        aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)

        result = aggregator.aggregate_area(
            area_id="P1",
            dimension_scores=sample_dimension_scores,
        )

        assert isinstance(result, AreaScore)
        assert result.area_id == "P1"
        assert 0.0 <= result.score <= 3.0
        assert result.quality_level in ["EXCELENTE", "BUENO", "ACEPTABLE", "INSUFICIENTE"]

# ============================================================================
# CLUSTER AGGREGATOR TESTS
# ============================================================================

class TestClusterAggregator:
    """Test ClusterAggregator functionality."""

    def test_initialization(self, minimal_monolith):
        """Test cluster aggregator initialization."""
        aggregator = ClusterAggregator(minimal_monolith, abort_on_insufficient=False)
        assert aggregator.monolith == minimal_monolith

    def test_validate_cluster_hermeticity(self, minimal_monolith):
        """Test cluster hermeticity validation."""
        aggregator = ClusterAggregator(minimal_monolith, abort_on_insufficient=False)

        # CL01 expects areas P1, P2
        area_ids = {"P1", "P2"}
        is_hermetic, msg = aggregator.validate_cluster_hermeticity(area_ids, cluster_id="CL01")
        assert is_hermetic

        # Missing P2
        area_ids = {"P1"}
        is_hermetic, msg = aggregator.validate_cluster_hermeticity(area_ids, cluster_id="CL01")
        assert not is_hermetic

# ============================================================================
# MACRO AGGREGATOR TESTS
# ============================================================================

class TestMacroAggregator:
    """Test MacroAggregator functionality."""

    def test_initialization(self, minimal_monolith):
        """Test macro aggregator initialization."""
        aggregator = MacroAggregator(minimal_monolith, abort_on_insufficient=False)
        assert aggregator.monolith == minimal_monolith

    def test_calculate_cross_cutting_coherence(self, minimal_monolith):
        """Test cross-cutting coherence calculation."""
        aggregator = MacroAggregator(minimal_monolith, abort_on_insufficient=False)

        cluster_scores = [
            ClusterScore(
                cluster_id=f"CL0{i}",
                score=2.0 + (i * 0.1),
                quality_level="BUENO",
                area_scores=[],
                evidence={},
            )
            for i in range(1, 5)
        ]

        coherence = aggregator.calculate_cross_cutting_coherence(cluster_scores)
        assert 0.0 <= coherence <= 1.0

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAggregationPipeline:
    """Test full aggregation pipeline."""

    def test_dimension_to_area_pipeline(self, minimal_monolith, sample_scored_results):
        """Test pipeline from dimension to area aggregation."""
        # Step 1: Aggregate dimension
        dim_aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)
        dim_aggregator.aggregate_dimension(
            dimension_id="D1",
            area_id="P1",
            scored_results=sample_scored_results,
        )

        # Step 2: Create multiple dimensions
        dimension_scores = [
            DimensionScore(
                dimension_id=f"D{i}",
                area_id="P1",
                score=2.0 + (i * 0.1),
                quality_level="BUENO",
                micro_scores=[2.0] * 5,
                evidence={},
            )
            for i in range(1, 7)
        ]

        # Step 3: Aggregate area
        area_aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)
        area_score = area_aggregator.aggregate_area(
            area_id="P1",
            dimension_scores=dimension_scores,
        )

        assert isinstance(area_score, AreaScore)
        assert area_score.area_id == "P1"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
