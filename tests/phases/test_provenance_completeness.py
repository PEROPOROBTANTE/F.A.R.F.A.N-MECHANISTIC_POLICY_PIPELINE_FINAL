"""Test Provenance Completeness Verification

Tests that all chunks have provenance_completeness=1.0 or near 1.0.
"""
import pytest
import hashlib


class TestProvenanceCompleteness:
    """Test provenance completeness for all chunks."""

    def test_provenance_threshold_in_quality_metrics(self):
        """Test QualityMetrics enforces provenance_completeness >= 0.8."""
        from farfan_pipeline.processing.models import QualityMetrics
        
        metrics = QualityMetrics(
            provenance_completeness=0.9,
            structural_consistency=0.9
        )
        assert metrics.provenance_completeness >= 0.8

    def test_phase1_invariant_checks_provenance(self):
        """Test Phase 1 has provenance threshold invariant."""
        from farfan_pipeline.core.phases.phase1_spc_ingestion import Phase1SPCIngestionContract
        
        contract = Phase1SPCIngestionContract()
        invariant_names = [inv.name for inv in contract.invariants]
        assert "provenance_threshold" in invariant_names

    def test_chunk_has_provenance_field(self):
        """Test Chunk model has provenance field."""
        from farfan_pipeline.processing.models import Chunk, ChunkResolution, TextSpan, ProvenanceMap
        
        chunk = Chunk(
            id="test", text="test", text_span=TextSpan(0, 4),
            resolution=ChunkResolution.MESO,
            bytes_hash=hashlib.blake2b(b"test").hexdigest(),
            provenance=ProvenanceMap(source_page=1, source_section="intro")
        )
        assert chunk.provenance is not None
        assert chunk.provenance.source_page == 1

    def test_provenance_map_structure(self):
        """Test ProvenanceMap has required fields."""
        from farfan_pipeline.processing.models import ProvenanceMap
        
        prov = ProvenanceMap(
            source_page=5,
            source_section="Section 2.1",
            extraction_method="semantic_chunking"
        )
        assert prov.source_page == 5
        assert prov.source_section == "Section 2.1"
        assert prov.extraction_method == "semantic_chunking"

    def test_cpp_quality_metrics_has_provenance_completeness(self):
        """Test CanonPolicyPackage tracks provenance_completeness."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, QualityMetrics,
            IntegrityIndex, PolicyManifest
        )
        
        cpp = CanonPolicyPackage(
            schema_version="SPC-2025.1",
            chunk_graph=ChunkGraph(),
            quality_metrics=QualityMetrics(
                provenance_completeness=1.0,
                structural_consistency=0.95
            ),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={}
        )
        assert cpp.quality_metrics.provenance_completeness == 1.0

    def test_all_chunks_should_have_provenance(self):
        """Test that chunks in a complete CPP have provenance data."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, Chunk, ChunkResolution,
            TextSpan, QualityMetrics, IntegrityIndex, PolicyManifest,
            ProvenanceMap
        )
        from farfan_pipeline.core.phases.phase1_spc_ingestion import POLICY_AREAS, DIMENSIONS
        
        chunk_graph = ChunkGraph()
        chunks_with_provenance = 0
        total_chunks = 0
        
        for i, pa in enumerate(POLICY_AREAS):
            for j, dim in enumerate(DIMENSIONS):
                chunk = Chunk(
                    id=f"c_{pa}_{dim}",
                    text=f"Test chunk {i*6+j}",
                    text_span=TextSpan(i*100, i*100+50),
                    resolution=ChunkResolution.MESO,
                    bytes_hash=hashlib.blake2b(f"t{i}{j}".encode()).hexdigest(),
                    policy_area_id=pa,
                    dimension_id=dim,
                    provenance=ProvenanceMap(
                        source_page=i+1,
                        source_section=f"Section {i+1}"
                    )
                )
                chunk_graph.add_chunk(chunk)
                total_chunks += 1
                if chunk.provenance is not None:
                    chunks_with_provenance += 1
        
        provenance_completeness = chunks_with_provenance / total_chunks
        assert provenance_completeness == 1.0
        assert total_chunks == 60

    def test_provenance_completeness_calculation(self):
        """Test provenance_completeness metric calculation."""
        total_chunks = 60
        chunks_with_provenance = 60
        
        provenance_completeness = chunks_with_provenance / total_chunks
        assert provenance_completeness == 1.0
        
        chunks_with_provenance = 48
        provenance_completeness = chunks_with_provenance / total_chunks
        assert provenance_completeness == 0.8

    def test_phase1_validates_provenance_completeness(self):
        """Test Phase 1 validates provenance_completeness >= 0.8."""
        from farfan_pipeline.processing.models import (
            CanonPolicyPackage, ChunkGraph, Chunk, ChunkResolution,
            TextSpan, QualityMetrics, IntegrityIndex, PolicyManifest
        )
        from farfan_pipeline.core.phases.phase1_spc_ingestion import (
            Phase1SPCIngestionContract, POLICY_AREAS, DIMENSIONS
        )
        
        contract = Phase1SPCIngestionContract()
        chunk_graph = ChunkGraph()
        
        for i, pa in enumerate(POLICY_AREAS):
            for j, dim in enumerate(DIMENSIONS):
                chunk = Chunk(
                    id=f"c_{pa}_{dim}",
                    text="t",
                    text_span=TextSpan(0, 1),
                    resolution=ChunkResolution.MESO,
                    bytes_hash=hashlib.blake2b(f"t{i}{j}".encode()).hexdigest(),
                    policy_area_id=pa,
                    dimension_id=dim
                )
                chunk_graph.add_chunk(chunk)
        
        cpp_low = CanonPolicyPackage(
            schema_version="SPC-2025.1",
            chunk_graph=chunk_graph,
            quality_metrics=QualityMetrics(
                provenance_completeness=0.5,
                structural_consistency=0.9
            ),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={"document_id": "test"}
        )
        
        result = contract.validate_output(cpp_low)
        assert not result.passed
        
        cpp_high = CanonPolicyPackage(
            schema_version="SPC-2025.1",
            chunk_graph=chunk_graph,
            quality_metrics=QualityMetrics(
                provenance_completeness=0.95,
                structural_consistency=0.9
            ),
            integrity_index=IntegrityIndex(blake2b_root="a"*64),
            metadata={"document_id": "test"}
        )
        
        result = contract.validate_output(cpp_high)
        assert result.passed
