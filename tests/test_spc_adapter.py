"""Tests for SPC Adapter.

Tests conversion from Smart Policy Chunks (SPC) / Canon Policy Package (CPP)
to PreprocessedDocument. These tests directly test SPCAdapter without wrappers.
"""

from __future__ import annotations

import pytest

from saaaaaa.utils.spc_adapter import SPCAdapter, SPCAdapterError, adapt_spc_to_orchestrator
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
    Budget,  # Fixed: was BudgetInfo, actual class name is Budget
    KPI,     # Fixed: was KPIInfo, actual class name is KPI
)

# Compatibility aliases for test code
BudgetInfo = Budget
KPIInfo = KPI


def create_test_chunk(
    chunk_id: str,
    text: str,
    start: int,
    end: int,
    resolution: ChunkResolution = ChunkResolution.MICRO,
    budget: BudgetInfo | None = None,
    kpi: KPIInfo | None = None,
) -> Chunk:
    """Create a test chunk."""
    return Chunk(
        id=chunk_id,
        bytes_hash=f"hash_{chunk_id}",
        text_span=TextSpan(start=start, end=end),
        resolution=resolution,
        text=text,
        policy_facets=PolicyFacet(
            axes=["Eje1", "Eje2"],
            programs=["Programa A"],
            projects=["Proyecto X"]
        ),
        time_facets=TimeFacet(years=[2024, 2025]),
        geo_facets=GeoFacet(territories=["Bogotá", "Antioquia"]),
        confidence=Confidence(layout=1.0, ocr=0.98, typing=0.95),
        budget=budget,
        kpi=kpi,
    )


def create_test_spc(chunks: list[Chunk]) -> CanonPolicyPackage:
    """Create a test SPC/CPP with given chunks."""
    chunk_graph = ChunkGraph()
    for chunk in chunks:
        chunk_graph.add_chunk(chunk)
    
    return CanonPolicyPackage(
        schema_version="SPC-2025.1",
        policy_manifest=PolicyManifest(
            axes=3,
            programs=10,
            projects=25,
            years=[2024, 2025],
            territories=["Bogotá", "Antioquia", "Valle"],
            indicators=15,
            budget_rows=50,
        ),
        chunk_graph=chunk_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(
            provenance_completeness=1.0,
            structural_consistency=0.95,
            boundary_f1=0.88,
            kpi_linkage_rate=0.75,
            budget_consistency_score=0.92,
            temporal_robustness=0.85,
            chunk_context_coverage=0.90,
        ),
        integrity_index=IntegrityIndex(
            blake3_root="test_root_hash_spc",
            chunk_hashes={
                "chunk_1": "hash1",
                "chunk_2": "hash2",
                "chunk_3": "hash3",
            }
        ),
    )


def test_spc_adapter_initialization() -> None:
    """Test SPC adapter initialization."""
    adapter = SPCAdapter()
    
    metrics = adapter.get_metrics()
    assert metrics["conversions_count"] == 0


def test_to_preprocessed_document_basic() -> None:
    """Test basic SPC to PreprocessedDocument conversion."""
    chunks = [
        create_test_chunk("chunk_1", "First chunk text.", 0, 17),
        create_test_chunk("chunk_2", "Second chunk text.", 18, 36),
        create_test_chunk("chunk_3", "Third chunk text.", 37, 54),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_doc_spc")
    
    assert doc.document_id == "test_doc_spc"
    assert "First chunk text." in doc.raw_text
    assert "Second chunk text." in doc.raw_text
    assert "Third chunk text." in doc.raw_text
    assert len(doc.sentences) == 3
    assert len(doc.metadata["chunks"]) == 3


def test_to_preprocessed_document_with_schema_version() -> None:
    """Test that schema_version is preserved in metadata."""
    chunks = [
        create_test_chunk("chunk_1", "Test content.", 0, 13),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_schema")
    
    assert doc.metadata["schema_version"] == "SPC-2025.1"
    assert doc.metadata["adapter_source"] == "cpp_adapter.CPPAdapter"


def test_to_preprocessed_document_with_policy_manifest() -> None:
    """Test that policy manifest is included in metadata."""
    chunks = [
        create_test_chunk("chunk_1", "Policy content.", 0, 15),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_manifest")
    
    assert "policy_manifest" in doc.metadata
    manifest = doc.metadata["policy_manifest"]
    assert manifest["axes"] == 3
    assert manifest["programs"] == 10
    assert manifest["projects"] == 25
    assert manifest["years"] == [2024, 2025]
    assert manifest["territories"] == ["Bogotá", "Antioquia", "Valle"]
    assert manifest["indicators"] == 15
    assert manifest["budget_rows"] == 50


def test_to_preprocessed_document_with_quality_metrics() -> None:
    """Test that quality metrics are included in metadata."""
    chunks = [
        create_test_chunk("chunk_1", "Quality test.", 0, 13),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_quality")
    
    assert "quality_metrics" in doc.metadata
    metrics = doc.metadata["quality_metrics"]
    assert metrics["provenance_completeness"] == 1.0
    assert metrics["structural_consistency"] == 0.95
    assert metrics["boundary_f1"] == 0.88
    assert metrics["kpi_linkage_rate"] == 0.75
    assert metrics["budget_consistency_score"] == 0.92
    assert metrics["temporal_robustness"] == 0.85
    assert metrics["chunk_context_coverage"] == 0.90


def test_to_preprocessed_document_with_integrity_index() -> None:
    """Test that integrity index is included in metadata."""
    chunks = [
        create_test_chunk("chunk_1", "Integrity test.", 0, 15),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_integrity")
    
    assert "integrity_index" in doc.metadata
    index = doc.metadata["integrity_index"]
    assert index["blake3_root"] == "test_root_hash_spc"
    assert index["chunk_hashes_count"] == 3


def test_to_preprocessed_document_with_budget_data() -> None:
    """Test that budget data is extracted into tables."""
    budget1 = BudgetInfo(
        source="Fuente A",
        use="Destino A",
        amount=1000000.0,
        year=2024,
        currency="COP"
    )
    budget2 = BudgetInfo(
        source="Fuente B",
        use="Destino B",
        amount=2500000.0,
        year=2025,
        currency="COP"
    )
    
    chunks = [
        create_test_chunk("chunk_1", "Budget chunk 1.", 0, 15, budget=budget1),
        create_test_chunk("chunk_2", "Budget chunk 2.", 16, 31, budget=budget2),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_budget")
    
    assert len(doc.tables) == 2
    assert doc.tables[0]["source"] == "Fuente A"
    assert doc.tables[0]["amount"] == 1000000.0
    assert doc.tables[0]["year"] == 2024
    assert doc.tables[1]["source"] == "Fuente B"
    assert doc.tables[1]["amount"] == 2500000.0


def test_to_preprocessed_document_chunk_ordering() -> None:
    """Test that chunks are ordered by text_span.start."""
    chunks = [
        create_test_chunk("chunk_3", "Third.", 100, 106),
        create_test_chunk("chunk_1", "First.", 0, 6),
        create_test_chunk("chunk_2", "Second.", 50, 57),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_order")
    
    # Check that sentences are in correct order
    assert doc.sentences[0]["text"] == "First."
    assert doc.sentences[1]["text"] == "Second."
    assert doc.sentences[2]["text"] == "Third."
    
    # Check raw text is concatenated in order
    assert doc.raw_text == "First. Second. Third."


def test_to_preprocessed_document_resolution_filter() -> None:
    """Test filtering by chunk resolution."""
    chunks = [
        create_test_chunk("chunk_1", "Micro 1.", 0, 8, ChunkResolution.MICRO),
        create_test_chunk("chunk_2", "Meso 1.", 9, 16, ChunkResolution.MESO),
        create_test_chunk("chunk_3", "Micro 2.", 17, 25, ChunkResolution.MICRO),
        create_test_chunk("chunk_4", "Macro 1.", 26, 34, ChunkResolution.MACRO),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    # Filter for MICRO chunks only
    doc = adapter.to_preprocessed_document(
        spc,
        document_id="test_filter",
        preserve_chunk_resolution=ChunkResolution.MICRO
    )
    
    assert len(doc.sentences) == 2
    assert doc.sentences[0]["text"] == "Micro 1."
    assert doc.sentences[1]["text"] == "Micro 2."
    assert doc.sentences[0]["resolution"] == "micro"
    assert doc.sentences[1]["resolution"] == "micro"


def test_to_preprocessed_document_chunk_metadata() -> None:
    """Test that chunk metadata is preserved."""
    kpi = KPIInfo(
        name="Tasa de cobertura",
        baseline=75.0,
        target=90.0,
        unit="%"
    )
    
    chunks = [
        create_test_chunk("chunk_1", "Chunk with KPI.", 0, 15, kpi=kpi),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_metadata")
    
    chunk_meta = doc.metadata["chunks"][0]
    assert chunk_meta["id"] == "chunk_1"
    assert chunk_meta["resolution"] == "micro"
    assert chunk_meta["text_span"]["start"] == 0
    assert chunk_meta["text_span"]["end"] == 15
    assert chunk_meta["has_kpi"] is True
    assert chunk_meta["has_budget"] is False
    assert chunk_meta["confidence"]["layout"] == 1.0
    assert chunk_meta["confidence"]["ocr"] == 0.98
    assert chunk_meta["confidence"]["typing"] == 0.95


def test_to_preprocessed_document_empty_chunk_graph_error() -> None:
    """Test error when chunk graph is empty."""
    spc = CanonPolicyPackage(
        schema_version="SPC-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=ChunkGraph(),  # Empty
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="test"),
    )
    
    adapter = SPCAdapter()
    
    with pytest.raises(SPCAdapterError) as exc_info:
        adapter.to_preprocessed_document(spc, document_id="test")
    
    assert "chunk graph is empty" in str(exc_info.value).lower()


def test_to_preprocessed_document_none_spc_error() -> None:
    """Test error when SPC is None."""
    adapter = SPCAdapter()
    
    with pytest.raises(SPCAdapterError) as exc_info:
        adapter.to_preprocessed_document(None, document_id="test")
    
    assert "cannot convert none" in str(exc_info.value).lower()


def test_to_preprocessed_document_no_chunks_with_resolution_error() -> None:
    """Test error when no chunks match the requested resolution."""
    chunks = [
        create_test_chunk("chunk_1", "Micro only.", 0, 11, ChunkResolution.MICRO),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    with pytest.raises(SPCAdapterError) as exc_info:
        adapter.to_preprocessed_document(
            spc,
            document_id="test",
            preserve_chunk_resolution=ChunkResolution.MACRO
        )
    
    error_msg = str(exc_info.value).lower()
    assert "no chunks found" in error_msg
    assert "macro" in error_msg


def test_adapt_spc_to_orchestrator_convenience_function() -> None:
    """Test the convenience function."""
    chunks = [
        create_test_chunk("chunk_1", "Convenience test.", 0, 17),
    ]
    
    spc = create_test_spc(chunks)
    
    doc = adapt_spc_to_orchestrator(spc, document_id="test_convenience")
    
    assert doc.document_id == "test_convenience"
    assert "Convenience test." in doc.raw_text


def test_adapter_metrics_tracking() -> None:
    """Test that adapter tracks conversion metrics."""
    adapter = SPCAdapter()
    
    chunks = [create_test_chunk("chunk_1", "Test.", 0, 5)]
    spc = create_test_spc(chunks)
    
    # Perform multiple conversions
    adapter.to_preprocessed_document(spc, document_id="doc1")
    adapter.to_preprocessed_document(spc, document_id="doc2")
    adapter.to_preprocessed_document(spc, document_id="doc3")
    
    metrics = adapter.get_metrics()
    assert metrics["conversions_count"] == 3


def test_spc_adapter_is_cpp_adapter_alias() -> None:
    """Test that SPCAdapter is correctly aliased to CPPAdapter."""
    from saaaaaa.utils.cpp_adapter import CPPAdapter
    
    # They should be the same class
    assert SPCAdapter is CPPAdapter


def test_provenance_completeness_calculation() -> None:
    """Test provenance completeness calculation."""
    # Create chunks with provenance
    chunk1 = create_test_chunk("chunk_1", "With provenance.", 0, 16)
    chunk1.provenance = {"page": 1, "tokens": [0, 1, 2]}
    
    chunk2 = create_test_chunk("chunk_2", "No provenance.", 17, 31)
    chunk2.provenance = None
    
    chunk3 = create_test_chunk("chunk_3", "With provenance.", 32, 48)
    chunk3.provenance = {"page": 2, "tokens": [3, 4, 5]}
    
    chunks = [chunk1, chunk2, chunk3]
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    doc = adapter.to_preprocessed_document(spc, document_id="test_provenance")
    
    # 2 out of 3 chunks have provenance = 2/3 ≈ 0.667
    assert abs(doc.metadata["provenance_completeness"] - 0.667) < 0.01
    
    # Check individual chunk provenance flags
    chunk_meta = doc.metadata["chunks"]
    assert chunk_meta[0]["has_provenance"] is True
    assert chunk_meta[1]["has_provenance"] is False
    assert chunk_meta[2]["has_provenance"] is True


def test_document_id_auto_generation() -> None:
    """Test automatic document ID generation from chunk IDs."""
    chunks = [
        create_test_chunk("mydoc_chunk_1", "Content.", 0, 8),
    ]
    
    spc = create_test_spc(chunks)
    adapter = SPCAdapter()
    
    # Don't provide document_id
    doc = adapter.to_preprocessed_document(spc)
    
    # Should extract 'mydoc' from first chunk ID
    assert doc.document_id == "mydoc"
