"""Test Failure Propagation (Phase N Failure → ABORT)

Tests that phase failures propagate correctly and halt pipeline execution.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from farfan_pipeline.core.phases.phase_protocol import PhaseContract, ContractValidationResult


class TestFailurePropagation:
    """Test phase failure propagation."""

    @pytest.mark.asyncio
    async def test_input_validation_failure_aborts(self):
        """Test input validation failure aborts phase execution."""
        
        class TestContract(PhaseContract):
            def validate_input(self, data):
                return ContractValidationResult(
                    passed=False, contract_type="input", phase_name="test",
                    errors=["Input validation failed"]
                )
            
            def validate_output(self, data):
                return ContractValidationResult(True, "output", "test")
            
            async def execute(self, data):
                return data
        
        contract = TestContract("test")
        
        with pytest.raises(ValueError) as exc_info:
            await contract.run("invalid_input")
        
        assert "Input contract validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_output_validation_failure_aborts(self):
        """Test output validation failure aborts phase execution."""
        
        class TestContract(PhaseContract):
            def validate_input(self, data):
                return ContractValidationResult(True, "input", "test")
            
            def validate_output(self, data):
                return ContractValidationResult(
                    passed=False, contract_type="output", phase_name="test",
                    errors=["Output validation failed"]
                )
            
            async def execute(self, data):
                return "invalid_output"
        
        contract = TestContract("test")
        
        with pytest.raises(ValueError) as exc_info:
            await contract.run("input")
        
        assert "Output contract validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invariant_failure_aborts(self):
        """Test invariant failure aborts phase execution."""
        
        class TestContract(PhaseContract):
            def __init__(self):
                super().__init__("test")
                self.add_invariant(
                    "test_invariant", "Test invariant",
                    lambda data: False, "Invariant failed"
                )
            
            def validate_input(self, data):
                return ContractValidationResult(True, "input", "test")
            
            def validate_output(self, data):
                return ContractValidationResult(True, "output", "test")
            
            async def execute(self, data):
                return data
        
        contract = TestContract()
        
        with pytest.raises(RuntimeError) as exc_info:
            await contract.run("input")
        
        assert "Phase invariants failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_execution_error_captured_in_metadata(self):
        """Test execution errors are captured in phase metadata."""
        
        class TestContract(PhaseContract):
            def validate_input(self, data):
                return ContractValidationResult(True, "input", "test")
            
            def validate_output(self, data):
                return ContractValidationResult(True, "output", "test")
            
            async def execute(self, data):
                raise RuntimeError("Execution failed")
        
        contract = TestContract("test")
        
        with pytest.raises(RuntimeError):
            await contract.run("input")
        
        assert contract.metadata is not None
        assert contract.metadata.success is False
        assert "Execution failed" in contract.metadata.error

    @pytest.mark.asyncio
    async def test_phase_failure_prevents_subsequent_phases(self):
        """Test phase failure prevents subsequent phases from executing."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        from pathlib import Path
        
        orchestrator = PhaseOrchestrator()
        
        with patch.object(orchestrator.phase0, 'run', side_effect=ValueError("Phase 0 failed")):
            result = await orchestrator.run_pipeline(
                pdf_path=Path("nonexistent.pdf"),
                run_id="test_run",
                questionnaire_path=None
            )
            
            assert result.success is False
            assert len(result.errors) > 0
            assert result.phases_completed == 0


class TestPipelineAbortBehavior:
    """Test pipeline abort behavior on failure."""

    @pytest.mark.asyncio
    async def test_phase0_failure_aborts_pipeline(self):
        """Test Phase 0 failure aborts entire pipeline."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        from pathlib import Path
        
        orchestrator = PhaseOrchestrator()
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None
        )
        
        assert result.success is False
        assert result.phases_completed == 0
        assert result.canonical_input is None

    @pytest.mark.asyncio
    async def test_manifest_records_failure_point(self):
        """Test manifest records which phase failed."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        from pathlib import Path
        
        orchestrator = PhaseOrchestrator()
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None
        )
        
        manifest = result.manifest
        assert "phases" in manifest or len(result.errors) > 0
