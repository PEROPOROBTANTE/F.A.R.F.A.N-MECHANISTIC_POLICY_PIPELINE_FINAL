"""
Comprehensive test suite for ChunkMatrix validation and construction.

Tests cover:
- Deterministic ordering (multi-run stability)
- 60-chunk invariant enforcement
- Missing/duplicate chunk detection
- chunk_id validation (PA01-PA10, DIM01-DIM06 format)
- ValueError message verification
- Audit log structure validation
- Property-based tests using Hypothesis
"""

from datetime import datetime
from typing import Any

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.synchronization.irrigation_synchronizer import ChunkMatrix


def create_chunk(
    chunk_id: int,
    policy_area_id: str,
    dimension_id: str,
    text: str = "test content",
    chunk_type: str = "diagnostic",
) -> ChunkData:
    """Factory for creating test chunks with configurable attributes."""
    return ChunkData(
        id=chunk_id,
        text=text,
        chunk_type=chunk_type,  # type: ignore[arg-type]
        sentences=[],
        tables=[],
        start_pos=0,
        end_pos=len(text),
        confidence=0.95,
        policy_area_id=policy_area_id,
        dimension_id=dimension_id,
    )


def create_complete_document(chunk_order: str = "sequential") -> PreprocessedDocument:
    """Create a valid document with all 60 required chunks.

    Args:
        chunk_order: How to order chunks - 'sequential', 'reversed', or 'shuffled'
    """
    chunks = []
    chunk_id = 0
    for pa_num in range(1, 11):
        for dim_num in range(1, 7):
            pa_id = f"PA{pa_num:02d}"
            dim_id = f"DIM{dim_num:02d}"
            chunks.append(create_chunk(chunk_id, pa_id, dim_id))
            chunk_id += 1

    if chunk_order == "reversed":
        chunks = list(reversed(chunks))
    elif chunk_order == "shuffled":
        import random

        random.seed(42)
        random.shuffle(chunks)

    return PreprocessedDocument(
        document_id="test-doc",
        raw_text="test",
        sentences=[],
        tables=[],
        metadata={},
        chunks=chunks,
        ingested_at=datetime.now(),
    )


class TestChunkMatrixDeterministicOrdering:
    """Test deterministic ordering and multi-run stability."""

    def test_matrix_construction_is_deterministic_sequential_order(self) -> None:
        """ChunkMatrix construction should be deterministic across multiple runs with sequential input."""
        doc = create_complete_document("sequential")

        matrices = [ChunkMatrix(doc) for _ in range(5)]

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"

                chunks = [m.get_chunk(pa_id, dim_id) for m in matrices]
                first_chunk = chunks[0]

                for chunk in chunks[1:]:
                    assert chunk.id == first_chunk.id
                    assert chunk.text == first_chunk.text
                    assert chunk.policy_area_id == first_chunk.policy_area_id
                    assert chunk.dimension_id == first_chunk.dimension_id

    def test_matrix_construction_is_deterministic_reversed_order(self) -> None:
        """ChunkMatrix should produce same results regardless of input chunk ordering."""
        doc_sequential = create_complete_document("sequential")
        doc_reversed = create_complete_document("reversed")

        matrix_seq = ChunkMatrix(doc_sequential)
        matrix_rev = ChunkMatrix(doc_reversed)

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"

                chunk_seq = matrix_seq.get_chunk(pa_id, dim_id)
                chunk_rev = matrix_rev.get_chunk(pa_id, dim_id)

                assert chunk_seq.policy_area_id == chunk_rev.policy_area_id
                assert chunk_seq.dimension_id == chunk_rev.dimension_id

    def test_matrix_construction_is_deterministic_shuffled_order(self) -> None:
        """ChunkMatrix should handle shuffled input order deterministically."""
        doc_sequential = create_complete_document("sequential")
        doc_shuffled = create_complete_document("shuffled")

        matrix_seq = ChunkMatrix(doc_sequential)
        matrix_shuf = ChunkMatrix(doc_shuffled)

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"

                chunk_seq = matrix_seq.get_chunk(pa_id, dim_id)
                chunk_shuf = matrix_shuf.get_chunk(pa_id, dim_id)

                assert chunk_seq.policy_area_id == chunk_shuf.policy_area_id
                assert chunk_seq.dimension_id == chunk_shuf.dimension_id

    def test_multi_run_stability_with_identical_input(self) -> None:
        """Multiple ChunkMatrix constructions from same document should be identical."""
        doc = create_complete_document()

        runs = 10
        matrices = [ChunkMatrix(doc) for _ in range(runs)]

        test_keys = [("PA01", "DIM01"), ("PA05", "DIM03"), ("PA10", "DIM06")]

        for pa_id, dim_id in test_keys:
            chunks = [m.get_chunk(pa_id, dim_id) for m in matrices]
            first = chunks[0]

            for chunk in chunks[1:]:
                assert chunk.id == first.id
                assert chunk.policy_area_id == first.policy_area_id
                assert chunk.dimension_id == first.dimension_id


class TestSixtyChunkInvariantEnforcement:
    """Test strict enforcement of 60-chunk requirement."""

    def test_accepts_exactly_60_chunks(self) -> None:
        """ChunkMatrix should accept exactly 60 valid chunks."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        chunk = matrix.get_chunk("PA01", "DIM01")
        assert chunk.policy_area_id == "PA01"
        assert chunk.dimension_id == "DIM01"

    def test_rejects_59_chunks(self) -> None:
        """ChunkMatrix should reject documents with 59 chunks by detecting missing combination."""
        doc = create_complete_document()
        doc.chunks = doc.chunks[:59]

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        error_msg = str(exc_info.value)
        assert "Missing required chunk combinations" in error_msg

    def test_rejects_61_chunks(self) -> None:
        """ChunkMatrix should reject documents with 61 chunks."""
        doc = create_complete_document()
        first_chunk = doc.chunks[0]
        assert first_chunk.policy_area_id is not None
        assert first_chunk.dimension_id is not None
        duplicate_chunk = create_chunk(
            60, first_chunk.policy_area_id, first_chunk.dimension_id
        )
        doc.chunks.append(duplicate_chunk)

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        assert "Duplicate key detected" in str(exc_info.value)

    def test_rejects_0_chunks(self) -> None:
        """ChunkMatrix should reject documents with no chunks."""
        doc = PreprocessedDocument(
            document_id="test-doc",
            raw_text="test",
            sentences=[],
            tables=[],
            metadata={},
            chunks=[],
            ingested_at=datetime.now(),
        )

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        error_msg = str(exc_info.value)
        assert "Missing required chunk combinations" in error_msg

    def test_rejects_arbitrary_incorrect_count(self) -> None:
        """ChunkMatrix should reject any count other than 60."""
        for count in [1, 10, 30, 45, 58, 59, 62, 70]:
            if count > 60:
                continue
            doc = create_complete_document()
            doc.chunks = doc.chunks[:count]

            with pytest.raises(ValueError) as exc_info:
                ChunkMatrix(doc)

            error_msg = str(exc_info.value)
            assert (
                "Missing required chunk combinations" in error_msg
                or "Expected exactly 60 chunks" in error_msg
            )


class TestMissingChunkDetection:
    """Test detection and reporting of missing chunk combinations."""

    def test_detects_single_missing_chunk(self) -> None:
        """ChunkMatrix should detect and report a single missing PA-DIM combination."""
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
        assert "Missing required chunk combinations" in error_msg
        assert "PA05-DIM03" in error_msg

    def test_detects_multiple_missing_chunks(self) -> None:
        """ChunkMatrix should detect and report multiple missing combinations."""
        chunks = []
        chunk_id = 0
        missing_keys = [("PA02", "DIM01"), ("PA07", "DIM04"), ("PA10", "DIM06")]

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                if (pa_id, dim_id) in missing_keys:
                    continue
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
        assert "Missing required chunk combinations" in error_msg
        for pa_id, dim_id in missing_keys:
            assert f"{pa_id}-{dim_id}" in error_msg

    def test_missing_chunks_reported_in_sorted_order(self) -> None:
        """Missing chunk combinations should be reported in sorted order."""
        chunks = []
        chunk_id = 0
        missing_keys = [("PA10", "DIM06"), ("PA01", "DIM01"), ("PA05", "DIM03")]

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                if (pa_id, dim_id) in missing_keys:
                    continue
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
        assert "Missing required chunk combinations" in error_msg

        missing_str = error_msg.split("Missing required chunk combinations: ")[1]
        missing_list = missing_str.split(", ")
        assert missing_list == sorted(missing_list)


class TestDuplicateChunkDetection:
    """Test detection and reporting of duplicate chunk combinations."""

    def test_detects_duplicate_pa_dim_combination(self) -> None:
        """ChunkMatrix should detect duplicate PA-DIM combinations."""
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

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        error_msg = str(exc_info.value)
        assert "Duplicate key detected" in error_msg
        assert "PA01-DIM01" in error_msg

    def test_detects_duplicate_with_60_chunks(self) -> None:
        """ChunkMatrix should detect duplicates even when chunk count is 60."""
        doc = create_complete_document()
        doc.chunks[0] = create_chunk(0, "PA01", "DIM02")

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        error_msg = str(exc_info.value)
        assert (
            "Duplicate key detected" in error_msg
            or "Missing required chunk combinations" in error_msg
        )

    def test_detects_multiple_duplicates(self) -> None:
        """ChunkMatrix should detect first duplicate in sequence."""
        chunks = []
        chunks.append(create_chunk(0, "PA01", "DIM01"))
        chunks.append(create_chunk(1, "PA01", "DIM01"))
        chunks.append(create_chunk(2, "PA02", "DIM02"))
        chunks.append(create_chunk(3, "PA02", "DIM02"))

        chunk_id = 4
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                if (pa_num == 1 and dim_num == 1) or (pa_num == 2 and dim_num == 2):
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
        assert "Duplicate key detected" in error_msg


class TestChunkIdValidation:
    """Test validation of chunk_id format (PA01-PA10, DIM01-DIM06)."""

    def test_accepts_valid_pa_range(self) -> None:
        """ChunkMatrix should accept all valid PA values (PA01-PA10)."""
        for pa_num in range(1, 11):
            pa_id = f"PA{pa_num:02d}"
            chunks = []
            chunk_id = 0

            for dim_num in range(1, 7):
                dim_id = f"DIM{dim_num:02d}"
                chunks.append(create_chunk(chunk_id, pa_id, dim_id))
                chunk_id += 1

            for other_pa_num in range(1, 11):
                if other_pa_num == pa_num:
                    continue
                other_pa_id = f"PA{other_pa_num:02d}"
                for dim_num in range(1, 7):
                    dim_id = f"DIM{dim_num:02d}"
                    chunks.append(create_chunk(chunk_id, other_pa_id, dim_id))
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

            matrix = ChunkMatrix(doc)
            assert matrix.get_chunk(pa_id, "DIM01").policy_area_id == pa_id

    def test_accepts_valid_dim_range(self) -> None:
        """ChunkMatrix should accept all valid DIM values (DIM01-DIM06)."""
        for dim_num in range(1, 7):
            dim_id = f"DIM{dim_num:02d}"
            doc = create_complete_document()
            matrix = ChunkMatrix(doc)

            for pa_num in range(1, 11):
                pa_id = f"PA{pa_num:02d}"
                assert matrix.get_chunk(pa_id, dim_id).dimension_id == dim_id

    def test_rejects_pa00(self) -> None:
        """ChunkData should reject PA00 at creation time."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA00", "DIM01")

        error_msg = str(exc_info.value)
        assert "Invalid chunk_id" in error_msg
        assert "PA00-DIM01" in error_msg

    def test_rejects_pa11(self) -> None:
        """ChunkData should reject PA11 at creation time."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA11", "DIM01")

        error_msg = str(exc_info.value)
        assert "Invalid chunk_id" in error_msg
        assert "PA11-DIM01" in error_msg

    def test_rejects_dim00(self) -> None:
        """ChunkData should reject DIM00 at creation time."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA01", "DIM00")

        error_msg = str(exc_info.value)
        assert "Invalid chunk_id" in error_msg
        assert "PA01-DIM00" in error_msg

    def test_rejects_dim07(self) -> None:
        """ChunkData should reject DIM07 at creation time."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA01", "DIM07")

        error_msg = str(exc_info.value)
        assert "Invalid chunk_id" in error_msg
        assert "PA01-DIM07" in error_msg

    def test_rejects_malformed_pa_format(self) -> None:
        """ChunkData should reject malformed PA identifiers at creation time."""
        invalid_formats = ["P01", "PA1", "PA001", "pa01", "XA01", "PA-01"]

        for invalid_pa in invalid_formats:
            with pytest.raises(ValueError) as exc_info:
                create_chunk(0, invalid_pa, "DIM01")

            error_msg = str(exc_info.value)
            assert "Invalid chunk_id" in error_msg

    def test_rejects_malformed_dim_format(self) -> None:
        """ChunkData should reject malformed DIM identifiers at creation time."""
        invalid_formats = ["D01", "DIM1", "DIM001", "dim01", "XIM01", "DIM-01"]

        for invalid_dim in invalid_formats:
            with pytest.raises(ValueError) as exc_info:
                create_chunk(0, "PA01", invalid_dim)

            error_msg = str(exc_info.value)
            assert "Invalid chunk_id" in error_msg


class TestNullMetadataValidation:
    """Test validation of null policy_area_id and dimension_id."""

    def test_rejects_null_policy_area_id(self) -> None:
        """ChunkData should reject chunks with null policy_area_id at creation time."""
        with pytest.raises(ValueError) as exc_info:
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

        error_msg = str(exc_info.value)
        assert "chunk_id is required" in error_msg

    def test_rejects_null_dimension_id(self) -> None:
        """ChunkData should reject chunks with null dimension_id at creation time."""
        with pytest.raises(ValueError) as exc_info:
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

        error_msg = str(exc_info.value)
        assert "chunk_id is required" in error_msg

    def test_rejects_multiple_null_metadata(self) -> None:
        """ChunkData should detect missing chunk_id when both PA and DIM are null."""
        with pytest.raises(ValueError) as exc_info:
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
                dimension_id=None,
            )

        error_msg = str(exc_info.value)
        assert "chunk_id is required" in error_msg


class TestValueErrorMessages:
    """Test clarity and completeness of ValueError messages."""

    def test_missing_chunk_error_includes_expected_format(self) -> None:
        """Missing chunk error should explain expected format."""
        doc = create_complete_document()
        doc.chunks = doc.chunks[:59]

        with pytest.raises(ValueError) as exc_info:
            ChunkMatrix(doc)

        error_msg = str(exc_info.value)
        assert "PA" in error_msg and "DIM" in error_msg

    def test_invalid_format_error_includes_expected_pattern(self) -> None:
        """Invalid format error should show expected PA{01-10}-DIM{01-06} pattern."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA99", "DIM01")

        error_msg = str(exc_info.value)
        assert (
            "expected format PA{01-10}-DIM{01-06}" in error_msg.lower()
            or "invalid chunk_id" in error_msg.lower()
        )

    def test_duplicate_error_includes_specific_key(self) -> None:
        """Duplicate error should include the specific duplicate key."""
        chunks = [create_chunk(0, "PA05", "DIM03"), create_chunk(1, "PA05", "DIM03")]

        chunk_id = 2
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
        assert "PA05" in error_msg and "DIM03" in error_msg

    def test_null_metadata_error_message(self) -> None:
        """Null metadata error should have clear message."""
        with pytest.raises(ValueError) as exc_info:
            ChunkData(
                id=42,
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

        error_msg = str(exc_info.value)
        assert "chunk_id is required" in error_msg


class TestChunkMatrixAccess:
    """Test ChunkMatrix access patterns and guarantees."""

    def test_get_chunk_returns_correct_chunk(self) -> None:
        """get_chunk should return the chunk with matching PA and DIM."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        chunk = matrix.get_chunk("PA07", "DIM04")
        assert chunk.policy_area_id == "PA07"
        assert chunk.dimension_id == "DIM04"

    def test_get_chunk_all_60_combinations(self) -> None:
        """get_chunk should work for all 60 valid PA-DIM combinations."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = matrix.get_chunk(pa_id, dim_id)
                assert chunk.policy_area_id == pa_id
                assert chunk.dimension_id == dim_id

    def test_get_chunk_raises_keyerror_for_invalid_combination(self) -> None:
        """get_chunk should raise KeyError for invalid combinations."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        with pytest.raises(KeyError) as exc_info:
            matrix.get_chunk("PA11", "DIM01")

        error_msg = str(exc_info.value)
        assert "Chunk not found" in error_msg
        assert "PA11-DIM01" in error_msg

    def test_get_chunk_preserves_chunk_metadata(self) -> None:
        """get_chunk should preserve all chunk metadata."""
        doc = create_complete_document()
        doc.chunks[0] = ChunkData(
            id=999,
            text="specific content",
            chunk_type="activity",
            sentences=[1, 2, 3],
            tables=[0],
            start_pos=100,
            end_pos=200,
            confidence=0.87,
            policy_area_id="PA01",
            dimension_id="DIM01",
        )

        matrix = ChunkMatrix(doc)
        chunk = matrix.get_chunk("PA01", "DIM01")

        assert chunk.id == 999
        assert chunk.text == "specific content"
        assert chunk.chunk_type == "activity"
        assert chunk.sentences == [1, 2, 3]
        assert chunk.tables == [0]
        assert chunk.start_pos == 100
        assert chunk.end_pos == 200
        assert chunk.confidence == 0.87


@st.composite
def valid_chunk_id_strategy(draw: Any) -> int:  # type: ignore[misc]
    """Strategy for generating valid chunk IDs."""
    return draw(st.integers(min_value=0, max_value=10000))  # type: ignore[no-any-return]


@st.composite
def valid_pa_id_strategy(draw: Any) -> str:  # type: ignore[misc]
    """Strategy for generating valid PA identifiers (PA01-PA10)."""
    pa_num: int = draw(st.integers(min_value=1, max_value=10))
    return f"PA{pa_num:02d}"


@st.composite
def valid_dim_id_strategy(draw: Any) -> str:  # type: ignore[misc]
    """Strategy for generating valid DIM identifiers (DIM01-DIM06)."""
    dim_num: int = draw(st.integers(min_value=1, max_value=6))
    return f"DIM{dim_num:02d}"


@st.composite
def invalid_pa_id_strategy(draw: Any) -> str:  # type: ignore[misc]
    """Strategy for generating invalid PA identifiers."""
    return draw(  # type: ignore[no-any-return]
        st.one_of(
            st.just("PA00"),
            st.just("PA11"),
            st.just("PA99"),
            st.just("P01"),
            st.just("PA1"),
            st.just("pa01"),
        )
    )


@st.composite
def invalid_dim_id_strategy(draw: Any) -> str:  # type: ignore[misc]
    """Strategy for generating invalid DIM identifiers."""
    return draw(  # type: ignore[no-any-return]
        st.one_of(
            st.just("DIM00"),
            st.just("DIM07"),
            st.just("DIM99"),
            st.just("D01"),
            st.just("DIM1"),
            st.just("dim01"),
        )
    )


class TestChunkMatrixPropertyBased:
    """Property-based tests using Hypothesis for ChunkMatrix validation."""

    @given(chunk_order=st.sampled_from(["sequential", "reversed", "shuffled"]))
    @settings(max_examples=20, deadline=2000)
    def test_property_ordering_invariance(self, chunk_order: str) -> None:  # type: ignore[misc]
        """Property: ChunkMatrix construction is invariant to input chunk ordering."""
        doc = create_complete_document(chunk_order)
        matrix = ChunkMatrix(doc)

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunk = matrix.get_chunk(pa_id, dim_id)
                assert chunk.policy_area_id == pa_id
                assert chunk.dimension_id == dim_id

    @given(
        pa_id=valid_pa_id_strategy(),
        dim_id=valid_dim_id_strategy(),
    )
    @settings(max_examples=50, deadline=1000)
    def test_property_valid_ids_accepted(self, pa_id: str, dim_id: str) -> None:  # type: ignore[misc]
        """Property: All valid PA-DIM combinations are accepted."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        chunk = matrix.get_chunk(pa_id, dim_id)
        assert chunk.policy_area_id == pa_id
        assert chunk.dimension_id == dim_id

    @given(invalid_pa=invalid_pa_id_strategy())
    @settings(
        max_examples=20,
        deadline=1000,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_property_invalid_pa_rejected(self, invalid_pa: str) -> None:  # type: ignore[misc]
        """Property: Invalid PA identifiers are rejected at ChunkData creation."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, invalid_pa, "DIM01")

        assert "Invalid chunk_id" in str(exc_info.value)

    @given(invalid_dim=invalid_dim_id_strategy())
    @settings(
        max_examples=20,
        deadline=1000,
        suppress_health_check=[HealthCheck.filter_too_much],
    )
    def test_property_invalid_dim_rejected(self, invalid_dim: str) -> None:  # type: ignore[misc]
        """Property: Invalid DIM identifiers are rejected at ChunkData creation."""
        with pytest.raises(ValueError) as exc_info:
            create_chunk(0, "PA01", invalid_dim)

        assert "Invalid chunk_id" in str(exc_info.value)

    @given(
        pa_num=st.integers(min_value=1, max_value=10),
        dim_num=st.integers(min_value=1, max_value=6),
    )
    @settings(max_examples=60, deadline=1000)
    def test_property_all_combinations_accessible(  # type: ignore[misc]
        self, pa_num: int, dim_num: int
    ) -> None:
        """Property: All 60 PA-DIM combinations are accessible via get_chunk."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        pa_id = f"PA{pa_num:02d}"
        dim_id = f"DIM{dim_num:02d}"

        chunk = matrix.get_chunk(pa_id, dim_id)
        assert chunk is not None
        assert chunk.policy_area_id == pa_id
        assert chunk.dimension_id == dim_id

    @given(
        missing_pa=st.integers(min_value=1, max_value=10),
        missing_dim=st.integers(min_value=1, max_value=6),
    )
    @settings(max_examples=30, deadline=1000)
    def test_property_missing_chunks_detected(  # type: ignore[misc]
        self, missing_pa: int, missing_dim: int
    ) -> None:
        """Property: Missing any PA-DIM combination is detected."""
        chunks = []
        chunk_id = 0
        missing_pa_id = f"PA{missing_pa:02d}"
        missing_dim_id = f"DIM{missing_dim:02d}"

        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                if pa_id == missing_pa_id and dim_id == missing_dim_id:
                    continue
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
        assert "Missing required chunk combinations" in error_msg
        assert f"{missing_pa_id}-{missing_dim_id}" in error_msg

    @given(
        dup_pa=st.integers(min_value=1, max_value=10),
        dup_dim=st.integers(min_value=1, max_value=6),
    )
    @settings(max_examples=30, deadline=1000)
    def test_property_duplicates_detected(self, dup_pa: int, dup_dim: int) -> None:  # type: ignore[misc]
        """Property: Duplicate PA-DIM combinations are always detected."""
        dup_pa_id = f"PA{dup_pa:02d}"
        dup_dim_id = f"DIM{dup_dim:02d}"

        chunks = [
            create_chunk(0, dup_pa_id, dup_dim_id),
            create_chunk(1, dup_pa_id, dup_dim_id),
        ]

        chunk_id = 2
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                if pa_id == dup_pa_id and dim_id == dup_dim_id:
                    continue
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
        assert "Duplicate key detected" in error_msg
        assert dup_pa_id in error_msg and dup_dim_id in error_msg

    @given(text=st.text(min_size=1, max_size=1000))
    @settings(max_examples=30, deadline=1000)
    def test_property_chunk_content_preserved(self, text: str) -> None:  # type: ignore[misc]
        """Property: Chunk text content is preserved through matrix construction."""
        doc = create_complete_document()
        doc.chunks[0] = create_chunk(0, "PA01", "DIM01", text=text)

        matrix = ChunkMatrix(doc)
        chunk = matrix.get_chunk("PA01", "DIM01")

        assert chunk.text == text


class TestChunkMatrixAuditLog:
    """Test audit log structure and validation metadata."""

    def test_matrix_internal_structure_is_dict(self) -> None:
        """ChunkMatrix internal structure should be accessible as dict."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        assert hasattr(matrix, "_matrix")
        assert isinstance(matrix._matrix, dict)

    def test_matrix_stores_all_60_chunks(self) -> None:
        """ChunkMatrix should store exactly 60 chunks internally."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        assert len(matrix._matrix) == 60

    def test_matrix_keys_are_tuples(self) -> None:
        """ChunkMatrix keys should be (policy_area_id, dimension_id) tuples."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        for key in matrix._matrix.keys():
            assert isinstance(key, tuple)
            assert len(key) == 2
            assert isinstance(key[0], str)
            assert isinstance(key[1], str)

    def test_matrix_values_are_chunk_data(self) -> None:
        """ChunkMatrix values should be ChunkData instances."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        for value in matrix._matrix.values():
            assert isinstance(value, ChunkData)

    def test_matrix_contains_all_expected_keys(self) -> None:
        """ChunkMatrix should contain all 60 expected PA-DIM combinations as keys."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        expected_keys = {
            (f"PA{pa:02d}", f"DIM{dim:02d}")
            for pa in range(1, 11)
            for dim in range(1, 7)
        }

        assert set(matrix._matrix.keys()) == expected_keys

    def test_matrix_key_to_chunk_mapping_is_correct(self) -> None:
        """ChunkMatrix keys should correctly map to their corresponding chunks."""
        doc = create_complete_document()
        matrix = ChunkMatrix(doc)

        for (pa_id, dim_id), chunk in matrix._matrix.items():
            assert chunk.policy_area_id == pa_id
            assert chunk.dimension_id == dim_id


class TestChunkMatrixConstants:
    """Test ChunkMatrix class constants and configuration."""

    def test_policy_areas_constant(self) -> None:
        """ChunkMatrix.POLICY_AREAS should contain PA01-PA10."""
        expected = [f"PA{i:02d}" for i in range(1, 11)]
        assert expected == ChunkMatrix.POLICY_AREAS

    def test_dimensions_constant(self) -> None:
        """ChunkMatrix.DIMENSIONS should contain DIM01-DIM06."""
        expected = [f"DIM{i:02d}" for i in range(1, 7)]
        assert expected == ChunkMatrix.DIMENSIONS

    def test_expected_chunk_count_constant(self) -> None:
        """ChunkMatrix.EXPECTED_CHUNK_COUNT should be 60."""
        assert ChunkMatrix.EXPECTED_CHUNK_COUNT == 60

    def test_chunk_id_pattern_validates_correctly(self) -> None:
        """ChunkMatrix.CHUNK_ID_PATTERN should validate correct formats."""
        pattern = ChunkMatrix.CHUNK_ID_PATTERN

        valid_ids = [
            f"PA{pa:02d}-DIM{dim:02d}" for pa in range(1, 11) for dim in range(1, 7)
        ]

        for chunk_id in valid_ids:
            assert pattern.match(chunk_id), f"Valid ID rejected: {chunk_id}"

    def test_chunk_id_pattern_rejects_invalid(self) -> None:
        """ChunkMatrix.CHUNK_ID_PATTERN should reject invalid formats."""
        pattern = ChunkMatrix.CHUNK_ID_PATTERN

        invalid_ids = [
            "PA00-DIM01",
            "PA11-DIM01",
            "PA01-DIM00",
            "PA01-DIM07",
            "P01-DIM01",
            "PA1-DIM01",
            "PA01-D01",
            "PA01-DIM1",
            "pa01-dim01",
            "PA01_DIM01",
        ]

        for chunk_id in invalid_ids:
            assert not pattern.match(chunk_id), f"Invalid ID accepted: {chunk_id}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
