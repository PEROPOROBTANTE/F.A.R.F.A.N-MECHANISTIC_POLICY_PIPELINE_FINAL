#!/usr/bin/env python3
"""
Validate scoring parity across modalities.

This script ensures that:
1. Normalization formulas are correct for each modality
2. Quality thresholds are identical across all modalities
3. Boundary conditions produce correct quality levels
4. No modality has an unfair advantage at quality boundaries

Usage:
    python tools/validation/validate_scoring_parity.py
    python tools/validation/validate_scoring_parity.py --verbose
"""

import sys

# Quality thresholds (must be identical across all modalities)
QUALITY_THRESHOLDS = {
    "EXCELENTE": 0.85,
    "BUENO": 0.70,
    "ACEPTABLE": 0.55,
    "INSUFICIENTE": 0.00
}

# Modality score ranges
MODALITY_RANGES = {
    "TYPE_A": (0, 4),
    "TYPE_B": (0, 3),
    "TYPE_C": (0, 3),
    "TYPE_D": (0, 3),
    "TYPE_E": (0, 3),
    "TYPE_F": (0, 3),
}

def normalize_score(raw_score: float, modality: str) -> float:
    """Normalize a raw score to [0, 1] range based on modality."""
    min_score, max_score = MODALITY_RANGES[modality]
    if raw_score < min_score or raw_score > max_score:
        raise ValueError(f"Score {raw_score} out of range for {modality}: [{min_score}, {max_score}]")
    return (raw_score - min_score) / (max_score - min_score)

def determine_quality_level(normalized_score: float) -> str:
    """Determine quality level from normalized score."""
    # Use small epsilon for floating point comparison
    epsilon = 1e-9
    if normalized_score >= QUALITY_THRESHOLDS["EXCELENTE"] - epsilon:
        return "EXCELENTE"
    elif normalized_score >= QUALITY_THRESHOLDS["BUENO"] - epsilon:
        return "BUENO"
    elif normalized_score >= QUALITY_THRESHOLDS["ACEPTABLE"] - epsilon:
        return "ACEPTABLE"
    else:
        return "INSUFICIENTE"

def test_normalization_formulas() -> bool:
    """Test that normalization formulas are correct."""
    print("Testing normalization formulas...")

    test_cases = [
        ("TYPE_A", 0, 0.0),
        ("TYPE_A", 2, 0.5),
        ("TYPE_A", 4, 1.0),
        ("TYPE_B", 0, 0.0),
        ("TYPE_B", 1.5, 0.5),
        ("TYPE_B", 3, 1.0),
        ("TYPE_C", 0, 0.0),
        ("TYPE_C", 1.5, 0.5),
        ("TYPE_C", 3, 1.0),
    ]

    passed = 0
    failed = 0

    for modality, raw, expected in test_cases:
        actual = normalize_score(raw, modality)
        if abs(actual - expected) < 0.001:
            passed += 1
            if "--verbose" in sys.argv:
                print(f"  ✓ {modality}: {raw} → {actual:.3f} (expected {expected:.3f})")
        else:
            failed += 1
            print(f"  ✗ {modality}: {raw} → {actual:.3f} (expected {expected:.3f})")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0

def test_parity_at_thresholds() -> bool:
    """Test that all modalities produce the same quality level at threshold scores."""
    print("\nTesting parity at quality thresholds...")

    # Calculate equivalent raw scores for each threshold
    test_cases = []
    for quality, threshold in QUALITY_THRESHOLDS.items():
        if quality == "INSUFICIENTE":
            continue  # Skip lower bound

        for modality, (min_score, max_score) in MODALITY_RANGES.items():
            raw_score = min_score + threshold * (max_score - min_score)
            test_cases.append((modality, raw_score, quality))

    passed = 0
    failed = 0

    for modality, raw_score, expected_quality in test_cases:
        normalized = normalize_score(raw_score, modality)
        actual_quality = determine_quality_level(normalized)

        if actual_quality == expected_quality:
            passed += 1
            if "--verbose" in sys.argv:
                print(f"  ✓ {modality} at {raw_score:.2f} → {actual_quality}")
        else:
            failed += 1
            print(f"  ✗ {modality} at {raw_score:.2f} → {actual_quality} (expected {expected_quality})")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0

def test_boundary_conditions() -> bool:
    """Test boundary conditions (just above/below thresholds)."""
    print("\nTesting boundary conditions...")

    # Test scores just below and just above EXCELENTE threshold

    test_cases = [
        # Just below EXCELENTE (should be BUENO)
        ("TYPE_A", 3.396, "BUENO"),  # 3.396/4 = 0.849
        ("TYPE_B", 2.547, "BUENO"),  # 2.547/3 = 0.849

        # Just at EXCELENTE threshold
        ("TYPE_A", 3.4, "EXCELENTE"),  # 3.4/4 = 0.85
        ("TYPE_B", 2.55, "EXCELENTE"),  # 2.55/3 = 0.85

        # Just above EXCELENTE
        ("TYPE_A", 3.404, "EXCELENTE"),  # 3.404/4 = 0.851
        ("TYPE_B", 2.553, "EXCELENTE"),  # 2.553/3 = 0.851
    ]

    passed = 0
    failed = 0

    for modality, raw_score, expected_quality in test_cases:
        normalized = normalize_score(raw_score, modality)
        actual_quality = determine_quality_level(normalized)

        if actual_quality == expected_quality:
            passed += 1
            if "--verbose" in sys.argv:
                print(f"  ✓ {modality}: {raw_score:.3f} (norm={normalized:.4f}) → {actual_quality}")
        else:
            failed += 1
            print(f"  ✗ {modality}: {raw_score:.3f} (norm={normalized:.4f}) → {actual_quality} (expected {expected_quality})")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0

def test_no_unfair_advantage() -> bool:
    """Test that no modality has an unfair advantage at boundaries."""
    print("\nTesting for unfair advantages...")

    # For each quality threshold, calculate the "difficulty" (raw score needed)
    # relative to the maximum possible score
    difficulties = {}

    for quality, threshold in QUALITY_THRESHOLDS.items():
        if quality == "INSUFICIENTE":
            continue

        difficulties[quality] = {}
        for modality, (min_score, max_score) in MODALITY_RANGES.items():
            raw_needed = min_score + threshold * (max_score - min_score)
            relative_difficulty = raw_needed / max_score
            difficulties[quality][modality] = relative_difficulty

    passed = 0
    failed = 0

    for quality, modality_difficulties in difficulties.items():
        # All modalities should have the same relative difficulty
        values = list(modality_difficulties.values())
        max_diff = max(values) - min(values)

        if max_diff < 0.001:  # Allow 0.1% variance
            passed += 1
            if "--verbose" in sys.argv:
                print(f"  ✓ {quality}: all modalities have equal difficulty (max diff: {max_diff:.6f})")
        else:
            failed += 1
            print(f"  ✗ {quality}: modalities have unequal difficulty (max diff: {max_diff:.6f})")
            for modality, diff in modality_difficulties.items():
                print(f"      {modality}: {diff:.6f}")

    print(f"  Passed: {passed}/{passed + failed}")
    return failed == 0

def main() -> int:
    """Run all parity validation tests."""
    print("=" * 60)
    print("Scoring Parity Validation")
    print("=" * 60)

    all_passed = True

    # Run all tests
    all_passed &= test_normalization_formulas()
    all_passed &= test_parity_at_thresholds()
    all_passed &= test_boundary_conditions()
    all_passed &= test_no_unfair_advantage()

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All parity validation tests PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ Some parity validation tests FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
