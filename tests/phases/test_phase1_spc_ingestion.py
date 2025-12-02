"""Test Phase 1: SPC Ingestion Contract

Tests 60 chunks, PA×DIM tagging, quality thresholds, hash stability.
"""
import hashlib
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timezone

from farfan_pipeline.core.phases.phase0_input_validation import CanonicalInput
from farfan_pipeline.core.phases.phase1_spc_ingestion import (
    Phase1SPCIngestionContract, EXPECTED_CHUNK_COUNT, POLICY_AREAS, DIMENSIONS
)


class TestPhase1Contract:
    """Test Phase 1 contract validation."""

    def test_expected_chunk_count(self):
        """Test expected 60 chunks (10 PA × 6 DIM)."""
        assert EXPECTED_CHUNK_COUNT == 60
        assert len(POLICY_AREAS) == 10
        assert len(DIMENSIONS) == 6

    def test_input_validation_requires_canonical_input(self, tmp_path):
        """Test input must be CanonicalInput from Phase 0."""
        contract = Phase1SPCIngestionContract()
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"%PDF-1.4\n")
        q = tmp_path / "q.json"
        q.write_text('{}')

        valid_input = CanonicalInput(
            document_id="test", run_id="r1", pdf_path=pdf,
            pdf_sha256="a"*64, pdf_size_bytes=100, pdf_page_count=5,
            questionnaire_path=q, questionnaire_sha256="b"*64,
            created_at=datetime.now(timezone.utc), phase0_version="1.0.0",
            validation_passed=True, validation_errors=[], validation_warnings=[]
        )
        result = contract.validate_input(valid_input)
        assert result.passed

    def test_output_requires_60_chunks(self):
        """Test output must have exactly 60 chunks."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, Chunk, ChunkResolution,
            TextSpan, QualityMetrics, IntegrityIndex, PolicyManifest
        )
        contract = Phase1SPCIngestionContract()
        
        chunk_graph = ChunkGraph()
        for i, pa in enumerate(POLICY_AREAS):
            for j, dim in enumerate(DIMENSIONS):
                chunk = Chunk(
                    id=f"c_{pa}_{dim}", text=f"Chunk {i*6+j}",
                    text_span=TextSpan(i*100, i*100+50),
                    resolution=ChunkResolution.MESO,
                    bytes_hash=hashlib.blake2b(f"t{i}{j}".encode()).hexdigest(),
                    policy_area_id=pa, dimension_id=dim
                )
                chunk_graph.add_chunk(chunk)

        cpp = CanonPolicyPackage(
            schema_version="SPC-2025.1", chunk_graph=chunk_graph,
            policy_manifest=PolicyManifest(),
            quality_metrics=QualityMetrics(provenance_completeness=0.9, structural_consistency=0.9),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={"document_id": "test"}
        )
        
        result = contract.validate_output(cpp)
        assert result.passed

    def test_provenance_threshold_enforced(self):
        """Test provenance_completeness >= 0.8 enforced."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, Chunk, ChunkResolution,
            TextSpan, QualityMetrics, IntegrityIndex, PolicyManifest
        )
        contract = Phase1SPCIngestionContract()
        
        chunk_graph = ChunkGraph()
        for i, pa in enumerate(POLICY_AREAS):
            for j, dim in enumerate(DIMENSIONS):
                chunk = Chunk(
                    id=f"c_{pa}_{dim}", text="t",
                    text_span=TextSpan(0, 1), resolution=ChunkResolution.MESO,
                    bytes_hash=hashlib.blake2b(f"t{i}{j}".encode()).hexdigest(),
                    policy_area_id=pa, dimension_id=dim
                )
                chunk_graph.add_chunk(chunk)

        cpp = CanonPolicyPackage(
            schema_version="SPC-2025.1", chunk_graph=chunk_graph,
            policy_manifest=PolicyManifest(),
            quality_metrics=QualityMetrics(provenance_completeness=0.5, structural_consistency=0.9),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={"document_id": "test"}
        )
        
        result = contract.validate_output(cpp)
        assert not result.passed


class TestPhase1HashStability:
    """Test BLAKE2b hash stability."""

    def test_blake2b_deterministic(self):
        """Test BLAKE2b produces same hash for same content."""
        content = b"test chunk content"
        hash1 = hashlib.blake2b(content).hexdigest()
        hash2 = hashlib.blake2b(content).hexdigest()
        assert hash1 == hash2
        assert len(hash1) == 128
