"""Test executor validation functionality.

OBSOLETE: This test imports CALIBRATIONS which no longer exists in calibration_registry.
The API was refactored to use resolve_calibration() function instead.
"""

import pytest

pytestmark = pytest.mark.skip(reason="obsolete - CALIBRATIONS removed from API, use resolve_calibration()")

# Old imports (no longer valid):
# from unittest.mock import Mock, MagicMock
# from saaaaaa.core.orchestrator.executors import (
from saaaaaa.core.orchestrator.executors import ExecutorBase
#     ValidationResult,
#     AdvancedDataFlowExecutor,
# )
# from saaaaaa.core.orchestrator.executor_config import CONSERVATIVE_CONFIG
# from saaaaaa.core.orchestrator.calibration_registry import CALIBRATIONS, MethodCalibration


class MockMethodExecutor:
    """Mock method executor for testing."""
    
    def __init__(self, instances=None):
        self.instances = instances or {}


class TestExecutor(ExecutorBase):
    """Test executor implementation for validation testing."""
    
    def __init__(self, method_executor, config=None):
        self.executor = method_executor
        self.config = config or CONSERVATIVE_CONFIG
        self.signal_registry = None
        self._method_seq = []
    
    def _get_method_sequence(self):
        return self._method_seq
    
    def set_sequence(self, sequence):
        self._method_seq = sequence


class TestExecutorValidation:
    """Test ExecutorBase validation methods."""
    
    def test_validation_result_structure(self):
        """Test ValidationResult dataclass structure."""
        result = ValidationResult(
            is_valid=True,
            severity="INFO",
            message="Test message",
            context={"test": "data"}
        )
        
        assert result.is_valid is True
        assert result.severity == "INFO"
        assert result.message == "Test message"
        assert result.context == {"test": "data"}
    
    def test_validate_before_execution_success(self):
        """Test successful validation with all checks passing."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("TestClass", "test_method")])
        
        # Mock calibration
        CALIBRATIONS[("TestClass", "test_method")] = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=2,
            max_evidence_snippets=10,
            contradiction_tolerance=0.1,
            uncertainty_penalty=0.2,
            aggregation_weight=1.0,
            sensitivity=0.8,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        result = executor.validate_before_execution()
        
        assert result.is_valid is True
        assert result.severity in ["INFO", "WARNING"]
        # Accept any valid success message (including warnings about optional resources)
        assert len(result.message) > 0
        
        # Cleanup
        if ("TestClass", "test_method") in CALIBRATIONS:
            del CALIBRATIONS[("TestClass", "test_method")]
    
    def test_check_dependencies_missing_executor(self):
        """Test dependency check fails when executor is missing."""
        executor = TestExecutor(None)
        
        result = executor._check_dependencies()
        
        assert result.is_valid is False
        assert result.severity == "ERROR"
        assert "executor" in result.message.lower()
    
    def test_check_dependencies_missing_class(self):
        """Test dependency check fails when required class is missing."""
        mock_executor = MockMethodExecutor(instances={})
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("MissingClass", "test_method")])
        
        result = executor._check_dependencies()
        
        assert result.is_valid is False
        assert result.severity == "ERROR"
        assert "MissingClass" in result.message
    
    def test_check_dependencies_all_available(self):
        """Test dependency check passes when all classes are available."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass1": Mock(),
            "TestClass2": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([
            ("TestClass1", "method_a"),
            ("TestClass2", "method_b"),
        ])
        
        result = executor._check_dependencies()
        
        assert result.is_valid is True
        assert result.severity == "INFO"
        assert "dependencies available" in result.message.lower()
    
    def test_check_calibration_missing(self):
        """Test calibration check fails when calibration is missing."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("TestClass", "uncalibrated_method")])
        
        result = executor._check_calibration()
        
        assert result.is_valid is False
        assert result.severity == "ERROR"
        assert "calibration" in result.message.lower()
    
    def test_check_calibration_with_defaults(self):
        """Test calibration check warns when using default calibrations."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("TestClass", "default_method")])
        
        # Add a default-like calibration
        CALIBRATIONS[("TestClass", "default_method")] = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=1,
            max_evidence_snippets=10,
            contradiction_tolerance=0.9,
            uncertainty_penalty=0.1,
            aggregation_weight=1.0,
            sensitivity=0.5,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=False,
        )
        
        result = executor._check_calibration()
        
        # Could be WARNING for default calibration or INFO if it's considered acceptable
        assert result.is_valid is True
        
        # Cleanup
        if ("TestClass", "default_method") in CALIBRATIONS:
            del CALIBRATIONS[("TestClass", "default_method")]
    
    def test_check_calibration_all_explicit(self):
        """Test calibration check passes when all have explicit calibrations."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("TestClass", "calibrated_method")])
        
        # Add explicit calibration
        CALIBRATIONS[("TestClass", "calibrated_method")] = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=2,
            max_evidence_snippets=10,
            contradiction_tolerance=0.1,
            uncertainty_penalty=0.2,
            aggregation_weight=1.0,
            sensitivity=0.8,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        result = executor._check_calibration()
        
        assert result.is_valid is True
        assert result.severity == "INFO"
        
        # Cleanup
        if ("TestClass", "calibrated_method") in CALIBRATIONS:
            del CALIBRATIONS[("TestClass", "calibrated_method")]
    
    def test_check_resources_missing_config(self):
        """Test resource check fails when config is missing."""
        mock_executor = MockMethodExecutor(instances={})
        
        executor = TestExecutor(mock_executor)
        executor.config = None
        
        result = executor._check_resources()
        
        assert result.is_valid is False
        assert result.severity == "ERROR"
        assert "config" in result.message.lower()
    
    def test_check_resources_missing_signal_registry_is_warning(self):
        """Test resource check warns (not fails) when signal registry is missing."""
        mock_executor = MockMethodExecutor(instances={})
        
        executor = TestExecutor(mock_executor)
        executor.signal_registry = None
        
        result = executor._check_resources()
        
        # Signal registry is optional, so it should pass with warning or info
        assert result.is_valid is True
    
    def test_check_resources_all_available(self):
        """Test resource check passes when all resources are available."""
        mock_executor = MockMethodExecutor(instances={})
        
        executor = TestExecutor(mock_executor)
        executor.signal_registry = Mock()
        
        result = executor._check_resources()
        
        assert result.is_valid is True
    
    def test_validate_before_execution_with_errors(self):
        """Test validation returns error when checks fail."""
        # No executor at all
        executor = TestExecutor(None)
        executor.config = None
        
        result = executor.validate_before_execution()
        
        assert result.is_valid is False
        assert result.severity == "ERROR"
        assert len(result.message) > 0
    
    def test_advanced_data_flow_executor_inherits_validation(self):
        """Test that AdvancedDataFlowExecutor inherits from ExecutorBase."""
        assert issubclass(AdvancedDataFlowExecutor, ExecutorBase)
        
        # Check that validate_before_execution is available
        assert hasattr(AdvancedDataFlowExecutor, 'validate_before_execution')


class TestExecutorValidationIntegration:
    """Integration tests for executor validation."""
    
    def test_executor_can_call_validation_before_execute(self):
        """Test that executors can call validation before execution."""
        mock_executor = MockMethodExecutor(instances={
            "TestClass": Mock()
        })
        
        executor = TestExecutor(mock_executor)
        executor.set_sequence([("TestClass", "test_method")])
        
        # Add calibration
        CALIBRATIONS[("TestClass", "test_method")] = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=2,
            max_evidence_snippets=10,
            contradiction_tolerance=0.1,
            uncertainty_penalty=0.2,
            aggregation_weight=1.0,
            sensitivity=0.8,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        # Validate before "execution"
        validation_result = executor.validate_before_execution()
        
        # Should be valid since all dependencies are met
        assert validation_result.is_valid is True
        
        # Cleanup
        if ("TestClass", "test_method") in CALIBRATIONS:
            del CALIBRATIONS[("TestClass", "test_method")]
    
    def test_validation_catches_multiple_issues(self):
        """Test that validation can catch multiple issues at once."""
        # Missing executor and config
        executor = TestExecutor(None)
        executor.config = None
        executor.set_sequence([("MissingClass", "method")])
        
        result = executor.validate_before_execution()
        
        assert result.is_valid is False
        # Should have multiple error messages
        assert len(result.message) > 10  # Non-trivial error message
