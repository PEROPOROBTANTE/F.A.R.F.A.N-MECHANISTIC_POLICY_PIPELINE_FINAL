"""Test schema gates and execution graph validation (PROMPT_SCHEMA_GATES_ENFORCER and PROMPT_NONEMPTY_EXECUTION_GRAPH_ENFORCER)."""

import pytest

from saaaaaa.core.orchestrator.core import Orchestrator, validate_phase_definitions
from saaaaaa.core.orchestrator.factory import validate_questionnaire_structure


class TestQuestionnaireSchemaGate:
    """Test PROMPT_SCHEMA_GATES_ENFORCER for questionnaire validation."""
    
    def test_valid_questionnaire_passes(self):
        """Valid questionnaire should pass validation."""
        valid_data = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {
                        "question_id": "Q1",
                        "question_global": 1,
                        "base_slot": "D1-Q1"
                    }
                ]
            }
        }
        
        # Should not raise
        validate_questionnaire_structure(valid_data)
    
    def test_empty_micro_questions_rejected(self):
        """Empty micro_questions list should be rejected."""
        invalid_data = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": []  # Empty list
            }
        }
        
        with pytest.raises(ValueError, match="must have at least 1 micro question"):
            validate_questionnaire_structure(invalid_data)
    
    def test_missing_version_rejected(self):
        """Missing 'version' key should be rejected."""
        invalid_data = {
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [{"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"}]
            }
        }
        
        with pytest.raises(ValueError, match="Questionnaire missing keys"):
            validate_questionnaire_structure(invalid_data)
    
    def test_duplicate_question_id_rejected(self):
        """Duplicate question_id should be rejected."""
        invalid_data = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"},
                    {"question_id": "Q1", "question_global": 2, "base_slot": "D1-Q2"}  # Duplicate ID
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Duplicate question_id"):
            validate_questionnaire_structure(invalid_data)
    
    def test_duplicate_question_global_rejected(self):
        """Duplicate question_global should be rejected."""
        invalid_data = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"},
                    {"question_id": "Q2", "question_global": 1, "base_slot": "D1-Q2"}  # Duplicate global
                ]
            }
        }
        
        with pytest.raises(ValueError, match="Duplicate question_global"):
            validate_questionnaire_structure(invalid_data)
    
    def test_invalid_question_id_type_rejected(self):
        """Non-string question_id should be rejected."""
        invalid_data = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": 123, "question_global": 1, "base_slot": "D1-Q1"}  # Should be string
                ]
            }
        }
        
        with pytest.raises(ValueError, match="question_id must be string"):
            validate_questionnaire_structure(invalid_data)


class TestPhaseSchemaGate:
    """Test PROMPT_SCHEMA_GATES_ENFORCER for phase validation."""
    
    def test_valid_phases_pass(self):
        """Valid phase definitions should pass."""
        valid_phases = [
            (0, "sync", "_load_configuration", "Phase 0"),
            (1, "async", "_ingest_document", "Phase 1"),
        ]
        
        # Should not raise
        validate_phase_definitions(valid_phases, Orchestrator)
    
    def test_empty_phases_rejected(self):
        """Empty FASES should be rejected."""
        with pytest.raises(RuntimeError, match="FASES cannot be empty"):
            validate_phase_definitions([], Orchestrator)
    
    def test_non_contiguous_phase_ids_rejected(self):
        """Non-contiguous phase IDs should be rejected."""
        invalid_phases = [
            (0, "sync", "_load_configuration", "Phase 0"),
            (2, "sync", "_ingest_document", "Phase 2"),  # Skipped 1
        ]
        
        with pytest.raises(RuntimeError, match="must be contiguous"):
            validate_phase_definitions(invalid_phases, Orchestrator)
    
    def test_duplicate_phase_id_rejected(self):
        """Duplicate phase IDs should be rejected."""
        invalid_phases = [
            (0, "sync", "_load_configuration", "Phase 0"),
            (0, "async", "_ingest_document", "Phase 0 duplicate"),  # Duplicate
        ]
        
        with pytest.raises(RuntimeError, match="Duplicate phase ID"):
            validate_phase_definitions(invalid_phases, Orchestrator)
    
    def test_invalid_mode_rejected(self):
        """Invalid mode should be rejected."""
        invalid_phases = [
            (0, "invalid_mode", "_load_configuration", "Phase 0"),
        ]
        
        with pytest.raises(RuntimeError, match="invalid mode"):
            validate_phase_definitions(invalid_phases, Orchestrator)
    
    def test_nonexistent_handler_rejected(self):
        """Non-existent handler method should be rejected."""
        invalid_phases = [
            (0, "sync", "_nonexistent_method", "Phase 0"),
        ]
        
        with pytest.raises(RuntimeError, match="does not exist"):
            validate_phase_definitions(invalid_phases, Orchestrator)
    
    def test_phases_not_starting_from_zero_rejected(self):
        """Phase IDs not starting from 0 should be rejected."""
        invalid_phases = [
            (1, "sync", "_load_configuration", "Phase 1"),
            (2, "sync", "_ingest_document", "Phase 2"),
        ]
        
        with pytest.raises(RuntimeError, match="must start from 0"):
            validate_phase_definitions(invalid_phases, Orchestrator)


class TestExecutionGraphGate:
    """Test PROMPT_NONEMPTY_EXECUTION_GRAPH_ENFORCER."""
    
    def test_empty_catalog_rejected(self):
        """Empty catalog should be rejected."""
        valid_monolith = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"}
                ]
            }
        }
        
        # Empty dict catalog
        with pytest.raises(RuntimeError, match="Method catalog is empty"):
            Orchestrator(monolith=valid_monolith, catalog={})
    
    def test_catalog_with_empty_methods_rejected(self):
        """Catalog with empty 'methods' attribute should be rejected.
        
        This test validates that an empty methods list is caught during catalog
        validation, which happens before MethodExecutor initialization, so it
        doesn't require full dependencies.
        """
        valid_monolith = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"}
                ]
            }
        }
        
        # Catalog with empty methods - this triggers before MethodExecutor so should work
        with pytest.raises(RuntimeError, match="catalog.methods is empty"):
            Orchestrator(monolith=valid_monolith, catalog={"methods": []})
    
    def test_invalid_questionnaire_in_init_rejected(self):
        """Invalid questionnaire should be rejected during __init__."""
        invalid_monolith = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": []  # Empty - invalid
            }
        }
        
        with pytest.raises(RuntimeError, match="Questionnaire structure validation failed"):
            Orchestrator(monolith=invalid_monolith)


class TestNoLimitedMode:
    """Test that no 'limited mode' is allowed with broken schemas."""
    
    def test_validation_logic_prevents_limited_mode(self):
        """Test that validation logic is in place to prevent limited mode.
        
        When MethodExecutor.instances is empty (e.g., due to import failures),
        the Orchestrator should raise RuntimeError instead of continuing in
        "limited mode".
        
        Note: This test validates the enforcement exists but doesn't test the
        actual runtime behavior which requires missing dependencies.
        """
        # The validation is in Orchestrator.__init__ after MethodExecutor creation
        # It checks: if not self.executor.instances: raise RuntimeError(...)
        
        # We can verify the check exists by reading the source
        import inspect
        source = inspect.getsource(Orchestrator.__init__)
        
        # Check that the validation is present
        assert "if not self.executor.instances:" in source
        assert "RuntimeError" in source
        assert "MethodExecutor.instances is empty" in source
    
    def test_catalog_validation_prevents_limited_mode(self):
        """Empty catalog triggers hard failure, not limited mode."""
        valid_monolith = {
            "version": "1.0.0",
            "schema_version": "1.0",
            "blocks": {
                "micro_questions": [
                    {"question_id": "Q1", "question_global": 1, "base_slot": "D1-Q1"}
                ]
            }
        }
        
        # Empty catalog should raise RuntimeError
        with pytest.raises(RuntimeError, match="Method catalog is empty"):
            Orchestrator(monolith=valid_monolith, catalog={})


class TestCanonicalQuestionnaireIntegration:
    """Test modern CanonicalQuestionnaire pattern (preferred over monolith dict).

    These tests demonstrate the recommended initialization pattern introduced
    in the factory pattern refactoring (commit 3cff800).
    """

    def test_orchestrator_with_canonical_questionnaire(self):
        """Orchestrator should accept CanonicalQuestionnaire instances."""
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
        from saaaaaa.core.orchestrator.factory import build_processor

        # Load canonical questionnaire (type-safe, immutable, hash-verified)
        canonical = load_questionnaire()

        # Build processor for catalog
        processor = build_processor()

        # Initialize with canonical questionnaire (preferred pattern)
        orchestrator = Orchestrator(
            questionnaire=canonical,
            catalog=processor.factory.catalog
        )

        # Verify initialization succeeded
        assert orchestrator is not None
        assert hasattr(orchestrator, 'executor')
        assert hasattr(orchestrator, 'micro_questions')

    def test_canonical_questionnaire_is_immutable(self):
        """CanonicalQuestionnaire data should be immutable (MappingProxyType)."""
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire
        from types import MappingProxyType

        canonical = load_questionnaire()

        # Data should be wrapped in MappingProxyType for immutability
        assert isinstance(canonical.data, MappingProxyType)

        # Verify cannot modify the data
        with pytest.raises(TypeError):
            canonical.data['version'] = 'hacked'

    def test_canonical_questionnaire_has_verification_data(self):
        """CanonicalQuestionnaire should include hash and verification metadata."""
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire

        canonical = load_questionnaire()

        # Should have hash verification
        assert hasattr(canonical, 'sha256')
        assert isinstance(canonical.sha256, str)
        assert len(canonical.sha256) == 64  # SHA256 hex length

        # Should have question counts
        assert hasattr(canonical, 'total_question_count')
        assert canonical.total_question_count > 0

        # Should have file size
        assert hasattr(canonical, 'file_size_bytes')
        assert canonical.file_size_bytes > 0

    def test_factory_pattern_produces_valid_processor(self):
        """build_processor() should produce valid processor bundle."""
        from saaaaaa.core.orchestrator.factory import build_processor

        processor = build_processor()

        # Verify processor structure
        assert hasattr(processor, 'factory')
        assert hasattr(processor.factory, 'catalog')
        assert processor.factory.catalog is not None
        assert 'methods' in processor.factory.catalog
        assert len(processor.factory.catalog['methods']) > 0

    def test_orchestrator_rejects_both_monolith_and_questionnaire(self):
        """Orchestrator should reject if both monolith and questionnaire provided."""
        from saaaaaa.core.orchestrator.questionnaire import load_questionnaire

        canonical = load_questionnaire()
        dict_monolith = dict(canonical.data)

        # Cannot provide both - should raise ValueError
        with pytest.raises(ValueError, match="Cannot specify both 'questionnaire' and 'monolith'"):
            Orchestrator(
                monolith=dict_monolith,
                questionnaire=canonical
            )
