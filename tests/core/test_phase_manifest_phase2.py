"""
Tests for Phase 2 (Microquestions) Integration into PhaseOrchestrator Manifest
================================================================================

Validates that the `PhaseOrchestrator` correctly:
1.  Records a manifest entry for `phase2_microquestions`.
2.  Marks the phase as 'success' only when the core orchestrator succeeds AND
    the structural invariant (non-empty questions list) is met.
3.  Marks the phase as 'failed' if the core orchestrator fails.
4.  Marks the phase as 'failed' if the structural invariant is not met.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Types to be tested
from saaaaaa.core.phases.phase_orchestrator import PhaseOrchestrator
from saaaaaa.core.orchestrator.core import PhaseResult as CorePhaseResult
from saaaaaa.core.phases.phase2_types import Phase2Result

# Dummy data for successful Phase 2 output
SUCCESSFUL_PHASE2_DATA: Phase2Result = {
    "questions": [
        {
            "base_slot": "slot1", "question_id": "q1", "question_global": 1,
            "policy_area_id": "pa1", "dimension_id": "d1", "cluster_id": "c1",
            "evidence": {}, "validation": {}, "trace": {}
        }
    ]
}

@pytest.fixture
def mock_build_processor():
    """Mocks the `build_processor` call to inject a controlled orchestrator."""
    with patch('saaaaaa.core.phases.phase_orchestrator.build_processor') as mock_build:
        mock_processor = MagicMock()
        mock_core_orchestrator = MagicMock()
        mock_processor.orchestrator = mock_core_orchestrator
        mock_core_orchestrator.process_development_plan_async = AsyncMock()
        mock_build.return_value = mock_processor
        yield mock_core_orchestrator

@pytest.mark.asyncio
async def test_phase2_manifest_success(mock_build_processor):
    """
    Verify that a successful Phase 2 run with valid data is marked
    as 'success' in the manifest.
    """
    # Arrange: Mock a successful core orchestrator result for Phase 2
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True), # Phase 0
        MagicMock(spec=CorePhaseResult, success=True), # Phase 1
        MagicMock(spec=CorePhaseResult, success=True, data=SUCCESSFUL_PHASE2_DATA, error=None, duration_ms=123.4),
    ]
    mock_build_processor.process_development_plan_async.return_value = mock_core_results

    # Act: Run the pipeline
    orchestrator = PhaseOrchestrator()
    # Mock previous phases to run successfully and provide necessary inputs
    with patch.object(orchestrator.phase0, 'run', return_value=(MagicMock(), MagicMock(duration_ms=10))), \
         patch.object(orchestrator.phase1, 'run', return_value=(MagicMock(), MagicMock(duration_ms=20))), \
         patch.object(orchestrator.adapter, 'run', return_value=(MagicMock(), MagicMock(duration_ms=5))):
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("dummy.pdf"), run_id="test_success"
        )

    # Assert
    assert result.success is True
    manifest = result.manifest
    assert "phase2_microquestions" in manifest["phases"]
    phase2_manifest_entry = manifest["phases"]["phase2_microquestions"]

    assert phase2_manifest_entry["status"] == "success"
    assert phase2_manifest_entry["error"] is None
    assert phase2_manifest_entry.get("question_count", 0) >= 1
    assert "questions_are_present_and_non_empty" in phase2_manifest_entry["invariants_checked"]
    assert phase2_manifest_entry["invariants_satisfied"] is True

@pytest.mark.asyncio
async def test_phase2_manifest_failure_structural_invariant(mock_build_processor):
    """
    Verify that a successful Phase 2 run with an EMPTY questions list
    is marked as 'failed' due to the structural invariant.
    """
    # Arrange: Mock a core result that is successful but has empty data
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True), # Phase 0
        MagicMock(spec=CorePhaseResult, success=True), # Phase 1
        MagicMock(spec=CorePhaseResult, success=True, data={"questions": []}, error=None, duration_ms=50.0),
    ]
    mock_build_processor.process_development_plan_async.return_value = mock_core_results

    # Act
    orchestrator = PhaseOrchestrator()
    with patch.object(orchestrator.phase0, 'run', return_value=(MagicMock(), MagicMock(duration_ms=10))), \
         patch.object(orchestrator.phase1, 'run', return_value=(MagicMock(), MagicMock(duration_ms=20))), \
         patch.object(orchestrator.adapter, 'run', return_value=(MagicMock(), MagicMock(duration_ms=5))):
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("dummy.pdf"), run_id="test_structural_fail"
        )

    # Assert
    assert result.success is False
    manifest = result.manifest
    
    assert "phase2_microquestions" in manifest["phases"]
    phase2_manifest_entry = manifest["phases"]["phase2_microquestions"]

    assert phase2_manifest_entry["status"] == "failed"
    assert "questions list is empty or missing" in phase2_manifest_entry["error"]
    assert phase2_manifest_entry.get("question_count", 0) == 0
    assert phase2_manifest_entry["invariants_satisfied"] is False

@pytest.mark.asyncio
async def test_phase2_manifest_failure_internal_error(mock_build_processor):
    """
    Verify that a failed Phase 2 run (e.g., an internal exception)
    is marked as 'failed' in the manifest.
    """
    # Arrange: Mock a failed core result for Phase 2
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True), # Phase 0
        MagicMock(spec=CorePhaseResult, success=True), # Phase 1
        MagicMock(spec=CorePhaseResult, success=False, data=None, error="Internal timeout", duration_ms=600.0),
    ]
    mock_build_processor.process_development_plan_async.return_value = mock_core_results

    # Act
    orchestrator = PhaseOrchestrator()
    with patch.object(orchestrator.phase0, 'run', return_value=(MagicMock(), MagicMock(duration_ms=10))), \
         patch.object(orchestrator.phase1, 'run', return_value=(MagicMock(), MagicMock(duration_ms=20))), \
         patch.object(orchestrator.adapter, 'run', return_value=(MagicMock(), MagicMock(duration_ms=5))):
        
        result = await orchestrator.run_pipeline(
            pdf_path=Path("dummy.pdf"), run_id="test_internal_fail"
        )

    # Assert
    assert result.success is False
    manifest = result.manifest
    
    assert "phase2_microquestions" in manifest["phases"]
    phase2_manifest_entry = manifest["phases"]["phase2_microquestions"]

    assert phase2_manifest_entry["status"] == "failed"
    assert "Internal timeout" in phase2_manifest_entry["error"]
    assert phase2_manifest_entry.get("question_count", 0) == 0
    assert phase2_manifest_entry["invariants_satisfied"] is False
