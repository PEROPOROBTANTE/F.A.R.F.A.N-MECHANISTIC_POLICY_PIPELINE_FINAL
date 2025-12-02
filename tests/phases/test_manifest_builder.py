"""Test Phase Manifest Builder

Tests manifest completeness, phase recording, and artifact tracking.
"""
import pytest
from pathlib import Path
from datetime import datetime, timezone

from farfan_pipeline.core.phases.phase_protocol import (
    PhaseManifestBuilder, PhaseMetadata, ContractValidationResult,
    PhaseArtifact
)


class TestManifestBuilder:
    """Test PhaseManifestBuilder functionality."""

    def test_manifest_builder_initialization(self):
        """Test manifest builder initializes empty."""
        builder = PhaseManifestBuilder()
        assert len(builder.phases) == 0

    def test_record_phase_success(self):
        """Test recording successful phase execution."""
        builder = PhaseManifestBuilder()
        
        metadata = PhaseMetadata(
            phase_name="test_phase",
            started_at="2025-01-01T00:00:00Z",
            finished_at="2025-01-01T00:00:01Z",
            duration_ms=1000.0,
            success=True
        )
        
        input_validation = ContractValidationResult(
            passed=True, contract_type="input", phase_name="test_phase"
        )
        
        output_validation = ContractValidationResult(
            passed=True, contract_type="output", phase_name="test_phase"
        )
        
        builder.record_phase(
            phase_name="test_phase",
            metadata=metadata,
            input_validation=input_validation,
            output_validation=output_validation,
            invariants_checked=["inv1", "inv2"],
            artifacts=[]
        )
        
        assert "test_phase" in builder.phases
        assert builder.phases["test_phase"]["status"] == "success"
        assert builder.phases["test_phase"]["duration_ms"] == 1000.0

    def test_record_phase_failure(self):
        """Test recording failed phase execution."""
        builder = PhaseManifestBuilder()
        
        metadata = PhaseMetadata(
            phase_name="test_phase",
            started_at="2025-01-01T00:00:00Z",
            finished_at="2025-01-01T00:00:01Z",
            duration_ms=500.0,
            success=False,
            error="Test error"
        )
        
        input_validation = ContractValidationResult(
            passed=False, contract_type="input", phase_name="test_phase",
            errors=["Input validation failed"]
        )
        
        output_validation = ContractValidationResult(
            passed=False, contract_type="output", phase_name="test_phase"
        )
        
        builder.record_phase(
            phase_name="test_phase",
            metadata=metadata,
            input_validation=input_validation,
            output_validation=output_validation,
            invariants_checked=[],
            artifacts=[]
        )
        
        assert builder.phases["test_phase"]["status"] == "failed"
        assert builder.phases["test_phase"]["error"] == "Test error"

    def test_manifest_to_dict(self):
        """Test manifest conversion to dictionary."""
        builder = PhaseManifestBuilder()
        
        metadata = PhaseMetadata(
            phase_name="phase1", started_at="2025-01-01T00:00:00Z",
            finished_at="2025-01-01T00:00:01Z", success=True
        )
        
        builder.record_phase(
            "phase1", metadata,
            ContractValidationResult(True, "input", "phase1"),
            ContractValidationResult(True, "output", "phase1"),
            [], []
        )
        
        manifest_dict = builder.to_dict()
        assert "phases" in manifest_dict
        assert "total_phases" in manifest_dict
        assert "successful_phases" in manifest_dict
        assert "failed_phases" in manifest_dict
        assert manifest_dict["total_phases"] == 1
        assert manifest_dict["successful_phases"] == 1

    def test_manifest_completeness_all_phases(self):
        """Test manifest records all phases (0, 1, adapter, 2)."""
        builder = PhaseManifestBuilder()
        
        for phase_name in ["phase0_input_validation", "phase1_spc_ingestion", 
                           "phase1_to_phase2_adapter", "phase2_microquestions"]:
            metadata = PhaseMetadata(
                phase_name=phase_name,
                started_at="2025-01-01T00:00:00Z",
                finished_at="2025-01-01T00:00:01Z",
                success=True
            )
            builder.record_phase(
                phase_name, metadata,
                ContractValidationResult(True, "input", phase_name),
                ContractValidationResult(True, "output", phase_name),
                [], []
            )
        
        manifest_dict = builder.to_dict()
        assert manifest_dict["total_phases"] == 4
        assert all(p in builder.phases for p in [
            "phase0_input_validation", "phase1_spc_ingestion",
            "phase1_to_phase2_adapter", "phase2_microquestions"
        ])

    def test_manifest_tracks_invariants(self):
        """Test manifest tracks which invariants were checked."""
        builder = PhaseManifestBuilder()
        
        metadata = PhaseMetadata(
            phase_name="test_phase",
            started_at="2025-01-01T00:00:00Z",
            success=True
        )
        
        invariants = ["validation_passed", "hash_format", "count_positive"]
        
        builder.record_phase(
            "test_phase", metadata,
            ContractValidationResult(True, "input", "test_phase"),
            ContractValidationResult(True, "output", "test_phase"),
            invariants, []
        )
        
        assert builder.phases["test_phase"]["invariants_checked"] == invariants
        assert builder.phases["test_phase"]["invariants_satisfied"] is True

    def test_manifest_save(self, tmp_path):
        """Test manifest can be saved to file."""
        builder = PhaseManifestBuilder()
        
        metadata = PhaseMetadata(
            phase_name="test_phase",
            started_at="2025-01-01T00:00:00Z",
            success=True
        )
        
        builder.record_phase(
            "test_phase", metadata,
            ContractValidationResult(True, "input", "test_phase"),
            ContractValidationResult(True, "output", "test_phase"),
            [], []
        )
        
        manifest_path = tmp_path / "manifest.json"
        builder.save(manifest_path)
        
        assert manifest_path.exists()
        import json
        with open(manifest_path) as f:
            saved = json.load(f)
        assert "phases" in saved
        assert "test_phase" in saved["phases"]
