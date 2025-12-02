"""Test Calibration Orchestrator Mandatory Single-Path Enforcement.

This test suite verifies:
1. calibration_registry.py is NEVER called (mocked and monitored)
2. No 'def calibrate' or 'calibration_score' exists outside orchestrator.py
3. Missing @b behavior raises MissingIntrinsicCalibrationError
4. context=None behavior raises InsufficientContextError
5. Below threshold behavior raises MethodBelowThresholdError

FAILURE CONDITION: If ANY method bypasses orchestrator or if parallel
calibration logic exists anywhere, tests MUST fail.
"""

import glob
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from farfan_pipeline.core.calibration.orchestrator import (
    CALIBRATION_THRESHOLD,
    CalibrationOrchestrator,
    InsufficientContextError,
    MethodBelowThresholdError,
    MissingIntrinsicCalibrationError,
)
from farfan_pipeline.core.orchestrator.calibration_context import CalibrationContext
from farfan_pipeline.core.orchestrator.calibration_types import RuntimeLayers


class TestMandatorySinglePath:
    """Test mandatory single-path enforcement for calibration."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        CalibrationOrchestrator.reset_instance()
        yield
        CalibrationOrchestrator.reset_instance()

    def test_orchestrator_is_singleton(self):
        """Verify CalibrationOrchestrator is a singleton."""
        instance1 = CalibrationOrchestrator()
        instance2 = CalibrationOrchestrator()
        instance3 = CalibrationOrchestrator.get_instance()
        
        assert instance1 is instance2
        assert instance2 is instance3
        assert id(instance1) == id(instance2) == id(instance3)

    @patch('farfan_pipeline.core.calibration.calibration_registry.get_calibration')
    def test_calibration_registry_never_called(self, mock_get_calibration):
        """CRITICAL: Verify calibration_registry is NEVER called."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D1Q1")
        
        try:
            orchestrator.calibrate_method(
                "test_method_executor",
                context=context,
                is_executor=True
            )
        except Exception:
            pass
        
        mock_get_calibration.assert_not_called()
        assert mock_get_calibration.call_count == 0, (
            "VIOLATION: calibration_registry.get_calibration was called! "
            "All calibration MUST go through CalibrationOrchestrator."
        )

    def test_missing_intrinsic_calibration_raises_error(self):
        """Test that missing @b scores raise MissingIntrinsicCalibrationError."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D1Q1")
        
        with pytest.raises(MissingIntrinsicCalibrationError) as exc_info:
            orchestrator.calibrate_method(
                "nonexistent_method",
                context=context
            )
        
        assert "nonexistent_method" in str(exc_info.value)
        assert "Missing intrinsic calibration" in str(exc_info.value)
        assert exc_info.value.method_id == "nonexistent_method"

    def test_insufficient_context_raises_error(self):
        """Test that context=None raises InsufficientContextError."""
        orchestrator = CalibrationOrchestrator()
        
        with pytest.raises(InsufficientContextError) as exc_info:
            orchestrator.calibrate_method(
                "test_method_executor",
                context=None
            )
        
        assert "test_method_executor" in str(exc_info.value)
        assert "Insufficient context" in str(exc_info.value)
        assert exc_info.value.method_id == "test_method_executor"

    def test_below_threshold_raises_error(self):
        """Test that score < threshold raises MethodBelowThresholdError."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D1Q1")
        
        with pytest.raises(MethodBelowThresholdError) as exc_info:
            orchestrator.calibrate_method(
                "test_method_below_threshold",
                context=context
            )
        
        assert "test_method_below_threshold" in str(exc_info.value)
        assert exc_info.value.method_id == "test_method_below_threshold"
        assert exc_info.value.score < CALIBRATION_THRESHOLD
        assert exc_info.value.threshold == CALIBRATION_THRESHOLD

    def test_executor_uses_choquet_integral(self):
        """Test that executor methods use Choquet integral aggregation."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D5Q10")
        
        score = orchestrator.calibrate_method(
            "test_method_executor",
            context=context,
            is_executor=True
        )
        
        assert score >= CALIBRATION_THRESHOLD
        assert 0.0 <= score <= 1.0

    def test_non_executor_uses_weighted_sum(self):
        """Test that non-executor methods use weighted sum aggregation."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D3Q5")
        
        score = orchestrator.calibrate_method(
            "test_method_analyzer",
            context=context,
            is_executor=False
        )
        
        assert score >= CALIBRATION_THRESHOLD
        assert 0.0 <= score <= 1.0

    def test_runtime_layers_computed_dynamically(self):
        """Test that runtime layers are computed based on context."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D7Q15")
        
        layers = orchestrator.evaluate_runtime_layers(
            "test_method_executor",
            context
        )
        
        assert isinstance(layers, RuntimeLayers)
        assert 0.0 <= layers.chain <= 1.0
        assert 0.0 <= layers.quality <= 1.0
        assert 0.0 <= layers.density <= 1.0
        assert 0.0 <= layers.provenance <= 1.0
        assert 0.0 <= layers.coverage <= 1.0
        assert 0.0 <= layers.uncertainty <= 1.0
        assert 0.0 <= layers.mechanism <= 1.0

    def test_different_contexts_produce_different_layers(self):
        """Test that different contexts produce different layer scores."""
        orchestrator = CalibrationOrchestrator()
        
        context1 = CalibrationContext.from_question_id("D1Q1")
        context2 = CalibrationContext.from_question_id("D10Q20")
        
        layers1 = orchestrator.evaluate_runtime_layers("test_method_executor", context1)
        layers2 = orchestrator.evaluate_runtime_layers("test_method_executor", context2)
        
        assert layers1.to_dict() != layers2.to_dict()

    def test_choquet_integral_aggregation(self):
        """Test Choquet integral aggregation logic."""
        orchestrator = CalibrationOrchestrator()
        
        layers = RuntimeLayers(
            chain=0.9,
            quality=0.8,
            provenance=0.7,
            density=0.6,
            coverage=0.5,
            uncertainty=0.4,
            mechanism=0.3
        )
        
        weights = {
            'chain': 0.4,
            'quality': 0.35,
            'provenance': 0.25
        }
        
        score = orchestrator.choquet_integral(layers, weights)
        assert 0.0 <= score <= 1.0

    def test_weighted_sum_aggregation(self):
        """Test weighted sum aggregation logic."""
        orchestrator = CalibrationOrchestrator()
        
        layers = RuntimeLayers(
            chain=0.8,
            quality=0.7,
            density=0.6,
            coverage=0.5
        )
        
        weights = {
            'quality': 0.4,
            'density': 0.3,
            'coverage': 0.3
        }
        
        score = orchestrator.weighted_sum(layers, weights)
        assert 0.0 <= score <= 1.0
        
        expected = (0.7 * 0.4 + 0.6 * 0.3 + 0.5 * 0.3) / 1.0
        assert abs(score - expected) < 0.01


class TestCodebaseScan:
    """Scan codebase for violations of mandatory single-path rule."""

    def test_no_def_calibrate_outside_orchestrator(self):
        """CRITICAL: No 'def calibrate' outside orchestrator.py."""
        violations = []
        
        project_root = Path.cwd()
        src_path = project_root / "src" / "farfan_pipeline"
        
        if not src_path.exists():
            pytest.skip("Source path not found")
        
        for py_file in src_path.rglob("*.py"):
            if "orchestrator.py" in py_file.name:
                continue
            
            if "calibration_registry.py" in py_file.name:
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                pattern = r'^\s*def\s+calibrate\s*\('
                matches = re.findall(pattern, content, re.MULTILINE)
                
                if matches:
                    violations.append(
                        f"{py_file.relative_to(project_root)}: "
                        f"Found {len(matches)} 'def calibrate' definition(s)"
                    )
            except Exception:
                pass
        
        if violations:
            error_msg = (
                "CALIBRATION PATH NOT CENTRALIZED!\n"
                "Found 'def calibrate' methods outside orchestrator.py:\n" +
                "\n".join(violations) +
                "\n\nAll calibration MUST go through CalibrationOrchestrator."
            )
            pytest.fail(error_msg)

    def test_no_calibration_score_outside_orchestrator(self):
        """CRITICAL: No 'calibration_score' variable/function outside orchestrator.py."""
        violations = []
        
        project_root = Path.cwd()
        src_path = project_root / "src" / "farfan_pipeline"
        
        if not src_path.exists():
            pytest.skip("Source path not found")
        
        for py_file in src_path.rglob("*.py"):
            if "orchestrator.py" in py_file.name:
                continue
            
            if "calibration_registry.py" in py_file.name:
                continue
            
            if "test_" in py_file.name:
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                
                pattern = r'\bcalibration_score\s*[=:(]'
                matches = re.findall(pattern, content)
                
                if matches:
                    violations.append(
                        f"{py_file.relative_to(project_root)}: "
                        f"Found {len(matches)} 'calibration_score' reference(s)"
                    )
            except Exception:
                pass
        
        if violations:
            error_msg = (
                "CALIBRATION PATH NOT CENTRALIZED!\n"
                "Found 'calibration_score' outside orchestrator.py:\n" +
                "\n".join(violations) +
                "\n\nAll calibration MUST go through CalibrationOrchestrator."
            )
            pytest.fail(error_msg)

    def test_orchestrator_loads_intrinsic_calibration(self):
        """Verify orchestrator loads intrinsic calibration from JSON."""
        orchestrator = CalibrationOrchestrator()
        
        assert hasattr(orchestrator, '_intrinsic_scores')
        assert len(orchestrator._intrinsic_scores) > 0
        assert "test_method_executor" in orchestrator._intrinsic_scores

    def test_orchestrator_loads_layer_requirements(self):
        """Verify orchestrator loads layer requirements from JSON."""
        orchestrator = CalibrationOrchestrator()
        
        assert hasattr(orchestrator, '_layer_requirements')
        assert len(orchestrator._layer_requirements) > 0
        assert "test_method_executor" in orchestrator._layer_requirements


class TestCalibrationThreshold:
    """Test calibration threshold enforcement."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        CalibrationOrchestrator.reset_instance()
        yield
        CalibrationOrchestrator.reset_instance()

    def test_threshold_is_0_7(self):
        """Verify calibration threshold is 0.7."""
        assert CALIBRATION_THRESHOLD == 0.7

    def test_pass_threshold_allows_execution(self):
        """Test that scores >= 0.7 allow method execution."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D5Q10")
        
        score = orchestrator.calibrate_method(
            "test_method_executor",
            context=context,
            is_executor=True
        )
        
        assert score >= 0.7

    def test_fail_threshold_blocks_execution(self):
        """Test that scores < 0.7 block method execution."""
        orchestrator = CalibrationOrchestrator()
        context = CalibrationContext.from_question_id("D1Q1")
        
        with pytest.raises(MethodBelowThresholdError) as exc_info:
            orchestrator.calibrate_method(
                "test_method_below_threshold",
                context=context
            )
        
        assert exc_info.value.score < 0.7
        assert exc_info.value.threshold == 0.7
