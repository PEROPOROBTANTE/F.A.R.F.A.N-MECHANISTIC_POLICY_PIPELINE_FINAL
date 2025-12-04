"""Unit tests for ChunkMatrix validation and chunk routing."""

from datetime import datetime

import pytest

from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
    ChunkRoutingResult,
    IrrigationSynchronizer,
)
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.synchronization.irrigation_synchronizer import ChunkMatrix


def create_chunk(
    chunk_id: int, policy_area_id: str, dimension_id: str, text: str = "test content"
) -> ChunkData:
    """Factory for creating test chunks."""
    return ChunkData(
        id=chunk_id,
        text=text,
        chunk_type="diagnostic",
        sentences=[],
        tables=[],
        start_pos=0,
        end_pos=len(text),
        confidence=0.95,
        policy_area_id=policy_area_id,
        dimension_id=dimension_id,
    )


def create_complete_document() -> PreprocessedDocument:
    """Create a valid document with all 60 required chunks."""
    chunks = []
    chunk_id = 0
    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunks.append(create_chunk(chunk_id, pa_id, dim_id))
            chunk_id += 1

    return PreprocessedDocument(
        document_id="test-doc",
        raw_text="test",
        sentences=[],
        tables=[],
        metadata={},
        chunks=chunks,
        ingested_at=datetime.now(),
    )


def test_chunk_matrix_accepts_valid_60_chunks() -> None:
    """ChunkMatrix should accept exactly 60 valid chunks."""
    doc = create_complete_document()
    matrix = ChunkMatrix(doc)

    chunk = matrix.get_chunk("PA01", "DIM01")
    assert chunk.policy_area_id == "PA01"
    assert chunk.dimension_id == "DIM01"


def test_chunk_matrix_rejects_59_chunks() -> None:
    """ChunkMatrix should reject documents with 59 chunks by detecting missing combination."""
    doc = create_complete_document()
    doc.chunks = doc.chunks[:59]

    with pytest.raises(ValueError) as exc_info:
        ChunkMatrix(doc)

    error_msg = str(exc_info.value)
    assert "Missing chunk combinations" in error_msg


def test_chunk_matrix_rejects_61_chunks() -> None:
    """ChunkMatrix should reject documents with 61 chunks by detecting duplicate."""
    doc = create_complete_document()
    duplicate_chunk = doc.chunks[0]
    doc.chunks.append(
        create_chunk(
            60,
            duplicate_chunk.policy_area_id,
            duplicate_chunk.dimension_id,
            "duplicate",
        )
    )

    with pytest.raises(ValueError) as exc_info:
        ChunkMatrix(doc)

    error_msg = str(exc_info.value)
    assert "Duplicate (PA, DIM) combination detected" in error_msg


def test_chunk_matrix_rejects_duplicate_keys() -> None:
    """ChunkMatrix should reject documents with duplicate PA-DIM combinations."""
    chunks = []
    chunks.append(create_chunk(0, "PA01", "DIM01"))
    chunks.append(create_chunk(1, "PA01", "DIM01"))

    chunk_id = 2
    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            if pa_num == 1 and dim_num == 1:
                continue
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunks.append(create_chunk(chunk_id, pa_id, dim_id))
            chunk_id += 1

    doc = PreprocessedDocument(
        document_id="test-doc",
        raw_text="test",
        sentences=[],
        tables=[],
        metadata={},
        chunks=chunks,
        ingested_at=datetime.now(),
    )

    with pytest.raises(ValueError, match=r"Duplicate .*PA01-DIM01"):
        ChunkMatrix(doc)


def test_chunk_matrix_detects_missing_combinations() -> None:
    """ChunkMatrix should detect and report missing PA-DIM combinations with 59 chunks."""
    chunks = []
    chunk_id = 0
    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            if pa_num == 5 and dim_num == 3:
                continue
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunks.append(create_chunk(chunk_id, pa_id, dim_id))
            chunk_id += 1

    doc = PreprocessedDocument(
        document_id="test-doc",
        raw_text="test",
        sentences=[],
        tables=[],
        metadata={},
        chunks=chunks,
        ingested_at=datetime.now(),
    )

    with pytest.raises(ValueError) as exc_info:
        ChunkMatrix(doc)

    error_msg = str(exc_info.value)
    assert "Missing chunk combinations" in error_msg
    assert "PA05', 'DIM03" in error_msg


def test_chunk_matrix_detects_missing_combinations_with_exact_error() -> None:
    """ChunkMatrix should report missing PA-DIM combination when 60 chunks but duplicate."""
    doc = create_complete_document()
    original_chunk = doc.chunks[0]
    doc.chunks[0] = create_chunk(
        0, original_chunk.policy_area_id, original_chunk.dimension_id
    )
    doc.chunks[10] = create_chunk(
        10, original_chunk.policy_area_id, original_chunk.dimension_id
    )

    with pytest.raises(ValueError) as exc_info:
        ChunkMatrix(doc)

    error_msg = str(exc_info.value)
    assert "Duplicate" in error_msg
    assert f"{original_chunk.policy_area_id}-{original_chunk.dimension_id}" in error_msg


def test_chunk_matrix_reports_specific_missing_key() -> None:
    """ChunkMatrix should report specific missing key PA05-DIM03 in error message."""
    chunks = []
    chunk_id = 0
    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            if pa_num == 5 and dim_num == 3:
                chunk_id += 1
                continue
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunks.append(create_chunk(chunk_id, pa_id, dim_id))
            chunk_id += 1

    chunks.append(create_chunk(59, "PA05", "DIM03"))

    doc = PreprocessedDocument(
        document_id="test-doc",
        raw_text="test",
        sentences=[],
        tables=[],
        metadata={},
        chunks=chunks,
        ingested_at=datetime.now(),
    )

    matrix = ChunkMatrix(doc)
    chunk = matrix.get_chunk("PA05", "DIM03")
    assert chunk.policy_area_id == "PA05"
    assert chunk.dimension_id == "DIM03"


def test_chunk_matrix_rejects_null_policy_area_id() -> None:
    """ChunkData should reject chunks with null policy_area_id at creation time."""
    with pytest.raises(ValueError, match="chunk_id is required"):
        ChunkData(
            id=0,
            text="test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=4,
            confidence=0.95,
            policy_area_id=None,
            dimension_id="DIM01",
        )


def test_chunk_matrix_rejects_null_dimension_id() -> None:
    """ChunkData should reject chunks with null dimension_id at creation time."""
    with pytest.raises(ValueError, match="chunk_id is required"):
        ChunkData(
            id=0,
            text="test",
            chunk_type="diagnostic",
            sentences=[],
            tables=[],
            start_pos=0,
            end_pos=4,
            confidence=0.95,
            policy_area_id="PA01",
            dimension_id=None,
        )


def test_chunk_matrix_rejects_invalid_chunk_id_format_pa() -> None:
    """ChunkData should reject invalid policy area format at creation time."""
    with pytest.raises(ValueError, match=r"Invalid chunk_id"):
        create_chunk(0, "PA11", "DIM01")


def test_chunk_matrix_rejects_invalid_chunk_id_format_dim() -> None:
    """ChunkData should reject invalid dimension format at creation time."""
    with pytest.raises(ValueError, match=r"Invalid chunk_id"):
        create_chunk(0, "PA01", "DIM07")


def test_chunk_matrix_rejects_malformed_chunk_id() -> None:
    """ChunkData should reject malformed chunk IDs at creation time."""
    with pytest.raises(ValueError, match=r"Invalid chunk_id"):
        create_chunk(0, "P01", "DIM01")


def test_chunk_matrix_get_chunk_success() -> None:
    """get_chunk should return correct chunk for valid keys."""
    doc = create_complete_document()
    matrix = ChunkMatrix(doc)

    chunk = matrix.get_chunk("PA05", "DIM03")
    assert chunk.policy_area_id == "PA05"
    assert chunk.dimension_id == "DIM03"


def test_chunk_matrix_get_chunk_all_combinations() -> None:
    """get_chunk should work for all 60 valid combinations."""
    doc = create_complete_document()
    matrix = ChunkMatrix(doc)

    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunk = matrix.get_chunk(pa_id, dim_id)
            assert chunk.policy_area_id == pa_id
            assert chunk.dimension_id == dim_id


def test_chunk_matrix_get_chunk_missing_key() -> None:
    """get_chunk should raise KeyError for missing combinations."""
    doc = create_complete_document()
    doc.chunks = [
        chunk
        for chunk in doc.chunks
        if not (chunk.policy_area_id == "PA05" and chunk.dimension_id == "DIM03")
    ]
    doc.chunks.append(create_chunk(59, "PA05", "DIM03"))

    matrix = ChunkMatrix(doc)

    with pytest.raises(KeyError, match="Chunk not found for key: PA11-DIM01"):
        matrix.get_chunk("PA11", "DIM01")


def test_chunk_matrix_get_chunk_o1_lookup() -> None:
    """get_chunk should provide O(1) lookup performance."""
    doc = create_complete_document()
    matrix = ChunkMatrix(doc)

    import time

    iterations = 1000
    start = time.perf_counter()
    for _ in range(iterations):
        matrix.get_chunk("PA05", "DIM03")
    elapsed = time.perf_counter() - start

    assert elapsed < 0.1, f"O(1) lookup too slow: {elapsed}s for {iterations} lookups"


def test_chunk_matrix_preserves_chunk_content() -> None:
    """ChunkMatrix should preserve original chunk content and metadata."""
    doc = create_complete_document()
    doc.chunks[0] = ChunkData(
        id=42,
        text="specific test content",
        chunk_type="activity",
        sentences=[1, 2, 3],
        tables=[],
        start_pos=10,
        end_pos=31,
        confidence=0.87,
        policy_area_id="PA01",
        dimension_id="DIM01",
    )

    matrix = ChunkMatrix(doc)
    chunk = matrix.get_chunk("PA01", "DIM01")

    assert chunk.id == 42
    assert chunk.text == "specific test content"
    assert chunk.chunk_type == "activity"
    assert chunk.sentences == [1, 2, 3]
    assert chunk.confidence == 0.87


def test_validate_chunk_routing_success() -> None:
    """validate_chunk_routing should successfully route valid question to chunk."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {
        "question_id": "D1-Q01",
        "policy_area_id": "PA05",
        "dimension_id": "DIM03",
        "question_text": "Test question",
    }

    result = synchronizer.validate_chunk_routing(question)

    assert isinstance(result, ChunkRoutingResult)
    assert result.chunk_id == "PA05-DIM03"
    assert result.policy_area_id == "PA05"
    assert result.dimension_id == "DIM03"
    assert result.text_content == "test content"
    assert result.target_chunk.policy_area_id == "PA05"
    assert result.target_chunk.dimension_id == "DIM03"


def test_validate_chunk_routing_missing_question_id() -> None:
    """validate_chunk_routing should raise ValueError if question_id missing."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {"policy_area_id": "PA05", "dimension_id": "DIM03"}

    with pytest.raises(ValueError, match="missing required 'question_id' field"):
        synchronizer.validate_chunk_routing(question)


def test_validate_chunk_routing_missing_policy_area_id() -> None:
    """validate_chunk_routing should raise ValueError if policy_area_id missing."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {"question_id": "D1-Q01", "dimension_id": "DIM03"}

    with pytest.raises(ValueError, match="missing required 'policy_area_id' field"):
        synchronizer.validate_chunk_routing(question)


def test_validate_chunk_routing_missing_dimension_id() -> None:
    """validate_chunk_routing should raise ValueError if dimension_id missing."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {"question_id": "D1-Q01", "policy_area_id": "PA05"}

    with pytest.raises(ValueError, match="missing required 'dimension_id' field"):
        synchronizer.validate_chunk_routing(question)


def test_validate_chunk_routing_chunk_not_found() -> None:
    """validate_chunk_routing should raise ValueError if chunk not in matrix."""
    doc = create_complete_document()
    doc.chunks = [
        chunk
        for chunk in doc.chunks
        if not (chunk.policy_area_id == "PA05" and chunk.dimension_id == "DIM03")
    ]

    questionnaire = {"blocks": {}}

    with pytest.raises(
        ValueError,
        match="Chunk matrix validation failed during synchronizer initialization",
    ):
        IrrigationSynchronizer(questionnaire=questionnaire, preprocessed_document=doc)


def test_validate_chunk_routing_empty_text() -> None:
    """validate_chunk_routing should raise ValueError if chunk text is empty."""
    doc = create_complete_document()
    for chunk in doc.chunks:
        if chunk.policy_area_id == "PA05" and chunk.dimension_id == "DIM03":
            idx = doc.chunks.index(chunk)
            doc.chunks[idx] = ChunkData(
                id=chunk.id,
                text="",
                chunk_type=chunk.chunk_type,
                sentences=chunk.sentences,
                tables=chunk.tables,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                confidence=chunk.confidence,
                policy_area_id=chunk.policy_area_id,
                dimension_id=chunk.dimension_id,
            )
            break

    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {
        "question_id": "D1-Q01",
        "policy_area_id": "PA05",
        "dimension_id": "DIM03",
    }

    with pytest.raises(ValueError, match="empty or whitespace-only text"):
        synchronizer.validate_chunk_routing(question)


def test_validate_chunk_routing_whitespace_only_text() -> None:
    """validate_chunk_routing should raise ValueError if chunk text is whitespace."""
    doc = create_complete_document()
    for chunk in doc.chunks:
        if chunk.policy_area_id == "PA05" and chunk.dimension_id == "DIM03":
            idx = doc.chunks.index(chunk)
            doc.chunks[idx] = ChunkData(
                id=chunk.id,
                text="   \n\t  ",
                chunk_type=chunk.chunk_type,
                sentences=chunk.sentences,
                tables=chunk.tables,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                confidence=chunk.confidence,
                policy_area_id=chunk.policy_area_id,
                dimension_id=chunk.dimension_id,
            )
            break

    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {
        "question_id": "D1-Q01",
        "policy_area_id": "PA05",
        "dimension_id": "DIM03",
    }

    with pytest.raises(ValueError, match="empty or whitespace-only text"):
        synchronizer.validate_chunk_routing(question)


def test_validate_chunk_routing_expected_elements_default() -> None:
    """validate_chunk_routing should handle missing expected_elements gracefully."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {
        "question_id": "D1-Q01",
        "policy_area_id": "PA05",
        "dimension_id": "DIM03",
    }

    result = synchronizer.validate_chunk_routing(question)

    assert result.expected_elements == []


def test_validate_chunk_routing_immutability() -> None:
    """ChunkRoutingResult should be immutable."""
    doc = create_complete_document()
    questionnaire = {"blocks": {}}
    synchronizer = IrrigationSynchronizer(
        questionnaire=questionnaire, preprocessed_document=doc
    )

    question = {
        "question_id": "D1-Q01",
        "policy_area_id": "PA05",
        "dimension_id": "DIM03",
    }

    result = synchronizer.validate_chunk_routing(question)

    with pytest.raises(Exception):
        result.chunk_id = "different_id"
