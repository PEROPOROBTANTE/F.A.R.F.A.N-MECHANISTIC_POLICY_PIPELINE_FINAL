#!/usr/bin/env python3
"""Validation script for calibration modules.

This script validates that the calibration registry and context modules
are working correctly by running a series of tests.
"""

import sys
from pathlib import Path

# Add src to path

def test_calibration_registry():
    """Test calibration registry module."""
    print("=" * 80)
    print("Testing Calibration Registry")
    print("=" * 80)
    
    from saaaaaa.core.orchestrator.calibration_registry import (
        MethodCalibration,
        resolve_calibration,
        resolve_calibration_with_context,
    )
    
    # Test 1: Create MethodCalibration
    print("\n1. Creating MethodCalibration...")
    mc = MethodCalibration(
        score_min=0.0,
        score_max=1.0,
        min_evidence_snippets=5,
        max_evidence_snippets=20,
        contradiction_tolerance=0.1,
        uncertainty_penalty=0.3,
        aggregation_weight=1.0,
        sensitivity=0.75,
        requires_numeric_support=False,
        requires_temporal_support=False,
        requires_source_provenance=True,
    )
    print(f"   ✓ Created: {mc}")
    
    # Test 2: Resolve base calibration
    print("\n2. Testing resolve_calibration()...")
    result = resolve_calibration("TestClass", "test_method")
    print(f"   ✓ Resolved calibration for TestClass.test_method")
    print(f"     Evidence range: {result.min_evidence_snippets}-{result.max_evidence_snippets}")
    print(f"     Sensitivity: {result.sensitivity}")
    
    # Test 3: Resolve with context
    print("\n3. Testing resolve_calibration_with_context()...")
    result_ctx = resolve_calibration_with_context(
        "TestClass", "test_method", question_id="D1Q1"
    )
    print(f"   ✓ Resolved with context for D1Q1")
    print(f"     Evidence range: {result_ctx.min_evidence_snippets}-{result_ctx.max_evidence_snippets}")
    print(f"     Sensitivity: {result_ctx.sensitivity}")
    
    if result_ctx.min_evidence_snippets != result.min_evidence_snippets:
        print(f"   ✓ Context applied! Base={result.min_evidence_snippets}, Context={result_ctx.min_evidence_snippets}")
    
    print("\n✓ Calibration Registry tests passed!")
    return True


def test_calibration_context():
    """Test calibration context module."""
    print("\n" + "=" * 80)
    print("Testing Calibration Context")
    print("=" * 80)
    
    from saaaaaa.core.orchestrator.calibration_context import (
        CalibrationContext,
        CalibrationModifier,
        PolicyArea,
        UnitOfAnalysis,
        resolve_contextual_calibration,
        infer_context_from_question_id,
    )
    from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
    
    # Test 1: Parse question IDs
    print("\n1. Testing question ID parsing...")
    test_cases = [
        ("D1Q1", 1, 1),
        ("D6Q3", 6, 3),
        ("d2q5", 2, 5),
        ("D10Q25", 10, 25),
    ]
    for qid, exp_dim, exp_q in test_cases:
        ctx = CalibrationContext.from_question_id(qid)
        assert ctx.dimension == exp_dim and ctx.question_num == exp_q
        print(f"   ✓ {qid} -> dimension={ctx.dimension}, question={ctx.question_num}")
    
    # Test 2: Immutable updates
    print("\n2. Testing immutable context updates...")
    ctx = CalibrationContext.from_question_id("D1Q1")
    ctx2 = ctx.with_policy_area(PolicyArea.FISCAL)
    assert ctx.policy_area == PolicyArea.UNKNOWN
    assert ctx2.policy_area == PolicyArea.FISCAL
    print(f"   ✓ Original unchanged: {ctx.policy_area}")
    print(f"   ✓ New context: {ctx2.policy_area}")
    
    # Test 3: CalibrationModifier
    print("\n3. Testing CalibrationModifier...")
    base = MethodCalibration(
        score_min=0.0,
        score_max=1.0,
        min_evidence_snippets=10,
        max_evidence_snippets=20,
        contradiction_tolerance=0.1,
        uncertainty_penalty=0.3,
        aggregation_weight=1.0,
        sensitivity=0.75,
        requires_numeric_support=False,
        requires_temporal_support=False,
        requires_source_provenance=True,
    )
    
    modifier = CalibrationModifier(
        min_evidence_multiplier=1.5,
        max_evidence_multiplier=1.2,
    )
    result = modifier.apply(base)
    assert result.min_evidence_snippets == 15  # 10 * 1.5
    assert result.max_evidence_snippets == 24  # 20 * 1.2
    print(f"   ✓ Modifier applied: {base.min_evidence_snippets},{base.max_evidence_snippets} -> {result.min_evidence_snippets},{result.max_evidence_snippets}")
    
    # Test 4: Contextual resolution
    print("\n4. Testing resolve_contextual_calibration()...")
    ctx = CalibrationContext.from_question_id("D1Q1")
    result = resolve_contextual_calibration(base, ctx)
    print(f"   ✓ D1 context: min_evidence {base.min_evidence_snippets} -> {result.min_evidence_snippets}")
    
    # Test 5: No context returns base
    result_no_ctx = resolve_contextual_calibration(base, None)
    assert result_no_ctx == base
    print(f"   ✓ No context returns base unchanged")
    
    # Test 6: infer_context_from_question_id
    print("\n5. Testing infer_context_from_question_id()...")
    ctx = infer_context_from_question_id("D5Q12")
    assert ctx.dimension == 5 and ctx.question_num == 12
    print(f"   ✓ Inferred: D5Q12 -> dimension={ctx.dimension}, question={ctx.question_num}")
    
    print("\n✓ Calibration Context tests passed!")
    return True


def main():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("CALIBRATION MODULES VALIDATION")
    print("=" * 80)
    
    try:
        # Test calibration registry
        if not test_calibration_registry():
            print("\n✗ Calibration Registry tests failed!")
            return 1
        
        # Test calibration context
        if not test_calibration_context():
            print("\n✗ Calibration Context tests failed!")
            return 1
        
        print("\n" + "=" * 80)
        print("✓✓✓ ALL CALIBRATION VALIDATION TESTS PASSED ✓✓✓")
        print("=" * 80)
        return 0
        
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
