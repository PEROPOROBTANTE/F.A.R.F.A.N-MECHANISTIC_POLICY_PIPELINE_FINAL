import pytest
from farfan_core.farfan_core.utils.cpp_adapter import CPPAdapter
from farfan_core.farfan_core.core.phases.phase1_models import Chunk as CanonChunk
from farfan_core.farfan_core.core.orchestrator.core import PreprocessedDocument

class MockProvenance:
    def __init__(self, page_number, section_header):
        self.page_number = page_number
        self.section_header = section_header

class MockCanonPolicyPackage:
    def __init__(self, chunks):
        self.chunk_graph = lambda: None
        self.chunk_graph.chunks = {chunk.id: chunk for chunk in chunks}
        self.schema_version = 'SPC-2025.1'
        self.quality_metrics = None
        self.policy_manifest = None
        self.metadata = None

def create_mock_chunk(i):
    chunk = CanonChunk(
        id=f"c{i}",
        text=f"This is chunk {i}.",
        text_span_start=i * 20,
        policy_area_id=f"PA{i % 10 + 1:02d}",
        dimension_id=f"DIM{i % 6 + 1:02d}",
        chunk_type="diagnostic",
    )
    chunk.provenance = MockProvenance(page_number=i + 1, section_header=f"Section {i + 1}")
    return chunk

def test_spc_adapter_integration():
    """
    Integration test for the SPC to PreprocessedDocument conversion.
    """
    # 1. Create a canonical test document with 60 chunks
    chunks = [create_mock_chunk(i) for i in range(60)]
    canon_package = MockCanonPolicyPackage(chunks)

    # 2. Run the adapter
    adapter = CPPAdapter()
    preprocessed_doc = adapter.to_preprocessed_document(canon_package, "test_doc")

    # 3. Verify the invariants
    assert isinstance(preprocessed_doc, PreprocessedDocument)
    assert preprocessed_doc.document_id == "test_doc"
    assert preprocessed_doc.processing_mode == "chunked"
    assert len(preprocessed_doc.chunks) == 60

    for i, chunk_data in enumerate(preprocessed_doc.chunks):
        assert chunk_data.policy_area_id is not None
        assert chunk_data.dimension_id is not None
        assert chunk_data.chunk_type is not None
        assert chunk_data.provenance is not None
        assert chunk_data.provenance.page_number is not None
        assert chunk_data.provenance.section_header is not None
