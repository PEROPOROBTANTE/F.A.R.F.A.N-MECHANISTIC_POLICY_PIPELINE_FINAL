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

import copy
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


def _build_weighted_monolith() -> dict[str, Any]:
    """Construct a monolith payload with explicit aggregation weights."""
    policy_areas = [
        {
            "policy_area_id": "PA01",
            "i18n": {"keys": {"label_es": "Area 1"}},
            "dimension_ids": ["D1", "D2"],
        },
        {
            "policy_area_id": "PA02",
            "i18n": {"keys": {"label_es": "Area 2"}},
            "dimension_ids": ["D1", "D2"],
        },
    ]

    clusters = [
        {
            "cluster_id": "CL01",
            "i18n": {"keys": {"label_es": "Cluster 1"}},
            "policy_area_ids": ["PA01", "PA02"],
        }
    ]

    micro_questions = []
    dimension_questions = {"D1": ["Q001", "Q002"], "D2": ["Q003", "Q004"]}
    for area_id in ("PA01", "PA02"):
        for dimension_id, question_ids in dimension_questions.items():
            for qid in question_ids:
                micro_questions.append(
                    {
                        "question_id": qid,
                        "base_slot": f"{dimension_id}-{qid}",
                        "dimension_id": dimension_id,
                        "policy_area_id": area_id,
                    }
                )

    aggregation = {
        "dimension_question_weights": {
            "D1": {"Q001": 0.8, "Q002": 0.2},
            "D2": {"Q003": 0.4, "Q004": 0.6},
        },
        "policy_area_dimension_weights": {
            "PA01": {"D1": 0.75, "D2": 0.25},
            "PA02": {"D1": 0.25, "D2": 0.75},
        },
        "cluster_policy_area_weights": {
            "CL01": {"PA01": 0.2, "PA02": 0.8},
        },
        "macro_cluster_weights": {"CL01": 1.0},
    }

    return {
        "blocks": {
            "scoring": {},
            "micro_questions": micro_questions,
            "niveles_abstraccion": {
                "policy_areas": policy_areas,
                "dimensions": [{"dimension_id": "D1"}, {"dimension_id": "D2"}],
                "clusters": clusters,
            },
        },
        "aggregation": aggregation,
    }

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
            ClusterScore(
                cluster_id="CL01",
                cluster_name="C1",
                areas=[],
                score=2.5,
                coherence=0.8,
                variance=0.0,
                weakest_area=None,
                area_scores=[],
            )
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


def test_dimension_aggregation_uses_config_weights():
    """Dimension aggregation should respect configured question weights."""
    monolith = _build_weighted_monolith()
    aggregator = DimensionAggregator(monolith, abort_on_insufficient=False)
    results = [
        ScoredResult(
            question_global=1,
            base_slot="D1-Q001",
            policy_area="PA01",
            dimension="D1",
            score=1.0,
            quality_level="BUENO",
            evidence={},
            raw_results={},
        ),
        ScoredResult(
            question_global=2,
            base_slot="D1-Q002",
            policy_area="PA01",
            dimension="D1",
            score=3.0,
            quality_level="BUENO",
            evidence={},
            raw_results={},
        ),
    ]
    score = aggregator.aggregate_dimension(results, {"policy_area": "PA01", "dimension": "D1"})
    assert score.score == pytest.approx(1.4)


def test_area_aggregation_uses_config_weights():
    """Area aggregation should use the policy-area dimension weights."""
    monolith = _build_weighted_monolith()
    aggregator = AreaPolicyAggregator(monolith, abort_on_insufficient=False)
    dimension_scores = [
        DimensionScore(
            dimension_id="D1",
            area_id="PA01",
            score=1.0,
            quality_level="BUENO",
            contributing_questions=[],
        ),
        DimensionScore(
            dimension_id="D2",
            area_id="PA01",
            score=3.0,
            quality_level="BUENO",
            contributing_questions=[],
        ),
    ]
    area_score = aggregator.aggregate_area(dimension_scores, {"area_id": "PA01"})
    assert area_score.score == pytest.approx(1.5)


def test_cluster_aggregation_uses_config_weights():
    """Cluster aggregation should apply configured policy-area weights."""
    monolith = _build_weighted_monolith()
    aggregator = ClusterAggregator(monolith, abort_on_insufficient=False)
    area_scores = [
        AreaScore(
            area_id="PA01",
            area_name="Area 1",
            score=1.0,
            quality_level="BUENO",
            dimension_scores=[],
        ),
        AreaScore(
            area_id="PA02",
            area_name="Area 2",
            score=3.0,
            quality_level="BUENO",
            dimension_scores=[],
        ),
    ]
    cluster_score = aggregator.aggregate_cluster(area_scores, {"cluster_id": "CL01"})
    # Weighted score = 2.6; std dev = 1.0 → penalty factor 0.9 → 2.34
    assert cluster_score.score == pytest.approx(2.34, rel=1e-3)


def test_macro_aggregation_uses_macro_cluster_weights():
    """Macro aggregator should respect macro-level cluster weights."""
    monolith = copy.deepcopy(_build_weighted_monolith())
    monolith["blocks"]["niveles_abstraccion"]["clusters"] = [
        {
            "cluster_id": "CL01",
            "i18n": {"keys": {"label_es": "Cluster 1"}},
            "policy_area_ids": ["PA01"],
        },
        {
            "cluster_id": "CL02",
            "i18n": {"keys": {"label_es": "Cluster 2"}},
            "policy_area_ids": ["PA02"],
        },
    ]
    monolith["aggregation"]["cluster_policy_area_weights"] = {
        "CL01": {"PA01": 1.0},
        "CL02": {"PA02": 1.0},
    }
    monolith["aggregation"]["macro_cluster_weights"] = {"CL01": 0.2, "CL02": 0.8}

    aggregator = MacroAggregator(monolith, abort_on_insufficient=False)
    cluster_scores = [
        ClusterScore(
            cluster_id="CL01",
            cluster_name="Cluster 1",
            areas=["PA01"],
            score=1.0,
            coherence=1.0,
            variance=0.0,
            weakest_area="PA01",
            area_scores=[],
        ),
        ClusterScore(
            cluster_id="CL02",
            cluster_name="Cluster 2",
            areas=["PA02"],
            score=3.0,
            coherence=1.0,
            variance=0.0,
            weakest_area="PA02",
            area_scores=[],
        ),
    ]
    area_scores = [
        AreaScore(
            area_id="PA01",
            area_name="Area 1",
            score=1.0,
            quality_level="BUENO",
            dimension_scores=[],
        ),
        AreaScore(
            area_id="PA02",
            area_name="Area 2",
            score=3.0,
            quality_level="BUENO",
            dimension_scores=[],
        ),
    ]
    dimension_scores = [
        DimensionScore(
            dimension_id="D1",
            area_id="PA01",
            score=1.0,
            quality_level="BUENO",
            contributing_questions=[],
        ),
        DimensionScore(
            dimension_id="D1",
            area_id="PA02",
            score=3.0,
            quality_level="BUENO",
            contributing_questions=[],
        ),
    ]

    macro = aggregator.evaluate_macro(cluster_scores, area_scores, dimension_scores)
    assert macro.score == pytest.approx(2.6)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
