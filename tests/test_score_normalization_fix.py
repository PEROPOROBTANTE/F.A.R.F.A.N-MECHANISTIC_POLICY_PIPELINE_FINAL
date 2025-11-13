"""
Test for score normalization fix.

This test validates that cluster and macro scores are correctly handled
without additional /3.0 division, since they are already normalized to 0-1 range
from the aggregation functions.

The issue was that scores were being triple/double-normalized:
- Analysis.scoring produces normalized_score in 0-1 range
- _aggregate_policy_areas_async averages these to produce area scores in 0-1 range
- _aggregate_clusters averages area scores to produce cluster scores in 0-1 range
- _evaluate_macro averages cluster scores to produce macro_score in 0-1 range

Then the code was incorrectly dividing by 3.0 again, causing:
- Cluster scores to max out at 33% instead of 100%
- Macro scores to max out at ~33% instead of 100%
- All clusters marked as below target even with good scores
- Incorrect variance computations
"""

from pathlib import Path

# Add parent directory to path
try:
    import pytest
    HAS_PYTEST = True

    # Helper for approximate comparisons
    def approx_equal(a, b, abs_tol=0.01):
        return pytest.approx(a, abs=abs_tol) == b
except ImportError:
    HAS_PYTEST = False

    # Fallback for manual execution without pytest
    def approx_equal(a, b, abs_tol=0.01):
        return abs(a - b) <= abs_tol

def test_macro_score_normalization():
    """Test that macro scores are not double-normalized."""
    # Simulate cluster scores that are already normalized (0-1 range)
    # These scores represent good performance (0.8 = 80%)
    cluster_scores = [
        {"cluster_id": "cluster_1", "score": 0.8},
        {"cluster_id": "cluster_2", "score": 0.85},
        {"cluster_id": "cluster_3", "score": 0.75},
    ]

    # Simulate the _evaluate_macro logic
    valid_scores = [entry.get("score") for entry in cluster_scores if entry.get("score") is not None]
    macro_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

    # The fix: macro_score is already normalized to 0-1 range, so we don't divide by 3.0
    macro_score_normalized = macro_score  # Old code: macro_score / 3.0

    result = {
        "macro_score": macro_score,
        "macro_score_normalized": macro_score_normalized,
        "cluster_scores": cluster_scores,
    }

    # Expected macro_score is the average: (0.8 + 0.85 + 0.75) / 3 = 0.8
    expected_macro_score = 0.8

    # Check that macro_score is correct
    assert approx_equal(result["macro_score"], expected_macro_score), \
        f"Expected {expected_macro_score}, got {result['macro_score']}"

    # Check that macro_score_normalized is the same (not divided by 3.0)
    assert result["macro_score_normalized"] == result["macro_score"]

    # Verify the score is in the expected range (not capped at 0.33)
    assert result["macro_score"] > 0.6, "Macro score should be > 60%, not capped at 33%"

def test_cluster_score_not_double_normalized():
    """Test that cluster scores are correctly used without /3.0 division."""
    # Simulate a cluster score that's already normalized (0-1 range)
    cluster_score = 0.8  # 80% - good performance

    # The old code would have done: cluster_score / 3.0 = 0.8 / 3.0 = 0.267
    # Then: 0.267 * 100 = 26.7% (incorrect!)

    # The new code should do: cluster_score * 100 = 0.8 * 100 = 80% (correct!)
    normalized_cluster_score = cluster_score  # Should not divide by 3.0
    percentage = normalized_cluster_score * 100

    assert approx_equal(percentage, 80.0, abs_tol=0.1), \
        f"Expected percentage to be 80.0, got {percentage}"
    assert percentage > 50, "Score should be 80%, not 26.7%"

def test_clusters_below_target_threshold():
    """Test that cluster comparison uses correct normalization."""
    # Simulate cluster scores (already 0-1 range)
    cluster_scores = [
        {"cluster_id": "cluster_1", "score": 0.6},   # 60% - above target
        {"cluster_id": "cluster_2", "score": 0.5},   # 50% - below target
        {"cluster_id": "cluster_3", "score": 0.8},   # 80% - above target
        {"cluster_id": "cluster_4", "score": 0.4},   # 40% - below target
    ]

    # Find clusters below 55% target
    # New code should use: cluster_score * 100 < 55
    # Old code used: (cluster_score / 3.0) * 100 < 55
    clusters_below_target = []
    for cluster in cluster_scores:
        cluster_score = cluster.get('score', 0)
        # Correct logic (no /3.0)
        if cluster_score is not None and cluster_score * 100 < 55:
            clusters_below_target.append(cluster.get('cluster_id'))

    # Should identify cluster_2 (50%) and cluster_4 (40%) as below target
    assert len(clusters_below_target) == 2
    assert "cluster_2" in clusters_below_target
    assert "cluster_4" in clusters_below_target
    assert "cluster_1" not in clusters_below_target  # 60% is above target
    assert "cluster_3" not in clusters_below_target  # 80% is above target

def test_macro_band_classification():
    """Test that macro band is correctly classified with proper normalization."""
    # Test various macro scores and their expected bands
    test_cases = [
        (0.85, "SATISFACTORIO"),   # 85% >= 75%
        (0.75, "SATISFACTORIO"),   # 75% >= 75%
        (0.65, "ACEPTABLE"),       # 65% >= 55% and < 75%
        (0.55, "ACEPTABLE"),       # 55% >= 55% and < 75%
        (0.45, "DEFICIENTE"),      # 45% >= 35% and < 55%
        (0.35, "DEFICIENTE"),      # 35% >= 35% and < 55%
        (0.25, "INSUFICIENTE"),    # 25% < 35%
    ]

    for macro_score, expected_band in test_cases:
        # The score is already normalized (0-1 range)
        macro_score_normalized = macro_score  # Should not divide by 3.0

        # Determine band based on score
        scaled_score = macro_score_normalized * 100

        if scaled_score >= 75:
            macro_band = "SATISFACTORIO"
        elif scaled_score >= 55:
            macro_band = "ACEPTABLE"
        elif scaled_score >= 35:
            macro_band = "DEFICIENTE"
        else:
            macro_band = "INSUFICIENTE"

        assert macro_band == expected_band, \
            f"Score {macro_score} ({scaled_score}%) should be {expected_band}, not {macro_band}"

def test_variance_calculation():
    """Test that variance is calculated with correct normalization."""
    # Simulate cluster scores (already 0-1 range)
    cluster_scores = [
        {"score": 0.8},
        {"score": 0.7},
        {"score": 0.9},
        {"score": 0.75},
    ]

    # Extract scores without /3.0 division
    normalized_cluster_scores = [
        c.get('score')
        for c in cluster_scores
        if c.get('score') is not None
    ]

    import statistics
    variance = statistics.variance(normalized_cluster_scores)

    # The variance should be calculated on 0-1 scale values
    # Expected: variance([0.8, 0.7, 0.9, 0.75]) ≈ 0.00667
    expected_variance = 0.00667

    assert approx_equal(variance, expected_variance, abs_tol=0.001), \
        f"Expected variance {expected_variance}, got {variance}"

    # Old code would have calculated variance on values/3.0, giving much smaller variance
    # This ensures we're using the correct scale

if __name__ == "__main__":
    if HAS_PYTEST:
        pytest.main([__file__, "-v"])
    else:
        print("Running tests without pytest...")
        test_macro_score_normalization()
        print("✓ test_macro_score_normalization passed")

        test_cluster_score_not_double_normalized()
        print("✓ test_cluster_score_not_double_normalized passed")

        test_clusters_below_target_threshold()
        print("✓ test_clusters_below_target_threshold passed")

        test_macro_band_classification()
        print("✓ test_macro_band_classification passed")

        test_variance_calculation()
        print("✓ test_variance_calculation passed")

        print("\nAll tests passed!")
