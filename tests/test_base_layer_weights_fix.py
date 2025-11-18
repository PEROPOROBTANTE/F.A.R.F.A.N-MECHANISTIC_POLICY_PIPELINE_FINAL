"""
Test to verify BaseLayerEvaluator weight bug fix.

This test verifies that BaseLayerEvaluator now:
1. Loads weights from JSON (_base_weights section)
2. Uses correct weights (0.4, 0.35, 0.25) instead of old hardcoded (0.4, 0.4, 0.2)
3. Produces same scores as IntrinsicScoreLoader
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.saaaaaa.core.calibration.base_layer import BaseLayerEvaluator
from src.saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader


def test_weights_loaded_from_json():
    """Test that weights are loaded from JSON file."""
    print("=" * 80)
    print("TEST 1: Weights Loaded from JSON")
    print("=" * 80)
    print()

    evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")

    # Expected weights from JSON
    expected_theory = 0.4
    expected_impl = 0.35
    expected_deploy = 0.25

    print(f"Expected weights from JSON:")
    print(f"  w_theory: {expected_theory}")
    print(f"  w_impl:   {expected_impl}")
    print(f"  w_deploy: {expected_deploy}")
    print()

    print(f"Actual weights in BaseLayerEvaluator:")
    print(f"  theory_weight:  {evaluator.theory_weight}")
    print(f"  impl_weight:    {evaluator.impl_weight}")
    print(f"  deploy_weight:  {evaluator.deploy_weight}")
    print()

    # Verify
    theory_ok = abs(evaluator.theory_weight - expected_theory) < 1e-6
    impl_ok = abs(evaluator.impl_weight - expected_impl) < 1e-6
    deploy_ok = abs(evaluator.deploy_weight - expected_deploy) < 1e-6

    if theory_ok and impl_ok and deploy_ok:
        print("✓ All weights match JSON values")
        return True
    else:
        print("✗ Weights don't match JSON:")
        if not theory_ok:
            print(f"  theory: expected {expected_theory}, got {evaluator.theory_weight}")
        if not impl_ok:
            print(f"  impl: expected {expected_impl}, got {evaluator.impl_weight}")
        if not deploy_ok:
            print(f"  deploy: expected {expected_deploy}, got {evaluator.deploy_weight}")
        return False


def test_weights_sum_to_one():
    """Test that weights sum to 1.0."""
    print("=" * 80)
    print("TEST 2: Weights Sum to 1.0")
    print("=" * 80)
    print()

    evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")

    total = evaluator.theory_weight + evaluator.impl_weight + evaluator.deploy_weight

    print(f"Weight sum: {total}")
    print()

    if abs(total - 1.0) < 1e-6:
        print("✓ Weights sum to 1.0")
        return True
    else:
        print(f"✗ Weights sum to {total}, not 1.0")
        return False


def test_consistency_with_intrinsic_loader():
    """Test that BaseLayerEvaluator produces same scores as IntrinsicScoreLoader."""
    print("=" * 80)
    print("TEST 3: Consistency with IntrinsicScoreLoader")
    print("=" * 80)
    print()

    base_evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")
    intrinsic_loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

    # Test a few methods (only calibrated ones)
    test_methods = [
        "orchestrator.__init__.__getattr__",
        "orchestrator.factory.build_processor",
        "src.saaaaaa.core.orchestrator.executors.D1Q1_Executor.execute",
        "src.saaaaaa.core.orchestrator.executors.D3Q2_Executor.execute",
        "src.saaaaaa.core.orchestrator.executors.D6Q5_Executor.execute",
    ]

    print("Comparing scores (calibrated methods only):")
    print()

    all_match = True
    for method_id in test_methods:
        # Skip if not calibrated
        if not intrinsic_loader.is_calibrated(method_id):
            print(f"⊘ {method_id[:55]:55s} (not calibrated, skipping)")
            continue
        # Get score from BaseLayerEvaluator
        layer_score = base_evaluator.evaluate(method_id)
        base_score = layer_score.score

        # Get score from IntrinsicScoreLoader
        intrinsic_score = intrinsic_loader.get_score(method_id)

        # Compare
        difference = abs(base_score - intrinsic_score)
        match = difference < 0.001

        status = "✓" if match else "✗"

        if not match:
            all_match = False

        print(f"{status} {method_id[:55]:55s}")
        print(f"   BaseLayer:  {base_score:.6f}")
        print(f"   Intrinsic:  {intrinsic_score:.6f}")
        print(f"   Difference: {difference:.6f}")
        print()

    if all_match:
        print("✓ All scores match between BaseLayerEvaluator and IntrinsicScoreLoader")
        return True
    else:
        print("✗ Some scores don't match")
        return False


def test_no_old_hardcoded_weights():
    """Test that old hardcoded weights (0.4, 0.4, 0.2) are NOT used."""
    print("=" * 80)
    print("TEST 4: Old Hardcoded Weights NOT Used")
    print("=" * 80)
    print()

    evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")

    # Old buggy weights
    old_theory = 0.4
    old_impl = 0.4
    old_deploy = 0.2

    print(f"Old (buggy) hardcoded weights:")
    print(f"  theory: {old_theory}")
    print(f"  impl:   {old_impl}")
    print(f"  deploy: {old_deploy}")
    print()

    print(f"Current weights:")
    print(f"  theory: {evaluator.theory_weight}")
    print(f"  impl:   {evaluator.impl_weight}")
    print(f"  deploy: {evaluator.deploy_weight}")
    print()

    # Check if using old weights
    using_old = (
        abs(evaluator.theory_weight - old_theory) < 1e-6 and
        abs(evaluator.impl_weight - old_impl) < 1e-6 and
        abs(evaluator.deploy_weight - old_deploy) < 1e-6
    )

    if not using_old:
        print("✓ NOT using old hardcoded weights")
        return True
    else:
        print("✗ STILL USING old hardcoded weights (BUG NOT FIXED!)")
        return False


if __name__ == "__main__":
    print("\nBASE LAYER EVALUATOR WEIGHT FIX VERIFICATION")
    print()

    # Run tests
    test1 = test_weights_loaded_from_json()
    print()
    test2 = test_weights_sum_to_one()
    print()
    test3 = test_consistency_with_intrinsic_loader()
    print()
    test4 = test_no_old_hardcoded_weights()

    # Summary
    print()
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"Weights loaded from JSON: {'✅ PASS' if test1 else '❌ FAIL'}")
    print(f"Weights sum to 1.0: {'✅ PASS' if test2 else '❌ FAIL'}")
    print(f"Consistency with IntrinsicScoreLoader: {'✅ PASS' if test3 else '❌ FAIL'}")
    print(f"Old weights NOT used: {'✅ PASS' if test4 else '❌ FAIL'}")
    print()

    if all([test1, test2, test3, test4]):
        print("🎉 ALL TESTS PASSED - BUG FIXED!")
        sys.exit(0)
    else:
        print("⚠️  SOME TESTS FAILED - BUG NOT FULLY FIXED")
        sys.exit(1)
