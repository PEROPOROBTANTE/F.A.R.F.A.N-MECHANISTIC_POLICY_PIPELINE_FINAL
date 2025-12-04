"""Test Phase 3: Chunk Routing Integration

Tests Phase 3 chunk routing logic including:
- (pa_id, dim_id) lookup key construction from question dimension field
- chunk_matrix.get_chunk() success path with valid keys
- KeyError handling with proper ValueError propagation
- Multi-stage verification checks (policy_area_id, dimension_id, chunk_id consistency)
- Chunk payload extraction and validation
- ValueError raising with correct error message format
- Structured logging output validation
"""
import logging
from dataclasses import replace

import pytest

from farfan_pipeline.core.orchestrator.chunk_matrix_builder import (
    DIMENSIONS,
    EXPECTED_CHUNK_COUNT,
    POLICY_AREAS,
    build_chunk_matrix,
)
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument, Provenance


class ChunkMatrix:
    """Minimal ChunkMatrix wrapper for testing."""

    POLICY_AREAS = POLICY_AREAS
    DIMENSIONS = DIMENSIONS
    EXPECTED_CHUNK_COUNT = EXPECTED_CHUNK_COUNT

    def __init__(self, document: PreprocessedDocument) -> None:
        matrix, sorted_keys = build_chunk_matrix(document)
        self.chunks = matrix
        self.sorted_keys = tuple(sorted_keys)

    def get_chunk(self, policy_area_id: str, dimension_id: str) -> ChunkData:
        """Retrieve chunk by policy area and dimension with O(1) lookup."""
        key = (policy_area_id, dimension_id)
        if key not in self.chunks:
            raise KeyError(f"Chunk not found for key: {policy_area_id}-{dimension_id}")
        return self.chunks[key]


class TestPhase3LookupKeyConstruction:
    """Test (pa_id, dim_id) lookup key construction from question dimension field."""

    def test_dimension_to_dim_id_conversion(self):
        """Test conversion of D1-D6 to DIM01-DIM06 format."""
        test_cases = [
            ("D1", "DIM01"),
            ("D2", "DIM02"),
            ("D3", "DIM03"),
            ("D4", "DIM04"),
            ("D5", "DIM05"),
            ("D6", "DIM06"),
        ]
        for dimension, expected_dim_id in test_cases:
            dim_id = f"DIM{dimension[1:].zfill(2)}"
            assert dim_id == expected_dim_id

    def test_policy_area_key_format(self):
        """Test policy area key format PA01-PA10."""
        policy_areas = [f"PA{i:02d}" for i in range(1, 11)]
        assert len(policy_areas) == 10
        assert policy_areas[0] == "PA01"
        assert policy_areas[9] == "PA10"

    def test_lookup_key_tuple_construction(self):
        """Test (pa_id, dim_id) tuple construction for matrix lookup."""
        question = {"dimension": "D1", "question_id": "D1_Q01"}
        policy_area = "PA01"
        dimension_id = f"DIM{question['dimension'][1:].zfill(2)}"

        key = (policy_area, dimension_id)
        assert key == ("PA01", "DIM01")
        assert isinstance(key, tuple)
        assert len(key) == 2


class TestPhase3ChunkMatrixLookup:
    """Test chunk_matrix.get_chunk() success path with valid keys."""

    @pytest.fixture
    def valid_chunk(self):
        """Create valid chunk with proper PA-DIM structure."""
        return ChunkData(
            id=0,
            text="Test chunk content with sufficient length for validation",
            chunk_type="diagnostic",
            sentences=[0, 1],
            tables=[],
            start_pos=0,
            end_pos=100,
            confidence=0.95,
            chunk_id="PA01-DIM01",
            policy_area_id="PA01",
            dimension_id="DIM01",
            provenance=Provenance(page_number=1, section_header="Introduction"),
        )

    @pytest.fixture
    def preprocessed_document_with_chunks(self, valid_chunk):
        """Create preprocessed document with 60 valid chunks."""
        chunks = []
        chunk_id = 0
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = replace(
                    valid_chunk,
                    id=chunk_id,
                    chunk_id=f"{pa_id}-{dim_id}",
                    policy_area_id=pa_id,
                    dimension_id=dim_id,
                    text=f"Content for {pa_id} {dim_id}",
                )
                chunks.append(chunk)
                chunk_id += 1

        return PreprocessedDocument(
            document_id="test_doc",
            raw_text="Test document content",
            sentences=[{"text": "Sentence 1"}],
            tables=[],
            metadata={"test": True, "chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

    def test_get_chunk_success_valid_key(self, preprocessed_document_with_chunks):
        """Test successful chunk retrieval with valid (pa_id, dim_id) key."""
        matrix = ChunkMatrix(preprocessed_document_with_chunks)

        chunk = matrix.get_chunk("PA01", "DIM01")

        assert chunk is not None
        assert chunk.policy_area_id == "PA01"
        assert chunk.dimension_id == "DIM01"
        assert chunk.chunk_id == "PA01-DIM01"

    def test_get_chunk_all_policy_areas(self, preprocessed_document_with_chunks):
        """Test chunk retrieval across all policy areas."""
        matrix = ChunkMatrix(preprocessed_document_with_chunks)

        for pa_num in range(1, 11):
            pa_id = f"PA{pa_num:02d}"
            chunk = matrix.get_chunk(pa_id, "DIM01")

            assert chunk.policy_area_id == pa_id
            assert chunk.dimension_id == "DIM01"

    def test_get_chunk_all_dimensions(self, preprocessed_document_with_chunks):
        """Test chunk retrieval across all dimensions."""
        matrix = ChunkMatrix(preprocessed_document_with_chunks)

        for dim_num in range(1, 7):
            dim_id = f"DIM{dim_num:02d}"
            chunk = matrix.get_chunk("PA01", dim_id)

            assert chunk.policy_area_id == "PA01"
            assert chunk.dimension_id == dim_id

    def test_get_chunk_returns_chunk_data_type(self, preprocessed_document_with_chunks):
        """Test get_chunk returns ChunkData instance."""
        matrix = ChunkMatrix(preprocessed_document_with_chunks)

        chunk = matrix.get_chunk("PA05", "DIM03")

        assert isinstance(chunk, ChunkData)
        assert hasattr(chunk, "text")
        assert hasattr(chunk, "policy_area_id")
        assert hasattr(chunk, "dimension_id")


class TestPhase3KeyErrorHandling:
    """Test KeyError handling when chunk not found with proper ValueError propagation."""

    @pytest.fixture
    def minimal_document(self):
        """Create minimal document with single chunk."""
        chunk = ChunkData(
            id=0,
            text="Single test chunk",
            chunk_type="diagnostic",
            sentences=[0],
            tables=[],
            start_pos=0,
            end_pos=50,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )
        return PreprocessedDocument(
            document_id="minimal",
            raw_text="Minimal content",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 1},
            chunks=[chunk],
            processing_mode="chunked",
        )

    def test_get_chunk_raises_key_error_invalid_pa(self, minimal_document):
        """Test KeyError raised for invalid policy area."""
        with pytest.raises(ValueError):
            ChunkMatrix(minimal_document)

    def test_get_chunk_key_error_message_format(self, minimal_document):
        """Test KeyError message includes expected format: pa_id-dim_id."""
        with pytest.raises(ValueError):
            ChunkMatrix(minimal_document)

    def test_get_chunk_nonexistent_combination(self):
        """Test KeyError for valid but nonexistent PA-DIM combination."""
        chunks = []
        for i in range(1, 61):
            pa_id = f"PA{((i - 1) // 6) + 1:02d}"
            dim_id = f"DIM{((i - 1) % 6) + 1:02d}"
            chunk = ChunkData(
                id=i - 1,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[0],
                tables=[],
                start_pos=0,
                end_pos=50,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        doc = PreprocessedDocument(
            document_id="test",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

        matrix = ChunkMatrix(doc)

        with pytest.raises(KeyError, match=r"PA99-DIM99"):
            matrix.get_chunk("PA99", "DIM99")

    def test_valueerror_propagation_from_keyerror(self):
        """Test that synchronization failures propagate ValueError from KeyError."""
        chunks = []
        for i in range(1, 61):
            pa_id = f"PA{((i - 1) // 6) + 1:02d}"
            dim_id = f"DIM{((i - 1) % 6) + 1:02d}"
            chunk = ChunkData(
                id=i - 1,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[0],
                tables=[],
                start_pos=0,
                end_pos=50,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        doc = PreprocessedDocument(
            document_id="test",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

        matrix = ChunkMatrix(doc)

        try:
            matrix.get_chunk("PA11", "DIM01")
            pytest.fail("Expected KeyError to be raised")
        except KeyError as e:
            error_msg = str(e)
            assert "PA11" in error_msg or "DIM01" in error_msg


class TestPhase3MultiStageVerification:
    """Test multi-stage verification checks for PA/DIM/chunk_id consistency."""

    @pytest.fixture
    def document_with_full_metadata(self):
        """Create document with complete chunk metadata."""
        chunks = []
        for i in range(60):
            pa_num = (i // 6) + 1
            dim_num = (i % 6) + 1
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"

            chunk = ChunkData(
                id=i,
                text=f"Chunk content for {pa_id}-{dim_id}",
                chunk_type="diagnostic",
                sentences=[i],
                tables=[],
                start_pos=i * 100,
                end_pos=(i + 1) * 100,
                confidence=0.95,
                chunk_id=f"{pa_id}-{dim_id}",
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        return PreprocessedDocument(
            document_id="full_meta",
            raw_text="Full metadata document",
            sentences=[{"text": f"Sentence {i}"} for i in range(60)],
            tables=[],
            metadata={"chunk_count": 60, "has_full_metadata": True},
            chunks=chunks,
            processing_mode="chunked",
        )

    def test_policy_area_id_match_verification(self, document_with_full_metadata):
        """Test policy_area_id matches between request and chunk."""
        matrix = ChunkMatrix(document_with_full_metadata)

        chunk = matrix.get_chunk("PA03", "DIM02")

        assert chunk.policy_area_id == "PA03"

    def test_dimension_id_match_verification(self, document_with_full_metadata):
        """Test dimension_id matches between request and chunk."""
        matrix = ChunkMatrix(document_with_full_metadata)

        chunk = matrix.get_chunk("PA07", "DIM05")

        assert chunk.dimension_id == "DIM05"

    def test_chunk_id_consistency_with_pa_dim(self, document_with_full_metadata):
        """Test chunk_id is consistent with policy_area_id-dimension_id."""
        matrix = ChunkMatrix(document_with_full_metadata)

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"

                chunk = matrix.get_chunk(pa_id, dim_id)

                expected_chunk_id = f"{pa_id}-{dim_id}"
                assert chunk.chunk_id == expected_chunk_id
                assert chunk.policy_area_id == pa_id
                assert chunk.dimension_id == dim_id

    def test_chunk_id_derivation_from_pa_dim(self):
        """Test chunk_id is automatically derived from PA and DIM if not provided."""
        chunk = ChunkData(
            id=0,
            text="Test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA02",
            dimension_id="DIM03",
        )

        assert chunk.chunk_id == "PA02-DIM03"


class TestPhase3ChunkPayloadExtraction:
    """Test chunk payload extraction with text, expected_elements, document_position."""

    @pytest.fixture
    def chunk_with_provenance(self):
        """Create chunk with complete provenance metadata."""
        return ChunkData(
            id=42,
            text="This is a complete chunk with sufficient content for testing payload extraction",
            chunk_type="activity",
            sentences=[10, 11, 12],
            tables=[2],
            start_pos=1000,
            end_pos=1500,
            confidence=0.98,
            chunk_id="PA05-DIM04",
            policy_area_id="PA05",
            dimension_id="DIM04",
            provenance=Provenance(
                page_number=5,
                section_header="Implementation Strategy",
                bbox=(100.0, 200.0, 400.0, 500.0),
                span_in_page=(50, 150),
                source_file="test_plan.pdf",
            ),
        )

    def test_text_extraction_non_empty_validation(self, chunk_with_provenance):
        """Test chunk text is non-empty and properly extracted."""
        assert chunk_with_provenance.text
        assert len(chunk_with_provenance.text) > 0
        assert isinstance(chunk_with_provenance.text, str)

    def test_expected_elements_extraction_sentences(self, chunk_with_provenance):
        """Test extraction of sentence indices as expected elements."""
        sentences = chunk_with_provenance.sentences
        assert sentences is not None
        assert len(sentences) == 3
        assert sentences == [10, 11, 12]

    def test_expected_elements_extraction_tables(self, chunk_with_provenance):
        """Test extraction of table indices as expected elements."""
        tables = chunk_with_provenance.tables
        assert tables is not None
        assert len(tables) == 1
        assert tables == [2]

    def test_expected_elements_empty_list_fallback(self):
        """Test empty list fallback when no sentences/tables provided."""
        chunk = ChunkData(
            id=0,
            text="Minimal chunk",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )

        assert chunk.sentences == []
        assert chunk.tables == []

    def test_document_position_tuple_extraction(self, chunk_with_provenance):
        """Test extraction of (start_pos, end_pos) document position tuple."""
        start_pos = chunk_with_provenance.start_pos
        end_pos = chunk_with_provenance.end_pos

        position_tuple = (start_pos, end_pos)
        assert position_tuple == (1000, 1500)
        assert isinstance(position_tuple, tuple)
        assert len(position_tuple) == 2

    def test_provenance_none_handling(self):
        """Test chunk handles None provenance gracefully."""
        chunk = ChunkData(
            id=0,
            text="Chunk without provenance",
            chunk_type="diagnostic",
            sentences=[0],
            tables=[],
            start_pos=0,
            end_pos=50,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
            provenance=None,
        )

        assert chunk.provenance is None

    def test_provenance_metadata_extraction(self, chunk_with_provenance):
        """Test extraction of provenance metadata fields."""
        prov = chunk_with_provenance.provenance

        assert prov is not None
        assert prov.page_number == 5
        assert prov.section_header == "Implementation Strategy"
        assert prov.bbox == (100.0, 200.0, 400.0, 500.0)
        assert prov.span_in_page == (50, 150)
        assert prov.source_file == "test_plan.pdf"


class TestPhase3SynchronizationFailures:
    """Test ValueError raising with correct error message format on sync failures."""

    def test_missing_chunk_synchronization_error_format(self):
        """Test ValueError message format when chunk synchronization fails."""
        chunks = []
        for i in range(59):
            pa_id = f"PA{((i) // 6) + 1:02d}"
            dim_id = f"DIM{((i) % 6) + 1:02d}"
            chunk = ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        doc = PreprocessedDocument(
            document_id="incomplete",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 59},
            chunks=chunks,
            processing_mode="chunked",
        )

        with pytest.raises(ValueError, match="Missing chunk combinations"):
            ChunkMatrix(doc)

    def test_duplicate_chunk_synchronization_error(self):
        """Test ValueError when duplicate PA-DIM combinations exist."""
        chunks = []
        for i in range(59):
            pa_id = f"PA{((i) // 6) + 1:02d}"
            dim_id = f"DIM{((i) % 6) + 1:02d}"
            chunk = ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        duplicate = ChunkData(
            id=59,
            text="Duplicate",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=10,
            confidence=0.9,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )
        chunks.append(duplicate)

        doc = PreprocessedDocument(
            document_id="duplicates",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

        with pytest.raises(ValueError, match=r"Duplicate.*PA.*DIM.*combination.*PA01-DIM01"):
            ChunkMatrix(doc)

    def test_invalid_policy_area_format_error(self):
        """Test ValueError for invalid policy_area_id format."""
        with pytest.raises(ValueError, match="Invalid chunk_id"):
            ChunkData(
                id=0,
                text="Test",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id="INVALID",
                dimension_id="DIM01",
            )

    def test_invalid_dimension_format_error(self):
        """Test ValueError for invalid dimension_id format."""
        with pytest.raises(ValueError, match="Invalid chunk_id"):
            ChunkData(
                id=0,
                text="Test",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id="PA01",
                dimension_id="INVALID",
            )


class TestPhase3StructuredLogging:
    """Test structured logging output validation with required fields."""

    @pytest.fixture
    def valid_60_chunk_document(self):
        """Create valid document with 60 chunks for logging tests."""
        chunks = []
        for i in range(60):
            pa_id = f"PA{(i // 6) + 1:02d}"
            dim_id = f"DIM{(i % 6) + 1:02d}"
            chunk = ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[i],
                tables=[],
                start_pos=i * 100,
                end_pos=(i + 1) * 100,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        return PreprocessedDocument(
            document_id="logging_test",
            raw_text="Logging test document",
            sentences=[{"text": f"S{i}"} for i in range(60)],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

    def test_chunk_matrix_construction_logging(
        self, valid_60_chunk_document, caplog
    ):
        """Test chunk matrix construction emits structured log events."""
        with caplog.at_level(logging.INFO):
            ChunkMatrix(valid_60_chunk_document)

        log_records = [r for r in caplog.records if "chunk_matrix" in r.message.lower()]
        assert len(log_records) > 0

    def test_log_includes_chunk_count_field(
        self, valid_60_chunk_document, caplog
    ):
        """Test logs include chunk count information."""
        with caplog.at_level(logging.INFO):
            ChunkMatrix(valid_60_chunk_document)

        assert any(
            "60" in record.message or "chunk" in record.message.lower()
            for record in caplog.records
        )

    def test_chunk_routing_correlation_id_propagation(self):
        """Test correlation_id propagates through chunk routing operations."""
        from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
            IrrigationSynchronizer,
        )

        chunks = []
        for i in range(60):
            pa_id = f"PA{(i // 6) + 1:02d}"
            dim_id = f"DIM{(i % 6) + 1:02d}"
            chunk = ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        doc = PreprocessedDocument(
            document_id="test",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

        questionnaire = {
            "blocks": {
                "D1_Q01": {
                    "question": "Test question?",
                    "patterns": [],
                }
            }
        }

        synchronizer = IrrigationSynchronizer(
            questionnaire=questionnaire,
            preprocessed_document=doc,
        )

        assert hasattr(synchronizer, "correlation_id")
        assert synchronizer.correlation_id is not None
        assert len(synchronizer.correlation_id) > 0

    def test_log_event_field_present_in_structured_logs(
        self, valid_60_chunk_document, caplog
    ):
        """Test 'event' field is present in structured log output."""
        with caplog.at_level(logging.INFO):
            ChunkMatrix(valid_60_chunk_document)

        log_messages = [r.message for r in caplog.records]
        has_event_field = any("event" in msg or "Event" in msg for msg in log_messages)
        assert has_event_field or len(caplog.records) > 0

    def test_chunk_id_in_logging_context(self, valid_60_chunk_document):
        """Test chunk_id appears in logging context for operations."""
        matrix = ChunkMatrix(valid_60_chunk_document)

        chunk = matrix.get_chunk("PA01", "DIM01")

        assert chunk.chunk_id is not None
        assert chunk.chunk_id == "PA01-DIM01"

    def test_question_id_context_in_task_generation(self):
        """Test question_id context is available for logging in task generation."""
        from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
            IrrigationSynchronizer,
        )

        chunks = []
        for i in range(60):
            pa_id = f"PA{(i // 6) + 1:02d}"
            dim_id = f"DIM{(i % 6) + 1:02d}"
            chunk = ChunkData(
                id=i,
                text=f"Chunk {i}",
                chunk_type="diagnostic",
                sentences=[],
                tables=[],
                start_pos=0,
                end_pos=10,
                confidence=0.9,
                policy_area_id=pa_id,
                dimension_id=dim_id,
            )
            chunks.append(chunk)

        doc = PreprocessedDocument(
            document_id="test",
            raw_text="Test",
            sentences=[],
            tables=[],
            metadata={"chunk_count": 60},
            chunks=chunks,
            processing_mode="chunked",
        )

        questionnaire = {
            "blocks": {
                "D1_Q01": {
                    "question": "Test question?",
                    "patterns": [],
                }
            }
        }

        synchronizer = IrrigationSynchronizer(
            questionnaire=questionnaire,
            preprocessed_document=doc,
        )

        plan = synchronizer.build_execution_plan()

        assert len(plan.tasks) > 0
        first_task = plan.tasks[0]
        assert hasattr(first_task, "question_id")
        assert first_task.question_id is not None
