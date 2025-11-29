"""
Integration test for Phase 2 Hardening (SPC Invariants).

Verifies that CPPAdapter strictly enforces:
1. Exactly 60 chunks.
2. Mandatory metadata (policy_area_id, dimension_id).
3. Degradation to 'flat' mode upon violation.
"""

import pytest
from unittest.mock import MagicMock
from saaaaaa.utils.cpp_adapter import CPPAdapter, CPPAdapterError
from saaaaaa.core.orchestrator.core import ChunkData

class MockChunk:
    def __init__(self, id, text="test", start=0, end=10, pa="PA01", dim="DIM01"):
        self.id = id
        self.text = text
        self.text_span = MagicMock(start=start, end=end)
        self.policy_area_id = pa
        self.dimension_id = dim
        self.chunk_type = "diagnostic"
        self.resolution = MagicMock()
        self.resolution.value = "macro"
        self.confidence = MagicMock(overall=1.0)
        self.budget = None
        self.kpi = None
        self.provenance = True

class MockCPP:
    def __init__(self, chunks):
        self.chunk_graph = MagicMock()
        self.chunk_graph.chunks = {c.id: c for c in chunks}
        self.schema_version = "SPC-2025.1"
        self.metadata = {}

def test_cpp_adapter_valid_60_chunks():
    """Test that 60 valid chunks result in 'chunked' mode."""
    chunks = [MockChunk(id=f"chk_{i}", start=i*10, end=i*10+9) for i in range(60)]
    cpp = MockCPP(chunks)
    
    adapter = CPPAdapter(enable_runtime_validation=False)
    doc = adapter.to_preprocessed_document(cpp, "doc_valid")
    
    assert doc.processing_mode == "chunked"
    assert len(doc.chunks) == 60

def test_cpp_adapter_invalid_count():
    """Test that != 60 chunks result in 'flat' mode."""
    # 59 chunks
    chunks = [MockChunk(id=f"chk_{i}", start=i*10, end=i*10+9) for i in range(59)]
    cpp = MockCPP(chunks)
    
    adapter = CPPAdapter(enable_runtime_validation=False)
    doc = adapter.to_preprocessed_document(cpp, "doc_invalid_count")
    
    assert doc.processing_mode == "flat"
    # Chunks are still present, but mode is flat
    assert len(doc.chunks) == 59

def test_cpp_adapter_missing_metadata():
    """Test that missing metadata results in 'flat' mode."""
    chunks = [MockChunk(id=f"chk_{i}", start=i*10, end=i*10+9) for i in range(60)]
    # Corrupt one chunk
    chunks[30].policy_area_id = None
    
    cpp = MockCPP(chunks)
    
    adapter = CPPAdapter(enable_runtime_validation=False)
    doc = adapter.to_preprocessed_document(cpp, "doc_missing_meta")
    
    assert doc.processing_mode == "flat"
