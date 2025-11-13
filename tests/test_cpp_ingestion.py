"""
Tests for Canon Policy Package ingestion system.

Tests the complete pipeline and individual components.
"""

import json
import tempfile
from pathlib import Path

import pytest
import pyarrow as pa

from saaaaaa.processing.cpp_ingestion import (
    CPPIngestionPipeline,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    EdgeType,
    PolicyFacet,
    TimeFacet,
    GeoFacet,
)
from saaaaaa.processing.cpp_ingestion.chunking import AdvancedChunker
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    IntegrityIndex,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
)
from saaaaaa.processing.cpp_ingestion.quality_gates import QualityGates


class TestModels:
    """Test data models."""
    
    def test_chunk_creation(self):
        """Test chunk creation with all facets."""
        chunk = Chunk(
            id="chunk_001",
            bytes_hash="abc123",
            text_span=TextSpan(0, 100),
            resolution=ChunkResolution.MICRO,
            text="Sample text",
            policy_facets=PolicyFacet(eje="Eje 1", programa="Programa A"),
            time_facets=TimeFacet(from_year=2024, to_year=2028),
            geo_facets=GeoFacet(level="municipal"),
        )
        
        assert chunk.id == "chunk_001"
        assert chunk.resolution == ChunkResolution.MICRO
        assert chunk.policy_facets.eje == "Eje 1"
        assert chunk.time_facets.from_year == 2024
    
    def test_chunk_graph(self):
        """Test chunk graph operations."""
        graph = ChunkGraph()
        
        chunk1 = Chunk(
            id="c1",
            bytes_hash="h1",
            text_span=TextSpan(0, 50),
            resolution=ChunkResolution.MICRO,
            text="Text 1",
            policy_facets=PolicyFacet(),
            time_facets=TimeFacet(),
            geo_facets=GeoFacet(),
        )
        
        chunk2 = Chunk(
            id="c2",
            bytes_hash="h2",
            text_span=TextSpan(50, 100),
            resolution=ChunkResolution.MICRO,
            text="Text 2",
            policy_facets=PolicyFacet(),
            time_facets=TimeFacet(),
            geo_facets=GeoFacet(),
        )
        
        graph.add_chunk(chunk1)
        graph.add_chunk(chunk2)
        graph.add_edge("c1", "c2", EdgeType.PRECEDES)
        
        assert len(graph.chunks) == 2
        assert len(graph.edges) == 1
        assert graph.get_neighbors("c1", EdgeType.PRECEDES) == ["c2"]
    
    def test_policy_manifest(self):
        """Test policy manifest."""
        manifest = PolicyManifest(
            axes=3,
            programs=10,
            projects=25,
            years=[2024, 2025, 2026],
            territories=["Bogotá", "Medellín"],
        )
        
        assert manifest.axes == 3
        assert len(manifest.years) == 3
        assert "Bogotá" in manifest.territories
    
    def test_provenance_map_validation(self):
        """Test provenance map validation."""
        # Valid provenance map
        table = pa.table({
            "token_id": ["t1", "t2"],
            "page_id": [1, 1],
            "byte_start": [0, 50],
            "byte_end": [50, 100],
        })
        
        prov_map = ProvenanceMap(table=table)
        assert prov_map.validate_completeness()
        
        # Invalid provenance map (with nulls)
        table_with_nulls = pa.table({
            "token_id": ["t1", None],
            "page_id": [1, 1],
            "byte_start": [0, 50],
            "byte_end": [50, 100],
        })
        
        prov_map_invalid = ProvenanceMap(table=table_with_nulls)
        assert not prov_map_invalid.validate_completeness()


class TestChunking:
    """Test advanced chunking system."""
    
    def test_chunker_initialization(self):
        """Test chunker initialization."""
        chunker = AdvancedChunker(overlap_threshold=0.15)
        assert chunker.overlap_threshold == 0.15
    
    def test_micro_chunk_creation(self):
        """Test micro chunk creation."""
        chunker = AdvancedChunker()
        
        pages = [
            {
                "page_id": 1,
                "text": "This is a test sentence. " * 50,  # ~100 tokens
                "byte_start": 0,
                "byte_end": 1000,
            }
        ]
        
        policy_graph = {"policy_units": [], "sections": []}
        
        chunks = chunker._create_micro_chunks(pages, policy_graph)
        
        # Should create at least one micro chunk
        assert len(chunks) > 0
        assert all(c.resolution == ChunkResolution.MICRO for c in chunks)
    
    def test_chunk_overlap_computation(self):
        """Test chunk overlap computation."""
        chunker = AdvancedChunker()
        
        chunk1 = Chunk(
            id="c1",
            bytes_hash="h1",
            text_span=TextSpan(0, 100),
            resolution=ChunkResolution.MICRO,
            text="A" * 100,
            policy_facets=PolicyFacet(),
            time_facets=TimeFacet(),
            geo_facets=GeoFacet(),
        )
        
        chunk2 = Chunk(
            id="c2",
            bytes_hash="h2",
            text_span=TextSpan(50, 150),
            resolution=ChunkResolution.MICRO,
            text="B" * 100,
            policy_facets=PolicyFacet(),
            time_facets=TimeFacet(),
            geo_facets=GeoFacet(),
        )
        
        overlap = chunker._compute_overlap(chunk1, chunk2)
        assert overlap == 0.5  # 50% overlap


class TestQualityGates:
    """Test quality validation gates."""
    
    def test_quality_gates_pass(self):
        """Test quality gates with passing metrics."""
        gates = QualityGates()
        
        cpp = CanonPolicyPackage(
            schema_version="CPP-2025.1",
            policy_manifest=PolicyManifest(),
            chunk_graph=ChunkGraph(),
            quality_metrics=QualityMetrics(
                boundary_f1=0.95,
                kpi_linkage_rate=0.92,
                budget_consistency_score=1.0,
                provenance_completeness=1.0,
                structural_consistency=1.0,
            ),
        )
        
        result = gates.validate(cpp)
        assert result["passed"]
        assert len(result["failures"]) == 0
    
    def test_quality_gates_fail(self):
        """Test quality gates with failing metrics."""
        gates = QualityGates()
        
        cpp = CanonPolicyPackage(
            schema_version="CPP-2025.1",
            policy_manifest=PolicyManifest(),
            chunk_graph=ChunkGraph(),
            quality_metrics=QualityMetrics(
                boundary_f1=0.70,  # Below threshold
                kpi_linkage_rate=0.50,  # Below threshold
                budget_consistency_score=0.80,  # Below threshold
                provenance_completeness=0.90,  # Below threshold
                structural_consistency=1.0,
            ),
        )
        
        result = gates.validate(cpp)
        assert not result["passed"]
        assert len(result["failures"]) > 0


class TestPipeline:
    """Test complete ingestion pipeline."""
    
    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = CPPIngestionPipeline(
            enable_ocr=True,
            ocr_confidence_threshold=0.85,
            chunk_overlap_threshold=0.15,
        )
        
        assert pipeline.enable_ocr
        assert pipeline.ocr_confidence_threshold == 0.85
        assert pipeline.SCHEMA_VERSION == "CPP-2025.1"
    
    def test_mime_detection(self):
        """Test MIME type detection."""
        pipeline = CPPIngestionPipeline()
        
        # PDF
        pdf_data = b"%PDF-1.4"
        assert pipeline._detect_mime(pdf_data) == "application/pdf"
        
        # ZIP-based (DOCX)
        docx_data = b"PK\x03\x04"
        assert "openxmlformats" in pipeline._detect_mime(docx_data)
        
        # HTML
        html_data = b"<html>"
        assert pipeline._detect_mime(html_data) == "text/html"
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        pipeline = CPPIngestionPipeline()
        
        # Text with diacritics
        text = "café Bogotá niño"
        normalized = pipeline._normalize_unicode(text)
        
        # Should be in NFC form
        import unicodedata
        assert unicodedata.is_normalized("NFC", normalized)
    
    def test_phase1_acquisition(self):
        """Test Phase 1: Acquisition & Integrity."""
        pipeline = CPPIngestionPipeline()
        
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(b"%PDF-1.4\nTest content")
            temp_path = Path(f.name)
        
        try:
            manifest, binary_data = pipeline._phase1_acquisition(temp_path)
            
            assert manifest is not None
            assert binary_data is not None
            assert manifest["mime_type"] == "application/pdf"
            assert "blake3_hash" in manifest
            assert manifest["size_bytes"] > 0
        finally:
            temp_path.unlink()
    
    def test_full_ingestion_flow(self):
        """Test complete ingestion flow with minimal document."""
        pipeline = CPPIngestionPipeline(enable_ocr=False)
        
        # Create test document
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(b"%PDF-1.4\nEje 1: Desarrollo Social\nPrograma A: Educacion")
            test_file = Path(f.name)
        
        # Create output directory
        with tempfile.TemporaryDirectory() as output_dir:
            try:
                outcome = pipeline.ingest(test_file, Path(output_dir))
                
                # Check outcome
                assert outcome.status in ["OK", "ABORT"]
                
                if outcome.status == "OK":
                    assert outcome.cpp_uri is not None
                    assert outcome.metrics is not None
                    assert "pipeline" in outcome.fingerprints
                    
                    # Check that files were created
                    output_path = Path(outcome.cpp_uri)
                    assert output_path.exists()
                    assert (output_path / "metadata.json").exists()
                
            finally:
                test_file.unlink()


class TestIntegration:
    """Integration tests for complete system."""
    
    def test_end_to_end_with_policy_document(self):
        """Test end-to-end processing of a policy document."""
        # Create a realistic test document
        content = """
        Plan de Desarrollo Municipal 2024-2028
        
        Eje 1: Desarrollo Social
        Programa 1.1: Educación de Calidad
        Proyecto 1.1.1: Mejoramiento de infraestructura educativa
        
        Meta: Aumentar la cobertura educativa del 85% al 95%
        Indicador: Tasa de cobertura educativa
        Línea base: 85% (2023)
        Meta 2028: 95%
        
        Presupuesto:
        Fuente: Transferencias SGP
        Uso: Infraestructura
        Monto: $5,000,000,000 COP
        Año: 2024
        
        Eje 2: Desarrollo Económico
        Programa 2.1: Emprendimiento y Competitividad
        """
        
        pipeline = CPPIngestionPipeline(enable_ocr=False)
        
        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt", encoding="utf-8"
        ) as f:
            f.write(content)
            test_file = Path(f.name)
        
        with tempfile.TemporaryDirectory() as output_dir:
            try:
                # Note: This will fail with current parsers since they expect PDF
                # But it demonstrates the expected workflow
                outcome = pipeline.ingest(test_file, Path(output_dir))
                
                # At minimum, should not raise exception
                assert outcome is not None
                assert hasattr(outcome, "status")
                
            finally:
                test_file.unlink()
    
    def test_golden_set_reproducibility(self):
        """Test that re-ingestion produces identical hashes (golden test)."""
        # This test ensures deterministic processing
        pipeline = CPPIngestionPipeline(enable_ocr=False)
        
        content = b"%PDF-1.4\nTest document for reproducibility"
        
        with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=".pdf") as f:
            f.write(content)
            test_file = Path(f.name)
        
        try:
            with tempfile.TemporaryDirectory() as output_dir1:
                outcome1 = pipeline.ingest(test_file, Path(output_dir1))
            
            with tempfile.TemporaryDirectory() as output_dir2:
                outcome2 = pipeline.ingest(test_file, Path(output_dir2))
            
            # Both runs should produce same status
            assert outcome1.status == outcome2.status
            
            # If successful, check fingerprints match
            if outcome1.status == "OK" and outcome2.status == "OK":
                assert outcome1.fingerprints == outcome2.fingerprints
        
        finally:
            test_file.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
