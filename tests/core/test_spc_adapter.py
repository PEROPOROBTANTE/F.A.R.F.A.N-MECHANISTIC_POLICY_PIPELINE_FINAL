import pytest
from farfan_core.farfan_core.utils.cpp_adapter import CPPAdapter, CPPAdapterError

class MockProvenance:
    def __init__(self, page_number=None, section_header=None):
        self.page_number = page_number
        self.section_header = section_header

class MockChunk:
    def __init__(self, id, text, text_span_start, policy_area_id=None, dimension_id=None):
        self.id = id
        self.text = text
        self.text_span = lambda: None
        self.text_span.start = text_span_start
        self.policy_area_id = policy_area_id
        self.dimension_id = dimension_id
        self.provenance = None

class MockCanonPackage:
    def __init__(self, chunks):
        self.chunk_graph = lambda: None
        self.chunk_graph.chunks = {chunk.id: chunk for chunk in chunks}

def test_enforce_60_chunks():
    adapter = CPPAdapter()

    # Test with 59 chunks
    chunks_59 = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10) for i in range(59)]
    package_59 = MockCanonPackage(chunks_59)
    with pytest.raises(CPPAdapterError, match="Cardinality mismatch: Expected 60 chunks"):
        adapter.to_preprocessed_document(package_59, "doc1")

    # Test with 61 chunks
    chunks_61 = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10) for i in range(61)]
    package_61 = MockCanonPackage(chunks_61)
    with pytest.raises(CPPAdapterError, match="Cardinality mismatch: Expected 60 chunks"):
        adapter.to_preprocessed_document(package_61, "doc1")

    # Test with 60 chunks (should pass)
    chunks_60 = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_60:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(page_number=1, section_header="Section 1")
    package_60 = MockCanonPackage(chunks_60)
    adapter.to_preprocessed_document(package_60, "doc1")

def test_enforce_metadata():
    adapter = CPPAdapter()

    # Test with missing policy_area_id
    chunks_missing_pa = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_missing_pa:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(page_number=1, section_header="Section 1")
    package_missing_pa = MockCanonPackage(chunks_missing_pa)
    with pytest.raises(CPPAdapterError, match="Missing policy_area_id"):
        adapter.to_preprocessed_document(package_missing_pa, "doc1")

    # Test with missing dimension_id
    chunks_missing_dim = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01") for i in range(60)]
    for chunk in chunks_missing_dim:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(page_number=1, section_header="Section 1")
    package_missing_dim = MockCanonPackage(chunks_missing_dim)
    with pytest.raises(CPPAdapterError, match="Missing dimension_id"):
        adapter.to_preprocessed_document(package_missing_dim, "doc1")

    # Test with missing chunk_type
    chunks_missing_chunk_type = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    package_missing_chunk_type = MockCanonPackage(chunks_missing_chunk_type)
    with pytest.raises(CPPAdapterError, match="Missing chunk_type"):
        adapter.to_preprocessed_document(package_missing_chunk_type, "doc1")

    # Test with invalid chunk_type
    chunks_invalid_chunk_type = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_invalid_chunk_type:
        chunk.chunk_type = "invalid"
    package_invalid_chunk_type = MockCanonPackage(chunks_invalid_chunk_type)
    with pytest.raises(CPPAdapterError, match="Invalid chunk_type"):
        adapter.to_preprocessed_document(package_invalid_chunk_type, "doc1")

def test_enforce_provenance():
    adapter = CPPAdapter()

    # Test with missing provenance
    chunks_missing_prov = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_missing_prov:
        chunk.chunk_type = "diagnostic"
    package_missing_prov = MockCanonPackage(chunks_missing_prov)
    with pytest.raises(CPPAdapterError, match="Missing provenance"):
        adapter.to_preprocessed_document(package_missing_prov, "doc1")

    # Test with missing page_number
    chunks_missing_page = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_missing_page:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(section_header="Section 1")
    package_missing_page = MockCanonPackage(chunks_missing_page)
    with pytest.raises(CPPAdapterError, match="Missing provenance.page_number"):
        adapter.to_preprocessed_document(package_missing_page, "doc1")

    # Test with missing section_header
    chunks_missing_section = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_missing_section:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(page_number=1)
    package_missing_section = MockCanonPackage(chunks_missing_section)
    with pytest.raises(CPPAdapterError, match="Missing provenance.section_header"):
        adapter.to_preprocessed_document(package_missing_section, "doc1")

def test_processing_mode():
    adapter = CPPAdapter()

    # Test with valid SPC
    chunks_valid = [MockChunk(id=f"c{i}", text=f"chunk {i}", text_span_start=i*10, policy_area_id="PA01", dimension_id="DIM01") for i in range(60)]
    for chunk in chunks_valid:
        chunk.chunk_type = "diagnostic"
        chunk.provenance = MockProvenance(page_number=1, section_header="Section 1")
    package_valid = MockCanonPackage(chunks_valid)
    doc = adapter.to_preprocessed_document(package_valid, "doc1")
    assert doc.processing_mode == "chunked"
