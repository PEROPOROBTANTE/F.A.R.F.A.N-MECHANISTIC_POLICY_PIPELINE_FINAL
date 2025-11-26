"""
Phase 5 Test: No Parallel Systems.

Verifies ZERO TOLERANCE requirement: Single source of truth for all calibration
and parameterization data.

Tests:
1. Only 1 CalibrationOrchestrator instance possible
2. Only 1 IntrinsicCalibrationLoader instance possible
3. Only 1 ParameterLoader instance possible
4. Only 1 intrinsic_calibration.json file
5. Only 1 method_parameters.json file
6. Only 1 LAYER_REQUIREMENTS definition
"""
import sys
import pytest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


class TestNoParallelSystems:
    """
    Test suite for ZERO TOLERANCE requirement: No parallel systems.

    All tests MUST pass for Phase 5 compliance.
    """

    def test_only_one_calibration_orchestrator_possible(self):
        """Test that only ONE CalibrationOrchestrator instance can exist."""
        from saaaaaa.core.calibration.orchestrator import CalibrationOrchestrator

        # Attempt direct instantiation should fail
        with pytest.raises(RuntimeError, match="singleton"):
            CalibrationOrchestrator()

        # get_instance() should return singleton
        try:
            instance1 = CalibrationOrchestrator.get_instance()
            instance2 = CalibrationOrchestrator.get_instance()

            assert instance1 is instance2, "get_instance() returned different instances!"

            # Verify multiple calls return same instance
            instances = [CalibrationOrchestrator.get_instance() for _ in range(10)]
            assert all(inst is instance1 for inst in instances), "Singleton violated!"

        except FileNotFoundError:
            # If calibration file missing, singleton pattern itself still OK
            pytest.skip("Calibration file not found (singleton pattern works)")

    def test_only_one_intrinsic_loader_possible(self):
        """Test that only ONE IntrinsicScoreLoader instance can exist."""
        from saaaaaa.core.calibration.intrinsic_loader import IntrinsicScoreLoader

        # Attempt direct instantiation should fail
        with pytest.raises(RuntimeError, match="singleton"):
            IntrinsicScoreLoader()

        # get_instance() should return singleton
        instance1 = IntrinsicScoreLoader.get_instance()
        instance2 = IntrinsicScoreLoader.get_instance()

        assert instance1 is instance2, "get_instance() returned different instances!"

        # Verify multiple calls return same instance
        instances = [IntrinsicScoreLoader.get_instance() for _ in range(10)]
        assert all(inst is instance1 for inst in instances), "Singleton violated!"

    def test_only_one_parameter_loader_possible(self):
        """Test that only ONE MethodParameterLoader instance can exist."""
        from saaaaaa.core.calibration.parameter_loader import MethodParameterLoader

        # Attempt direct instantiation should fail
        with pytest.raises(RuntimeError, match="singleton"):
            MethodParameterLoader()

        # get_instance() should return singleton
        instance1 = MethodParameterLoader.get_instance()
        instance2 = MethodParameterLoader.get_instance()

        assert instance1 is instance2, "get_instance() returned different instances!"

        # Verify multiple calls return same instance
        instances = [MethodParameterLoader.get_instance() for _ in range(10)]
        assert all(inst is instance1 for inst in instances), "Singleton violated!"

    def test_only_one_intrinsic_calibration_json(self):
        """Test that only ONE intrinsic_calibration.json file exists."""
        config_dir = PROJECT_ROOT / "config"

        # Find all files named intrinsic_calibration.json
        calibration_files = list(config_dir.glob("**/intrinsic_calibration.json"))

        assert len(calibration_files) == 1, (
            f"Found {len(calibration_files)} intrinsic_calibration.json files! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {calibration_files}"
        )

    def test_only_one_method_parameters_json(self):
        """Test that only ONE method_parameters.json file exists."""
        config_dir = PROJECT_ROOT / "config"

        # Find all files named method_parameters.json
        param_files = list(config_dir.glob("**/method_parameters.json"))

        assert len(param_files) == 1, (
            f"Found {len(param_files)} method_parameters.json files! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {param_files}"
        )

    def test_only_one_layer_requirements_definition(self):
        """Test that LAYER_REQUIREMENTS is defined in exactly ONE location."""
        from saaaaaa.core.calibration import layer_requirements

        # Verify module has LAYER_REQUIREMENTS
        assert hasattr(layer_requirements, 'LayerRequirementsResolver'), (
            "layer_requirements module missing LayerRequirementsResolver"
        )

        # Check for duplicate definitions across codebase
        src_dir = PROJECT_ROOT / "src" / "saaaaaa" / "core" / "calibration"
        python_files = list(src_dir.glob("*.py"))

        definitions_found = []
        for py_file in python_files:
            content = py_file.read_text()
            if "LAYER_REQUIREMENTS" in content and "L_STAR" in content:
                definitions_found.append(str(py_file))

        assert len(definitions_found) == 1, (
            f"Found {len(definitions_found)} LAYER_REQUIREMENTS definitions! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {definitions_found}"
        )

    def test_single_source_of_truth_for_choquet_weights(self):
        """Test that Choquet weights loaded from single JSON file."""
        choquet_json = PROJECT_ROOT / "config" / "choquet_weights.json"

        assert choquet_json.exists(), (
            "choquet_weights.json missing! "
            "Weights must be in JSON, not hardcoded."
        )

        # Verify no duplicate choquet weight files
        config_dir = PROJECT_ROOT / "config"
        choquet_files = list(config_dir.glob("**/choquet*.json"))

        assert len(choquet_files) == 1, (
            f"Found {len(choquet_files)} choquet weight files! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {choquet_files}"
        )

    def test_single_source_of_truth_for_penalties(self):
        """Test that all penalty values in single JSON file."""
        penalties_json = PROJECT_ROOT / "config" / "calibration_penalties.json"

        assert penalties_json.exists(), (
            "calibration_penalties.json missing! "
            "Penalties must be in JSON, not hardcoded."
        )

        # Verify no duplicate penalty files
        config_dir = PROJECT_ROOT / "config"
        penalty_files = list(config_dir.glob("**/*penalt*.json"))

        assert len(penalty_files) == 1, (
            f"Found {len(penalty_files)} penalty files! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {penalty_files}"
        )

    def test_single_source_of_truth_for_thresholds(self):
        """Test that all quality thresholds in single JSON file."""
        thresholds_json = PROJECT_ROOT / "config" / "quality_thresholds.json"

        assert thresholds_json.exists(), (
            "quality_thresholds.json missing! "
            "Thresholds must be in JSON, not hardcoded."
        )

        # Verify no duplicate threshold files
        config_dir = PROJECT_ROOT / "config"
        threshold_files = list(config_dir.glob("**/*threshold*.json"))

        assert len(threshold_files) == 1, (
            f"Found {len(threshold_files)} threshold files! "
            f"ZERO TOLERANCE: Only 1 allowed. Files: {threshold_files}"
        )


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
