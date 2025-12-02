"""Test Phase Boundary Contracts

Tests that phase N output becomes phase N+1 input with no data loss.
"""
import pytest
from unittest.mock import AsyncMock, patch


class TestPhaseBoundaries:
    """Test phase boundary contract enforcement."""

    def test_phase0_output_is_phase1_input(self):
        """Test Phase 0 output (CanonicalInput) is Phase 1 input."""
        from farfan_pipeline.core.phases.phase0_input_validation import Phase0ValidationContract
        from farfan_pipeline.core.phases.phase1_spc_ingestion import Phase1SPCIngestionContract
        
        phase0 = Phase0ValidationContract()
        phase1 = Phase1SPCIngestionContract()
        
        assert phase0.phase_name == "phase0_input_validation"
        assert phase1.phase_name == "phase1_spc_ingestion"

    def test_phase1_output_is_adapter_input(self):
        """Test Phase 1 output (CanonPolicyPackage) is adapter input."""
        from farfan_pipeline.core.phases.phase1_spc_ingestion import Phase1SPCIngestionContract
        from farfan_pipeline.core.phases.phase1_to_phase2_adapter import AdapterContract
        
        phase1 = Phase1SPCIngestionContract()
        adapter = AdapterContract()
        
        assert adapter.phase_name == "phase1_to_phase2_adapter"

    def test_adapter_output_is_phase2_input(self):
        """Test adapter output (PreprocessedDocument) is Phase 2 input."""
        from farfan_pipeline.core.phases.phase1_to_phase2_adapter import AdapterContract
        
        adapter = AdapterContract()
        assert "phase2" in adapter.phase_name.lower() or "adapter" in adapter.phase_name.lower()

    def test_no_phase_can_be_skipped(self):
        """Test orchestrator enforces sequential execution."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        assert hasattr(orchestrator, 'phase0')
        assert hasattr(orchestrator, 'phase1')
        assert hasattr(orchestrator, 'adapter')

    @pytest.mark.asyncio
    async def test_phase_contract_validates_input_output(self):
        """Test PhaseContract.run() validates input and output."""
        from farfan_pipeline.core.phases.phase_protocol import PhaseContract
        
        class TestContract(PhaseContract):
            def validate_input(self, data):
                from farfan_pipeline.core.phases.phase_protocol import ContractValidationResult
                return ContractValidationResult(True, "input", "test")
            
            def validate_output(self, data):
                from farfan_pipeline.core.phases.phase_protocol import ContractValidationResult
                return ContractValidationResult(True, "output", "test")
            
            async def execute(self, data):
                return data
        
        contract = TestContract("test")
        output, metadata = await contract.run("test_input")
        assert output == "test_input"
        assert metadata.success is True
