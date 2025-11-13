"""
Tests for scoring module.

Tests all TYPE_A through TYPE_F modalities with various evidence structures.
"""

import sys
from dataclasses import replace
from pathlib import Path

import pytest

# Add parent directory to path
import saaaaaa.scoring.scoring as scoring_module
from saaaaaa.scoring.scoring import (
    EvidenceStructureError,
    ModalityValidationError,
    QualityLevel,
    ScoredResult,
    ScoringError,
    ScoringModality,
    ScoringValidator,
    apply_rounding,
    apply_scoring,
    determine_quality_level,
    score_type_a,
    score_type_b,
    score_type_c,
    score_type_d,
    score_type_e,
    score_type_f,
)
from saaaaaa.processing.aggregation import DimensionAggregator

# Alias for compatibility with test
AggregationScoredResult = ScoredResult

def test_scored_result_hash():
    """Test that evidence hash is computed correctly."""
    evidence1 = {"elements": [1, 2, 3], "confidence": 0.9}
    evidence2 = {"confidence": 0.9, "elements": [1, 2, 3]}  # Different order
    evidence3 = {"elements": [1, 2, 3], "confidence": 0.8}  # Different value

    hash1 = ScoredResult.compute_evidence_hash(evidence1)
    hash2 = ScoredResult.compute_evidence_hash(evidence2)
    hash3 = ScoredResult.compute_evidence_hash(evidence3)

    # Same content, different key order should produce same hash
    assert hash1 == hash2, "Hash should be order-independent"

    # Different content should produce different hash
    assert hash1 != hash3, "Different evidence should produce different hash"

    # Hash should be SHA-256 (64 hex characters)
    assert len(hash1) == 64, "Hash should be 64 characters"

    print("✓ test_scored_result_hash passed")

def test_modality_validation_type_a():
    """Test TYPE_A evidence validation."""
    modality = ScoringModality.TYPE_A

    # Valid evidence
    valid_evidence = {
        "elements": [1, 2, 3, 4],
        "confidence": 0.85,
    }
    ScoringValidator.validate(valid_evidence, modality)
    print("✓ TYPE_A valid evidence accepted")

    # Missing required key
    try:
        invalid_evidence = {"elements": [1, 2, 3]}
        ScoringValidator.validate(invalid_evidence, modality)
        raise AssertionError("Should have raised EvidenceStructureError")
    except EvidenceStructureError as e:
        assert "confidence" in str(e).lower()
        print("✓ TYPE_A missing key detected")

    # Invalid elements type
    try:
        invalid_evidence = {"elements": "not a list", "confidence": 0.85}
        ScoringValidator.validate(invalid_evidence, modality)
        raise AssertionError("Should have raised ModalityValidationError")
    except ModalityValidationError as e:
        assert "list" in str(e).lower()
        print("✓ TYPE_A invalid elements type detected")

def test_scoring_type_a():
    """Test TYPE_A scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_A)
    config.score_range[1]

    # Full score with high confidence
    evidence = {"elements": [1, 2, 3, 4], "confidence": 1.0}
    score, metadata = score_type_a(evidence, config)
    assert score == pytest.approx(3.0), f"Expected 3.0, got {score}"
    assert metadata["element_count"] == 4
    assert metadata["confidence"] == 1.0
    print(f"✓ TYPE_A full score: {score}")

    # Partial score with lower confidence
    evidence = {"elements": [1, 2], "confidence": 0.5}
    score, metadata = score_type_a(evidence, config)
    expected = (2 / 4) * 3.0 * 0.5  # 0.75
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_A partial score: {score}")

    # Zero score
    evidence = {"elements": [], "confidence": 0.0}
    score, metadata = score_type_a(evidence, config)
    assert score == 0.0, f"Expected 0.0, got {score}"
    print(f"✓ TYPE_A zero score: {score}")

def test_scoring_type_b():
    """Test TYPE_B scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_B)

    # Full score
    evidence = {"elements": [1, 2, 3], "completeness": 1.0}
    score, metadata = score_type_b(evidence, config)
    assert score == 3.0, f"Expected 3.0, got {score}"
    print(f"✓ TYPE_B full score: {score}")

    # Partial score
    evidence = {"elements": [1, 2], "completeness": 0.75}
    score, metadata = score_type_b(evidence, config)
    expected = 2.0 * 0.75  # 1.5
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_B partial score: {score}")

def test_scoring_type_c():
    """Test TYPE_C scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_C)

    # Full score
    evidence = {"elements": [1, 2], "coherence_score": 1.0}
    score, metadata = score_type_c(evidence, config)
    assert score == 3.0, f"Expected 3.0, got {score}"
    print(f"✓ TYPE_C full score: {score}")

    # Partial score
    evidence = {"elements": [1], "coherence_score": 0.6}
    score, metadata = score_type_c(evidence, config)
    expected = (1/2) * 3.0 * 0.6  # 0.9
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_C partial score: {score}")

def test_scoring_type_d():
    """Test TYPE_D scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_D)

    # Full score
    evidence = {"elements": [1, 2, 3], "pattern_matches": 3}
    score, metadata = score_type_d(evidence, config)
    assert score == 3.0, f"Expected 3.0, got {score}"
    print(f"✓ TYPE_D full score: {score}")

    # Partial score
    evidence = {"elements": [1, 2], "pattern_matches": 2}
    score, metadata = score_type_d(evidence, config)
    expected = (2/3) * 3.0  # 2.0
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_D partial score: {score}")

def test_scoring_type_e():
    """Test TYPE_E scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_E)

    # Full score with boolean
    evidence = {"elements": [1, 2], "traceability": True}
    score, metadata = score_type_e(evidence, config)
    assert score == 3.0, f"Expected 3.0, got {score}"
    print(f"✓ TYPE_E full score (boolean): {score}")

    # Partial score with numeric
    evidence = {"elements": [1, 2], "traceability": 0.5}
    score, metadata = score_type_e(evidence, config)
    expected = 3.0 * 0.5  # 1.5
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_E partial score (numeric): {score}")

    # Zero score
    evidence = {"elements": [], "traceability": True}
    score, metadata = score_type_e(evidence, config)
    assert score == 0.0, f"Expected 0.0, got {score}"
    print(f"✓ TYPE_E zero score (no elements): {score}")

def test_scoring_type_f():
    """Test TYPE_F scoring."""
    config = ScoringValidator.get_config(ScoringModality.TYPE_F)

    # Full score
    evidence = {"elements": [1, 2], "plausibility": 1.0}
    score, metadata = score_type_f(evidence, config)
    assert score == 3.0, f"Expected 3.0, got {score}"
    print(f"✓ TYPE_F full score: {score}")

    # Partial score
    evidence = {"elements": [1], "plausibility": 0.7}
    score, metadata = score_type_f(evidence, config)
    expected = 3.0 * 0.7  # 2.1
    assert abs(score - expected) < 0.01, f"Expected {expected}, got {score}"
    print(f"✓ TYPE_F partial score: {score}")

def test_quality_level_determination():
    """Test quality level determination."""

    # EXCELENTE
    level = determine_quality_level(0.90)
    assert level == QualityLevel.EXCELENTE
    print(f"✓ Quality level 0.90 -> {level.value}")

    # BUENO
    level = determine_quality_level(0.75)
    assert level == QualityLevel.BUENO
    print(f"✓ Quality level 0.75 -> {level.value}")

    # ACEPTABLE
    level = determine_quality_level(0.60)
    assert level == QualityLevel.ACEPTABLE
    print(f"✓ Quality level 0.60 -> {level.value}")

    # INSUFICIENTE
    level = determine_quality_level(0.40)
    assert level == QualityLevel.INSUFICIENTE
    print(f"✓ Quality level 0.40 -> {level.value}")

def test_quality_level_clamps_score():
    """Scores outside [0, 1] should be clamped when determining quality."""

    assert determine_quality_level(1.5) == QualityLevel.EXCELENTE
    assert determine_quality_level(-0.2) == QualityLevel.INSUFICIENTE

def test_quality_level_custom_thresholds():
    """Custom thresholds should be validated and applied."""

    thresholds = {"EXCELENTE": 0.9, "BUENO": 0.75, "ACEPTABLE": 0.6}
    level = determine_quality_level(0.88, thresholds)
    assert level == QualityLevel.BUENO

def test_quality_level_invalid_thresholds():
    """Invalid custom thresholds should raise an error."""

    with pytest.raises(ValueError):
        determine_quality_level(0.8, {"EXCELENTE": 0.7, "BUENO": 0.8, "ACEPTABLE": 0.5})

    with pytest.raises(ValueError):
        determine_quality_level(0.8, {"EXCELENTE": 1.2, "BUENO": 0.7, "ACEPTABLE": 0.5})

    with pytest.raises(ValueError):
        determine_quality_level(0.8, {"EXCELENTE": 0.9, "BUENO": 0.7})

def test_apply_scoring_type_a():
    """Test full scoring workflow for TYPE_A."""
    evidence = {
        "elements": [1, 2, 3, 4],
        "confidence": 0.9,
    }

    result = apply_scoring(
        question_global=1,
        base_slot="PA01-DIM01-Q001",
        policy_area="PA01",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_A",
    )

    assert result.question_global == 1
    assert result.base_slot == "PA01-DIM01-Q001"
    assert result.policy_area == "PA01"
    assert result.dimension == "DIM01"
    assert result.modality == "TYPE_A"
    assert 0 <= result.score <= 3.0
    assert 0 <= result.normalized_score <= 1.0
    assert result.quality_level in ["EXCELENTE", "BUENO", "ACEPTABLE", "INSUFICIENTE"]
    assert result.evidence_hash == ScoredResult.compute_evidence_hash(evidence)

    print(f"✓ Full scoring workflow TYPE_A: score={result.score:.2f}, quality={result.quality_level}")

def test_type_a_not_truncated():
    """TYPE_A scores should reach the new 3.0 ceiling without truncation."""
    evidence = {"elements": [1, 2, 3, 4], "confidence": 1.0}

    result = apply_scoring(
        question_global=1,
        base_slot="PA01-DIM01-Q001",
        policy_area="PA01",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_A",
    )

    assert result.score == pytest.approx(3.0)
    assert result.normalized_score == pytest.approx(1.0)

def test_apply_scoring_invalid_modality():
    """Test that invalid modality raises error."""
    evidence = {"elements": [1, 2, 3], "confidence": 0.9}

    try:
        apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_Z",  # Invalid
        )
        raise AssertionError("Should have raised ModalityValidationError")
    except ModalityValidationError as e:
        assert "TYPE_Z" in str(e)
        print("✓ Invalid modality detected")

def test_apply_scoring_missing_evidence():
    """Test that missing evidence raises error."""
    evidence = {"elements": [1, 2, 3]}  # Missing confidence

    try:
        apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_A",
        )
        raise AssertionError("Should have raised EvidenceStructureError")
    except EvidenceStructureError as e:
        assert "confidence" in str(e).lower()
        print("✓ Missing evidence detected")

def test_reproducibility():
    """Test that same evidence produces same result."""
    evidence = {
        "elements": [1, 2, 3, 4],
        "confidence": 0.85,
    }

    result1 = apply_scoring(
        question_global=1,
        base_slot="PA01-DIM01-Q001",
        policy_area="PA01",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_A",
    )

    result2 = apply_scoring(
        question_global=1,
        base_slot="PA01-DIM01-Q001",
        policy_area="PA01",
        dimension="DIM01",
        evidence=evidence,
        modality="TYPE_A",
    )

    # Scores should be identical
    assert result1.score == result2.score
    assert result1.normalized_score == result2.normalized_score
    assert result1.quality_level == result2.quality_level
    assert result1.evidence_hash == result2.evidence_hash

    print("✓ Scoring is reproducible")

def test_all_modalities():
    """Test that all modalities can be scored."""
    test_cases = [
        ("TYPE_A", {"elements": [1, 2, 3, 4], "confidence": 0.9}),
        ("TYPE_B", {"elements": [1, 2, 3], "completeness": 0.8}),
        ("TYPE_C", {"elements": [1, 2], "coherence_score": 0.75}),
        ("TYPE_D", {"elements": [1, 2, 3], "pattern_matches": 2}),
        ("TYPE_E", {"elements": [1, 2], "traceability": True}),
        ("TYPE_F", {"elements": [1, 2], "plausibility": 0.85}),
    ]

    for modality, evidence in test_cases:
        result = apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality=modality,
        )
        print(f"✓ {modality}: score={result.score:.2f}, quality={result.quality_level}")

def test_apply_scoring_rejects_invalid_score_range():
    """Scoring should fail fast when modality score ranges are degenerate."""
    mp = pytest.MonkeyPatch()
    try:
        original_config = ScoringValidator.get_config(ScoringModality.TYPE_A)
        invalid_config = replace(original_config, score_range=(1.0, 1.0))
        mp.setitem(
            ScoringValidator.MODALITY_CONFIGS,
            ScoringModality.TYPE_A,
            invalid_config,
        )

        evidence = {"elements": [1, 2, 3, 4], "confidence": 0.9}

        with pytest.raises(ScoringError):
            apply_scoring(
                question_global=1,
                base_slot="PA01-DIM01-Q001",
                policy_area="PA01",
                dimension="DIM01",
                evidence=evidence,
                modality="TYPE_A",
            )
    finally:
        mp.undo()

def test_apply_scoring_clamps_out_of_range_score():
    """Scores returned outside the configured range are clamped."""

    def inflated_score(_, config):
        raw = config.score_range[1] * 1.5
        return raw, {"raw_score": raw}

    mp = pytest.MonkeyPatch()
    try:
        mp.setitem(
            scoring_module.SCORING_FUNCTIONS,
            ScoringModality.TYPE_A,
            inflated_score,
        )

        evidence = {"elements": [1, 2, 3, 4], "confidence": 0.9}
        result = apply_scoring(
            question_global=1,
            base_slot="PA01-DIM01-Q001",
            policy_area="PA01",
            dimension="DIM01",
            evidence=evidence,
            modality="TYPE_A",
        )

        assert result.score == pytest.approx(3.0)
        assert 0.0 <= result.normalized_score <= 1.0
        assert result.metadata["score_clamped"] is True
    finally:
        mp.undo()

def test_apply_rounding_modes():
    """Rounding helper should respect all supported modes."""

    assert apply_rounding(1.235, mode="half_up", precision=2) == pytest.approx(1.24)
    assert apply_rounding(1.245, mode="bankers", precision=2) == pytest.approx(1.24)
    assert apply_rounding(1.239, mode="truncate", precision=2) == pytest.approx(1.23)

    with pytest.raises(ValueError):
        apply_rounding(1.23, mode="unknown", precision=2)

    with pytest.raises(ValueError):
        apply_rounding(1.23, mode="half_up", precision=-1)

def run_all_tests():
    """Run all tests."""
    print("\n=== Running Scoring Module Tests ===\n")

    tests = [
        test_scored_result_hash,
        test_modality_validation_type_a,
        test_scoring_type_a,
        test_scoring_type_b,
        test_scoring_type_c,
        test_scoring_type_d,
        test_scoring_type_e,
        test_scoring_type_f,
        test_quality_level_determination,
        test_apply_scoring_type_a,
        test_apply_scoring_invalid_modality,
        test_apply_scoring_missing_evidence,
        test_reproducibility,
        test_all_modalities,
    ]

    failed = 0
    for test in tests:
        try:
            print(f"\nRunning {test.__name__}...")
            test()
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n=== Test Results ===")
    print(f"Total: {len(tests)}")
    print(f"Passed: {len(tests) - failed}")
    print(f"Failed: {failed}")

    return failed == 0

if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)

def test_dimension_aggregation_preserves_precision():
    """Golden regression: no score truncation between scoring and aggregation."""

    monolith = {
        "blocks": {
            "scoring": {},
            "niveles_abstraccion": {},
        }
    }
    aggregator = DimensionAggregator(monolith, abort_on_insufficient=False)

    precise_scores = [
        2.987654321,
        2.987654322,
        2.987654323,
        2.987654324,
        2.987654325,
    ]

    scored_results = [
        AggregationScoredResult(
            question_global=index + 1,
            base_slot=f"Q{index + 1:03d}",
            policy_area="PA01",
            dimension="DIM01",
            score=value,
            quality_level="EXCELENTE",
            evidence={},
            raw_results={},
        )
        for index, value in enumerate(precise_scores)
    ]

    aggregated = aggregator.aggregate_dimension("DIM01", "PA01", scored_results)
    expected_average = sum(precise_scores) / len(precise_scores)

    assert aggregated.score == pytest.approx(expected_average, abs=1e-12)
    assert aggregated.quality_level == "EXCELENTE"
