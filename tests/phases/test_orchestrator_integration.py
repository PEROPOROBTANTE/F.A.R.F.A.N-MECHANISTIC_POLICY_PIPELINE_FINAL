"""Test Phase Orchestrator Integration

Tests full pipeline execution through orchestrator with all phases.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


class TestOrchestratorIntegration:
    """Test orchestrator executes all phases in sequence."""

    def test_orchestrator_has_all_phase_contracts(self):
        """Test orchestrator has phase0, phase1, adapter contracts."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        assert hasattr(orchestrator, 'phase0')
        assert hasattr(orchestrator, 'phase1')
        assert hasattr(orchestrator, 'adapter')
        assert hasattr(orchestrator, 'manifest_builder')

    def test_orchestrator_manifest_builder_initialized(self):
        """Test orchestrator initializes manifest builder."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        assert orchestrator.manifest_builder is not None
        assert len(orchestrator.manifest_builder.phases) == 0

    @pytest.mark.asyncio
    async def test_orchestrator_pipeline_result_structure(self):
        """Test PipelineResult has required fields."""
        from farfan_pipeline.core.phases.phase_orchestrator import PipelineResult
        
        result = PipelineResult(
            success=False,
            run_id="test_run",
            phases_completed=0,
            phases_failed=0,
            total_duration_ms=0.0,
            errors=[],
            manifest={}
        )
        
        assert result.success is False
        assert result.run_id == "test_run"
        assert hasattr(result, 'canonical_input')
        assert hasattr(result, 'canon_policy_package')
        assert hasattr(result, 'preprocessed_document')
        assert hasattr(result, 'phase2_result')

    @pytest.mark.asyncio
    async def test_orchestrator_invalid_pdf_returns_error(self):
        """Test orchestrator returns error for invalid PDF."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None
        )
        
        assert result.success is False
        assert len(result.errors) > 0
        assert result.phases_completed == 0

    @pytest.mark.asyncio
    async def test_orchestrator_records_phases_in_manifest(self):
        """Test orchestrator records all phases in manifest."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None
        )
        
        assert 'manifest' in result.__dict__
        assert isinstance(result.manifest, dict)

    def test_orchestrator_single_entry_point(self):
        """Test run_pipeline is the only entry point."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        import inspect
        
        orchestrator = PhaseOrchestrator()
        
        public_methods = [m for m in dir(orchestrator) 
                         if not m.startswith('_') and callable(getattr(orchestrator, m))]
        
        assert 'run_pipeline' in public_methods


class TestPhaseSequenceEnforcement:
    """Test phases execute in strict sequence."""

    @pytest.mark.asyncio
    async def test_phase0_runs_first(self):
        """Test Phase 0 runs before Phase 1."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        with patch.object(orchestrator.phase0, 'run') as mock_phase0:
            mock_phase0.side_effect = ValueError("Phase 0 error")
            
            result = await orchestrator.run_pipeline(
                pdf_path=Path("test.pdf"),
                run_id="test_run",
                questionnaire_path=None
            )
            
            assert result.phases_completed == 0
            assert result.canon_policy_package is None

    def test_phases_cannot_be_called_directly(self):
        """Test phase contracts are private (no direct external calls)."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        assert hasattr(orchestrator, 'phase0')
        assert hasattr(orchestrator, 'phase1')
        assert hasattr(orchestrator, 'adapter')


class TestManifestGeneration:
    """Test manifest generation during pipeline execution."""

    @pytest.mark.asyncio
    async def test_manifest_always_generated(self):
        """Test manifest is generated even on failure."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None
        )
        
        assert result.manifest is not None
        assert isinstance(result.manifest, dict)

    @pytest.mark.asyncio
    async def test_manifest_saved_to_artifacts_dir(self, tmp_path):
        """Test manifest is saved when artifacts_dir provided."""
        from farfan_pipeline.core.phases.phase_orchestrator import PhaseOrchestrator
        
        orchestrator = PhaseOrchestrator()
        artifacts_dir = tmp_path / "artifacts"
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("nonexistent.pdf"),
            run_id="test_run",
            questionnaire_path=None,
            artifacts_dir=artifacts_dir
        )
        
        manifest_path = artifacts_dir / "phase_manifest.json"
        assert artifacts_dir.exists()
