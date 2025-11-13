"""Tests for SPC ingestion validation in orchestrator.

Tests the critical validation logic added to prevent empty document creation
and enforce SPC-only ingestion.
"""

import pytest
from saaaaaa.core.orchestrator.core import (
    Orchestrator,
    PreprocessedDocument,
    PhaseInstrumentation,
)
from saaaaaa.core.orchestrator.factory import build_processor
from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
    IntegrityIndex,
)


def test_preprocessed_document_rejects_empty_raw_text():
    """Verify PreprocessedDocument.__post_init__ raises ValueError for empty raw_text."""
    with pytest.raises(ValueError, match="PreprocessedDocument cannot have empty raw_text"):
        PreprocessedDocument(
            document_id="test",
            raw_text="",
            sentences=[],
            tables=[],
            metadata={}
        )


def test_preprocessed_document_rejects_whitespace_only():
    """Verify PreprocessedDocument.__post_init__ raises ValueError for whitespace-only raw_text."""
    with pytest.raises(ValueError, match="PreprocessedDocument cannot have empty raw_text"):
        PreprocessedDocument(
            document_id="test",
            raw_text="   \n  \t  ",
            sentences=[],
            tables=[],
            metadata={}
        )


def test_preprocessed_document_accepts_valid_text():
    """Verify PreprocessedDocument allows non-empty raw_text."""
    doc = PreprocessedDocument(
        document_id="test",
        raw_text="Valid content",
        sentences=[],
        tables=[],
        metadata={}
    )
    assert doc.raw_text == "Valid content"
    assert doc.document_id == "test"


def test_ensure_raises_with_legacy_ingestion():
    """Verify ValueError when use_spc_ingestion=False."""
    chunk = Chunk(
        id="test",
        bytes_hash="hash",
        text_span=TextSpan(0, 10),
        resolution=ChunkResolution.MICRO,
        text="Test text.",
        confidence=Confidence(layout=1.0),
    )
    graph = ChunkGraph()
    graph.add_chunk(chunk)
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="hash"),
    )
    
    with pytest.raises(ValueError, match="SPC ingestion is now required"):
        PreprocessedDocument.ensure(cpp, use_spc_ingestion=False)


def test_ensure_validates_empty_chunk_graph():
    """Verify ValueError when chunk_graph is empty."""
    empty_graph = ChunkGraph()  # No chunks
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=empty_graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="hash"),
    )
    
    with pytest.raises(ValueError, match="chunk_graph is empty"):
        PreprocessedDocument.ensure(cpp, use_spc_ingestion=True)


def test_ensure_validates_chunk_graph_none():
    """Verify ValueError when chunk_graph is None."""
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=None,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="hash"),
    )
    
    with pytest.raises(ValueError, match="chunk_graph attribute but it is None"):
        PreprocessedDocument.ensure(cpp, use_spc_ingestion=True)


def test_ensure_validates_empty_text_from_spc():
    """Verify ValueError for empty raw_text after SPC adaptation."""
    # Create chunk with empty text
    empty_chunk = Chunk(
        id="empty",
        bytes_hash="hash",
        text_span=TextSpan(0, 0),
        resolution=ChunkResolution.MICRO,
        text="",  # Empty!
        confidence=Confidence(layout=1.0),
    )
    graph = ChunkGraph()
    graph.add_chunk(empty_chunk)
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="hash"),
    )
    
    # Note: This will raise ValueError from __post_init__ since adapter creates PreprocessedDocument
    with pytest.raises(ValueError, match="empty raw_text"):
        PreprocessedDocument.ensure(cpp, use_spc_ingestion=True)


def test_ensure_succeeds_with_valid_spc_document():
    """Verify successful conversion with valid SPC document."""
    chunk = Chunk(
        id="test",
        bytes_hash="hash",
        text_span=TextSpan(0, 50),
        resolution=ChunkResolution.MICRO,
        text="Valid policy document content for testing purposes.",
        confidence=Confidence(layout=1.0),
    )
    graph = ChunkGraph()
    graph.add_chunk(chunk)
    cpp = CanonPolicyPackage(
        schema_version="CPP-2025.1",
        policy_manifest=PolicyManifest(),
        chunk_graph=graph,
        provenance_map=ProvenanceMap(),
        quality_metrics=QualityMetrics(),
        integrity_index=IntegrityIndex(blake3_root="hash"),
    )
    
    doc = PreprocessedDocument.ensure(cpp, use_spc_ingestion=True)
    assert doc.raw_text
    assert len(doc.raw_text) > 0
    assert doc.metadata.get("chunk_count", 0) > 0


def test_ensure_rejects_unsupported_document_type():
    """Verify TypeError for documents without chunk_graph."""
    class FakeDocument:
        pass
    
    with pytest.raises(TypeError, match="Unsupported preprocessed document payload"):
        PreprocessedDocument.ensure(FakeDocument(), use_spc_ingestion=True)
