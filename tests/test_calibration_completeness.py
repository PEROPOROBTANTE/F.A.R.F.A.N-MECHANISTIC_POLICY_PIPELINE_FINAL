"""Test calibration completeness - ensure all methods have explicit calibration.

This test suite enforces the requirement that every method referenced by the
pipeline must have an explicit calibration entry. No silent defaults allowed.

Per the refactoring requirements:
- Every method must have explicit calibration indexed by method_fqn
- Missing calibrations must raise MissingCalibrationError
- No generic fallback calibrations permitted

OBSOLETE: This test uses the old calibration_registry API (CALIBRATIONS dict,
get_calibration_hash, etc.) which was refactored to use resolve_calibration().
New calibration tests are in tests/calibration/ subdirectory.
See tests/calibration/test_gap0_complete.py for current implementation.
"""

import pytest

pytestmark = pytest.mark.skip(reason="obsolete - calibration_registry API refactored, see tests/calibration/")

# Old imports (no longer valid):
# from saaaaaa.core.orchestrator.calibration_registry import (
#     CALIBRATIONS,
#     MissingCalibrationError,
#     resolve_calibration,
#     get_calibration_hash,
#     CALIBRATION_VERSION,
# )


class TestCalibrationCompleteness:
    """Test that all methods have explicit calibrations."""
    
    def test_calibration_version_exists(self):
        """Verify calibration version is defined."""
        assert CALIBRATION_VERSION is not None
        assert isinstance(CALIBRATION_VERSION, str)
        assert len(CALIBRATION_VERSION) > 0
    
    def test_calibration_hash_deterministic(self):
        """Verify calibration hash is deterministic."""
        hash1 = get_calibration_hash()
        hash2 = get_calibration_hash()
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex digest
    
    def test_calibrations_not_empty(self):
        """Verify calibration registry is not empty."""
        assert len(CALIBRATIONS) > 0
        # We know we have 166 calibrations from the generated registry
        assert len(CALIBRATIONS) >= 100
    
    def test_all_calibrations_have_valid_keys(self):
        """Verify all calibrations use proper (ClassName, method_name) keys."""
        for key in CALIBRATIONS.keys():
            assert isinstance(key, tuple)
            assert len(key) == 2
            class_name, method_name = key
            assert isinstance(class_name, str)
            assert isinstance(method_name, str)
            assert len(class_name) > 0
            assert len(method_name) > 0
    
    def test_all_calibrations_have_valid_values(self):
        """Verify all calibration values are MethodCalibration instances."""
        from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
        
        for key, calib in CALIBRATIONS.items():
            assert isinstance(calib, MethodCalibration), f"Invalid calibration for {key}"
            
            # Verify required fields
            assert 0.0 <= calib.score_min <= 1.0
            assert 0.0 <= calib.score_max <= 1.0
            assert calib.score_min <= calib.score_max
            assert calib.min_evidence_snippets >= 1
            assert calib.max_evidence_snippets >= calib.min_evidence_snippets
            assert 0.0 <= calib.contradiction_tolerance <= 1.0
            assert 0.0 <= calib.uncertainty_penalty <= 2.0
            assert calib.aggregation_weight >= 0.1
            assert 0.0 <= calib.sensitivity <= 1.0
    
    def test_resolve_calibration_strict_mode(self):
        """Test that strict mode raises error for missing calibrations."""
        # Should raise for non-existent method
        with pytest.raises(MissingCalibrationError) as exc_info:
            resolve_calibration("NonExistentClass", "nonexistent_method", strict=True)
        
        assert "NonExistentClass.nonexistent_method" in str(exc_info.value)
        assert "Missing calibration" in str(exc_info.value)
    
    def test_resolve_calibration_non_strict_mode(self):
        """Test that non-strict mode returns None for missing calibrations."""
        calib = resolve_calibration("NonExistentClass", "nonexistent_method", strict=False)
        assert calib is None
    
    def test_resolve_calibration_success(self):
        """Test successful calibration resolution."""
        # Use a known calibration from registry
        calib = resolve_calibration("BayesianEvidenceScorer", "compute_evidence_score", strict=True)
        
        assert calib is not None
        assert calib.score_min == 0.0
        assert calib.score_max == 1.0
        assert calib.min_evidence_snippets >= 1
    
    def test_no_default_like_calibrations_without_flag(self):
        """Verify that default-like calibrations have safe_default_allowed flag."""
        from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
        
        for key, calib in CALIBRATIONS.items():
            if calib.is_default_like():
                # If a calibration is "default-like", it should explicitly allow it
                # Currently none are expected to be default-like in strict regime
                # This test documents the expectation
                assert not calib.is_default_like(), (
                    f"Calibration for {key} appears default-like. "
                    f"If intentional, set safe_default_allowed=True"
                )
    
    def test_missing_calibration_error_attributes(self):
        """Test MissingCalibrationError has proper attributes."""
        error = MissingCalibrationError("TestClass.test_method", {"question_id": "D1Q1"})
        
        assert error.method_fqn == "TestClass.test_method"
        assert error.context == {"question_id": "D1Q1"}
        assert "TestClass.test_method" in str(error)
        assert "D1Q1" in str(error)


class TestCalibrationIndexing:
    """Test calibration indexing by different dimensions."""
    
    def test_calibrations_indexed_by_class_and_method(self):
        """Verify calibrations are indexed by (class_name, method_name)."""
        # Get a sample calibration
        sample_key = list(CALIBRATIONS.keys())[0]
        assert isinstance(sample_key, tuple)
        assert len(sample_key) == 2
    
    def test_method_fqn_construction(self):
        """Test that method FQN is properly constructed."""
        class_name = "TestClass"
        method_name = "test_method"
        expected_fqn = "TestClass.test_method"
        
        # MissingCalibrationError constructs FQN
        error = MissingCalibrationError(expected_fqn)
        assert error.method_fqn == expected_fqn


class TestCalibrationMetadata:
    """Test calibration metadata and tracking."""
    
    def test_calibration_has_document_type_field(self):
        """Verify MethodCalibration dataclass has document_type field."""
        from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
        
        # Create a calibration with document_type
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
            safe_default_allowed=False,
            document_type="plan_desarrollo_municipal"
        )
        
        assert calib.document_type == "plan_desarrollo_municipal"
    
    def test_calibration_safe_default_flag(self):
        """Verify safe_default_allowed flag is present."""
        from saaaaaa.core.orchestrator.calibration_registry import MethodCalibration
        
        calib = MethodCalibration(
            score_min=0.0,
            score_max=1.0,
            min_evidence_snippets=1,
            max_evidence_snippets=5,
            contradiction_tolerance=0.5,
            uncertainty_penalty=0.5,
            aggregation_weight=1.0,
            sensitivity=0.5,
            requires_numeric_support=False,
            requires_temporal_support=False,
            requires_source_provenance=False,
            safe_default_allowed=True  # Explicitly allowed
        )
        
        assert calib.safe_default_allowed is True


# FIXME(CALIBRATION): Add tests for specific question/method mappings
# Once question catalog is integrated, add tests to verify:
# - All questions have method assignments
# - All assigned methods have calibrations
# - Context-aware calibration resolution works for each question
