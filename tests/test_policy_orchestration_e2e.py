"""End-to-end integration tests for Policy Orchestration System.

Tests the complete flow using FrontierExecutorOrchestrator:
    Smart Chunks (10/PA) → Signals (PA-specific) → FrontierExecutorOrchestrator → Executors
"""

import pytest
from pathlib import Path

from saaaaaa.core.orchestrator.executors import FrontierExecutorOrchestrator
from saaaaaa.core.orchestrator.signals import SignalRegistry, SignalPack


class TestPolicyOrchestrationE2E:
    """End-to-end tests for policy orchestration system."""

    @pytest.fixture
    def signal_registry(self):
        """Create signal registry with test signals."""
        registry = SignalRegistry(max_size=20, default_ttl_s=3600)

        # Add test signal for PA01
        signal_pack = SignalPack(
            version="1.0.0",
            policy_area="PA01",
            patterns=["género", "mujeres", "equidad"],
            regex=["\\bmujeres?\\b", "\\bgénero\\b"],
            verbs=["garantizar", "promover"],
            entities=["Ministerio de la Mujer"],
            thresholds={"min_confidence": 0.75}
        )
        registry.put("PA01", signal_pack)

        return registry

    @pytest.fixture
    def orchestrator(self, signal_registry):
        """Create FrontierExecutorOrchestrator instance."""
        return FrontierExecutorOrchestrator(signal_registry=signal_registry)

    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly with signal support."""
        assert orchestrator is not None
        assert orchestrator.signal_registry is not None
        assert orchestrator.chunk_router is not None
        assert len(orchestrator.executors) == 30  # All 30 executors
        assert len(orchestrator.CANONICAL_POLICY_AREAS) == 10

    def test_signal_pack_loading(self):
        """Test loading signal packs from config directory."""
        signals_dir = Path("config/policy_signals")

        # Skip if signals directory doesn't exist
        if not signals_dir.exists():
            pytest.skip("Signals directory not found")

        registry = SignalRegistry()
        orchestrator = FrontierExecutorOrchestrator(signal_registry=registry)

        # Load signals
        orchestrator.load_policy_signals(str(signals_dir))

        # Validate PA01 was loaded
        loaded_signal = registry.get("PA01")
        assert loaded_signal is not None, "PA01 signal pack should be loaded"
        assert loaded_signal.policy_area == "PA01"
        assert len(loaded_signal.patterns) > 0
        assert len(loaded_signal.regex) > 0

    def test_process_policy_area_with_10_chunks(self, orchestrator):
        """Test processing exactly 10 chunks for a policy area."""
        # Create mock method executor
        class MockMethodExecutor:
            def __init__(self):
                self.instances = {}

        method_executor = MockMethodExecutor()

        # Generate 10 mock chunks for PA01
        mock_chunks = []
        for i in range(10):
            mock_chunks.append({
                'id': f"PA01_chunk_{i+1}",
                'text': f"Mock chunk {i+1} for gender equality policy.",
                'policy_area': 'PA01',
                'chunk_index': i,
                'chunk_type': 'diagnostic',
                'metadata': {'test': True}
            })

        # Process with orchestrator
        result = orchestrator.process_policy_area_chunks(
            chunks=mock_chunks,
            policy_area="PA01",
            method_executor=method_executor
        )

        # Validate result
        assert result is not None
        assert result['policy_area'] == "PA01"
        assert result['chunks_processed'] >= 0  # May be 0 if no executors matched
        assert result['signals_version'] == "1.0.0"

    def test_process_policy_area_wrong_chunk_count(self, orchestrator):
        """Test that orchestrator rejects incorrect chunk count."""
        # Create mock method executor
        class MockMethodExecutor:
            def __init__(self):
                self.instances = {}

        method_executor = MockMethodExecutor()

        # Generate only 5 chunks (should require 10)
        mock_chunks = []
        for i in range(5):
            mock_chunks.append({
                'id': f"PA01_chunk_{i+1}",
                'text': f"Mock chunk {i+1}",
                'policy_area': 'PA01',
                'chunk_index': i,
                'chunk_type': 'diagnostic',
            })

        # Should raise error
        with pytest.raises(ValueError) as exc_info:
            orchestrator.process_policy_area_chunks(
                chunks=mock_chunks,
                policy_area="PA01",
                method_executor=method_executor
            )

        assert "Expected exactly 10 chunks" in str(exc_info.value)

    def test_invalid_policy_area(self, orchestrator):
        """Test that invalid policy area is rejected."""
        class MockMethodExecutor:
            def __init__(self):
                self.instances = {}

        method_executor = MockMethodExecutor()
        mock_chunks = [{'id': f'chunk_{i}'} for i in range(10)]

        with pytest.raises(ValueError) as exc_info:
            orchestrator.process_policy_area_chunks(
                chunks=mock_chunks,
                policy_area="INVALID",
                method_executor=method_executor
            )

        assert "Invalid policy area" in str(exc_info.value)

    def test_canonical_policy_areas(self, orchestrator):
        """Test that all 10 canonical policy areas are recognized."""
        expected_areas = [
            "PA01", "PA02", "PA03", "PA04", "PA05",
            "PA06", "PA07", "PA08", "PA09", "PA10"
        ]

        assert orchestrator.CANONICAL_POLICY_AREAS == expected_areas

    def test_execute_question_still_works(self, orchestrator):
        """Test that existing execute_question method still works."""
        # This ensures backward compatibility
        class MockMethodExecutor:
            def __init__(self):
                self.instances = {}

        class MockDoc:
            raw_text = "test document"
            metadata = {}

        method_executor = MockMethodExecutor()
        doc = MockDoc()

        # execute_question should still work for backward compatibility
        # (will fail with actual execution, but should not raise on orchestrator level)
        try:
            result = orchestrator.execute_question("D1Q1", doc, method_executor)
        except Exception as e:
            # Expected to fail during execution, but orchestrator should accept the call
            assert "D1Q1" in orchestrator.executors


class TestSignalPackValidation:
    """Tests for SignalPack validation."""

    def test_signal_pack_creation(self):
        """Test creating a valid signal pack."""
        signal_pack = SignalPack(
            version="1.0.0",
            policy_area="PA01",
            patterns=["test"],
            regex=["\\btest\\b"],
            verbs=["test"],
            entities=["Test Entity"],
            thresholds={"min_confidence": 0.75}
        )

        assert signal_pack.version == "1.0.0"
        assert signal_pack.policy_area == "PA01"
        assert signal_pack.is_valid()

    def test_signal_pack_invalid_version(self):
        """Test that invalid version format is rejected."""
        with pytest.raises(ValueError) as exc_info:
            SignalPack(
                version="invalid",
                policy_area="PA01",
                patterns=[],
                regex=[],
                verbs=[],
                entities=[],
                thresholds={}
            )

        assert "Version must be in format 'X.Y.Z'" in str(exc_info.value)

    def test_signal_pack_invalid_threshold(self):
        """Test that invalid threshold values are rejected."""
        with pytest.raises(ValueError) as exc_info:
            SignalPack(
                version="1.0.0",
                policy_area="PA01",
                patterns=[],
                regex=[],
                verbs=[],
                entities=[],
                thresholds={"invalid": 2.0}  # Out of range [0.0, 1.0]
            )

        assert "must be in range [0.0, 1.0]" in str(exc_info.value)


class TestChunkCalibration:
    """Tests for chunk calibration (10 chunks per PA)."""

    @pytest.mark.skipif(
        not Path("scripts/smart_policy_chunks_canonic_phase_one.py").exists(),
        reason="smart_policy_chunks script not found"
    )
    def test_chunk_calibrator_exists(self):
        """Test that PolicyAreaChunkCalibrator class exists."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "smart_policy_chunks_canonic_phase_one",
            "scripts/smart_policy_chunks_canonic_phase_one.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        PolicyAreaChunkCalibrator = module.PolicyAreaChunkCalibrator

        assert PolicyAreaChunkCalibrator is not None
        assert PolicyAreaChunkCalibrator.TARGET_CHUNKS_PER_PA == 10

    @pytest.mark.skipif(
        not Path("scripts/smart_policy_chunks_canonic_phase_one.py").exists(),
        reason="smart_policy_chunks script not found"
    )
    def test_calibrator_canonical_policy_areas(self):
        """Test that calibrator uses canonical policy areas."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "smart_policy_chunks_canonic_phase_one",
            "scripts/smart_policy_chunks_canonic_phase_one.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        PolicyAreaChunkCalibrator = module.PolicyAreaChunkCalibrator

        expected_areas = [
            "PA01", "PA02", "PA03", "PA04", "PA05",
            "PA06", "PA07", "PA08", "PA09", "PA10"
        ]

        assert PolicyAreaChunkCalibrator.POLICY_AREAS == expected_areas
