"""
Verify Meta Layer weighted scoring.

Tests:
1. Weighted formula (0.5·t + 0.4·g + 0.1·c)
2. Discrete scores for each component
3. Score differentiation based on inputs
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.calibration.meta_layer import MetaLayerEvaluator
from saaaaaa.core.calibration.config import MetaLayerConfig

def test_meta_weighted_scoring():
    """Test meta layer weighted formula."""

    print("=" * 60)
    print("META LAYER VERIFICATION")
    print("=" * 60)

    config = MetaLayerConfig()
    evaluator = MetaLayerEvaluator(config)

    # Test Case 1: Perfect governance (all conditions met)
    perfect = evaluator.evaluate(
        method_id="test_method",
        method_version="v2.1.0",
        config_hash="abc123def456",
        formula_exported=True,
        full_trace=True,
        logs_conform=True,
        signature_valid=True,
        execution_time_s=0.5
    )
    print(f"\n1. Perfect governance")
    print(f"   Score: {perfect:.3f}")
    print(f"   Expected: ~1.0")

    # Test Case 2: Good transparency, poor governance
    good_transp = evaluator.evaluate(
        method_id="test_method",
        method_version="unknown",  # Poor version
        config_hash="",  # No hash
        formula_exported=True,
        full_trace=True,
        logs_conform=True,
        signature_valid=False,
        execution_time_s=0.5
    )
    print(f"\n2. Good transparency, poor governance")
    print(f"   Score: {good_transp:.3f}")
    print(f"   Expected: ~0.6 (0.5*1.0 + 0.4*0.0 + 0.1*1.0)")

    # Test Case 3: Poor transparency, good governance
    good_gov = evaluator.evaluate(
        method_id="test_method",
        method_version="v2.1.0",
        config_hash="abc123",
        formula_exported=False,
        full_trace=False,
        logs_conform=False,
        signature_valid=True,
        execution_time_s=0.5
    )
    print(f"\n3. Poor transparency, good governance")
    print(f"   Score: {good_gov:.3f}")
    print(f"   Expected: ~0.5 (0.5*0.0 + 0.4*1.0 + 0.1*1.0)")

    # Test Case 4: Slow execution
    slow = evaluator.evaluate(
        method_id="test_method",
        method_version="v2.1.0",
        config_hash="abc123",
        formula_exported=True,
        full_trace=True,
        logs_conform=True,
        signature_valid=True,
        execution_time_s=10.0  # Slow
    )
    print(f"\n4. Slow execution")
    print(f"   Score: {slow:.3f}")
    print(f"   Expected: ~0.95 (0.5*1.0 + 0.4*1.0 + 0.1*0.5)")

    # Verification
    print("\n" + "=" * 60)
    print("VERIFICATION CHECKS")
    print("=" * 60)

    checks = 0
    total = 8

    # Check 1: Perfect case high
    if perfect >= 0.95:
        print(f"✅ Check 1: Perfect case scores high ({perfect:.3f})")
        checks += 1
    else:
        print(f"❌ Check 1: Perfect should be >=0.95 (got {perfect:.3f})")

    # Check 2: Scores differentiated
    scores = [perfect, good_transp, good_gov, slow]
    if len(set(scores)) >= 3:
        print(f"✅ Check 2: At least 3 different scores")
        checks += 1
    else:
        print(f"❌ Check 2: Not enough differentiation: {scores}")

    # Check 3: Weighted formula (transparency dominates)
    if good_transp > good_gov:
        print(f"✅ Check 3: Transparency weighted more (0.5 > 0.4)")
        checks += 1
    else:
        print(f"❌ Check 3: Weight imbalance ({good_transp:.3f} vs {good_gov:.3f})")

    # Check 4: Not stub
    if not all(s == 1.0 for s in scores):
        print(f"✅ Check 4: Not returning stub 1.0 for all")
        checks += 1
    else:
        print(f"❌ Check 4: Still returning stub")

    # Check 5: All scores in range
    if all(0.0 <= s <= 1.0 for s in scores):
        print(f"✅ Check 5: All scores in [0.0, 1.0]")
        checks += 1
    else:
        print(f"❌ Check 5: Scores out of range: {scores}")

    # Check 6: Slow execution penalty
    if slow < perfect:
        print(f"✅ Check 6: Slow execution penalized")
        checks += 1
    else:
        print(f"❌ Check 6: No cost penalty ({slow:.3f} vs {perfect:.3f})")

    # Check 7: Formula approximately correct
    expected_good_transp = 0.5 * 1.0 + 0.4 * 0.0 + 0.1 * 1.0  # 0.6
    if abs(good_transp - expected_good_transp) < 0.1:
        print(f"✅ Check 7: Weighted formula correct")
        checks += 1
    else:
        print(f"❌ Check 7: Formula error ({good_transp:.3f} vs {expected_good_transp:.3f})")

    # Check 8: Components independent
    if good_transp != good_gov:
        print(f"✅ Check 8: Components are independent")
        checks += 1
    else:
        print(f"❌ Check 8: Components not independent")

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
    success = test_meta_weighted_scoring()
    sys.exit(0 if success else 1)
