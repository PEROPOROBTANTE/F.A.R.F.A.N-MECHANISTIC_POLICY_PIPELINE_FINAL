"""Tests for CPP Adapter.

Tests conversion from Canon Policy Package to PreprocessedDocument.
"""

from __future__ import annotations

import pytest

from saaaaaa.utils.cpp_adapter import CPPAdapter, CPPAdapterError, adapt_cpp_to_orchestrator
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    PolicyFacet,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
    TimeFacet,
    GeoFacet,
    IntegrityIndex,
)


def create_test_chunk(
    chunk_id: str,
    text: str,
    start: int,
    end: int,
    resolution: ChunkResolution = ChunkResolution.MICRO,
) -> Chunk:
    """Create a test chunk."""
    return Chunk(
        id=chunk_id,
        bytes_hash=f"hash_{chunk_id}",
        text_span=TextSpan(start=start, end=end),
        resolution=resolution,
        text=text,
        policy_facets=PolicyFacet(),
        time_facets=TimeFacet(),
        geo_facets=GeoFacet(),
        confidence=Confidence(layout=1.0),
    )


def create_test_cpp(chunks: list[Chunk]) -> CanonPolicyPackage:
    """Create a test CPP with given chunks."""
    chunk_graph = ChunkGraph()
    for chunk in chunks:
        chunk_graph.add_chunk(chunk)
    
    return CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(
            axes=3,
            programs=10,
            projects=25,
        ),
        chunk_graph=chunk_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(
            provenance_completeness=1.0,
            structural_consistency=0.95,
        ),
        integrity_index=IntegrityIndex(
            blake3_root="test_root_hash"
        ),
    )


def test_cpp_adapter_initialization() -> None:
    """Test CPP adapter initialization."""
    adapter = CPPAdapter()
    
    metrics = adapter.get_metrics()
    assert metrics["conversions_count"] == 0


def test_to_preprocessed_document_basic() -> None:
    """Test basic CPP to PreprocessedDocument conversion."""
    chunks = [
        create_test_chunk("chunk_1", "First chunk text.", 0, 17),
        create_test_chunk("chunk_2", "Second chunk text.", 18, 36),
        create_test_chunk("chunk_3", "Third chunk text.", 37, 54),
    ]
    
    cpp = create_test_cpp(chunks)
    adapter = CPPAdapter()
    
    doc = adapter.to_preprocessed_document(cpp, document_id="test_doc")
    
    assert doc.document_id == "test_doc"
    assert "First chunk text." in doc.raw_text
    assert "Second chunk text." in doc.raw_text
    assert "Third chunk text." in doc.raw_text
    assert len(doc.sentences) == 3
    assert len(doc.metadata["chunks"]) == 3


def test_to_preprocessed_document_chunk_ordering() -> None:
    """Test that chunks are ordered by text_span.start."""
    # Create chunks out of order
    chunks = [
        create_test_chunk("chunk_2", "Second chunk.", 20, 33),
        create_test_chunk("chunk_1", "First chunk.", 0, 12),
        create_test_chunk("chunk_3", "Third chunk.", 34, 46),
    ]
    
    cpp = create_test_cpp(chunks)
    adapter = CPPAdapter()
    
    doc = adapter.to_preprocessed_document(cpp)
    
    # Verify ordering in raw_text
    assert doc.raw_text.startswith("First chunk.")
    assert doc.raw_text.endswith("Third chunk.")
    
    # Verify ordering in sentences
    assert doc.sentences[0]["chunk_id"] == "chunk_1"
    assert doc.sentences[1]["chunk_id"] == "chunk_2"
    assert doc.sentences[2]["chunk_id"] == "chunk_3"


def test_to_preprocessed_document_with_resolution_filter() -> None:
    """Test filtering chunks by resolution."""
    chunks = [
        create_test_chunk("micro_1", "Micro chunk 1", 0, 13, ChunkResolution.MICRO),
        create_test_chunk("meso_1", "Meso chunk 1", 14, 26, ChunkResolution.MESO),
        create_test_chunk("micro_2", "Micro chunk 2", 27, 40, ChunkResolution.MICRO),
        create_test_chunk("macro_1", "Macro chunk 1", 41, 54, ChunkResolution.MACRO),
    ]
    
    cpp = create_test_cpp(chunks)
    adapter = CPPAdapter()
    
    # Filter to micro only
    doc = adapter.to_preprocessed_document(
        cpp,
        preserve_chunk_resolution=ChunkResolution.MICRO
    )
    
    assert len(doc.sentences) == 2
    assert "Micro chunk 1" in doc.raw_text
    assert "Micro chunk 2" in doc.raw_text
    assert "Meso chunk 1" not in doc.raw_text
    assert "Macro chunk 1" not in doc.raw_text


def test_to_preprocessed_document_provenance_completeness() -> None:
    """Test provenance completeness calculation."""
    # Create chunks with and without provenance
    chunk_with_prov = create_test_chunk("chunk_1", "Text with provenance", 0, 20)
    chunk_with_prov.provenance = {
        "page_id": 1,
        "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 100},
        "parser_id": "test_parser",
        "byte_range": (0, 20),
    }
    
    chunk_without_prov = create_test_chunk("chunk_2", "Text without provenance", 21, 44)
    
    cpp = create_test_cpp([chunk_with_prov, chunk_without_prov])
    adapter = CPPAdapter()
    
    doc = adapter.to_preprocessed_document(cpp)
    
    # Should be 0.5 (1 out of 2 chunks have provenance)
    assert doc.metadata["provenance_completeness"] == 0.5
    assert doc.metadata["chunks"][0]["has_provenance"] is True
    assert doc.metadata["chunks"][1]["has_provenance"] is False


def test_to_preprocessed_document_preserves_policy_manifest() -> None:
    """Test that policy manifest is preserved in metadata."""
    chunks = [create_test_chunk("chunk_1", "Test chunk", 0, 10)]
    cpp = create_test_cpp(chunks)
    cpp.policy_manifest.axes = 5
    cpp.policy_manifest.programs = 20
    cpp.policy_manifest.years = [2024, 2025, 2026]
    
    adapter = CPPAdapter()
    doc = adapter.to_preprocessed_document(cpp)
    
    assert doc.metadata["policy_manifest"]["axes"] == 5
    assert doc.metadata["policy_manifest"]["programs"] == 20
    assert doc.metadata["policy_manifest"]["years"] == [2024, 2025, 2026]


def test_to_preprocessed_document_preserves_quality_metrics() -> None:
    """Test that quality metrics are preserved in metadata."""
    chunks = [create_test_chunk("chunk_1", "Test chunk", 0, 10)]
    cpp = create_test_cpp(chunks)
    cpp.quality_metrics.boundary_f1 = 0.92
    cpp.quality_metrics.kpi_linkage_rate = 0.87
    
    adapter = CPPAdapter()
    doc = adapter.to_preprocessed_document(cpp)
    
    assert doc.metadata["quality_metrics"]["boundary_f1"] == 0.92
    assert doc.metadata["quality_metrics"]["kpi_linkage_rate"] == 0.87


def test_to_preprocessed_document_empty_cpp_error() -> None:
    """Test error when CPP has no chunks."""
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=ChunkGraph(),  # Empty
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="test"),
    )
    
    adapter = CPPAdapter()
    
    with pytest.raises(CPPAdapterError, match="chunk graph is empty"):
        adapter.to_preprocessed_document(cpp)


def test_to_preprocessed_document_none_cpp_error() -> None:
    """Test error when CPP is None."""
    adapter = CPPAdapter()
    
    with pytest.raises(CPPAdapterError, match="Cannot convert None CPP"):
        adapter.to_preprocessed_document(None)  # type: ignore


def test_to_preprocessed_document_invalid_resolution_filter() -> None:
    """Test error when filtered resolution has no chunks."""
    chunks = [
        create_test_chunk("chunk_1", "Micro chunk", 0, 11, ChunkResolution.MICRO),
        create_test_chunk("chunk_2", "Another micro", 12, 25, ChunkResolution.MICRO),
    ]
    
    cpp = create_test_cpp(chunks)
    adapter = CPPAdapter()
    
    with pytest.raises(CPPAdapterError, match="No chunks found with resolution"):
        adapter.to_preprocessed_document(
            cpp,
            preserve_chunk_resolution=ChunkResolution.MACRO
        )


def test_to_preprocessed_document_with_budget_tables() -> None:
    """Test extraction of budget data into tables."""
    from saaaaaa.processing.cpp_ingestion.models import BudgetInfo
    
    chunk_with_budget = create_test_chunk("chunk_1", "Budget chunk", 0, 12)
    chunk_with_budget.budget = BudgetInfo(
        source="Tesoro Nacional",
        use="Educación",
        amount=1_000_000.0,
        year=2025,
        currency="COP",
    )
    
    chunk_without_budget = create_test_chunk("chunk_2", "Regular chunk", 13, 26)
    
    cpp = create_test_cpp([chunk_with_budget, chunk_without_budget])
    adapter = CPPAdapter()
    
    doc = adapter.to_preprocessed_document(cpp)
    
    assert len(doc.tables) == 1
    assert doc.tables[0]["source"] == "Tesoro Nacional"
    assert doc.tables[0]["use"] == "Educación"
    assert doc.tables[0]["amount"] == 1_000_000.0
    assert doc.tables[0]["year"] == 2025


def test_adapt_cpp_to_orchestrator_convenience_function() -> None:
    """Test convenience function."""
    chunks = [create_test_chunk("chunk_1", "Test chunk", 0, 10)]
    cpp = create_test_cpp(chunks)
    
    doc = adapt_cpp_to_orchestrator(cpp, document_id="test_id")
    
    assert doc.document_id == "test_id"
    assert "Test chunk" in doc.raw_text


def test_adapter_metrics_tracking() -> None:
    """Test that adapter tracks conversion metrics."""
    adapter = CPPAdapter()
    
    chunks = [create_test_chunk("chunk_1", "Test", 0, 4)]
    cpp = create_test_cpp(chunks)
    
    adapter.to_preprocessed_document(cpp, document_id="doc1")
    adapter.to_preprocessed_document(cpp, document_id="doc2")
    adapter.to_preprocessed_document(cpp, document_id="doc3")
    
    metrics = adapter.get_metrics()
    assert metrics["conversions_count"] == 3


def test_to_preprocessed_document_metadata_completeness() -> None:
    """Test that metadata includes all expected fields."""
    chunks = [create_test_chunk("chunk_1", "Test chunk", 0, 10)]
    cpp = create_test_cpp(chunks)
    
    adapter = CPPAdapter()
    doc = adapter.to_preprocessed_document(cpp)
    
    # Check required metadata fields
    assert "adapter_source" in doc.metadata
    assert "schema_version" in doc.metadata
    assert "chunk_count" in doc.metadata
    assert "provenance_completeness" in doc.metadata
    assert "policy_manifest" in doc.metadata
    assert "quality_metrics" in doc.metadata
    assert "chunks" in doc.metadata
    
    assert doc.metadata["adapter_source"] == "cpp_adapter.CPPAdapter"
    assert doc.metadata["schema_version"] == "CPP-2025.1"
