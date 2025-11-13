#!/usr/bin/env python3
"""
Verify calibration is actually invoked during executor execution.

This is an INTEGRATION test that proves Fix 2 worked.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from saaaaaa.core.orchestrator.executors import D1Q1_Executor
from saaaaaa.core.orchestrator.core import MethodExecutor
from saaaaaa.core.calibration import CalibrationOrchestrator, DEFAULT_CALIBRATION_CONFIG


def test_calibration_is_invoked():
    """
    Test that calibration is actually called during execution.
    
    Returns:
        True if test passes, False otherwise
    """
    print("=" * 60)
    print("EXECUTOR CALIBRATION INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Setup
    print("\n1. Setting up executor with calibration...")
    method_exec = MethodExecutor()
    
    # Create calibration orchestrator
    compat_path = Path("data/method_compatibility.json")
    if not compat_path.exists():
        print(f"⚠️  SKIP: {compat_path} not found")
        print("   Creating minimal compatibility file for testing...")
        compat_path.parent.mkdir(parents=True, exist_ok=True)
        compat_path.write_text('{"pattern_extractor_v2": {"MICRO": 0.8}}')
    
    orch = CalibrationOrchestrator(
        config=DEFAULT_CALIBRATION_CONFIG,
        compatibility_path=compat_path
    )
    
    # Create executor WITH calibration
    executor = D1Q1_Executor(
        method_executor=method_exec,
        signal_registry=None,
        calibration_orchestrator=orch
    )
    
    print(f"   ✅ Executor created with calibration: {executor.calibration is not None}")
    
    # Create mock document
    print("\n2. Creating mock document...")
    class MockDoc:
        def __init__(self):
            from saaaaaa.core.calibration.pdt_structure import PDTStructure
            self.pdt_structure = PDTStructure(
                full_text="test document",
                total_tokens=100,
                blocks_found={
                    "Diagnóstico": {"tokens": 200, "numbers_count": 10}
                },
                indicator_matrix_present=True,
                indicator_rows=[
                    {"Línea Base": "100", "Meta Cuatrienio": "200", "Fuente": "Test"}
                ],
                ppi_matrix_present=True,
                ppi_rows=[
                    {"Costo Total": 1000000}
                ]
            )
            self.unit_quality = 0.75
    
    doc = MockDoc()
    print(f"   ✅ Mock document created (unit_quality={doc.unit_quality})")
    
    # Execute
    print("\n3. Executing with calibration...")
    try:
        result = executor.execute_with_optimization(
            doc=doc,
            question_id="Q001",
            dimension_id="DIM01",
            policy_area_id="PA01",
            method_sets={
                "analyzer": [{"id": "pattern_extractor_v2", "version": "v2.1.0"}]
            }
        )
        
        print(f"   ✅ Execution completed")
        
        # CRITICAL CHECK 1: _calibration field must exist
        print("\n4. Checking calibration output...")
        if "_calibration" not in result:
            print("   ❌ FAIL: _calibration field missing from output")
            print(f"   Output keys: {list(result.keys())}")
            return False
        
        print(f"   ✅ _calibration field exists")
        
        # CRITICAL CHECK 2: scores must be populated
        if "scores" not in result["_calibration"]:
            print("   ❌ FAIL: _calibration.scores missing")
            return False
        
        scores = result["_calibration"]["scores"]
        if len(scores) == 0:
            print("   ❌ FAIL: No methods were calibrated")
            return False
        
        print(f"   ✅ {len(scores)} method(s) calibrated")
        
        # CRITICAL CHECK 3: Verify structure
        print("\n5. Validating score structure...")
        first_method = list(scores.keys())[0]
        method_data = scores[first_method]
        
        required_fields = ["final_score", "layer_breakdown", "linear_contribution"]
        for field in required_fields:
            if field not in method_data:
                print(f"   ❌ FAIL: Missing field '{field}' in calibration output")
                return False
        
        print(f"   ✅ All required fields present")
        
        # CRITICAL CHECK 4: Layer breakdown not empty
        if not method_data["layer_breakdown"]:
            print("   ❌ FAIL: layer_breakdown is empty")
            return False
        
        print(f"   ✅ Layer breakdown has {len(method_data['layer_breakdown'])} layers")
        
        # CRITICAL CHECK 5: Metadata
        print("\n6. Checking metadata...")
        if "executed_at" not in result["_calibration"]:
            print("   ⚠️  WARNING: executed_at missing")
        else:
            print(f"   ✅ Execution timestamp: {result['_calibration']['executed_at']}")
        
        if "total_methods_calibrated" not in result["_calibration"]:
            print("   ⚠️  WARNING: total_methods_calibrated missing")
        else:
            print(f"   ✅ Total calibrated: {result['_calibration']['total_methods_calibrated']}")
        
        print(f"   ✅ Total skipped: {result['_calibration'].get('total_methods_skipped', 0)}")
        
        # SUCCESS
        print("\n" + "=" * 60)
        print("✅ ALL CHECKS PASSED - Calibration is integrated and working")
        print("=" * 60)
        print(f"\nSummary:")
        print(f"  Calibrated methods: {len(scores)}")
        print(f"  Skipped methods: {result['_calibration'].get('total_methods_skipped', 0)}")
        print(f"  Sample score: {method_data['final_score']:.3f}")
        print(f"  Sample layers: {list(method_data['layer_breakdown'].keys())}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ FAIL: Execution error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_calibration_is_invoked()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ ERROR: Test failed with exception")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
