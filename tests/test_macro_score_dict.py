"""Test MacroScoreDict typed container in core.py."""
import pytest


# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Macro scoring now part of gold_canario_macro_reporting")

from saaaaaa.core.orchestrator.core import MacroScoreDict
from saaaaaa.processing.aggregation import MacroScore, ClusterScore


def test_macro_score_dict_structure():
    """Test that MacroScoreDict has the expected structure."""
    # Create a sample MacroScore and ClusterScore
    macro_score = MacroScore(
        score=0.75,
        quality_level="ALTO",
        cross_cutting_coherence=0.8,
        systemic_gaps=[],
        strategic_alignment=0.9,
        cluster_scores=[],
        validation_passed=True,
        validation_details={}
    )
    
    cluster_scores = [
        ClusterScore(
            cluster_id="C1",
            cluster_name="Cluster 1",
            areas=["area1"],
            score=0.8,
            coherence=0.85,
            area_scores=[],
            validation_passed=True,
            validation_details={}
        )
    ]
    
    # Create MacroScoreDict
    result: MacroScoreDict = {
        "macro_score": macro_score,
        "macro_score_normalized": 0.75,
        "cluster_scores": cluster_scores
    }
    
    # Check types
    assert isinstance(result["macro_score"], MacroScore)
    assert isinstance(result["macro_score_normalized"], float)
    assert isinstance(result["cluster_scores"], list)
    assert all(isinstance(cs, ClusterScore) for cs in result["cluster_scores"])


def test_macro_score_dict_all_keys_present():
    """Test that MacroScoreDict has all required keys."""
    macro_score = MacroScore(
        score=0.65,
        quality_level="MEDIO",
        cross_cutting_coherence=0.7,
        systemic_gaps=[],
        strategic_alignment=0.8,
        cluster_scores=[],
        validation_passed=True,
        validation_details={}
    )
    
    result: MacroScoreDict = {
        "macro_score": macro_score,
        "macro_score_normalized": 0.65,
        "cluster_scores": []
    }
    
    # Check that all keys are present
    assert "macro_score" in result
    assert "macro_score_normalized" in result
    assert "cluster_scores" in result


def test_macro_score_normalized_is_float():
    """Test that macro_score_normalized is always a float."""
    macro_score = MacroScore(
        score=0.5,
        quality_level="MEDIO",
        cross_cutting_coherence=0.6,
        systemic_gaps=[],
        strategic_alignment=0.7,
        cluster_scores=[],
        validation_passed=True,
        validation_details={}
    )
    
    # Test with float conversion
    result: MacroScoreDict = {
        "macro_score": macro_score,
        "macro_score_normalized": float(macro_score.score),
        "cluster_scores": []
    }
    
    assert isinstance(result["macro_score_normalized"], float)
    assert result["macro_score_normalized"] == 0.5
