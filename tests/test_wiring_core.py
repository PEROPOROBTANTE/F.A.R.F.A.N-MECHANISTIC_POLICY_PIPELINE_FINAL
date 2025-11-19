"""Core wiring tests without heavy dependencies.

Tests the wiring system components in isolation without requiring
full TensorFlow/transformers imports.
"""

import json
from pathlib import Path

import pytest

from saaaaaa.core.orchestrator.signals import SignalClient, SignalRegistry
from saaaaaa.core.wiring.bootstrap import (
    CANONICAL_POLICY_AREA_DEFINITIONS,
    WiringBootstrap,
)
from saaaaaa.core.wiring.contracts import (
    CPPDeliverable,
    PreprocessedDocumentDeliverable,
    SignalPackDeliverable,
)
from saaaaaa.core.wiring.errors import (
    WiringContractError,
    WiringInitializationError,
    MissingDependencyError,
)
from saaaaaa.core.wiring.feature_flags import WiringFeatureFlags
from saaaaaa.core.wiring.validation import WiringValidator


class TestWiringContracts:
    """Test contract models."""
    
    def test_cpp_deliverable_valid(self):
        """Test valid CPP deliverable."""
        data = {
            "chunk_graph": {"chunks": {}},
            "policy_manifest": {"version": "1.0"},
            "provenance_completeness": 1.0,
            "schema_version": "2.0",
        }
        
        cpp = CPPDeliverable.model_validate(data)
        
        assert cpp.provenance_completeness == 1.0
        assert cpp.schema_version == "2.0"
    
    def test_cpp_deliverable_invalid_provenance(self):
        """Test CPP deliverable with invalid provenance."""
        data = {
            "chunk_graph": {"chunks": {}},
            "policy_manifest": {"version": "1.0"},
            "provenance_completeness": 0.5,  # Not 1.0!
            "schema_version": "2.0",
        }
        
        with pytest.raises(ValueError) as exc_info:
            CPPDeliverable.model_validate(data)
        
        assert "provenance_completeness" in str(exc_info.value)
    
    def test_preprocessed_document_deliverable_valid(self):
        """Test valid PreprocessedDocument deliverable."""
        data = {
            "sentence_metadata": [{"id": "s1", "text": "test"}],
            "resolution_index": {"micro": []},
            "provenance_completeness": 1.0,
            "document_id": "doc123",
        }
        
        doc = PreprocessedDocumentDeliverable.model_validate(data)
        
        assert doc.document_id == "doc123"
        assert len(doc.sentence_metadata) == 1
    
    def test_preprocessed_document_empty_sentences(self):
        """Test PreprocessedDocument with empty sentences."""
        data = {
            "sentence_metadata": [],  # Empty!
            "resolution_index": {},
            "provenance_completeness": 1.0,
            "document_id": "doc123",
        }
        
        with pytest.raises(ValueError):
            PreprocessedDocumentDeliverable.model_validate(data)
    
    def test_signal_pack_deliverable_valid(self):
        """Test valid SignalPack deliverable."""
        data = {
            "version": "1.0.0",
            "policy_area": "fiscal",
            "patterns": ["pattern1", "pattern2"],
            "indicators": ["ind1"],
        }
        
        signal = SignalPackDeliverable.model_validate(data)
        
        assert signal.version == "1.0.0"
        assert signal.policy_area == "fiscal"
    
    def test_signal_pack_empty_version(self):
        """Test SignalPack with empty version."""
        data = {
            "version": "",  # Empty!
            "policy_area": "fiscal",
            "patterns": [],
            "indicators": [],
        }
        
        with pytest.raises(ValueError):
            SignalPackDeliverable.model_validate(data)


class TestWiringErrors:
    """Test error classes."""
    
    def test_wiring_contract_error(self):
        """Test WiringContractError."""
        error = WiringContractError(
            link="cpp->adapter",
            expected_schema="CPPDeliverable",
            received_schema="dict",
            field="provenance_completeness",
            fix="Ensure ingestion completes successfully",
        )
        
        assert error.details["link"] == "cpp->adapter"
        assert error.details["field"] == "provenance_completeness"
        assert "Fix:" in str(error)
    
    def test_missing_dependency_error(self):
        """Test MissingDependencyError."""
        error = MissingDependencyError(
            dependency="questionnaire.json",
            required_by="WiringBootstrap",
            fix="Create questionnaire file",
        )
        
        assert error.details["dependency"] == "questionnaire.json"
        assert "Fix:" in str(error)
    
    def test_wiring_initialization_error(self):
        """Test WiringInitializationError."""
        error = WiringInitializationError(
            phase="load_resources",
            component="QuestionnaireResourceProvider",
            reason="File not found",
        )
        
        assert error.details["phase"] == "load_resources"
        assert "File not found" in str(error)


class TestWiringFeatureFlags:
    """Test feature flags."""
    
    def test_default_flags(self):
        """Test default flag values."""
        flags = WiringFeatureFlags()
        
        assert flags.use_cpp_ingestion is True
        assert flags.enable_http_signals is False
        assert flags.wiring_strict_mode is True
    
    def test_flags_to_dict(self):
        """Test flag serialization."""
        flags = WiringFeatureFlags(
            use_cpp_ingestion=False,
            enable_http_signals=True,
        )
        
        flags_dict = flags.to_dict()
        
        assert flags_dict["use_cpp_ingestion"] is False
        assert flags_dict["enable_http_signals"] is True
    
    def test_flags_validation_http_determinism_warning(self):
        """Test warning for HTTP + deterministic mode."""
        flags = WiringFeatureFlags(
            enable_http_signals=True,
            deterministic_mode=True,
        )
        
        warnings = flags.validate()
        
        assert len(warnings) > 0
        assert any("http" in w.lower() for w in warnings)
    
    def test_flags_validation_no_strict_mode_warning(self):
        """Test warning for disabled strict mode."""
        flags = WiringFeatureFlags(wiring_strict_mode=False)
        
        warnings = flags.validate()
        
        assert any("strict" in w.lower() for w in warnings)
    
    def test_flags_from_env(self, monkeypatch):
        """Test loading flags from environment."""
        monkeypatch.setenv("SAAAAAA_USE_CPP_INGESTION", "false")
        monkeypatch.setenv("SAAAAAA_ENABLE_HTTP_SIGNALS", "true")
        monkeypatch.setenv("SAAAAAA_WIRING_STRICT_MODE", "false")
        
        flags = WiringFeatureFlags.from_env()
        
        assert flags.use_cpp_ingestion is False
        assert flags.enable_http_signals is True
        assert flags.wiring_strict_mode is False


class TestWiringValidation:
    """Test validation without full bootstrap."""
    
    def test_validator_initialization(self):
        """Test validator initialization."""
        validator = WiringValidator()
        
        assert validator is not None
        metrics = validator.get_all_metrics()
        
        # Should have all expected links
        expected_links = [
            "cpp->adapter",
            "adapter->orchestrator",
            "orchestrator->argrouter",
            "argrouter->executors",
            "signals->registry",
            "executors->aggregate",
            "aggregate->score",
            "score->report",
        ]
        
        for link in expected_links:
            assert link in metrics
    
    def test_validate_cpp_to_adapter_success(self):
        """Test successful CPP → Adapter validation."""
        validator = WiringValidator()
        
        cpp_data = {
            "chunk_graph": {"chunks": {"c1": {}}},
            "policy_manifest": {"version": "1.0"},
            "provenance_completeness": 1.0,
            "schema_version": "2.0",
        }
        
        # Should not raise
        validator.validate_cpp_to_adapter(cpp_data)
        
        # Check metrics
        metrics = validator.get_all_metrics()
        assert metrics["cpp->adapter"]["validation_count"] == 1
        assert metrics["cpp->adapter"]["failure_count"] == 0
    
    def test_validate_cpp_to_adapter_failure(self):
        """Test failed CPP → Adapter validation."""
        validator = WiringValidator()
        
        bad_cpp_data = {
            "chunk_graph": {},
            # Missing required fields
        }
        
        with pytest.raises(WiringContractError) as exc_info:
            validator.validate_cpp_to_adapter(bad_cpp_data)
        
        error = exc_info.value
        assert error.details["link"] == "cpp->adapter"
        
        # Check metrics show failure
        metrics = validator.get_all_metrics()
        assert metrics["cpp->adapter"]["failure_count"] == 1
    
    def test_link_hash_determinism(self):
        """Test link hashing is deterministic."""
        validator = WiringValidator()
        
        data = {
            "key1": "value1",
            "key2": 42,
            "nested": {"a": 1, "b": 2},
        }
        
        hash1 = validator.compute_link_hash("cpp->adapter", data)
        hash2 = validator.compute_link_hash("cpp->adapter", data)
        
        assert hash1 == hash2
    
    def test_link_hash_order_independence(self):
        """Test link hashing is order-independent."""
        validator = WiringValidator()
        
        # Same data, different key order
        data1 = {"b": 2, "a": 1, "c": 3}
        data2 = {"a": 1, "c": 3, "b": 2}
        
        # Use a known link name
        hash1 = validator.compute_link_hash("cpp->adapter", data1)
        hash2 = validator.compute_link_hash("cpp->adapter", data2)
        
        assert hash1 == hash2
    
    def test_validation_summary(self):
        """Test validation summary."""
        validator = WiringValidator()
        
        # Perform some validations
        valid_cpp = {
            "chunk_graph": {"chunks": {}},
            "policy_manifest": {},
            "provenance_completeness": 1.0,
            "schema_version": "2.0",
        }
        
        validator.validate_cpp_to_adapter(valid_cpp)
        validator.validate_cpp_to_adapter(valid_cpp)
        
        summary = validator.get_summary()
        
        assert summary["total_validations"] == 2
        assert summary["total_failures"] == 0
        assert summary["overall_success_rate"] == 1.0


class TestWiringObservability:
    """Test observability helpers."""
    
    def test_has_otel_flag(self):
        """Test HAS_OTEL flag availability."""
        from saaaaaa.core.wiring.observability import HAS_OTEL
        
        # Should be bool
        assert isinstance(HAS_OTEL, bool)
    
    def test_trace_wiring_link_context(self):
        """Test trace_wiring_link context manager."""
        from saaaaaa.core.wiring.observability import trace_wiring_link
        
        attrs = None
        with trace_wiring_link("test_link", document_id="doc123") as dynamic_attrs:
            attrs = dynamic_attrs
            dynamic_attrs["result"] = "success"
        
        # Context manager should provide dict
        assert isinstance(attrs, dict)
        assert "result" in attrs
    
    def test_trace_wiring_init_context(self):
        """Test trace_wiring_init context manager."""
        from saaaaaa.core.wiring.observability import trace_wiring_init
        
        attrs = None
        with trace_wiring_init("test_phase", component="TestComponent") as dynamic_attrs:
            attrs = dynamic_attrs
            dynamic_attrs["status"] = "complete"
        
        assert isinstance(attrs, dict)
        assert "status" in attrs


class TestSignalSeeding:
    """Test signal seeding wiring."""

    class _StubProvider:
        def get_patterns_for_area(self, policy_area_id: str, limit: int | None = None) -> list[str]:
            count = limit or 4
            return [f"{policy_area_id.lower()}_pattern_{i}" for i in range(count)]

    def test_seed_signals_public_seeds_all_canonical_areas(self):
        """seed_signals_public should seed all canonical policy areas and aliases."""
        bootstrap = WiringBootstrap(flags=WiringFeatureFlags())
        client = SignalClient(base_url="memory://")
        registry = SignalRegistry()
        provider = self._StubProvider()

        metrics = bootstrap.seed_signals_public(client, registry, provider)

        assert metrics["canonical_areas"] == len(CANONICAL_POLICY_AREA_DEFINITIONS)
        assert metrics["hit_rate"] == pytest.approx(1.0)

        for area_id in CANONICAL_POLICY_AREA_DEFINITIONS:
            pack = registry.get(area_id)
            assert pack is not None, f"Missing signal pack for {area_id}"
            assert pack.metadata.get("canonical_id") == area_id
            assert pack.patterns, "Expected patterns for canonical signal pack"

        # Legacy aliases remain available for backward compatibility
        assert registry.get("fiscal") is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
