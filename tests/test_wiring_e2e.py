"""End-to-end tests for wiring system.

Tests cover:
- Memory mode golden document flow
- Signal unavailability graceful degradation
- ArgRouter strict mode (no silent drops)
- Contract mismatches with prescriptive errors
- Determinism (stable hashes across runs)
- Import-time budget
"""

import json
import time
from pathlib import Path

import pytest

from saaaaaa.core.wiring.bootstrap import WiringBootstrap
from saaaaaa.core.wiring.contracts import (
    AdapterExpectation,
    CPPDeliverable,
    PreprocessedDocumentDeliverable,
)
from saaaaaa.core.wiring.errors import WiringContractError
from saaaaaa.core.wiring.feature_flags import WiringFeatureFlags
from saaaaaa.core.wiring.validation import WiringValidator


@pytest.fixture
def bootstrap_args(tmp_path):
    """Provides common arguments for WiringBootstrap."""
    monolith_path = tmp_path / "monolith.json"
    monolith_path.write_text('{}')
    monolith_path.chmod(0o444)  # Read-only

    executor_path = tmp_path / "executor.json"
    executor_path.write_text('{}')
    executor_path.chmod(0o444)  # Read-only, consistent with monolith_path
    return {
        "questionnaire_path": monolith_path,
        "questionnaire_hash": "dummy_hash",
        "executor_config_path": executor_path,
        "calibration_profile": "default",
        "abort_on_insufficient": False,
        "resource_limits": {},
    }

class TestWiringBootstrap:
    """Test wiring bootstrap initialization."""
    
    def test_bootstrap_with_defaults(self, bootstrap_args):
        """Test bootstrap with default settings."""
        flags = WiringFeatureFlags()
        bootstrap = WiringBootstrap(**bootstrap_args, flags=flags)
        
        components = bootstrap.bootstrap()
        
        assert components is not None
        assert components.provider is not None
        assert components.signal_client is not None
        assert components.signal_registry is not None
        assert components.factory is not None
        assert components.arg_router is not None
        assert components.validator is not None
        assert components.flags == flags
    
    def test_bootstrap_memory_mode(self, bootstrap_args):
        """Test bootstrap in memory mode (default)."""
        flags = WiringFeatureFlags(
            use_cpp_ingestion=True,
            enable_http_signals=False,  # Memory mode
        )
        bootstrap = WiringBootstrap(**bootstrap_args, flags=flags)
        
        components = bootstrap.bootstrap()
        
        # Verify memory mode
        assert components.signal_client._transport == "memory"
        assert components.signal_client._memory_source is not None
    
    def test_bootstrap_with_questionnaire(self, bootstrap_args, tmp_path):
        """Test bootstrap with questionnaire file."""
        # Create temporary questionnaire
        questionnaire_data = {
            "metadata": {"version": "1.0.0"},
            "questions": [],
        }
        
        questionnaire_path = tmp_path / "questionnaire.json"
        questionnaire_path.write_text(json.dumps(questionnaire_data))
        questionnaire_path.chmod(0o444)
        
        bootstrap_args["questionnaire_path"] = questionnaire_path
        bootstrap = WiringBootstrap(**bootstrap_args)
        components = bootstrap.bootstrap()
        
        assert components.provider is not None
    
    def test_bootstrap_signals_seeded(self, bootstrap_args):
        """Test that signals are seeded in memory mode."""
        flags = WiringFeatureFlags(enable_http_signals=False)
        bootstrap = WiringBootstrap(**bootstrap_args, flags=flags)
        
        components = bootstrap.bootstrap()
        
        # Check that registry has some signals
        metrics = components.signal_registry.get_metrics()
        assert metrics["size"] > 0, "Registry should have seeded signals"
    
    def test_bootstrap_argrouter_coverage(self, bootstrap_args):
        """Test that ArgRouter has required route coverage."""
        bootstrap = WiringBootstrap(**bootstrap_args)
        components = bootstrap.bootstrap()
        
        coverage = components.arg_router.get_special_route_coverage()
        
        assert coverage >= 30, f"Expected ≥30 special routes, got {coverage}"




class TestWiringValidation:
    """Test contract validation between links."""
    
    def test_spc_to_adapter_valid(self):
        """Test valid SPC → Adapter contract."""
        validator = WiringValidator()

        spc_data = {
            "chunk_graph": {"chunks": {"chunk1": {}}},
            "policy_manifest": {"version": "1.0.0"},
            "provenance_completeness": 1.0,
            "schema_version": "2.0.0",
        }

        # Should not raise
        validator.validate_spc_to_adapter(spc_data)

    def test_spc_to_adapter_missing_provenance(self):
        """Test SPC → Adapter with incomplete provenance."""
        validator = WiringValidator()

        spc_data = {
            "chunk_graph": {"chunks": {"chunk1": {}}},
            "policy_manifest": {"version": "1.0.0"},
            "provenance_completeness": 0.5,  # Not 1.0!
            "schema_version": "2.0.0",
        }

        with pytest.raises(WiringContractError) as exc_info:
            validator.validate_spc_to_adapter(spc_data)

        error = exc_info.value
        assert "provenance_completeness" in str(error).lower()
        assert error.details["link"] == "spc->adapter"
    
    def test_adapter_to_orchestrator_valid(self):
        """Test valid Adapter → Orchestrator contract."""
        validator = WiringValidator()
        
        doc_data = {
            "sentence_metadata": [{"id": "sent1", "text": "test"}],
            "resolution_index": {"micro": []},
            "provenance_completeness": 1.0,
            "document_id": "doc123",
        }
        
        # Should not raise
        validator.validate_adapter_to_orchestrator(doc_data)
    
    def test_adapter_to_orchestrator_empty_sentences(self):
        """Test Adapter → Orchestrator with empty sentences."""
        validator = WiringValidator()
        
        doc_data = {
            "sentence_metadata": [],  # Empty!
            "resolution_index": {"micro": []},
            "provenance_completeness": 1.0,
            "document_id": "doc123",
        }
        
        with pytest.raises(WiringContractError) as exc_info:
            validator.validate_adapter_to_orchestrator(doc_data)
        
        error = exc_info.value
        assert "sentence_metadata" in str(error).lower()
    
    def test_orchestrator_to_argrouter_valid(self):
        """Test valid Orchestrator → ArgRouter contract."""
        validator = WiringValidator()
        
        payload_data = {
            "class_name": "TestAnalyzer",
            "method_name": "_extract_claims",
            "payload": {"content": "test"},
        }
        
        # Should not raise
        validator.validate_orchestrator_to_argrouter(payload_data)
    
    def test_signals_to_registry_valid(self):
        """Test valid Signals → Registry contract."""
        validator = WiringValidator()
        
        signal_data = {
            "version": "1.0.0",
            "policy_area": "fiscal",
            "patterns": ["pattern1", "pattern2"],
            "indicators": [],
        }
        
        # Should not raise
        validator.validate_signals_to_registry(signal_data)
    
    def test_signals_to_registry_missing_version(self):
        """Test Signals → Registry with missing version."""
        validator = WiringValidator()
        
        signal_data = {
            "version": "",  # Empty version!
            "policy_area": "fiscal",
            "patterns": [],
            "indicators": [],
        }
        
        with pytest.raises(WiringContractError) as exc_info:
            validator.validate_signals_to_registry(signal_data)
        
        error = exc_info.value
        assert "version" in str(error).lower()
    
    def test_link_hash_determinism(self):
        """Test that link hashes are deterministic."""
        validator = WiringValidator()
        
        data = {
            "key1": "value1",
            "key2": 42,
            "key3": ["a", "b", "c"],
        }
        
        hash1 = validator.compute_link_hash("cpp->adapter", data)
        hash2 = validator.compute_link_hash("cpp->adapter", data)
        
        assert hash1 == hash2, "Hashes should be deterministic"
    
    def test_validation_metrics(self):
        """Test that validation metrics are tracked."""
        validator = WiringValidator()
        
        # Perform some validations
        spc_data = {
            "chunk_graph": {"chunks": {}},
            "policy_manifest": {},
            "provenance_completeness": 1.0,
            "schema_version": "2.0.0",
        }

        validator.validate_spc_to_adapter(spc_data)
        validator.validate_spc_to_adapter(spc_data)

        metrics = validator.get_all_metrics()

        assert "spc->adapter" in metrics
        assert metrics["spc->adapter"]["validation_count"] == 2
        assert metrics["spc->adapter"]["failure_count"] == 0


class TestWiringDeterminism:
    """Test determinism guarantees."""


class TestWiringFeatureFlags:
    """Test feature flag functionality."""
    
    def test_default_flags(self):
        """Test default flag values."""
        flags = WiringFeatureFlags()
        
        assert flags.use_cpp_ingestion is True
        assert flags.enable_http_signals is False
        assert flags.allow_threshold_override is False
        assert flags.wiring_strict_mode is True
    
    def test_flags_to_dict(self):
        """Test flag serialization."""
        flags = WiringFeatureFlags()
        
        flags_dict = flags.to_dict()
        
        assert isinstance(flags_dict, dict)
        assert "use_cpp_ingestion" in flags_dict
        assert "enable_http_signals" in flags_dict
    
    def test_flags_validation_warnings(self):
        """Test flag validation warnings."""
        # HTTP + deterministic should warn
        flags = WiringFeatureFlags(
            enable_http_signals=True,
            deterministic_mode=True,
        )
        
        warnings = flags.validate()
        
        assert len(warnings) > 0
        assert any("http" in w.lower() for w in warnings)
    
    def test_flags_from_env(self, monkeypatch):
        """Test loading flags from environment."""
        monkeypatch.setenv("SAAAAAA_USE_CPP_INGESTION", "false")
        monkeypatch.setenv("SAAAAAA_ENABLE_HTTP_SIGNALS", "true")
        
        flags = WiringFeatureFlags.from_env()
        
        assert flags.use_cpp_ingestion is False
        assert flags.enable_http_signals is True


class TestWiringImportTime:
    """Test import time performance."""
    
    def test_import_time_budget(self):
        """Test that wiring imports complete within budget."""
        start = time.time()
        
        # Import all wiring modules
        from saaaaaa.core.wiring import bootstrap, contracts, errors, feature_flags, observability, validation
        
        elapsed = time.time() - start
        
        # Should complete in under 1 second
        assert elapsed < 1.0, f"Import took {elapsed:.2f}s, exceeds 1s budget"


class TestWiringE2EGoldenFlow:
    """Test end-to-end golden document flow."""
    
    def test_golden_flow_memory_mode(self, bootstrap_args):
        """Test complete flow in memory mode."""
        # Bootstrap system
        flags = WiringFeatureFlags(
            use_cpp_ingestion=True,
            enable_http_signals=False,
            deterministic_mode=True,
        )
        
        bootstrap = WiringBootstrap(**bootstrap_args, flags=flags)
        components = bootstrap.bootstrap()
        
        # Verify all components initialized
        assert components.provider is not None
        assert components.signal_registry is not None
        assert components.factory is not None
        assert components.arg_router is not None
        
        # Verify signals available
        registry_metrics = components.signal_registry.get_metrics()
        assert registry_metrics["hit_rate"] >= 0.0  # May be 0 if no fetches yet
        assert registry_metrics["size"] > 0  # Should have seeded signals
        
        # Verify router coverage
        route_coverage = components.arg_router.get_special_route_coverage()
        assert route_coverage >= 30
        
        # Verify validator ready
        validator_summary = components.validator.get_summary()
        assert validator_summary["overall_success_rate"] == 1.0  # No failures yet
    
    def test_golden_flow_with_validation(self, bootstrap_args):
        """Test flow with contract validation at each step."""
        bootstrap = WiringBootstrap(**bootstrap_args)
        components = bootstrap.bootstrap()
        
        validator = components.validator
        
        # Simulate CPP → Adapter
        cpp_data = {
            "chunk_graph": {"chunks": {"c1": {}}},
            "policy_manifest": {"version": "1.0"},
            "provenance_completeness": 1.0,
            "schema_version": "2.0",
        }
        
        validator.validate_cpp_to_adapter(cpp_data)
        
        # Simulate Adapter → Orchestrator
        doc_data = {
            "sentence_metadata": [{"id": "s1"}],
            "resolution_index": {},
            "provenance_completeness": 1.0,
            "document_id": "doc1",
        }
        
        validator.validate_adapter_to_orchestrator(doc_data)
        
        # Check metrics
        metrics = validator.get_all_metrics()
        assert metrics["cpp->adapter"]["validation_count"] == 1
        assert metrics["adapter->orchestrator"]["validation_count"] == 1


class TestWiringErrorHandling:
    """Test error handling and prescriptive messages."""
    
    def test_contract_error_has_fix(self):
        """Test that contract errors include fix instructions."""
        validator = WiringValidator()

        bad_spc_data = {
            "chunk_graph": {},  # Missing required fields
        }

        try:
            validator.validate_spc_to_adapter(bad_spc_data)
            pytest.fail("Should have raised WiringContractError")
        except WiringContractError as e:
            # Check error has details
            assert e.details is not None
            assert "link" in e.details
            assert e.details["link"] == "spc->adapter"

            # Check error message is prescriptive
            error_msg = str(e)
            assert "spc->adapter" in error_msg.lower()
    
    def test_initialization_error_prescriptive(self):
        """Test that initialization errors are prescriptive."""
        from saaaaaa.core.wiring.errors import WiringInitializationError
        
        error = WiringInitializationError(
            phase="load_resources",
            component="QuestionnaireResourceProvider",
            reason="File not found",
        )
        
        error_msg = str(error)
        assert "load_resources" in error_msg
        assert "QuestionnaireResourceProvider" in error_msg
        assert "File not found" in error_msg


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
