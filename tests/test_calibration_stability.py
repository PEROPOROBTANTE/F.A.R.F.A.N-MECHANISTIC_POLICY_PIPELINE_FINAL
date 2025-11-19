"""Test calibration stability - verify deterministic execution.

This test suite enforces that:
- Same calibration + same seed → same results
- Calibration changes → detectable via hash
- ExecutorConfig drives deterministic behavior

Per the refactoring requirements:
- Calibrations must be versioned and hashed
- Same config + seed must produce deterministic results
- Config changes must be traceable via hash

OBSOLETE: This test uses old calibration_registry API (get_calibration_hash,
CALIBRATION_VERSION) which no longer exist. See tests/calibration/ for current tests.
"""

import pytest

pytestmark = pytest.mark.skip(reason="obsolete - calibration_registry API refactored, see tests/calibration/")

# Old imports (no longer valid):
# from saaaaaa.core.orchestrator.calibration_registry import (
#     get_calibration_hash,
#     CALIBRATION_VERSION,
#     resolve_calibration,
# )
# from saaaaaa.core.orchestrator.executor_config import ExecutorConfig


class TestCalibrationVersioning:
    """Test calibration versioning and hashing."""
    
    def test_calibration_version_stable(self):
        """Verify calibration version is stable across calls."""
        version1 = CALIBRATION_VERSION
        version2 = CALIBRATION_VERSION
        
        assert version1 == version2
        assert isinstance(version1, str)
    
    def test_calibration_hash_stable(self):
        """Verify calibration hash is stable across calls."""
        hash1 = get_calibration_hash()
        hash2 = get_calibration_hash()
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA256
    
    def test_calibration_hash_changes_with_data(self):
        """Verify hash would change if calibrations change.
        
        This is a documentation test - we verify hash is computed from
        calibration data, not just a constant.
        """
        hash_value = get_calibration_hash()
        
        # Hash should be non-trivial
        assert hash_value != "0" * 64
        assert hash_value != "f" * 64
        
        # Hash should be deterministic hex
        assert all(c in "0123456789abcdef" for c in hash_value)


class TestExecutorConfigDeterminism:
    """Test ExecutorConfig produces deterministic behavior."""
    
    def test_executor_config_hash_deterministic(self):
        """Verify ExecutorConfig.compute_hash() is deterministic."""
        config1 = ExecutorConfig(
            max_tokens=2048,
            temperature=0.0,
            timeout_s=30.0,
            retry=2,
            seed=42
        )
        
        config2 = ExecutorConfig(
            max_tokens=2048,
            temperature=0.0,
            timeout_s=30.0,
            retry=2,
            seed=42
        )
        
        hash1 = config1.compute_hash()
        hash2 = config2.compute_hash()
        
        assert hash1 == hash2
    
    def test_executor_config_hash_changes_with_params(self):
        """Verify ExecutorConfig hash changes when parameters change."""
        config1 = ExecutorConfig(seed=42)
        config2 = ExecutorConfig(seed=43)
        
        hash1 = config1.compute_hash()
        hash2 = config2.compute_hash()
        
        assert hash1 != hash2
    
    def test_executor_config_zero_temperature_deterministic(self):
        """Verify temperature=0.0 is documented as deterministic."""
        config = ExecutorConfig(temperature=0.0, seed=42)
        
        # temperature=0.0 should be deterministic per docstring
        assert config.temperature == 0.0
        
        # Seed should also be set for full determinism
        assert config.seed == 42
    
    def test_executor_config_seed_range(self):
        """Verify seed is in valid range for reproducibility."""
        # Valid seed
        config = ExecutorConfig(seed=42)
        assert 0 <= config.seed <= 2147483647
        
        # Boundary values
        config_min = ExecutorConfig(seed=0)
        assert config_min.seed == 0
        
        config_max = ExecutorConfig(seed=2147483647)
        assert config_max.seed == 2147483647
        
        # Out of range should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            ExecutorConfig(seed=-1)
        
        with pytest.raises(Exception):  # Pydantic validation error
            ExecutorConfig(seed=2147483648)


class TestCalibrationStability:
    """Test that calibration resolution is stable."""
    
    def test_resolve_same_calibration_multiple_times(self):
        """Verify resolving same calibration yields identical results."""
        calib1 = resolve_calibration("BayesianEvidenceScorer", "compute_evidence_score", strict=False)
        calib2 = resolve_calibration("BayesianEvidenceScorer", "compute_evidence_score", strict=False)
        
        if calib1 is not None:
            assert calib1 == calib2
            # Verify immutability
            assert id(calib1) == id(calib2)  # Should be same frozen object
    
    def test_calibration_immutability(self):
        """Verify MethodCalibration is immutable (frozen dataclass)."""
        from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
        
        calib = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=3,
            max_evidence_snippets=10,
            contradiction_tolerance=0.1,
            uncertainty_penalty=0.2,
            aggregation_weight=1.0,
            sensitivity=0.8,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=True,
        )
        
        # Frozen dataclass should not allow mutation
        with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
            calib.score_min = 0.5  # type: ignore


class TestCalibrationContextDeterminism:
    """Test context-aware calibration is deterministic."""
    
    def test_context_resolution_deterministic(self):
        """Verify context-aware calibration resolution is deterministic."""
        from saaaaaa.core.orchestrator.calibration_registry import resolve_calibration_with_context
        
        # Same inputs should yield same calibration
        calib1 = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
            policy_area="fiscal",
            unit_of_analysis="baseline_gap",
            method_position=0,
            total_methods=3,
        )
        
        calib2 = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
            policy_area="fiscal",
            unit_of_analysis="baseline_gap",
            method_position=0,
            total_methods=3,
        )
        
        if calib1 is not None:
            assert calib1 == calib2
    
    def test_context_changes_yield_different_calibrations(self):
        """Verify different contexts yield different calibrations."""
        from saaaaaa.core.orchestrator.calibration_registry import resolve_calibration_with_context
        
        # D1 vs D9 should have different modifiers
        calib_d1 = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D1Q1",
        )
        
        calib_d9 = resolve_calibration_with_context(
            "BayesianEvidenceScorer",
            "compute_evidence_score",
            question_id="D9Q1",
        )
        
        if calib_d1 is not None and calib_d9 is not None:
            # D9 (financial) should have stricter requirements than D1
            # This is based on dimension modifiers in calibration_context.py
            assert calib_d9.min_evidence_snippets >= calib_d1.min_evidence_snippets


class TestCalibrationDocumentation:
    """Test that calibrations are properly documented."""
    
    def test_calibration_context_has_document_type(self):
        """Verify CalibrationContext includes document_type dimension."""
        from saaaaaa.core.orchestrator.calibration_context import CalibrationContext, DocumentType
        
        context = CalibrationContext(
            question_id="D1Q1",
            dimension=1,
            question_num=1,
            document_type=DocumentType.PLAN_DESARROLLO_MUNICIPAL
        )
        
        assert context.document_type == DocumentType.PLAN_DESARROLLO_MUNICIPAL
    
    def test_document_type_enum_exists(self):
        """Verify DocumentType enum is defined."""
        from saaaaaa.core.orchestrator.calibration_context import DocumentType
        
        # Verify expected document types
        assert hasattr(DocumentType, "PLAN_DESARROLLO_MUNICIPAL")
        assert hasattr(DocumentType, "POLITICA_PUBLICA")
        assert hasattr(DocumentType, "UNKNOWN")
    
    def test_document_type_modifiers_exist(self):
        """Verify document type modifiers are defined."""
        from saaaaaa.core.orchestrator import calibration_context
        
        # Internal variable should exist
        assert hasattr(calibration_context, "_DOCUMENT_TYPE_MODIFIERS")
        
        modifiers = calibration_context._DOCUMENT_TYPE_MODIFIERS
        assert len(modifiers) > 0


# FIXME(CALIBRATION): Add integration tests once pipeline is wired
# Test that actual pipeline execution:
# - Uses ExecutorConfig for all runtime decisions
# - Produces same results with same config + seed
# - Exposes calibration_hash in artifacts
# - Blocks execution when calibration missing
