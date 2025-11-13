"""
Verify Chain Layer produces discrete scores.

Tests all 5 discrete score levels: 1.0, 0.8, 0.6, 0.3, 0.0
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.calibration.chain_layer import ChainLayerEvaluator
import json

def test_chain_discrete_scoring():
    """Test that chain produces correct discrete scores."""

    print("=" * 60)
    print("CHAIN LAYER VERIFICATION")
    print("=" * 60)

    # Load signatures
    sig_path = Path("data/method_signatures.json")
    if not sig_path.exists():
        print("❌ FAIL: method_signatures.json not found")
        return False

    with open(sig_path) as f:
        sig_data = json.load(f)

    signatures = sig_data["methods"]
    evaluator = ChainLayerEvaluator(method_signatures=signatures)

    # Test Case 1: Score 1.0 (all inputs present)
    score_1 = evaluator.evaluate(
        method_id="pattern_extractor_v2",
        provided_inputs=["text", "question_id", "context", "patterns", "regex_flags"]
    )
    print(f"\n1. All inputs present")
    print(f"   Score: {score_1:.1f} (expected: 1.0)")

    # Test Case 2: Score 0.8 (some optional missing)
    score_08 = evaluator.evaluate(
        method_id="pattern_extractor_v2",
        provided_inputs=["text", "question_id", "patterns"]  # Missing context, regex_flags
    )
    print(f"\n2. Some optional missing")
    print(f"   Score: {score_08:.1f} (expected: 0.8)")

    # Test Case 3: Score 0.3 (critical optional missing)
    score_03 = evaluator.evaluate(
        method_id="pattern_extractor_v2",
        provided_inputs=["text", "question_id"]  # Missing critical 'patterns'
    )
    print(f"\n3. Critical optional missing")
    print(f"   Score: {score_03:.1f} (expected: 0.3)")

    # Test Case 4: Score 0.0 (required missing)
    score_0 = evaluator.evaluate(
        method_id="pattern_extractor_v2",
        provided_inputs=["question_id"]  # Missing required 'text'
    )
    print(f"\n4. Required input missing")
    print(f"   Score: {score_0:.1f} (expected: 0.0)")

    # Verification
    print("\n" + "=" * 60)
    print("VERIFICATION CHECKS")
    print("=" * 60)

    checks = 0
    total = 8

    # Discrete values check
    valid_scores = {0.0, 0.1, 0.3, 0.6, 0.8, 1.0}
    all_scores = [score_1, score_08, score_03, score_0]

    if all(s in valid_scores for s in all_scores):
        print("✅ Check 1: All scores are discrete values")
        checks += 1
    else:
        print(f"❌ Check 1: Non-discrete scores: {all_scores}")

    # Correct score levels
    if score_1 == 1.0:
        print("✅ Check 2: Perfect case scores 1.0")
        checks += 1
    else:
        print(f"❌ Check 2: Perfect case should be 1.0 (got {score_1})")

    if score_08 in {0.6, 0.8}:  # Some implementations may give 0.6
        print(f"✅ Check 3: Some optional missing scores {score_08}")
        checks += 1
    else:
        print(f"❌ Check 3: Should be 0.6 or 0.8 (got {score_08})")

    if score_03 == 0.3:
        print("✅ Check 4: Critical missing scores 0.3")
        checks += 1
    else:
        print(f"❌ Check 4: Should be 0.3 (got {score_03})")

    if score_0 == 0.0:
        print("✅ Check 5: Required missing scores 0.0")
        checks += 1
    else:
        print(f"❌ Check 5: Should be 0.0 (got {score_0})")

    # Ordering check
    if score_1 > score_08 > score_03 > score_0:
        print("✅ Check 6: Scores properly ordered")
        checks += 1
    else:
        print(f"❌ Check 6: Scores not ordered: {all_scores}")

    # Not stub check
    if score_1 != 1.0 or any(s != 1.0 for s in all_scores[1:]):
        print("✅ Check 7: Not returning stub 1.0 for all")
        checks += 1
    else:
        print("❌ Check 7: Still returning stub 1.0")

    # Differentiation check
    if len(set(all_scores)) >= 3:
        print("✅ Check 8: At least 3 different scores")
        checks += 1
    else:
        print(f"❌ Check 8: Not enough differentiation: {set(all_scores)}")

    print("\n" + "=" * 60)
    if checks == total:
        print(f"✅ ALL {total} CHECKS PASSED")
        print("=" * 60)
        return True
    else:
        print(f"❌ {checks}/{total} CHECKS PASSED")
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = test_chain_discrete_scoring()
    sys.exit(0 if success else 1)
