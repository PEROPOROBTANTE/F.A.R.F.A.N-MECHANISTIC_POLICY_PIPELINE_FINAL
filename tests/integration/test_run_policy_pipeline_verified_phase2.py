"""
Tests for Phase 2 Integration into the Verified Runner
========================================================

Validates that `scripts/run_policy_pipeline_verified.py`:
1.  Correctly identifies a Phase 2 success or failure.
2.  Returns a non-zero exit code when Phase 2 fails.
3.  Writes a verification manifest with `success: false` when Phase 2 fails.
4.  Propagates Phase 2 structural invariant failures as a pipeline failure.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock, ANY
from pathlib import Path
import json

# The script's runner class
from saaaaaa.scripts.run_policy_pipeline_verified import VerifiedPipelineRunner

# Types for mocking
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
def mock_core_orchestrator():
    """
    Mocks the `process_development_plan_async` method called by the
    VerifiedPipelineRunner.
    """
    # This path is where the runner will look for the method
    with patch('saaaaaa.core.orchestrator.factory.build_processor') as mock_build:
        mock_processor = MagicMock()
        mock_core_orchestrator = MagicMock()
        mock_processor.orchestrator = mock_core_orchestrator
        mock_core_orchestrator.process_development_plan_async = AsyncMock()
        mock_build.return_value = mock_processor
        yield mock_core_orchestrator

@pytest.fixture
def runner_instance(tmp_path):
    """Provides a VerifiedPipelineRunner instance with temporary artifact paths."""
    pdf_path = tmp_path / "plan.pdf"
    pdf_path.touch()
    questionnaire_path = tmp_path / "questionnaire.json"
    questionnaire_path.touch()
    artifact_path = tmp_path / "artifacts" / "dummy.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("{}", encoding="utf-8")
    
    preprocessed_mock = MagicMock()
    preprocessed_mock.chunks = [1, 2, 3, 4, 5]
    preprocessed_mock.processing_mode = "chunked"
    preprocessed_mock.sentences = ["one"]
    preprocessed_mock.raw_text = "text"

    # Mock away the parts of the runner we don't want to execute
    with patch.object(VerifiedPipelineRunner, 'verify_input', return_value=True), \
         patch.object(VerifiedPipelineRunner, 'run_spc_ingestion', return_value=MagicMock()), \
         patch.object(VerifiedPipelineRunner, 'run_cpp_adapter', return_value=preprocessed_mock), \
         patch.object(VerifiedPipelineRunner, 'save_artifacts', return_value=([str(artifact_path)], {str(artifact_path): "fakehash"})):

        runner = VerifiedPipelineRunner(
            plan_pdf_path=pdf_path,
            artifacts_dir=tmp_path / "artifacts",
            questionnaire_path=questionnaire_path,
        )
        yield runner

@pytest.mark.asyncio
async def test_runner_success_with_valid_phase2(runner_instance, mock_core_orchestrator):
    """
    Verify the runner succeeds when Phase 2 is successful and passes invariants.
    """
    # Arrange: Mock a successful core orchestrator result for Phase 2
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True, phase_id='0'),
        MagicMock(spec=CorePhaseResult, success=True, phase_id='1'),
        MagicMock(spec=CorePhaseResult, success=True, data=SUCCESSFUL_PHASE2_DATA, error=None, phase_id='2'),
    ]
    mock_core_orchestrator.process_development_plan_async.return_value = mock_core_results

    # Act: Run the pipeline
    success = await runner_instance.run()

    # Assert: The pipeline should succeed
    assert success is True
    assert runner_instance.phases_failed == 0
    assert len(runner_instance.errors) == 0

    # Assert manifest reflects success
    manifest_path = runner_instance.artifacts_dir / "verification_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["success"] is True
    assert manifest["phases"]["phase2"]["success"] is True

@pytest.mark.asyncio
async def test_runner_fails_on_phase2_structural_invariant(runner_instance, mock_core_orchestrator):
    """
    Verify the runner fails if Phase 2 succeeds but its output is structurally invalid.
    """
    # Arrange: Mock a Phase 2 result with an empty questions list
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True, phase_id='0'),
        MagicMock(spec=CorePhaseResult, success=True, phase_id='1'),
        MagicMock(spec=CorePhaseResult, success=True, data={"questions": []}, error=None, phase_id='2'),
    ]
    mock_core_orchestrator.process_development_plan_async.return_value = mock_core_results

    # Act: Run the pipeline
    success = await runner_instance.run()

    # Assert: The pipeline should fail
    assert success is False
    assert runner_instance.phases_failed > 0
    assert len(runner_instance.errors) > 0
    assert "questions list is empty or missing" in runner_instance.errors[0]

    # Assert manifest reflects failure
    manifest_path = runner_instance.artifacts_dir / "verification_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["success"] is False
    assert manifest["phases"]["phase2"]["success"] is False
    assert "questions list is empty or missing" in manifest["errors"][0]

@pytest.mark.asyncio
async def test_runner_fails_on_phase2_internal_error(runner_instance, mock_core_orchestrator):
    """
    Verify the runner fails if Phase 2 fails internally within the core orchestrator.
    """
    # Arrange: Mock a failed Phase 2 result
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True, phase_id='0'),
        MagicMock(spec=CorePhaseResult, success=True, phase_id='1'),
        MagicMock(spec=CorePhaseResult, success=False, data=None, error="Internal Exception", phase_id='2'),
    ]
    mock_core_orchestrator.process_development_plan_async.return_value = mock_core_results

    # Act: Run the pipeline
    success = await runner_instance.run()

    # Assert: The pipeline should fail
    assert success is False
    assert runner_instance.phases_failed > 0
    assert len(runner_instance.errors) > 0
    assert "Phase 2 failed internally" in runner_instance.errors[0]

    # Assert manifest reflects failure
    manifest_path = runner_instance.artifacts_dir / "verification_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["success"] is False
    assert manifest["phases"]["phase2"]["success"] is False
    assert "Phase 2 failed internally" in manifest["errors"][0]

@pytest.mark.asyncio
async def test_runner_fails_if_phase2_missing_from_results(runner_instance, mock_core_orchestrator):
    """
    Verify the runner fails if the core orchestrator returns fewer results than expected.
    """
    # Arrange: Mock a truncated result list
    mock_core_results = [
        MagicMock(spec=CorePhaseResult, success=True, phase_id='0'),
    ]
    mock_core_orchestrator.process_development_plan_async.return_value = mock_core_results

    # Act: Run the pipeline
    success = await runner_instance.run()

    # Assert: The pipeline should fail
    assert success is False
    assert runner_instance.phases_failed > 0
    assert len(runner_instance.errors) > 0
    assert "did not produce a result for Phase 2" in runner_instance.errors[0]
    
    # Assert manifest reflects failure
    manifest_path = runner_instance.artifacts_dir / "verification_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as f:
        manifest = json.load(f)
    assert manifest["success"] is False
    assert manifest["phases"]["phase2"]["success"] is False
    assert "did not produce a result for Phase 2" in manifest["errors"][0]
