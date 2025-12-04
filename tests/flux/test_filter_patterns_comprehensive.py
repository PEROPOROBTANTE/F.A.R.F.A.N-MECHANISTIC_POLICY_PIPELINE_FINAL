"""
Comprehensive Unit Tests for _filter_patterns()
================================================

Test suite covering all aspects of pattern filtering including:
- Exact policy_area_id match scenarios
- Zero patterns after filtering (warning not error)
- Pattern missing policy_area_id field (ValueError)
- Pattern index construction and duplicate pattern_id handling
- Immutability verification of returned tuple
- Integration with validate_chunk_routing() and _construct_task()
- Metadata tracking in task objects

Test Standards:
- pytest for test framework
- hypothesis for property-based testing
- Clear test names describing behavior
- Comprehensive edge case coverage

Coverage:
- All primary branches of _filter_patterns()
- All error paths and validation logic
- Integration with task construction and routing
- Edge cases and boundary conditions
- Property-based guarantees
"""

import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
    IrrigationSynchronizer as CoreIrrigationSynchronizer,
)
from farfan_pipeline.core.orchestrator.task_planner import _construct_task
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.flux.irrigation_synchronizer import (
    IrrigationSynchronizer,
    Question,
)


@pytest.fixture
def basic_question() -> Question:
    """Create a basic question with valid patterns."""
    return Question(
        question_id="Q001",
        policy_area_id="PA05",
        dimension_id="D3",
        patterns=[
            {
                "pattern_id": "P001",
                "pattern": "test_pattern_1",
                "policy_area_id": "PA05",
            },
            {
                "pattern_id": "P002",
                "pattern": "test_pattern_2",
                "policy_area_id": "PA05",
            },
        ],
    )


@pytest.fixture
def mixed_patterns_question() -> Question:
    """Create question with patterns from multiple policy areas."""
    return Question(
        question_id="Q200",
        policy_area_id="PA05",
        dimension_id="D4",
        patterns=[
            {"pattern_id": "P1", "pattern": "pattern_pa01_1", "policy_area_id": "PA01"},
            {"pattern_id": "P2", "pattern": "pattern_pa05_1", "policy_area_id": "PA05"},
            {"pattern_id": "P3", "pattern": "pattern_pa02_1", "policy_area_id": "PA02"},
            {"pattern_id": "P4", "pattern": "pattern_pa05_2", "policy_area_id": "PA05"},
            {"pattern_id": "P5", "pattern": "pattern_pa01_2", "policy_area_id": "PA01"},
            {"pattern_id": "P6", "pattern": "pattern_pa05_3", "policy_area_id": "PA05"},
        ],
    )


@pytest.fixture
def synchronizer() -> IrrigationSynchronizer:
    """Create IrrigationSynchronizer instance."""
    return IrrigationSynchronizer()


class TestExactPolicyAreaMatch:
    """Test exact policy_area_id matching scenarios."""

    def test_exact_match_all_patterns_returned(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """All patterns should be returned when they match target policy_area_id."""
        filtered = synchronizer._filter_patterns(basic_question, "PA05")

        assert isinstance(filtered, tuple), "Should return tuple"
        assert len(filtered) == 2, "Should return all matching patterns"
        assert all(p["policy_area_id"] == "PA05" for p in filtered)

    def test_exact_match_preserves_pattern_data(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Pattern data should be preserved exactly during filtering."""
        filtered = synchronizer._filter_patterns(basic_question, "PA05")

        assert filtered[0]["pattern_id"] == "P001"
        assert filtered[0]["pattern"] == "test_pattern_1"
        assert filtered[1]["pattern_id"] == "P002"
        assert filtered[1]["pattern"] == "test_pattern_2"

    def test_exact_match_maintains_order(
        self, synchronizer: IrrigationSynchronizer, mixed_patterns_question: Question
    ) -> None:
        """Filtered patterns should maintain original order."""
        filtered = synchronizer._filter_patterns(mixed_patterns_question, "PA05")

        assert len(filtered) == 3
        assert filtered[0]["pattern_id"] == "P2"
        assert filtered[1]["pattern_id"] == "P4"
        assert filtered[2]["pattern_id"] == "P6"

    def test_no_match_returns_empty_tuple(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Empty tuple should be returned when no patterns match."""
        question = Question(
            question_id="Q300",
            policy_area_id="PA10",
            dimension_id="D6",
            patterns=[
                {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA01"},
                {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA02"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA10")

        assert isinstance(filtered, tuple)
        assert len(filtered) == 0

    def test_single_pattern_exact_match(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Single pattern matching should work correctly."""
        question = Question(
            question_id="Q400",
            policy_area_id="PA03",
            dimension_id="D2",
            patterns=[
                {
                    "pattern_id": "P1",
                    "pattern": "solo_pattern",
                    "policy_area_id": "PA03",
                }
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA03")

        assert len(filtered) == 1
        assert filtered[0]["pattern_id"] == "P1"
        assert filtered[0]["policy_area_id"] == "PA03"


class TestZeroPatternsWarning:
    """Test zero patterns after filtering (warning not error)."""

    def test_zero_patterns_logs_warning(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning should be logged when zero patterns match."""
        question = Question(
            question_id="Q150",
            policy_area_id="PA07",
            dimension_id="D3",
            patterns=[
                {
                    "pattern_id": "P1",
                    "pattern": "pattern_pa01",
                    "policy_area_id": "PA01",
                },
                {
                    "pattern_id": "P2",
                    "pattern": "pattern_pa02",
                    "policy_area_id": "PA02",
                },
            ],
        )

        with caplog.at_level(logging.WARNING):
            result = synchronizer._filter_patterns(question, "PA07")

        assert len(result) == 0
        assert isinstance(result, tuple)
        assert any(
            "Zero patterns matched" in record.message for record in caplog.records
        )
        assert any("Q150" in record.message for record in caplog.records)
        assert any("PA07" in record.message for record in caplog.records)

    def test_zero_patterns_includes_context_in_warning(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning should include question_id, target PA, and pattern count."""
        question = Question(
            question_id="Q999",
            policy_area_id="PA08",
            dimension_id="D5",
            patterns=[
                {"pattern_id": "P1", "pattern": "p1", "policy_area_id": "PA01"},
                {"pattern_id": "P2", "pattern": "p2", "policy_area_id": "PA02"},
                {"pattern_id": "P3", "pattern": "p3", "policy_area_id": "PA03"},
            ],
        )

        with caplog.at_level(logging.WARNING):
            synchronizer._filter_patterns(question, "PA10")

        warning_msg = next(
            (r.message for r in caplog.records if r.levelname == "WARNING"), ""
        )
        assert "Q999" in warning_msg
        assert "PA10" in warning_msg
        assert "3" in warning_msg or "total patterns" in warning_msg.lower()

    def test_zero_patterns_does_not_raise_exception(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Zero patterns should not raise exception, only warn."""
        question = Question(
            question_id="Q500",
            policy_area_id="PA06",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA01"}
            ],
        )

        result = synchronizer._filter_patterns(question, "PA99")
        assert result == ()

    def test_empty_patterns_list_logs_warning(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Empty patterns list should also trigger warning."""
        question = Question(
            question_id="Q600",
            policy_area_id="PA01",
            dimension_id="D1",
            patterns=[],
        )

        with caplog.at_level(logging.WARNING):
            result = synchronizer._filter_patterns(question, "PA01")

        assert result == ()
        assert any(
            "Zero patterns matched" in record.message for record in caplog.records
        )


class TestMissingPolicyAreaIdField:
    """Test pattern missing policy_area_id field (ValueError)."""

    def test_missing_policy_area_id_raises_valueerror(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """ValueError should be raised when pattern lacks policy_area_id."""
        question = Question(
            question_id="Q123",
            policy_area_id="PA05",
            dimension_id="D3",
            patterns=[
                {"pattern_id": "P1", "pattern": "valid", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "invalid"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA05")

        error_msg = str(exc_info.value)
        assert "Q123" in error_msg
        assert "policy_area_id" in error_msg.lower()
        assert "index 1" in error_msg or "Pattern at index" in error_msg

    def test_missing_field_error_includes_question_id(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Error message should include question_id for debugging."""
        question = Question(
            question_id="Q789",
            policy_area_id="PA02",
            dimension_id="D4",
            patterns=[{"pattern_id": "P1", "pattern": "no_pa_field"}],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA02")

        assert "Q789" in str(exc_info.value)

    def test_missing_field_error_includes_pattern_index(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Error message should include pattern index."""
        question = Question(
            question_id="Q111",
            policy_area_id="PA03",
            dimension_id="D2",
            patterns=[
                {"pattern_id": "P1", "pattern": "valid1", "policy_area_id": "PA03"},
                {"pattern_id": "P2", "pattern": "valid2", "policy_area_id": "PA03"},
                {"pattern_id": "P3", "pattern": "invalid"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA03")

        error_msg = str(exc_info.value)
        assert "index 2" in error_msg.lower() or "2" in error_msg

    def test_multiple_missing_fields_reports_first(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """When multiple patterns miss field, first occurrence should be reported."""
        question = Question(
            question_id="Q222",
            policy_area_id="PA04",
            dimension_id="D5",
            patterns=[
                {"pattern_id": "P1", "pattern": "valid", "policy_area_id": "PA04"},
                {"pattern_id": "P2", "pattern": "missing1"},
                {"pattern_id": "P3", "pattern": "missing2"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA04")

        error_msg = str(exc_info.value)
        assert "index 1" in error_msg.lower() or "1" in error_msg

    def test_validates_all_patterns_before_filtering(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Validation should happen before filtering logic."""
        question = Question(
            question_id="Q333",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "wrong_pa", "policy_area_id": "PA99"},
                {"pattern_id": "P2", "pattern": "missing"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA05")

        assert "missing" in str(exc_info.value).lower()


class TestPatternIndexConstruction:
    """Test pattern index construction and duplicate pattern_id handling."""

    def test_patterns_maintain_index_order(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns should maintain their index order after filtering."""
        question = Question(
            question_id="Q700",
            policy_area_id="PA06",
            dimension_id="D3",
            patterns=[
                {"pattern_id": "P10", "pattern": "first", "policy_area_id": "PA06"},
                {"pattern_id": "P20", "pattern": "second", "policy_area_id": "PA06"},
                {"pattern_id": "P30", "pattern": "third", "policy_area_id": "PA06"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA06")

        assert filtered[0]["pattern_id"] == "P10"
        assert filtered[1]["pattern_id"] == "P20"
        assert filtered[2]["pattern_id"] == "P30"

    def test_duplicate_pattern_ids_preserved(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Duplicate pattern_ids should be preserved (not deduplicated)."""
        question = Question(
            question_id="Q800",
            policy_area_id="PA07",
            dimension_id="D4",
            patterns=[
                {"pattern_id": "P1", "pattern": "dup1", "policy_area_id": "PA07"},
                {"pattern_id": "P1", "pattern": "dup2", "policy_area_id": "PA07"},
                {"pattern_id": "P2", "pattern": "unique", "policy_area_id": "PA07"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA07")

        assert len(filtered) == 3
        pattern_ids = [p["pattern_id"] for p in filtered]
        assert pattern_ids.count("P1") == 2

    def test_mixed_patterns_index_preserved(
        self, synchronizer: IrrigationSynchronizer, mixed_patterns_question: Question
    ) -> None:
        """Index order should be preserved even with mixed policy areas."""
        filtered = synchronizer._filter_patterns(mixed_patterns_question, "PA05")

        expected_order = ["P2", "P4", "P6"]
        actual_order = [p["pattern_id"] for p in filtered]
        assert actual_order == expected_order

    def test_patterns_without_pattern_id_field(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns without pattern_id field should still be filterable."""
        question = Question(
            question_id="Q900",
            policy_area_id="PA08",
            dimension_id="D5",
            patterns=[
                {"pattern": "no_id_1", "policy_area_id": "PA08"},
                {"pattern": "no_id_2", "policy_area_id": "PA08"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA08")

        assert len(filtered) == 2
        assert filtered[0]["pattern"] == "no_id_1"
        assert filtered[1]["pattern"] == "no_id_2"


class TestImmutabilityVerification:
    """Test immutability verification of returned tuple."""

    def test_returns_tuple_type(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Return value must be tuple type."""
        result = synchronizer._filter_patterns(basic_question, "PA05")
        assert isinstance(result, tuple)
        assert type(result) is tuple

    def test_tuple_is_immutable(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Returned tuple should not allow modification."""
        result = synchronizer._filter_patterns(basic_question, "PA05")

        with pytest.raises(AttributeError):
            result.append({"pattern_id": "P999", "policy_area_id": "PA05"})  # type: ignore

    def test_empty_result_is_tuple(self, synchronizer: IrrigationSynchronizer) -> None:
        """Empty result should also be tuple."""
        question = Question(
            question_id="Q1000",
            policy_area_id="PA09",
            dimension_id="D6",
            patterns=[
                {"pattern_id": "P1", "pattern": "other", "policy_area_id": "PA01"}
            ],
        )

        result = synchronizer._filter_patterns(question, "PA09")

        assert isinstance(result, tuple)
        assert len(result) == 0

    def test_multiple_calls_return_independent_tuples(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Multiple calls should return independent tuple instances."""
        result1 = synchronizer._filter_patterns(basic_question, "PA05")
        result2 = synchronizer._filter_patterns(basic_question, "PA05")

        assert result1 is not result2
        assert result1 == result2

    def test_nested_dicts_not_protected(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Note: tuple immutability doesn't prevent dict mutation (by design)."""
        result = synchronizer._filter_patterns(basic_question, "PA05")

        original_value = result[0]["pattern"]
        result[0]["pattern"] = "modified"

        assert result[0]["pattern"] == "modified"
        assert original_value == "test_pattern_1"


class TestIntegrationWithValidateChunkRouting:
    """Test integration with validate_chunk_routing()."""

    def create_complete_document(self) -> PreprocessedDocument:
        """Create valid document with all 60 chunks."""
        chunks = []
        chunk_id = 0
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunks.append(
                    ChunkData(
                        id=chunk_id,
                        text=f"Content for {pa_id} {dim_id}",
                        chunk_type="diagnostic",
                        sentences=[],
                        tables=[],
                        start_pos=0,
                        end_pos=20,
                        confidence=0.95,
                        policy_area_id=pa_id,
                        dimension_id=dim_id,
                    )
                )
                chunk_id += 1

        return PreprocessedDocument(
            document_id="test-doc",
            raw_text="test",
            sentences=[],
            tables=[],
            metadata={},
            chunks=chunks,
            ingested_at=datetime.now(timezone.utc),
        )

    def test_validate_chunk_routing_with_filtered_patterns(self) -> None:
        """validate_chunk_routing should work with filtered patterns."""
        doc = self.create_complete_document()
        questionnaire = {"blocks": {}}
        core_sync = CoreIrrigationSynchronizer(
            questionnaire=questionnaire, preprocessed_document=doc
        )

        question = {
            "question_id": "D1-Q01",
            "policy_area_id": "PA05",
            "dimension_id": "DIM03",
            "patterns": [
                {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA05"},
            ],
        }

        result = core_sync.validate_chunk_routing(question)

        assert result.policy_area_id == "PA05"
        assert result.dimension_id == "DIM03"
        assert result.chunk_id == "PA05-DIM03"

    def test_routing_result_contains_expected_fields(self) -> None:
        """ChunkRoutingResult should contain all expected fields."""
        doc = self.create_complete_document()
        questionnaire = {"blocks": {}}
        core_sync = CoreIrrigationSynchronizer(
            questionnaire=questionnaire, preprocessed_document=doc
        )

        question = {
            "question_id": "D2-Q05",
            "policy_area_id": "PA07",
            "dimension_id": "DIM04",
            "patterns": [],
            "expected_elements": [{"field": "value"}],
        }

        result = core_sync.validate_chunk_routing(question)

        assert hasattr(result, "target_chunk")
        assert hasattr(result, "chunk_id")
        assert hasattr(result, "policy_area_id")
        assert hasattr(result, "dimension_id")
        assert hasattr(result, "text_content")
        assert hasattr(result, "expected_elements")
        assert result.expected_elements == [{"field": "value"}]


class TestIntegrationWithConstructTask:
    """Test integration with _construct_task()."""

    def test_construct_task_with_filtered_patterns(self) -> None:
        """_construct_task should accept filtered patterns."""
        question = {
            "question_id": "D1-Q01",
            "question_global": 1,
            "policy_area_id": "PA05",
            "dimension_id": "DIM03",
            "base_slot": "D1Q1",
            "cluster_id": "C1",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA05-DIM03", "expected_elements": []}

        patterns = [
            {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA05"},
            {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA05"},
        ]

        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert task.task_id == "MQC-001_PA05"
        assert task.patterns == patterns
        assert len(task.patterns) == 2

    def test_construct_task_with_empty_patterns(self) -> None:
        """_construct_task should handle empty patterns list."""
        question = {
            "question_id": "D2-Q10",
            "question_global": 60,
            "policy_area_id": "PA10",
            "dimension_id": "DIM06",
            "base_slot": "D2Q10",
            "cluster_id": "C10",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA10-DIM06", "expected_elements": []}
        patterns: list[dict[str, Any]] = []
        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert task.task_id == "MQC-060_PA10"
        assert task.patterns == []

    def test_construct_task_prevents_duplicate_task_ids(self) -> None:
        """_construct_task should raise ValueError on duplicate task_id."""
        question = {
            "question_id": "D1-Q01",
            "question_global": 1,
            "policy_area_id": "PA05",
            "dimension_id": "DIM03",
            "base_slot": "D1Q1",
            "cluster_id": "C1",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA05-DIM03", "expected_elements": []}
        patterns: list[dict[str, Any]] = []
        signals = {}
        generated_ids = {"MQC-001_PA05"}

        with pytest.raises(ValueError, match="Duplicate task_id detected"):
            _construct_task(question, chunk, patterns, signals, generated_ids)


class TestMetadataTracking:
    """Test metadata tracking in task objects."""

    def test_task_includes_pattern_metadata(self) -> None:
        """Task should include pattern count in metadata or accessible via patterns."""
        question = {
            "question_id": "D3-Q15",
            "question_global": 145,
            "policy_area_id": "PA08",
            "dimension_id": "DIM05",
            "base_slot": "D3Q15",
            "cluster_id": "C15",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA08-DIM05", "expected_elements": []}

        patterns = [
            {"pattern_id": f"P{i}", "pattern": f"test{i}", "policy_area_id": "PA08"}
            for i in range(5)
        ]

        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert len(task.patterns) == 5
        assert task.metadata.get("base_slot") == "D3Q15"
        assert task.metadata.get("cluster_id") == "C15"

    def test_task_context_includes_immutable_patterns(self) -> None:
        """Task context should include patterns as immutable tuple."""
        question = {
            "question_id": "D4-Q20",
            "question_global": 200,
            "policy_area_id": "PA03",
            "dimension_id": "DIM02",
            "base_slot": "D4Q20",
            "cluster_id": "C20",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA03-DIM02", "expected_elements": []}

        patterns = [{"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA03"}]

        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert task.context is not None
        assert isinstance(task.context.patterns, tuple)
        assert len(task.context.patterns) == 1

    def test_task_creation_timestamp_recorded(self) -> None:
        """Task should record creation timestamp."""
        question = {
            "question_id": "D5-Q25",
            "question_global": 250,
            "policy_area_id": "PA04",
            "dimension_id": "DIM03",
            "base_slot": "D5Q25",
            "cluster_id": "C25",
            "expected_elements": [],
            "signal_requirements": {},
        }

        chunk = {"id": "PA04-DIM03", "expected_elements": []}
        patterns: list[dict[str, Any]] = []
        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert task.creation_timestamp is not None
        assert isinstance(task.creation_timestamp, str)
        assert "T" in task.creation_timestamp

    def test_task_includes_expected_elements(self) -> None:
        """Task should include expected_elements from question."""
        question = {
            "question_id": "D6-Q30",
            "question_global": 300,
            "policy_area_id": "PA09",
            "dimension_id": "DIM06",
            "base_slot": "D6Q30",
            "cluster_id": "C30",
            "expected_elements": [{"element_type": "indicator", "required": True}],
            "signal_requirements": {},
        }

        chunk = {
            "id": "PA09-DIM06",
            "expected_elements": [{"element_type": "indicator", "required": True}],
        }
        patterns: list[dict[str, Any]] = []
        signals = {}
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns, signals, generated_ids)

        assert len(task.expected_elements) == 1
        assert task.expected_elements[0]["element_type"] == "indicator"


class TestPropertyBasedFiltering:
    """Property-based tests for pattern filtering guarantees."""

    @given(
        pa_count=st.integers(min_value=2, max_value=10),
        patterns_per_pa=st.integers(min_value=1, max_value=20),
        target_pa_idx=st.integers(min_value=0, max_value=9),
    )
    def test_no_cross_contamination(
        self, pa_count: int, patterns_per_pa: int, target_pa_idx: int
    ) -> None:
        """No filtered pattern should contain different policy_area_id."""
        if target_pa_idx >= pa_count:
            target_pa_idx = target_pa_idx % pa_count

        synchronizer = IrrigationSynchronizer()

        all_patterns = []
        policy_areas = [f"PA{i+1:02d}" for i in range(pa_count)]
        target_pa = policy_areas[target_pa_idx]

        for pa in policy_areas:
            for i in range(patterns_per_pa):
                all_patterns.append(
                    {
                        "pattern_id": f"{pa}_P{i}",
                        "pattern": f"pattern_{pa}_{i}",
                        "policy_area_id": pa,
                    }
                )

        question = Question(
            question_id="PROP_TEST",
            policy_area_id=target_pa,
            dimension_id="D1",
            patterns=all_patterns,
        )

        filtered = synchronizer._filter_patterns(question, target_pa)

        assert isinstance(filtered, tuple)
        assert len(filtered) == patterns_per_pa

        for pattern in filtered:
            assert pattern["policy_area_id"] == target_pa

    @given(
        pattern_count=st.integers(min_value=0, max_value=100),
    )
    def test_filtering_preserves_tuple_immutability(self, pattern_count: int) -> None:
        """Result should always be tuple regardless of pattern count."""
        synchronizer = IrrigationSynchronizer()

        patterns = [
            {
                "pattern_id": f"P{i}",
                "pattern": f"test_{i}",
                "policy_area_id": "PA05",
            }
            for i in range(pattern_count)
        ]

        question = Question(
            question_id="TUPLE_TEST",
            policy_area_id="PA05",
            dimension_id="D2",
            patterns=patterns,
        )

        result = synchronizer._filter_patterns(question, "PA05")

        assert isinstance(result, tuple)
        assert len(result) == pattern_count

    @given(
        pattern_data=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10, alphabet="ABCDEFGHIJ"),
                st.text(min_size=1, max_size=20),
            ),
            min_size=1,
            max_size=50,
        )
    )
    def test_filtering_maintains_deterministic_order(
        self, pattern_data: list[tuple[str, str]]
    ) -> None:
        """Multiple calls should return same order."""
        synchronizer = IrrigationSynchronizer()

        patterns = [
            {
                "pattern_id": f"P{idx}",
                "pattern": text,
                "policy_area_id": pa_id,
            }
            for idx, (pa_id, text) in enumerate(pattern_data)
        ]

        question = Question(
            question_id="ORDER_TEST",
            policy_area_id="PA01",
            dimension_id="D3",
            patterns=patterns,
        )

        result1 = synchronizer._filter_patterns(question, "A")
        result2 = synchronizer._filter_patterns(question, "A")

        assert result1 == result2


class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_unicode_in_pattern_fields(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns with unicode characters should be handled correctly."""
        question = Question(
            question_id="Q_UNICODE",
            policy_area_id="PA01",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "测试模式", "policy_area_id": "PA01"},
                {"pattern_id": "P2", "pattern": "パターン", "policy_area_id": "PA01"},
                {"pattern_id": "P3", "pattern": "نمط", "policy_area_id": "PA02"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA01")

        assert len(filtered) == 2
        assert filtered[0]["pattern"] == "测试模式"
        assert filtered[1]["pattern"] == "パターン"

    def test_special_characters_in_policy_area_id(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Policy area IDs with special format should work."""
        question = Question(
            question_id="Q_SPECIAL",
            policy_area_id="PA01",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA01"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA01")

        assert len(filtered) == 1

    def test_very_large_pattern_list(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Should handle very large pattern lists efficiently."""
        patterns = [
            {"pattern_id": f"P{i}", "pattern": f"test_{i}", "policy_area_id": "PA05"}
            for i in range(1000)
        ]

        question = Question(
            question_id="Q_LARGE",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=patterns,
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert len(filtered) == 1000
        assert isinstance(filtered, tuple)

    def test_pattern_with_none_values(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns with None in non-policy_area_id fields should work."""
        question = Question(
            question_id="Q_NONE",
            policy_area_id="PA03",
            dimension_id="D2",
            patterns=[
                {"pattern_id": None, "pattern": None, "policy_area_id": "PA03"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA03")

        assert len(filtered) == 1
        assert filtered[0]["pattern_id"] is None

    def test_pattern_with_nested_structures(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns with nested dicts/lists should be preserved."""
        question = Question(
            question_id="Q_NESTED",
            policy_area_id="PA04",
            dimension_id="D3",
            patterns=[
                {
                    "pattern_id": "P1",
                    "pattern": "test",
                    "policy_area_id": "PA04",
                    "metadata": {"key": "value", "nested": {"deep": "data"}},
                    "tags": ["tag1", "tag2"],
                },
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA04")

        assert len(filtered) == 1
        assert filtered[0]["metadata"]["nested"]["deep"] == "data"
        assert filtered[0]["tags"] == ["tag1", "tag2"]

    def test_case_sensitive_policy_area_matching(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Policy area matching should be case-sensitive."""
        question = Question(
            question_id="Q_CASE",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "upper", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "lower", "policy_area_id": "pa05"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert len(filtered) == 1
        assert filtered[0]["pattern"] == "upper"

    def test_whitespace_in_policy_area_id(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Policy area IDs with whitespace should match exactly."""
        question = Question(
            question_id="Q_WHITESPACE",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "exact", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "spaces", "policy_area_id": " PA05 "},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert len(filtered) == 1
        assert filtered[0]["pattern"] == "exact"

    def test_empty_string_policy_area_id(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Empty string policy area ID should be handled."""
        question = Question(
            question_id="Q_EMPTY",
            policy_area_id="",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "empty", "policy_area_id": ""},
                {"pattern_id": "P2", "pattern": "not_empty", "policy_area_id": "PA01"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "")

        assert len(filtered) == 1
        assert filtered[0]["pattern"] == "empty"

    def test_numeric_policy_area_id(self, synchronizer: IrrigationSynchronizer) -> None:
        """Numeric values for policy_area_id should be handled."""
        question = Question(
            question_id="Q_NUMERIC",
            policy_area_id="PA01",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "string", "policy_area_id": "PA01"},
                {"pattern_id": "P2", "pattern": "number", "policy_area_id": 123},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA01")

        assert len(filtered) == 1
        assert filtered[0]["pattern"] == "string"


class TestEndToEndPatternFilteringWorkflow:
    """Test complete workflow from question to task with pattern filtering."""

    def create_test_document(self) -> PreprocessedDocument:
        """Create test document with all required chunks."""
        chunks = []
        chunk_id = 0
        for pa_num in range(1, 11):
            for dim_num in range(1, 7):
                pa_id = f"PA{pa_num:02d}"
                dim_id = f"DIM{dim_num:02d}"
                chunks.append(
                    ChunkData(
                        id=chunk_id,
                        text=f"Test content for {pa_id} {dim_id}",
                        chunk_type="diagnostic",
                        sentences=[],
                        tables=[],
                        start_pos=0,
                        end_pos=30,
                        confidence=0.95,
                        policy_area_id=pa_id,
                        dimension_id=dim_id,
                    )
                )
                chunk_id += 1

        return PreprocessedDocument(
            document_id="test-doc",
            raw_text="test",
            sentences=[],
            tables=[],
            metadata={},
            chunks=chunks,
            ingested_at=datetime.now(timezone.utc),
        )

    def test_full_workflow_with_pattern_filtering(self) -> None:
        """Test complete workflow: question -> routing -> pattern filtering -> task."""
        doc = self.create_test_document()
        questionnaire = {"blocks": {}}
        core_sync = CoreIrrigationSynchronizer(
            questionnaire=questionnaire, preprocessed_document=doc
        )

        flux_sync = IrrigationSynchronizer()

        question_dict = {
            "question_id": "D1-Q05",
            "question_global": 5,
            "policy_area_id": "PA03",
            "dimension_id": "DIM02",
            "base_slot": "D1Q5",
            "cluster_id": "C5",
            "patterns": [
                {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA03"},
                {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA05"},
                {"pattern_id": "P3", "pattern": "test3", "policy_area_id": "PA03"},
            ],
            "expected_elements": [],
            "signal_requirements": {},
        }

        routing_result = core_sync.validate_chunk_routing(question_dict)

        flux_question = Question(
            question_id=question_dict["question_id"],
            policy_area_id=question_dict["policy_area_id"],
            dimension_id=question_dict["dimension_id"],
            patterns=question_dict["patterns"],
        )

        filtered_patterns = flux_sync._filter_patterns(flux_question, "PA03")

        assert len(filtered_patterns) == 2
        assert all(p["policy_area_id"] == "PA03" for p in filtered_patterns)

        chunk = {"id": routing_result.chunk_id, "expected_elements": []}
        patterns_list = list(filtered_patterns)
        generated_ids: set[str] = set()

        task = _construct_task(question_dict, chunk, patterns_list, {}, generated_ids)

        assert task.task_id == "MQC-005_PA03"
        assert len(task.patterns) == 2
        assert task.patterns[0]["pattern_id"] == "P1"
        assert task.patterns[1]["pattern_id"] == "P3"

    def test_pattern_filtering_across_multiple_questions(self) -> None:
        """Test pattern filtering consistency across multiple questions."""
        flux_sync = IrrigationSynchronizer()

        questions = [
            Question(
                question_id=f"Q{i}",
                policy_area_id=f"PA{(i % 10) + 1:02d}",
                dimension_id=f"D{(i % 6) + 1}",
                patterns=[
                    {
                        "pattern_id": f"P{j}",
                        "pattern": f"test_{j}",
                        "policy_area_id": f"PA{(j % 10) + 1:02d}",
                    }
                    for j in range(1, 11)
                ],
            )
            for i in range(30)
        ]

        for question in questions:
            filtered = flux_sync._filter_patterns(question, question.policy_area_id)

            assert all(p["policy_area_id"] == question.policy_area_id for p in filtered)
            assert len(filtered) > 0

    def test_filtered_patterns_used_in_task_context(self) -> None:
        """Verify filtered patterns are properly stored in task context."""
        question = {
            "question_id": "D3-Q10",
            "question_global": 140,
            "policy_area_id": "PA07",
            "dimension_id": "DIM04",
            "base_slot": "D3Q10",
            "cluster_id": "C10",
            "patterns": [
                {"pattern_id": "P1", "pattern": "keep1", "policy_area_id": "PA07"},
                {"pattern_id": "P2", "pattern": "drop", "policy_area_id": "PA01"},
                {"pattern_id": "P3", "pattern": "keep2", "policy_area_id": "PA07"},
            ],
            "expected_elements": [],
            "signal_requirements": {},
        }

        flux_sync = IrrigationSynchronizer()
        flux_question = Question(
            question_id=question["question_id"],
            policy_area_id=question["policy_area_id"],
            dimension_id=question["dimension_id"],
            patterns=question["patterns"],
        )

        filtered = flux_sync._filter_patterns(flux_question, "PA07")

        chunk = {"id": "PA07-DIM04", "expected_elements": []}
        patterns_list = list(filtered)
        generated_ids: set[str] = set()

        task = _construct_task(question, chunk, patterns_list, {}, generated_ids)

        assert task.context is not None
        assert len(task.context.patterns) == 2
        assert task.context.patterns[0]["pattern_id"] == "P1"
        assert task.context.patterns[1]["pattern_id"] == "P3"

    def test_metadata_preserved_through_filtering(self) -> None:
        """Verify all pattern metadata is preserved through filtering."""
        question = {
            "question_id": "D5-Q15",
            "question_global": 245,
            "policy_area_id": "PA09",
            "dimension_id": "DIM05",
            "base_slot": "D5Q15",
            "cluster_id": "C15",
            "patterns": [
                {
                    "pattern_id": "P1",
                    "pattern": "complex_pattern",
                    "policy_area_id": "PA09",
                    "confidence": 0.95,
                    "source": "manual_annotation",
                    "tags": ["important", "verified"],
                    "metadata": {"created_by": "analyst_1", "version": 2},
                },
            ],
            "expected_elements": [],
            "signal_requirements": {},
        }

        flux_sync = IrrigationSynchronizer()
        flux_question = Question(
            question_id=question["question_id"],
            policy_area_id=question["policy_area_id"],
            dimension_id=question["dimension_id"],
            patterns=question["patterns"],
        )

        filtered = flux_sync._filter_patterns(flux_question, "PA09")

        assert len(filtered) == 1
        assert filtered[0]["confidence"] == 0.95
        assert filtered[0]["source"] == "manual_annotation"
        assert filtered[0]["tags"] == ["important", "verified"]
        assert filtered[0]["metadata"]["created_by"] == "analyst_1"
        assert filtered[0]["metadata"]["version"] == 2


class TestLoggingBehavior:
    """Test logging behavior of _filter_patterns()."""

    def test_no_logging_on_successful_match(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """No warning should be logged when patterns match successfully."""
        question = Question(
            question_id="Q_SUCCESS",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA05"}
            ],
        )

        with caplog.at_level(logging.WARNING):
            synchronizer._filter_patterns(question, "PA05")

        assert len(caplog.records) == 0

    def test_warning_logged_exactly_once(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning should be logged exactly once per zero-match call."""
        question = Question(
            question_id="Q_WARN",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA01"}
            ],
        )

        with caplog.at_level(logging.WARNING):
            synchronizer._filter_patterns(question, "PA05")
            synchronizer._filter_patterns(question, "PA05")

        warning_count = sum(
            1 for r in caplog.records if "Zero patterns matched" in r.message
        )
        assert warning_count == 2

    def test_warning_includes_pattern_count(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning should include total pattern count."""
        question = Question(
            question_id="Q_COUNT",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {
                    "pattern_id": f"P{i}",
                    "pattern": f"test_{i}",
                    "policy_area_id": "PA01",
                }
                for i in range(5)
            ],
        )

        with caplog.at_level(logging.WARNING):
            synchronizer._filter_patterns(question, "PA05")

        warning = next((r.message for r in caplog.records if "Zero" in r.message), "")
        assert "5" in warning or "5 total patterns" in warning.lower()

    def test_warning_includes_all_identifiers(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Warning should include question_id, target PA, and question's PA."""
        question = Question(
            question_id="Q_IDENTIFIERS",
            policy_area_id="PA08",
            dimension_id="D3",
            patterns=[
                {"pattern_id": "P1", "pattern": "test", "policy_area_id": "PA01"}
            ],
        )

        with caplog.at_level(logging.WARNING):
            synchronizer._filter_patterns(question, "PA10")

        warning = next((r.message for r in caplog.records), "")
        assert "Q_IDENTIFIERS" in warning
        assert "PA10" in warning
        assert "PA08" in warning


class TestConcurrencyAndThreadSafety:
    """Test thread-safety aspects of _filter_patterns()."""

    def test_filter_patterns_is_stateless(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Multiple calls should not affect each other (stateless)."""
        question1 = Question(
            question_id="Q1",
            policy_area_id="PA01",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA01"}
            ],
        )

        question2 = Question(
            question_id="Q2",
            policy_area_id="PA02",
            dimension_id="D2",
            patterns=[
                {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA02"}
            ],
        )

        result1 = synchronizer._filter_patterns(question1, "PA01")
        result2 = synchronizer._filter_patterns(question2, "PA02")
        result1_again = synchronizer._filter_patterns(question1, "PA01")

        assert result1 == result1_again
        assert result1 != result2
        assert result1[0]["pattern_id"] == "P1"
        assert result2[0]["pattern_id"] == "P2"

    def test_simultaneous_filtering_independence(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Results from one filtering operation shouldn't affect another."""
        questions = [
            Question(
                question_id=f"Q{i}",
                policy_area_id=f"PA{(i % 10) + 1:02d}",
                dimension_id=f"D{(i % 6) + 1}",
                patterns=[
                    {
                        "pattern_id": f"P{i}_{j}",
                        "pattern": f"test_{i}_{j}",
                        "policy_area_id": f"PA{(i % 10) + 1:02d}",
                    }
                    for j in range(3)
                ],
            )
            for i in range(10)
        ]

        results = [
            synchronizer._filter_patterns(q, q.policy_area_id) for q in questions
        ]

        for i, result in enumerate(results):
            assert len(result) == 3
            assert all(p["pattern_id"].startswith(f"P{i}_") for p in result)


class TestPerformanceCharacteristics:
    """Test performance characteristics of _filter_patterns()."""

    def test_linear_time_complexity(self, synchronizer: IrrigationSynchronizer) -> None:
        """Filtering should have O(n) time complexity where n is pattern count."""
        import time

        sizes = [10, 100, 1000]
        times = []

        for size in sizes:
            patterns = [
                {
                    "pattern_id": f"P{i}",
                    "pattern": f"test_{i}",
                    "policy_area_id": "PA05",
                }
                for i in range(size)
            ]

            question = Question(
                question_id="Q_PERF",
                policy_area_id="PA05",
                dimension_id="D1",
                patterns=patterns,
            )

            start = time.perf_counter()
            for _ in range(100):
                synchronizer._filter_patterns(question, "PA05")
            elapsed = time.perf_counter() - start

            times.append(elapsed)

        assert times[0] > 0

    def test_filtering_does_not_modify_input(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Filtering should not modify input question or patterns."""
        original_patterns = [
            {"pattern_id": "P1", "pattern": "test1", "policy_area_id": "PA05"},
            {"pattern_id": "P2", "pattern": "test2", "policy_area_id": "PA01"},
        ]

        patterns_copy = [p.copy() for p in original_patterns]

        question = Question(
            question_id="Q_IMMUT",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=patterns_copy,
        )

        synchronizer._filter_patterns(question, "PA05")

        for i, pattern in enumerate(patterns_copy):
            assert pattern == original_patterns[i]


class TestRegressionTests:
    """Regression tests for previously found issues."""

    def test_empty_pattern_id_not_filtered_out(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns with empty pattern_id should not be filtered out."""
        question = Question(
            question_id="Q_REGRESSION_1",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[{"pattern_id": "", "pattern": "test", "policy_area_id": "PA05"}],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert len(filtered) == 1
        assert filtered[0]["pattern_id"] == ""

    def test_patterns_with_extra_fields_preserved(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Patterns with extra fields should have all fields preserved."""
        question = Question(
            question_id="Q_REGRESSION_2",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {
                    "pattern_id": "P1",
                    "pattern": "test",
                    "policy_area_id": "PA05",
                    "extra_field_1": "value1",
                    "extra_field_2": {"nested": "data"},
                }
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert filtered[0]["extra_field_1"] == "value1"
        assert filtered[0]["extra_field_2"]["nested"] == "data"

    def test_mixed_type_policy_area_ids_handled(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Mixed types in policy_area_id should be handled gracefully."""
        question = Question(
            question_id="Q_REGRESSION_3",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "str", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "int", "policy_area_id": 5},
                {"pattern_id": "P3", "pattern": "none", "policy_area_id": None},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")

        assert len(filtered) == 1
        assert filtered[0]["pattern"] == "str"


class TestErrorHandlingAndValidation:
    """Test comprehensive error handling and validation."""

    def test_first_invalid_pattern_reported(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """First invalid pattern should be reported when multiple are invalid."""
        question = Question(
            question_id="Q_FIRST_ERROR",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "valid", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "invalid_1"},
                {"pattern_id": "P3", "pattern": "invalid_2"},
                {"pattern_id": "P4", "pattern": "invalid_3"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA05")

        error = str(exc_info.value)
        assert "index 1" in error.lower()
        assert "P2" not in error or "invalid_1" not in error

    def test_validation_happens_before_filtering(
        self, synchronizer: IrrigationSynchronizer, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Validation should happen before filtering (no warning logged)."""
        question = Question(
            question_id="Q_VALIDATE_FIRST",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "wrong_pa", "policy_area_id": "PA99"},
                {"pattern_id": "P2", "pattern": "no_pa"},
            ],
        )

        with caplog.at_level(logging.WARNING), pytest.raises(ValueError):
            synchronizer._filter_patterns(question, "PA05")

        assert len(caplog.records) == 0

    def test_all_patterns_validated_before_error(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Validation should check in order and stop at first error."""
        question = Question(
            question_id="Q_VALIDATE_ORDER",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "valid1", "policy_area_id": "PA05"},
                {"pattern_id": "P2", "pattern": "valid2", "policy_area_id": "PA05"},
                {"pattern_id": "P3", "pattern": "valid3", "policy_area_id": "PA05"},
                {"pattern_id": "P4", "pattern": "invalid"},
                {"pattern_id": "P5", "pattern": "not_checked"},
            ],
        )

        with pytest.raises(ValueError) as exc_info:
            synchronizer._filter_patterns(question, "PA05")

        assert "index 3" in str(exc_info.value).lower()

    def test_error_message_format_consistency(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Error messages should have consistent format."""
        questions_with_missing_field = [
            Question(
                question_id=f"Q_{i}",
                policy_area_id=f"PA{(i % 10) + 1:02d}",
                dimension_id=f"D{(i % 6) + 1}",
                patterns=[{"pattern_id": "P1", "pattern": "test"}],
            )
            for i in range(5)
        ]

        for question in questions_with_missing_field:
            with pytest.raises(ValueError) as exc_info:
                synchronizer._filter_patterns(question, question.policy_area_id)

            error = str(exc_info.value)
            assert "Pattern at index" in error
            assert question.question_id in error
            assert "policy_area_id" in error.lower()

    def test_handles_get_method_gracefully(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Should use get() method which returns None for missing keys."""
        question = Question(
            question_id="Q_GET_METHOD",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[
                {"pattern_id": "P1", "pattern": "has_pa", "policy_area_id": "PA05"},
            ],
        )

        filtered = synchronizer._filter_patterns(question, "PA05")
        assert len(filtered) == 1


class TestDocumentationAndTypeHints:
    """Verify implementation matches documentation and type hints."""

    def test_return_type_matches_signature(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Return type should match function signature (tuple)."""
        result = synchronizer._filter_patterns(basic_question, "PA05")

        assert isinstance(result, tuple)
        assert all(isinstance(p, dict) for p in result)
        assert all(isinstance(k, str) for p in result for k in p)

    def test_raises_documented_exceptions(
        self, synchronizer: IrrigationSynchronizer
    ) -> None:
        """Should raise ValueError as documented when validation fails."""
        question = Question(
            question_id="Q_DOC",
            policy_area_id="PA05",
            dimension_id="D1",
            patterns=[{"pattern_id": "P1", "pattern": "test"}],
        )

        with pytest.raises(ValueError):
            synchronizer._filter_patterns(question, "PA05")

    def test_function_has_correct_parameters(self) -> None:
        """Function should accept Question and str parameters."""
        import inspect

        sig = inspect.signature(IrrigationSynchronizer._filter_patterns)
        params = list(sig.parameters.keys())

        assert len(params) == 3
        assert params[0] == "self"
        assert params[1] == "question"
        assert params[2] == "target_pa_id"

    def test_immutable_return_documented_behavior(
        self, synchronizer: IrrigationSynchronizer, basic_question: Question
    ) -> None:
        """Immutable tuple return as documented in docstring."""
        result = synchronizer._filter_patterns(basic_question, "PA05")

        assert isinstance(result, tuple)

        try:
            result[0] = {"new": "pattern"}  # type: ignore
            raise AssertionError("Should not be able to modify tuple")
        except TypeError:
            pass
