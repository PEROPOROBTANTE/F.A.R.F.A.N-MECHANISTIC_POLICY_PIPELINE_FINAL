"""Integration test for SPC Adapter.

Tests direct SPCAdapter usage (not through CPPAdapter wrapper).
Verifies full compatibility between SPC ingestion and orchestrator.
"""

from __future__ import annotations

import pytest

from saaaaaa.utils.spc_adapter import SPCAdapter, SPCAdapterError
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    PolicyFacet,
    TextSpan,
)


def test_spc_adapter_basic_conversion():
    """Test basic SPCAdapter conversion from CanonPolicyPackage to PreprocessedDocument."""
    # Create test chunks
    chunk1 = Chunk(
        id="chunk_001",
        text="This is the first policy chunk.",
        text_span=TextSpan(start=0, end=32),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_001",
        confidence=Confidence(layout=0.95, ocr=0.98, typing=0.99),
        policy_facets=PolicyFacet(programs=["Program A"], axes=["Axis 1"]),
    )
    
    chunk2 = Chunk(
        id="chunk_002",
        text="This is the second policy chunk.",
        text_span=TextSpan(start=33, end=66),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_002",
        confidence=Confidence(layout=0.97, ocr=0.96, typing=0.98),
        policy_facets=PolicyFacet(programs=["Program B"], axes=["Axis 2"]),
    )
    
    # Create ChunkGraph
    chunk_graph = ChunkGraph(chunks={"chunk_001": chunk1, "chunk_002": chunk2})
    
    # Create CanonPolicyPackage
    cpp = CanonPolicyPackage(
        schema_version="3.0.0",
        chunk_graph=chunk_graph,
    )
    
    # Convert using SPCAdapter
    adapter = SPCAdapter()
    doc = adapter.to_preprocessed_document(cpp, document_id="test_doc")
    
    # Verify PreprocessedDocument structure
    assert doc.document_id == "test_doc"
    assert doc.raw_text == "This is the first policy chunk. This is the second policy chunk."
    assert len(doc.sentences) == 2
    assert doc.sentences[0]["text"] == "This is the first policy chunk."
    assert doc.sentences[0]["chunk_id"] == "chunk_001"
    assert doc.sentences[0]["resolution"] == "MICRO"
    assert doc.sentences[1]["text"] == "This is the second policy chunk."
    
    # Verify metadata
    assert doc.metadata["adapter_source"] == "spc_adapter.SPCAdapter"
    assert doc.metadata["schema_version"] == "3.0.0"
    assert doc.metadata["chunk_count"] == 2
    assert doc.metadata["provenance_completeness"] == 0.0  # No provenance in test data
    
    # Verify chunk details in metadata
    assert len(doc.metadata["chunks"]) == 2
    assert doc.metadata["chunks"][0]["id"] == "chunk_001"
    assert doc.metadata["chunks"][0]["resolution"] == "MICRO"
    assert doc.metadata["chunks"][0]["confidence"]["layout"] == 0.95


def test_spc_adapter_empty_chunk_graph():
    """Test SPCAdapter error handling for empty chunk graph."""
    cpp = CanonPolicyPackage(
        schema_version="3.0.0",
        chunk_graph=ChunkGraph(chunks={}),
    )
    
    adapter = SPCAdapter()
    
    with pytest.raises(SPCAdapterError) as exc_info:
        adapter.to_preprocessed_document(cpp)
    
    assert "chunk graph is empty" in str(exc_info.value).lower()


def test_spc_adapter_chunk_ordering():
    """Test that chunks are ordered by text_span.start for determinism."""
    # Create chunks in non-sequential order
    chunk3 = Chunk(
        id="chunk_003",
        text="Third chunk.",
        text_span=TextSpan(start=200, end=212),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_003",
    )
    
    chunk1 = Chunk(
        id="chunk_001",
        text="First chunk.",
        text_span=TextSpan(start=0, end=12),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_001",
    )
    
    chunk2 = Chunk(
        id="chunk_002",
        text="Second chunk.",
        text_span=TextSpan(start=100, end=113),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_002",
    )
    
    # Add chunks in non-sequential order
    chunk_graph = ChunkGraph(chunks={
        "chunk_003": chunk3,
        "chunk_001": chunk1,
        "chunk_002": chunk2,
    })
    
    cpp = CanonPolicyPackage(
        schema_version="3.0.0",
        chunk_graph=chunk_graph,
    )
    
    adapter = SPCAdapter()
    doc = adapter.to_preprocessed_document(cpp)
    
    # Verify chunks are ordered by text_span.start
    assert doc.sentences[0]["chunk_id"] == "chunk_001"  # start=0
    assert doc.sentences[1]["chunk_id"] == "chunk_002"  # start=100
    assert doc.sentences[2]["chunk_id"] == "chunk_003"  # start=200
    assert doc.raw_text == "First chunk. Second chunk. Third chunk."


def test_spc_adapter_metrics():
    """Test SPCAdapter metrics tracking."""
    adapter = SPCAdapter()
    
    initial_metrics = adapter.get_metrics()
    assert initial_metrics["conversions_count"] == 0
    
    # Perform a conversion
    chunk = Chunk(
        id="chunk_001",
        text="Test chunk.",
        text_span=TextSpan(start=0, end=11),
        resolution=ChunkResolution.MICRO,
        bytes_hash="hash_001",
    )
    
    cpp = CanonPolicyPackage(
        schema_version="3.0.0",
        chunk_graph=ChunkGraph(chunks={"chunk_001": chunk}),
    )
    
    adapter.to_preprocessed_document(cpp)
    
    metrics = adapter.get_metrics()
    assert metrics["conversions_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
