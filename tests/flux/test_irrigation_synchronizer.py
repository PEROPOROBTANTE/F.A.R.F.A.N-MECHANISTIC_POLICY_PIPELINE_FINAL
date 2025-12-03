"""
Tests for IrrigationSynchronizer - Question-to-Chunk Matching
============================================================

Comprehensive test suite covering:
- O(1) chunk matching with complete and incomplete matrices
- Pattern filtering with validation and cross-contamination checks
- Property-based testing for pattern isolation guarantees

Test Standards:
- pytest for test framework
- hypothesis for property-based testing
- Clear test names describing behavior
"""

import pytest
from hypothesis import given, strategies as st

from farfan_pipeline.flux.irrigation_synchronizer import (
    ChunkMatrix,
    Question,
    IrrigationSynchronizer,
)


@pytest.fixture
def complete_chunk_matrix() -> ChunkMatrix:
    """Create a complete 10×6 matrix with all 60 chunks."""
    chunks = {}
    for pa_idx in range(1, 11):
        pa_id = f"PA{pa_idx:02d}"
        for dim_idx in range(1, 7):
            dim_id = f"D{dim_idx}"
            chunks[(pa_id, dim_id)] = {
                "chunk_id": f"{pa_id}_{dim_id}",
                "policy_area_id": pa_id,
                "dimension_id": dim_id,
                "text": f"Chunk for {pa_id} {dim_id}",
            }
    return ChunkMatrix(chunks=chunks)


@pytest.fixture
def incomplete_chunk_matrix() -> ChunkMatrix:
    """Create matrix with 59 chunks (missing PA01_D1)."""
    chunks = {}
    for pa_idx in range(1, 11):
        pa_id = f"PA{pa_idx:02d}"
        for dim_idx in range(1, 7):
            dim_id = f"D{dim_idx}"
            if pa_id == "PA01" and dim_id == "D1":
                continue
            chunks[(pa_id, dim_id)] = {
                "chunk_id": f"{pa_id}_{dim_id}",
                "policy_area_id": pa_id,
                "dimension_id": dim_id,
                "text": f"Chunk for {pa_id} {dim_id}",
            }
    return ChunkMatrix(chunks=chunks)


@pytest.fixture
def sample_questions() -> list[Question]:
    """Create 300 questions (50 per dimension × 6 dimensions)."""
    questions = []
    q_idx = 1
    for dim_idx in range(1, 7):
        dim_id = f"D{dim_idx}"
        for pa_idx in range(1, 11):
            pa_id = f"PA{pa_idx:02d}"
            for q_in_pa in range(5):
                questions.append(
                    Question(
                        question_id=f"Q{q_idx:03d}",
                        policy_area_id=pa_id,
                        dimension_id=dim_id,
                        patterns=[
                            {
                                "pattern": f"pattern_{q_idx}",
                                "policy_area_id": pa_id,
                            }
                        ],
                    )
                )
                q_idx += 1
    return questions


def test_match_chunk_with_complete_matrix(
    complete_chunk_matrix: ChunkMatrix,
    sample_questions: list[Question]
) -> None:
    """Test _match_chunk succeeds with complete 60-chunk matrix and 300 questions."""
    synchronizer = IrrigationSynchronizer()
    
    assert len(sample_questions) == 300, "Should have 300 questions"
    assert len(complete_chunk_matrix.chunks) == 60, "Should have 60 chunks"
    
    for question in sample_questions:
        chunk = synchronizer._match_chunk(question, complete_chunk_matrix)
        
        assert chunk is not None
        assert chunk["policy_area_id"] == question.policy_area_id
        assert chunk["dimension_id"] == question.dimension_id
        assert chunk["chunk_id"] == f"{question.policy_area_id}_{question.dimension_id}"


def test_match_chunk_fails_on_missing_chunk(
    incomplete_chunk_matrix: ChunkMatrix
) -> None:
    """Test _match_chunk raises ValueError with descriptive message for missing chunk."""
    synchronizer = IrrigationSynchronizer()
    
    question = Question(
        question_id="Q001",
        policy_area_id="PA01",
        dimension_id="D1",
        patterns=[],
    )
    
    with pytest.raises(ValueError) as exc_info:
        synchronizer._match_chunk(question, incomplete_chunk_matrix)
    
    error_msg = str(exc_info.value)
    assert "Q001" in error_msg, "Error should include question_id"
    assert "PA01" in error_msg, "Error should include policy_area_id"
    assert "D1" in error_msg, "Error should include dimension_id"
    assert "No chunk found" in error_msg or "Failed to match" in error_msg


def test_filter_patterns_enforces_policy_area_id_field() -> None:
    """Test _filter_patterns validates all patterns have 'policy_area_id' field."""
    synchronizer = IrrigationSynchronizer()
    
    question_with_invalid_pattern = Question(
        question_id="Q123",
        policy_area_id="PA05",
        dimension_id="D3",
        patterns=[
            {"pattern": "valid_pattern", "policy_area_id": "PA05"},
            {"pattern": "invalid_pattern"},
        ],
    )
    
    with pytest.raises(ValueError) as exc_info:
        synchronizer._filter_patterns(question_with_invalid_pattern, "PA05")
    
    error_msg = str(exc_info.value)
    assert "Q123" in error_msg, "Error should include question_id"
    assert "policy_area_id" in error_msg.lower(), "Error should mention missing field"
    assert "index 1" in error_msg or "Pattern at index" in error_msg


def test_filter_patterns_returns_only_matching_pa() -> None:
    """Test _filter_patterns with mixed PA01/PA02/PA05 patterns filtering to PA05."""
    synchronizer = IrrigationSynchronizer()
    
    question = Question(
        question_id="Q200",
        policy_area_id="PA05",
        dimension_id="D4",
        patterns=[
            {"pattern": "pattern_pa01_1", "policy_area_id": "PA01"},
            {"pattern": "pattern_pa05_1", "policy_area_id": "PA05"},
            {"pattern": "pattern_pa02_1", "policy_area_id": "PA02"},
            {"pattern": "pattern_pa05_2", "policy_area_id": "PA05"},
            {"pattern": "pattern_pa01_2", "policy_area_id": "PA01"},
            {"pattern": "pattern_pa05_3", "policy_area_id": "PA05"},
        ],
    )
    
    filtered = synchronizer._filter_patterns(question, "PA05")
    
    assert isinstance(filtered, tuple), "Should return tuple for immutability"
    assert len(filtered) == 3, "Should have exactly 3 PA05 patterns"
    
    for pattern in filtered:
        assert pattern["policy_area_id"] == "PA05", "All patterns should be PA05"
    
    expected_patterns = {"pattern_pa05_1", "pattern_pa05_2", "pattern_pa05_3"}
    actual_patterns = {p["pattern"] for p in filtered}
    assert actual_patterns == expected_patterns, "Should have correct patterns"


def test_filter_patterns_returns_immutable_tuple() -> None:
    """Test that _filter_patterns returns tuple type for immutability."""
    synchronizer = IrrigationSynchronizer()
    
    question = Question(
        question_id="Q300",
        policy_area_id="PA10",
        dimension_id="D6",
        patterns=[
            {"pattern": "test_pattern", "policy_area_id": "PA10"},
        ],
    )
    
    result = synchronizer._filter_patterns(question, "PA10")
    
    assert isinstance(result, tuple), "Return type must be tuple"
    
    with pytest.raises(AttributeError):
        result.append({"pattern": "new_pattern", "policy_area_id": "PA10"})  # type: ignore


def test_filter_patterns_logs_warning_on_zero_matches(caplog: pytest.LogCaptureFixture) -> None:
    """Test _filter_patterns logs warning when zero patterns match but does not fail."""
    synchronizer = IrrigationSynchronizer()
    
    question = Question(
        question_id="Q150",
        policy_area_id="PA07",
        dimension_id="D3",
        patterns=[
            {"pattern": "pattern_pa01", "policy_area_id": "PA01"},
            {"pattern": "pattern_pa02", "policy_area_id": "PA02"},
        ],
    )
    
    with caplog.at_level("WARNING"):
        result = synchronizer._filter_patterns(question, "PA07")
    
    assert len(result) == 0, "Should return empty tuple"
    assert isinstance(result, tuple), "Should still return tuple"
    
    assert any("Zero patterns matched" in record.message for record in caplog.records)
    assert any("Q150" in record.message for record in caplog.records)
    assert any("PA07" in record.message for record in caplog.records)


@given(
    pa_count=st.integers(min_value=2, max_value=10),
    patterns_per_pa=st.integers(min_value=1, max_value=20),
    target_pa_idx=st.integers(min_value=0, max_value=9),
)
def test_filter_patterns_no_cross_contamination(
    pa_count: int,
    patterns_per_pa: int,
    target_pa_idx: int,
) -> None:
    """Property test verifying no filtered pattern contains different policy_area_id."""
    if target_pa_idx >= pa_count:
        target_pa_idx = target_pa_idx % pa_count
    
    synchronizer = IrrigationSynchronizer()
    
    all_patterns = []
    policy_areas = [f"PA{i+1:02d}" for i in range(pa_count)]
    target_pa = policy_areas[target_pa_idx]
    
    for pa in policy_areas:
        for i in range(patterns_per_pa):
            all_patterns.append({
                "pattern": f"pattern_{pa}_{i}",
                "policy_area_id": pa,
            })
    
    question = Question(
        question_id="PROP_TEST",
        policy_area_id=target_pa,
        dimension_id="D1",
        patterns=all_patterns,
    )
    
    filtered = synchronizer._filter_patterns(question, target_pa)
    
    assert isinstance(filtered, tuple), "Must return tuple"
    assert len(filtered) == patterns_per_pa, f"Should have {patterns_per_pa} patterns"
    
    for pattern in filtered:
        assert pattern["policy_area_id"] == target_pa, (
            f"Cross-contamination detected: pattern has policy_area_id="
            f"'{pattern['policy_area_id']}' but expected '{target_pa}'"
        )
    
    non_target_patterns = [p for p in all_patterns if p["policy_area_id"] != target_pa]
    filtered_set = {p["pattern"] for p in filtered}
    for non_target in non_target_patterns:
        assert non_target["pattern"] not in filtered_set, (
            f"Non-target pattern '{non_target['pattern']}' leaked into filtered results"
        )


def test_chunk_matrix_get_chunk_success() -> None:
    """Test ChunkMatrix.get_chunk succeeds for existing chunk."""
    chunks = {
        ("PA01", "D1"): {"chunk_id": "PA01_D1"},
        ("PA02", "D3"): {"chunk_id": "PA02_D3"},
    }
    matrix = ChunkMatrix(chunks=chunks)
    
    chunk = matrix.get_chunk("PA01", "D1")
    assert chunk["chunk_id"] == "PA01_D1"
    
    chunk = matrix.get_chunk("PA02", "D3")
    assert chunk["chunk_id"] == "PA02_D3"


def test_chunk_matrix_get_chunk_raises_on_missing() -> None:
    """Test ChunkMatrix.get_chunk raises ValueError for missing chunk."""
    chunks = {
        ("PA01", "D1"): {"chunk_id": "PA01_D1"},
    }
    matrix = ChunkMatrix(chunks=chunks)
    
    with pytest.raises(ValueError) as exc_info:
        matrix.get_chunk("PA99", "D9")
    
    error_msg = str(exc_info.value)
    assert "PA99" in error_msg
    assert "D9" in error_msg
    assert "No chunk found" in error_msg


def test_complete_workflow_300_questions_60_chunks(
    complete_chunk_matrix: ChunkMatrix,
    sample_questions: list[Question]
) -> None:
    """Integration test: complete workflow with 300 questions and 60 chunks."""
    synchronizer = IrrigationSynchronizer()
    
    results = []
    for question in sample_questions:
        chunk = synchronizer._match_chunk(question, complete_chunk_matrix)
        
        filtered_patterns = synchronizer._filter_patterns(
            question,
            question.policy_area_id
        )
        
        results.append({
            "question_id": question.question_id,
            "chunk_id": chunk["chunk_id"],
            "pattern_count": len(filtered_patterns),
        })
    
    assert len(results) == 300, "Should process all 300 questions"
    
    unique_chunks = {r["chunk_id"] for r in results}
    assert len(unique_chunks) == 60, "Should access all 60 unique chunks"
    
    for result in results:
        assert result["pattern_count"] >= 0, "Pattern count should be non-negative"
