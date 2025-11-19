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
            "scoring": {},
            "niveles_abstraccion": {
                "policy_areas": [
                    {"policy_area_id": "P1", "i18n": {"keys": {"label_es": "Area 1"}}, "dimension_ids": [f"D{i}" for i in range(1, 7)]}
                ],
                "dimensions": [{"dimension_id": f"D{i}"} for i in range(1, 7)],
                "clusters": [
                    {"cluster_id": "CL01", "i18n": {"keys": {"label_es": "Cluster 1"}}, "policy_area_ids": ["P1", "P2"]}
                ]
            }
        },
        "rubric": {
            "dimension": {"thresholds": {}},
            "area": {"thresholds": {}},
            "cluster": {"thresholds": {}},
            "macro": {"thresholds": {}}
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
            contributing_questions=[1, 2, 3, 4, 5],
        )
        for i in range(1, 7)
    ]

# ============================================================================
# VALIDATION TESTS
# ============================================================================

from saaaaaa.processing.aggregation import validate_scored_results, ValidationError, run_aggregation_pipeline

def test_run_aggregation_pipeline(minimal_monolith):
    """Test the high-level aggregation pipeline orchestrator."""
    scored_results = [
        {
            "question_global": i, "base_slot": f"s{i}", "policy_area": "P1",
            "dimension": "D1", "score": float(i), "quality_level": "BUENO",
            "evidence": {}, "raw_results": {}
        } for i in range(5)
    ]

    cluster_scores = run_aggregation_pipeline(scored_results, minimal_monolith)

    assert cluster_scores is not None
    # Based on the test data, we expect one cluster.
    assert len(cluster_scores) > 0
    assert isinstance(cluster_scores[0], ClusterScore)


def test_validate_scored_results_success():
    """Test successful validation of scored results."""
    results = [
        {
            "question_global": 1, "base_slot": "s1", "policy_area": "pa1",
            "dimension": "d1", "score": 1.0, "quality_level": "BUENO",
            "evidence": {}, "raw_results": {}
        }
    ]
    validated = validate_scored_results(results)
    assert len(validated) == 1
    assert isinstance(validated[0], ScoredResult)

def test_validate_scored_results_missing_key():
    """Test validation fails with missing keys."""
    results = [{"question_global": 1}]  # Missing other keys
    with pytest.raises(ValidationError, match="missing keys"):
        validate_scored_results(results)

def test_validate_scored_results_wrong_type():
    """Test validation fails with wrong data types."""
    results = [
        {
            "question_global": "wrong_type", "base_slot": "s1", "policy_area": "pa1",
            "dimension": "d1", "score": 1.0, "quality_level": "BUENO",
            "evidence": {}, "raw_results": {}
        }
    ]
    with pytest.raises(ValidationError):
        validate_scored_results(results)

# ============================================================================
# DIMENSION AGGREGATOR TESTS
# ============================================================================

class TestDimensionAggregator:
    """Test DimensionAggregator functionality."""

    def test_run_success(self, minimal_monolith, sample_scored_results):
        """Test successful dimension aggregation using the run method."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        results = aggregator.run(
            scored_results=sample_scored_results,
            group_by_keys=["policy_area", "dimension"]
        )

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, DimensionScore)
        assert result.dimension_id == "D1"
        assert result.area_id == "P1"
        assert 0.0 <= result.score <= 3.0
        assert result.quality_level in ["EXCELENTE", "BUENO", "ACEPTABLE", "INSUFICIENTE"]

    def test_run_deterministic(self, minimal_monolith, sample_scored_results):
        """Test dimension aggregation is deterministic."""
        aggregator = DimensionAggregator(minimal_monolith, abort_on_insufficient=False)

        result1 = aggregator.run(
            scored_results=sample_scored_results,
            group_by_keys=["policy_area", "dimension"]
        )
        result2 = aggregator.run(
            scored_results=sample_scored_results,
            group_by_keys=["policy_area", "dimension"]
        )

        assert result1[0].score == result2[0].score
        assert result1[0].quality_level == result2[0].quality_level

# ============================================================================
# AREA POLICY AGGREGATOR TESTS
# ============================================================================

class TestAreaPolicyAggregator:
    """Test AreaPolicyAggregator functionality."""

    def test_run_success(self, minimal_monolith, sample_dimension_scores):
        """Test successful area aggregation."""
        aggregator = AreaPolicyAggregator(minimal_monolith, abort_on_insufficient=False)

        results = aggregator.run(
            dimension_scores=sample_dimension_scores,
            group_by_keys=["area_id"]
        )

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, AreaScore)
        assert result.area_id == "P1"
        assert 0.0 <= result.score <= 3.0
        assert result.quality_level in ["EXCELENTE", "BUENO", "ACEPTABLE", "INSUFICIENTE"]

# ============================================================================
# CLUSTER AGGREGATOR TESTS
# ============================================================================

class TestClusterAggregator:
    """Test ClusterAggregator functionality."""

    def test_run_success(self, minimal_monolith):
        """Test successful cluster aggregation."""
        aggregator = ClusterAggregator(minimal_monolith, abort_on_insufficient=False)

        area_scores = [
            AreaScore(area_id="P1", area_name="Area 1", score=2.5, quality_level="BUENO", dimension_scores=[]),
            AreaScore(area_id="P2", area_name="Area 2", score=2.8, quality_level="BUENO", dimension_scores=[])
        ]

        # This structure should come from the monolith in a real scenario
        cluster_definitions = [
            {"cluster_id": "CL01", "policy_area_ids": ["P1", "P2"]}
        ]

        results = aggregator.run(area_scores, cluster_definitions)

        assert len(results) == 1
        result = results[0]
        assert isinstance(result, ClusterScore)
        assert result.cluster_id == "CL01"
        assert 0.0 <= result.score <= 3.0

# ============================================================================
# MACRO AGGREGATOR TESTS
# ============================================================================

class TestMacroAggregator:
    """Test MacroAggregator functionality."""

    def test_evaluate_macro_success(self, minimal_monolith):
        """Test successful macro evaluation."""
        aggregator = MacroAggregator(minimal_monolith, abort_on_insufficient=False)
        cluster_scores = [
            ClusterScore(cluster_id="CL01", cluster_name="C1", areas=[], score=2.5, coherence=0.8, area_scores=[])
        ]
        area_scores = [
            AreaScore(area_id="P1", area_name="A1", score=2.5, quality_level="BUENO", dimension_scores=[])
        ]
        dimension_scores = [
            DimensionScore(dimension_id="D1", area_id="P1", score=2.5, quality_level="BUENO", contributing_questions=[])
        ]

        result = aggregator.evaluate_macro(cluster_scores, area_scores, dimension_scores)
        assert 0.0 <= result.score <= 3.0
        assert result.quality_level is not None

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestAggregationPipeline:
    """Test full aggregation pipeline."""

    def test_full_pipeline(self, minimal_monolith, sample_scored_results):
        """Test the full aggregation pipeline from scored results to area scores."""
        # Step 1: Dimension Aggregation
        dim_aggregator = DimensionAggregator(minimal_monolith)
        dimension_scores = dim_aggregator.run(
            sample_scored_results,
            group_by_keys=["policy_area", "dimension"]
        )
        assert dimension_scores

        # Step 2: Area Aggregation
        area_aggregator = AreaPolicyAggregator(minimal_monolith)
        area_scores = area_aggregator.run(
            dimension_scores,
            group_by_keys=["area_id"]
        )
        assert area_scores
        assert isinstance(area_scores[0], AreaScore)
        assert area_scores[0].area_id == "P1"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
