#!/usr/bin/env python3
"""Test script for ParameterLoaderV2."""

import sys
from pathlib import Path

def test_imports():
    """Test that all imports work."""
    print("Testing imports...")
    try:
        from farfan_pipeline.core.parameters import ParameterLoaderV2
        print("  ✓ ParameterLoaderV2 import successful")
    except ImportError as e:
        print(f"  ✗ ParameterLoaderV2 import failed: {e}")
        return False
    
    try:
        from farfan_pipeline.core.calibration.calibration_registry import get_calibration
        print("  ✓ get_calibration import successful")
    except ImportError as e:
        print(f"  ✗ get_calibration import failed: {e}")
        return False
    
    try:
        from farfan_pipeline.core.calibration.decorators import calibrated_method
        print("  ✓ calibrated_method import successful")
    except ImportError as e:
        print(f"  ✗ calibrated_method import failed: {e}")
        return False
    
    return True


def test_parameter_loading():
    """Test parameter loading functionality."""
    print("\nTesting parameter loading...")
    from farfan_pipeline.core.parameters import ParameterLoaderV2
    
    # Test 1: Load specific parameter
    value = ParameterLoaderV2.get(
        "farfan_core.analysis.derek_beach.BayesianThresholdsConfig",
        "kl_divergence",
        0.0
    )
    if value == 0.01:
        print(f"  ✓ Single parameter load: kl_divergence={value}")
    else:
        print(f"  ✗ Single parameter load failed: expected 0.01, got {value}")
        return False
    
    # Test 2: Load all parameters
    all_params = ParameterLoaderV2.get_all(
        "farfan_core.analysis.derek_beach.BayesianThresholdsConfig"
    )
    if len(all_params) == 5:
        print(f"  ✓ All parameters load: {len(all_params)} params")
    else:
        print(f"  ✗ All parameters load failed: expected 5, got {len(all_params)}")
        return False
    
    # Test 3: get_calibration compatibility
    from farfan_pipeline.core.calibration.calibration_registry import get_calibration
    compat_params = get_calibration(
        "farfan_core.analysis.derek_beach.BayesianThresholdsConfig"
    )
    if len(compat_params) == 5:
        print(f"  ✓ Backward compatibility: get_calibration works")
    else:
        print(f"  ✗ Backward compatibility failed")
        return False
    
    return True


def test_nonexistent_method():
    """Test handling of nonexistent methods."""
    print("\nTesting nonexistent method handling...")
    from farfan_pipeline.core.parameters import ParameterLoaderV2
    
    value = ParameterLoaderV2.get("nonexistent.method", "param", "default_value")
    if value == "default_value":
        print("  ✓ Default value returned for nonexistent method")
        return True
    else:
        print(f"  ✗ Expected 'default_value', got {value}")
        return False


def main():
    """Run all tests."""
    print("="*70)
    print("PARAMETER LOADER V2 FUNCTIONALITY TEST")
    print("="*70)
    
    tests = [
        ("Imports", test_imports),
        ("Parameter Loading", test_parameter_loading),
        ("Nonexistent Method", test_nonexistent_method),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ {name} raised exception: {e}")
            results.append((name, False))
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = all(passed for _, passed in results)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {name}")
    
    if all_passed:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
