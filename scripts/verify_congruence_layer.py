"""
Verify Congruence Layer is data-driven.

Tests:
1. Different ensembles produce different scores
2. Perfect ensemble scores high (near 1.0)
3. Incompatible ensemble scores low (near 0.0)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.calibration.congruence_layer import CongruenceLayerEvaluator
import json

def test_congruence_differentiation():
    """Test that different ensembles produce different scores."""

    print("=" * 60)
    print("CONGRUENCE LAYER VERIFICATION")
    print("=" * 60)

    # Load method registry
    registry_path = Path("data/method_registry.json")
    if not registry_path.exists():
        print("❌ FAIL: method_registry.json not found")
        return False

    with open(registry_path) as f:
        registry_data = json.load(f)

    methods = registry_data["methods"]

    # Create evaluator
    evaluator = CongruenceLayerEvaluator(method_registry=methods)

    # Test Case 1: Perfect ensemble (identical ranges, high overlap)
    perfect_methods = ["pattern_extractor_v2", "coherence_validator"]
    perfect_score = evaluator.evaluate(
        method_ids=perfect_methods,
        subgraph_id="test_perfect",
        fusion_rule="weighted_average",
        provided_inputs=["extracted_text", "question_id", "reference_corpus"]
    )

    print(f"\n1. Perfect ensemble: {perfect_methods}")
    print(f"   Score: {perfect_score:.3f}")

    # Test Case 2: Partial ensemble (same range, some overlap)
    partial_methods = ["pattern_extractor_v2", "structural_scorer"]
    partial_score = evaluator.evaluate(
        method_ids=partial_methods,
        subgraph_id="test_partial",
        fusion_rule="weighted_average",
        provided_inputs=["extracted_text", "question_id"]  # Missing some inputs
    )

    print(f"\n2. Partial ensemble: {partial_methods}")
    print(f"   Score: {partial_score:.3f}")

    # Test Case 3: Invalid fusion rule
    invalid_score = evaluator.evaluate(
        method_ids=perfect_methods,
        subgraph_id="test_invalid",
        fusion_rule="invalid_rule",
        provided_inputs=["extracted_text"]
    )

    print(f"\n3. Invalid fusion rule")
    print(f"   Score: {invalid_score:.3f}")

    # Verification checks
    print("\n" + "=" * 60)
    print("VERIFICATION CHECKS")
    print("=" * 60)

    checks_passed = 0
    total_checks = 6

    # Check 1: Perfect score should be high (> 0.5)
    if perfect_score > 0.5:
        print("✅ Check 1: Perfect ensemble scores high")
        checks_passed += 1
    else:
        print(f"❌ Check 1: Perfect score too low ({perfect_score:.3f})")

    # Check 2: Partial score should be lower than perfect
    if partial_score < perfect_score:
        print("✅ Check 2: Partial ensemble scores lower than perfect")
        checks_passed += 1
    else:
        print(f"❌ Check 2: Partial not lower ({partial_score:.3f} vs {perfect_score:.3f})")

    # Check 3: Invalid score should be 0
    if invalid_score == 0.0:
        print("✅ Check 3: Invalid fusion rule scores 0.0")
        checks_passed += 1
    else:
        print(f"❌ Check 3: Invalid should be 0.0 (got {invalid_score:.3f})")

    # Check 4: Scores are differentiated
    scores = [perfect_score, partial_score, invalid_score]
    if len(set(scores)) == len(scores):
        print("✅ Check 4: All scores are different")
        checks_passed += 1
    else:
        print(f"❌ Check 4: Scores not differentiated: {scores}")

    # Check 5: No stub value (1.0)
    if all(s != 1.0 for s in scores):
        print("✅ Check 5: Not returning stub value (1.0)")
        checks_passed += 1
    else:
        print("❌ Check 5: Still returning stub 1.0")

    # Check 6: Scores in valid range
    if all(0.0 <= s <= 1.0 for s in scores):
        print("✅ Check 6: All scores in [0.0, 1.0]")
        checks_passed += 1
    else:
        print(f"❌ Check 6: Scores out of range: {scores}")

    print("\n" + "=" * 60)
    if checks_passed == total_checks:
        print(f"✅ ALL {total_checks} CHECKS PASSED")
        print("=" * 60)
        return True
    else:
        print(f"❌ {checks_passed}/{total_checks} CHECKS PASSED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_congruence_differentiation()
    sys.exit(0 if success else 1)
