"""
test_intrinsic_pipeline_behavior.py - Test pipeline execution with intrinsic calibration

Tests fallback behavior:
1. All computed: Normal execution with actual @b values
2. Mix of pending/excluded: Verify fallback behavior (pending→@b=0.5, excluded→skip, none→@b=0.3 with warning)

DEPRECATED: This test relies on outdated IntrinsicCalibrationLoader interface.
See tests/DEPRECATED_TESTS.md for details.
"""
import json
import tempfile
from pathlib import Path

import pytest

from src.farfan_pipeline.core.calibration.intrinsic_calibration_loader import (
    IntrinsicCalibrationLoader,
)

pytestmark = pytest.mark.obsolete


@pytest.fixture
def temp_calibration_file():
    """Create a temporary calibration file for testing."""
    data = {
        "_metadata": {
            "version": "1.0.0",
            "generated": "2025-01-15T00:00:00Z",
            "description": "Test calibration data",
            "total_methods": 5,
            "computed_methods": 4,
            "coverage_percent": 80.0
        },
        "TestClass.computed_method": {
            "intrinsic_score": [0.75, 0.85],
            "b_theory": 0.80,
            "b_impl": 0.78,
            "b_deploy": 0.83,
            "calibration_status": "computed",
            "layer": "engine",
            "last_updated": "2025-01-15T00:00:00Z"
        },
        "TestClass.pending_method": {
            "intrinsic_score": [0.0, 0.0],
            "b_theory": 0.0,
            "b_impl": 0.0,
            "b_deploy": 0.0,
            "calibration_status": "pending",
            "layer": "processor",
            "last_updated": "2025-01-15T00:00:00Z"
        },
        "TestClass.excluded_method": {
            "intrinsic_score": [0.0, 0.0],
            "b_theory": 0.0,
            "b_impl": 0.0,
            "b_deploy": 0.0,
            "calibration_status": "excluded",
            "layer": "utility",
            "last_updated": "2025-01-15T00:00:00Z"
        },
        "TestClass.none_method": {
            "intrinsic_score": [0.0, 0.0],
            "b_theory": 0.0,
            "b_impl": 0.0,
            "b_deploy": 0.0,
            "calibration_status": "none",
            "layer": "engine",
            "last_updated": "2025-01-15T00:00:00Z"
        },
        "TestClass.another_computed": {
            "intrinsic_score": [0.68, 0.78],
            "b_theory": 0.73,
            "b_impl": 0.70,
            "b_deploy": 0.76,
            "calibration_status": "computed",
            "layer": "processor",
            "last_updated": "2025-01-15T00:00:00Z"
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f, indent=2)
        temp_path = f.name

    yield temp_path
    Path(temp_path).unlink()


def test_loader_initialization(temp_calibration_file):
    """Test loader initializes correctly with valid data."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    metadata = loader.get_metadata()

    assert metadata["coverage_percent"] >= 80.0
    assert metadata["computed_methods"] == 4


def test_loader_rejects_low_coverage():
    """Test loader rejects data with <80% coverage."""
    data = {
        "_metadata": {
            "version": "1.0.0",
            "generated": "2025-01-15T00:00:00Z",
            "description": "Low coverage test",
            "total_methods": 100,
            "computed_methods": 70,
            "coverage_percent": 70.0
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f, indent=2)
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="coverage.*80"):
            IntrinsicCalibrationLoader(temp_path)
    finally:
        Path(temp_path).unlink()


def test_computed_method_returns_actual_values(temp_calibration_file):
    """Test computed method returns actual @b values from JSON."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.computed_method")

    assert cal is not None
    assert cal.calibration_status == "computed"
    assert cal.b_theory == 0.80
    assert cal.b_impl == 0.78
    assert cal.b_deploy == 0.83
    assert cal.intrinsic_score == (0.75, 0.85)
    assert cal.layer == "engine"


def test_pending_method_returns_fallback_05(temp_calibration_file):
    """Test pending method returns @b=0.5 fallback."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.pending_method")

    assert cal is not None
    assert cal.calibration_status == "pending"
    assert cal.b_theory == 0.5
    assert cal.b_impl == 0.5
    assert cal.b_deploy == 0.5
    assert cal.intrinsic_score == (0.48, 0.52)


def test_excluded_method_returns_none(temp_calibration_file):
    """Test excluded method returns None (signals skip)."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.excluded_method")

    assert cal is None


def test_none_method_returns_fallback_03(temp_calibration_file):
    """Test none status method returns @b=0.3 fallback."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.none_method")

    assert cal is not None
    assert cal.calibration_status == "none"
    assert cal.b_theory == 0.3
    assert cal.b_impl == 0.3
    assert cal.b_deploy == 0.3
    assert cal.intrinsic_score == (0.28, 0.32)


def test_missing_method_returns_fallback_03(temp_calibration_file):
    """Test method not in registry returns @b=0.3 fallback."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.unknown_method")

    assert cal is not None
    assert cal.calibration_status == "none"
    assert cal.b_theory == 0.3
    assert cal.b_impl == 0.3
    assert cal.b_deploy == 0.3


def test_contamination_detection():
    """Test loader detects contaminated data."""
    data = {
        "_metadata": {
            "version": "1.0.0",
            "generated": "2025-01-15T00:00:00Z",
            "description": "Contaminated test",
            "total_methods": 1,
            "computed_methods": 1,
            "coverage_percent": 100.0
        },
        "TestClass.contaminated_method": {
            "intrinsic_score": [0.75, 0.85],
            "b_theory": 0.80,
            "b_impl": 0.78,
            "b_deploy": 0.83,
            "final_score": 0.85,  # CONTAMINATION
            "calibration_status": "computed",
            "layer": "engine",
            "last_updated": "2025-01-15T00:00:00Z"
        }
    }

    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        json.dump(data, f, indent=2)
        temp_path = f.name

    try:
        loader = IntrinsicCalibrationLoader(temp_path)
        with pytest.raises(ValueError, match="CONTAMINATION"):
            loader.verify_purity()
    finally:
        Path(temp_path).unlink()


def test_composite_b_calculation(temp_calibration_file):
    """Test composite @b score calculation."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)
    cal = loader.get_calibration("TestClass.computed_method")

    expected_composite = (0.80 + 0.78 + 0.83) / 3.0
    assert abs(cal.get_composite_b() - expected_composite) < 0.001


def test_pipeline_execution_all_computed(temp_calibration_file):
    """Simulate pipeline execution with all computed methods."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)

    methods_to_execute = [
        "TestClass.computed_method",
        "TestClass.another_computed"
    ]

    results = {}
    for method_id in methods_to_execute:
        cal = loader.get_calibration(method_id)
        if cal is not None:  # Not excluded
            results[method_id] = {
                "executed": True,
                "composite_b": cal.get_composite_b(),
                "status": cal.calibration_status
            }

    assert len(results) == 2
    assert all(r["executed"] for r in results.values())
    assert all(r["status"] == "computed" for r in results.values())


def test_pipeline_execution_mixed_statuses(temp_calibration_file):
    """Simulate pipeline execution with mixed calibration statuses."""
    loader = IntrinsicCalibrationLoader(temp_calibration_file)

    methods_to_execute = [
        "TestClass.computed_method",
        "TestClass.pending_method",
        "TestClass.excluded_method",
        "TestClass.none_method"
    ]

    results = {}
    skipped = []

    for method_id in methods_to_execute:
        cal = loader.get_calibration(method_id)
        if cal is None:  # Excluded
            skipped.append(method_id)
        else:
            results[method_id] = {
                "executed": True,
                "composite_b": cal.get_composite_b(),
                "status": cal.calibration_status,
                "is_fallback": cal.calibration_status != "computed"
            }

    assert len(results) == 3  # computed, pending, none
    assert len(skipped) == 1  # excluded
    assert "TestClass.excluded_method" in skipped

    # Verify fallback behavior
    assert results["TestClass.pending_method"]["composite_b"] == 0.5
    assert results["TestClass.none_method"]["composite_b"] == 0.3
    assert results["TestClass.computed_method"]["composite_b"] > 0.7


def test_real_calibration_file_exists():
    """Test that the real calibration file exists and is valid."""
    cal_path = Path("config/intrinsic_calibration.json")
    assert cal_path.exists(), "Real calibration file must exist"

    loader = IntrinsicCalibrationLoader(str(cal_path))
    metadata = loader.get_metadata()

    assert metadata["coverage_percent"] >= 80.0
    assert metadata["computed_methods"] >= 30

    # Verify purity
    assert loader.verify_purity()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
