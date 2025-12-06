"""Test Phase 7: Task Construction

Tests Phase 7 task construction logic including:
- ExecutableTask immutability enforcement
- __post_init__ validation for all mandatory fields
- Type coercion for tuple/MappingProxyType fields
- Integration with _construct_task
- Boundary cases for question_global range
- Task ID generation and uniqueness
- Metadata construction and provenance
- Pattern and signal handling
- Expected elements validation
"""

from dataclasses import FrozenInstanceError
from datetime import datetime
from typing import Any

import pytest

from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
    ChunkRoutingResult,
)
from farfan_pipeline.core.orchestrator.task_planner import (
    MAX_QUESTION_GLOBAL,
    ExecutableTask,
    _construct_task,
    _construct_task_legacy,
)
from farfan_pipeline.core.types import ChunkData


def create_test_chunk_routing_result(
    policy_area_id: str = "PA01",
    chunk_id: str | None = None,
    dimension_id: str = "DIM01",
    text_content: str = "Test chunk content",
    expected_elements: list[dict[str, Any]] | None = None,
    document_position: tuple[int, int] | None = None,
) -> ChunkRoutingResult:
    """Helper function to create test ChunkRoutingResult with all required fields."""
    if expected_elements is None:
        expected_elements = []
    if document_position is None:
        document_position = (0, 100)
    if chunk_id is None:
        chunk_id = f"{policy_area_id}-{dimension_id}"

    target_chunk = ChunkData(
        id=0,
        text=text_content,
        chunk_type="diagnostic",
        sentences=[],
        tables=[],
        start_pos=0,
        end_pos=len(text_content),
        confidence=0.95,
        chunk_id=chunk_id,
        policy_area_id=policy_area_id,
        dimension_id=dimension_id,
    )

    return ChunkRoutingResult(
        target_chunk=target_chunk,
        chunk_id=chunk_id,
        policy_area_id=policy_area_id,
        dimension_id=dimension_id,
        text_content=text_content,
        expected_elements=expected_elements,
        document_position=document_position,
    )


class MockRoutingResult:
    """Mock routing result for legacy tests."""

    def __init__(self, policy_area_id: str = "PA01"):
        self.policy_area_id = policy_area_id


class TestPhase7ExecutableTaskImmutability:
    """Test ExecutableTask immutability enforcement via frozen dataclass."""

    def test_task_id_immutable(self):
        """Verify task_id cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.task_id = "MQC-002_PA01"  # type: ignore[misc]

    def test_question_id_immutable(self):
        """Verify question_id cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.question_id = "D1-Q2"  # type: ignore[misc]

    def test_question_global_immutable(self):
        """Verify question_global cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.question_global = 2  # type: ignore[misc]

    def test_policy_area_id_immutable(self):
        """Verify policy_area_id cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.policy_area_id = "PA02"  # type: ignore[misc]

    def test_dimension_id_immutable(self):
        """Verify dimension_id cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.dimension_id = "DIM02"  # type: ignore[misc]

    def test_chunk_id_immutable(self):
        """Verify chunk_id cannot be modified after creation."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.chunk_id = "chunk_002"  # type: ignore[misc]

    def test_patterns_immutable(self):
        """Verify patterns list cannot be reassigned."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[{"type": "pattern1"}],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.patterns = [{"type": "pattern2"}]  # type: ignore[misc]

    def test_signals_immutable(self):
        """Verify signals dict cannot be reassigned."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={"signal1": 0.5},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.signals = {"signal2": 0.7}  # type: ignore[misc]

    def test_creation_timestamp_immutable(self):
        """Verify creation_timestamp cannot be modified."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.creation_timestamp = "2024-01-02T00:00:00Z"  # type: ignore[misc]

    def test_expected_elements_immutable(self):
        """Verify expected_elements list cannot be reassigned."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[{"type": "test"}],
            metadata={},
        )

        with pytest.raises(FrozenInstanceError):
            task.expected_elements = []  # type: ignore[misc]

    def test_metadata_immutable(self):
        """Verify metadata dict cannot be reassigned."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="D1-Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={"key": "value"},
        )

        with pytest.raises(FrozenInstanceError):
            task.metadata = {}  # type: ignore[misc]


class TestPhase7PostInitValidation:
    """Test __post_init__ validation for all mandatory fields."""

    def test_empty_task_id_raises_error(self):
        """Test empty task_id raises ValueError."""
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            ExecutableTask(
                task_id="",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_empty_question_id_raises_error(self):
        """Test empty question_id raises ValueError."""
        with pytest.raises(ValueError, match="question_id cannot be empty"):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_non_integer_question_global_raises_error(self):
        """Test non-integer question_global raises ValueError."""
        with pytest.raises(
            ValueError, match="question_global must be an integer, got str"
        ):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global="1",  # type: ignore[arg-type]
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_question_global_below_zero_raises_error(self):
        """Test question_global below 0 raises ValueError."""
        with pytest.raises(
            ValueError,
            match=f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}",
        ):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=-1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_question_global_above_max_raises_error(self):
        """Test question_global above MAX_QUESTION_GLOBAL raises ValueError."""
        with pytest.raises(
            ValueError,
            match=f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}",
        ):
            ExecutableTask(
                task_id="MQC-999_PA01",
                question_id="D1-Q1",
                question_global=MAX_QUESTION_GLOBAL + 1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_empty_policy_area_id_raises_error(self):
        """Test empty policy_area_id raises ValueError."""
        with pytest.raises(ValueError, match="policy_area_id cannot be empty"):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_empty_dimension_id_raises_error(self):
        """Test empty dimension_id raises ValueError."""
        with pytest.raises(ValueError, match="dimension_id cannot be empty"):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_empty_chunk_id_raises_error(self):
        """Test empty chunk_id raises ValueError."""
        with pytest.raises(ValueError, match="chunk_id cannot be empty"):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_empty_creation_timestamp_raises_error(self):
        """Test empty creation_timestamp raises ValueError."""
        with pytest.raises(ValueError, match="creation_timestamp cannot be empty"):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="D1-Q1",
                question_global=1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="",
                expected_elements=[],
                metadata={},
            )

    def test_valid_minimum_question_global(self):
        """Test valid minimum question_global value (0)."""
        task = ExecutableTask(
            task_id="MQC-000_PA01",
            question_id="D1-Q0",
            question_global=0,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )
        assert task.question_global == 0

    def test_valid_maximum_question_global(self):
        """Test valid maximum question_global value (MAX_QUESTION_GLOBAL)."""
        task = ExecutableTask(
            task_id=f"MQC-{MAX_QUESTION_GLOBAL:03d}_PA01",
            question_id="D1-Q999",
            question_global=MAX_QUESTION_GLOBAL,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )
        assert task.question_global == MAX_QUESTION_GLOBAL

    def test_all_valid_fields_create_task(self):
        """Test task creation with all valid fields."""
        task = ExecutableTask(
            task_id="MQC-042_PA05",
            question_id="D2-Q12",
            question_global=42,
            policy_area_id="PA05",
            dimension_id="DIM02",
            chunk_id="chunk_010",
            patterns=[{"type": "pattern1"}, {"type": "pattern2"}],
            signals={"signal1": 0.8, "signal2": 0.9},
            creation_timestamp="2024-01-01T12:30:45.123456Z",
            expected_elements=[{"type": "test", "minimum": 2}],
            metadata={"key1": "value1", "key2": "value2"},
        )
        assert task.task_id == "MQC-042_PA05"
        assert task.question_id == "D2-Q12"
        assert task.question_global == 42
        assert task.policy_area_id == "PA05"
        assert task.dimension_id == "DIM02"
        assert task.chunk_id == "chunk_010"


class TestPhase7ConstructTaskIntegration:
    """Test integration with _construct_task function."""

    def test_construct_task_generates_correct_task_id(self):
        """Test _construct_task generates correct task_id format."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result(policy_area_id="PA01")
        generated_task_ids: set[str] = set()
        correlation_id = "corr-123"

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            correlation_id,
        )

        assert task.task_id == "MQC-001_PA01"
        assert "MQC-001_PA01" in generated_task_ids

    def test_construct_task_with_various_question_globals(self):
        """Test _construct_task with various question_global values."""
        test_cases = [
            (0, "MQC-000_PA01"),
            (1, "MQC-001_PA01"),
            (50, "MQC-050_PA01"),
            (150, "MQC-150_PA01"),
            (300, "MQC-300_PA01"),
            (999, "MQC-999_PA01"),
        ]

        for question_global, expected_task_id in test_cases:
            question = {
                "question_id": f"Q{question_global}",
                "question_global": question_global,
                "dimension_id": "DIM01",
                "base_slot": f"Q{question_global}",
                "cluster_id": "CL01",
                "expected_elements": [],
            }
            routing_result = create_test_chunk_routing_result(policy_area_id="PA01")
            generated_task_ids: set[str] = set()

            task = _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

            assert task.task_id == expected_task_id
            assert task.question_global == question_global

    def test_construct_task_detects_duplicate_task_ids(self):
        """Test _construct_task detects duplicate task_ids."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result(policy_area_id="PA01")
        generated_task_ids = {"MQC-001_PA01"}  # Pre-populate with duplicate

        with pytest.raises(
            ValueError, match="Duplicate task_id detected: MQC-001_PA01"
        ):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_missing_question_global(self):
        """Test _construct_task raises error when question_global is missing."""
        question = {
            "question_id": "D1-Q1",
            # question_global is missing
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        with pytest.raises(ValueError, match="question_global field missing or None"):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_question_global_none(self):
        """Test _construct_task raises error when question_global is None."""
        question = {
            "question_id": "D1-Q1",
            "question_global": None,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        with pytest.raises(ValueError, match="question_global field missing or None"):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_question_global_not_integer(self):
        """Test _construct_task raises error when question_global is not integer."""
        question = {
            "question_id": "D1-Q1",
            "question_global": "1",  # String instead of int
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        with pytest.raises(
            ValueError, match="question_global must be an integer, got str"
        ):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_question_global_below_range(self):
        """Test _construct_task raises error when question_global is below 0."""
        question = {
            "question_id": "D1-Q1",
            "question_global": -1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        with pytest.raises(
            ValueError,
            match=f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}, got -1",
        ):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_question_global_above_range(self):
        """Test _construct_task raises error when question_global exceeds MAX."""
        question = {
            "question_id": "D1-Q1000",
            "question_global": 1000,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        with pytest.raises(
            ValueError,
            match=f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}, got 1000",
        ):
            _construct_task(
                question,
                routing_result,
                (),
                (),
                generated_task_ids,
                "corr-id",
            )

    def test_construct_task_with_patterns_tuple(self):
        """Test _construct_task handles patterns as tuple."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        applicable_patterns = (
            {"type": "pattern1", "value": 0.8},
            {"type": "pattern2", "value": 0.9},
        )
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            applicable_patterns,
            (),
            generated_task_ids,
            "corr-id",
        )

        assert len(task.patterns) == 2
        assert isinstance(task.patterns, list)
        assert task.patterns[0]["type"] == "pattern1"
        assert task.patterns[1]["type"] == "pattern2"

    def test_construct_task_with_signals_tuple(self):
        """Test _construct_task handles signals as tuple and converts to dict."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()

        # Signals as tuple of dicts with signal_type
        resolved_signals = (
            {"signal_type": "signal1", "value": 0.8},
            {"signal_type": "signal2", "value": 0.9},
        )
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            resolved_signals,
            generated_task_ids,
            "corr-id",
        )

        assert isinstance(task.signals, dict)
        assert "signal1" in task.signals
        assert "signal2" in task.signals
        assert task.signals["signal1"]["value"] == 0.8
        assert task.signals["signal2"]["value"] == 0.9

    def test_construct_task_with_expected_elements(self):
        """Test _construct_task includes expected_elements in task."""
        expected_elements = [
            {"type": "fuentes_oficiales", "minimum": 2, "required": True},
            {"type": "indicadores_cuantitativos", "minimum": 3, "required": False},
        ]
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": expected_elements,
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert len(task.expected_elements) == 2
        assert isinstance(task.expected_elements, list)
        assert task.expected_elements[0]["type"] == "fuentes_oficiales"
        assert task.expected_elements[1]["type"] == "indicadores_cuantitativos"

    def test_construct_task_includes_metadata(self):
        """Test _construct_task includes comprehensive metadata."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [{"type": "test"}],
        }
        routing_result = create_test_chunk_routing_result(document_position=(100, 200))
        applicable_patterns = ({"pattern": "p1"}, {"pattern": "p2"})
        resolved_signals = ({"signal_type": "s1", "value": 0.5},)
        generated_task_ids: set[str] = set()
        correlation_id = "corr-abc-123"

        task = _construct_task(
            question,
            routing_result,
            applicable_patterns,
            resolved_signals,
            generated_task_ids,
            correlation_id,
        )

        assert "base_slot" in task.metadata
        assert "cluster_id" in task.metadata
        assert "document_position" in task.metadata
        assert "synchronizer_version" in task.metadata
        assert "correlation_id" in task.metadata
        assert "original_pattern_count" in task.metadata
        assert "original_signal_count" in task.metadata
        assert "filtered_pattern_count" in task.metadata
        assert "resolved_signal_count" in task.metadata
        assert "schema_element_count" in task.metadata

        assert task.metadata["base_slot"] == "D1-Q1"
        assert task.metadata["cluster_id"] == "CL01"
        assert task.metadata["document_position"] == (100, 200)
        assert task.metadata["correlation_id"] == "corr-abc-123"
        assert task.metadata["original_pattern_count"] == 2
        assert task.metadata["original_signal_count"] == 1
        assert task.metadata["filtered_pattern_count"] == 2
        assert task.metadata["resolved_signal_count"] == 1
        assert task.metadata["schema_element_count"] == 1

    def test_construct_task_timestamp_format(self):
        """Test _construct_task creates ISO 8601 timestamp."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        # Timestamp should be ISO 8601 format with timezone
        assert "T" in task.creation_timestamp
        # Should be parseable by datetime
        parsed = datetime.fromisoformat(task.creation_timestamp)
        assert parsed.tzinfo is not None

    def test_construct_task_uses_routing_result_dimension(self):
        """Test _construct_task uses dimension_id from routing_result."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",  # Different from routing_result
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result(dimension_id="DIM02")
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        # Should use routing_result dimension_id, not question dimension_id
        assert task.dimension_id == "DIM02"


class TestPhase7ConstructTaskLegacy:
    """Test legacy _construct_task_legacy function."""

    def test_construct_task_legacy_generates_correct_task_id(self):
        """Test _construct_task_legacy generates correct task_id format."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "policy_area_id": "PA01",
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001", "expected_elements": []}
        patterns: list[dict[str, Any]] = []
        signals: dict[str, Any] = {}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult(policy_area_id="PA01")

        task = _construct_task_legacy(
            question, chunk, patterns, signals, generated_task_ids, routing_result
        )

        assert task.task_id == "MQC-001_PA01"
        assert "MQC-001_PA01" in generated_task_ids

    def test_construct_task_legacy_detects_duplicate_task_ids(self):
        """Test _construct_task_legacy detects duplicate task_ids."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001", "expected_elements": []}
        generated_task_ids = {"MQC-001_PA01"}
        routing_result = MockRoutingResult(policy_area_id="PA01")

        with pytest.raises(
            ValueError,
            match="Duplicate task_id detected: MQC-001_PA01 for question D1-Q1",
        ):
            _construct_task_legacy(
                question, chunk, [], {}, generated_task_ids, routing_result
            )

    def test_construct_task_legacy_invalid_question_global_type(self):
        """Test _construct_task_legacy raises error for non-integer question_global."""
        question = {
            "question_id": "D1-Q1",
            "question_global": "not_an_int",
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        with pytest.raises(
            ValueError, match="Invalid question_global.*Must be an integer in range"
        ):
            _construct_task_legacy(
                question, chunk, [], {}, generated_task_ids, routing_result
            )

    def test_construct_task_legacy_question_global_below_range(self):
        """Test _construct_task_legacy raises error for negative question_global."""
        question = {
            "question_id": "D1-Q1",
            "question_global": -1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        with pytest.raises(
            ValueError, match="Invalid question_global.*Must be an integer in range"
        ):
            _construct_task_legacy(
                question, chunk, [], {}, generated_task_ids, routing_result
            )

    def test_construct_task_legacy_question_global_above_range(self):
        """Test _construct_task_legacy raises error for question_global > MAX."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1000,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        with pytest.raises(
            ValueError, match="Invalid question_global.*Must be an integer in range"
        ):
            _construct_task_legacy(
                question, chunk, [], {}, generated_task_ids, routing_result
            )

    def test_construct_task_legacy_coerces_patterns_to_list(self):
        """Test _construct_task_legacy coerces patterns tuple to list."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        patterns = ({"pattern": "p1"}, {"pattern": "p2"})  # Tuple
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        task = _construct_task_legacy(
            question, chunk, patterns, {}, generated_task_ids, routing_result  # type: ignore[arg-type]
        )

        assert isinstance(task.patterns, list)
        assert len(task.patterns) == 2

    def test_construct_task_legacy_coerces_signals_to_dict(self):
        """Test _construct_task_legacy coerces signals to dict if needed."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        signals = {"signal1": 0.8, "signal2": 0.9}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        task = _construct_task_legacy(
            question, chunk, [], signals, generated_task_ids, routing_result
        )

        assert isinstance(task.signals, dict)
        assert task.signals == signals

    def test_construct_task_legacy_timestamp_is_iso8601(self):
        """Test _construct_task_legacy creates ISO 8601 timestamp."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        chunk = {"id": "chunk_001"}
        generated_task_ids: set[str] = set()
        routing_result = MockRoutingResult()

        task = _construct_task_legacy(
            question, chunk, [], {}, generated_task_ids, routing_result
        )

        # Should have "T" separator for ISO 8601
        assert "T" in task.creation_timestamp
        # Should be parseable
        parsed = datetime.fromisoformat(task.creation_timestamp)
        assert parsed is not None


class TestPhase7BoundaryConditions:
    """Test boundary conditions for question_global range."""

    def test_question_global_boundary_zero(self):
        """Test question_global=0 is valid."""
        task = ExecutableTask(
            task_id="MQC-000_PA01",
            question_id="Q0",
            question_global=0,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )
        assert task.question_global == 0

    def test_question_global_boundary_max(self):
        """Test question_global=MAX_QUESTION_GLOBAL is valid."""
        task = ExecutableTask(
            task_id=f"MQC-{MAX_QUESTION_GLOBAL:03d}_PA01",
            question_id=f"Q{MAX_QUESTION_GLOBAL}",
            question_global=MAX_QUESTION_GLOBAL,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )
        assert task.question_global == MAX_QUESTION_GLOBAL

    def test_question_global_just_below_zero_invalid(self):
        """Test question_global=-1 is invalid."""
        with pytest.raises(ValueError):
            ExecutableTask(
                task_id="MQC-001_PA01",
                question_id="Q-1",
                question_global=-1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_question_global_just_above_max_invalid(self):
        """Test question_global=MAX_QUESTION_GLOBAL+1 is invalid."""
        with pytest.raises(ValueError):
            ExecutableTask(
                task_id=f"MQC-{MAX_QUESTION_GLOBAL+1:03d}_PA01",
                question_id=f"Q{MAX_QUESTION_GLOBAL+1}",
                question_global=MAX_QUESTION_GLOBAL + 1,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )

    def test_construct_task_boundaries_validated(self):
        """Test _construct_task validates question_global boundaries."""
        # Test minimum valid
        question_min = {
            "question_id": "Q0",
            "question_global": 0,
            "dimension_id": "DIM01",
            "base_slot": "Q0",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task_min = _construct_task(
            question_min,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )
        assert task_min.question_global == 0

        # Test maximum valid
        question_max = {
            "question_id": f"Q{MAX_QUESTION_GLOBAL}",
            "question_global": MAX_QUESTION_GLOBAL,
            "dimension_id": "DIM01",
            "base_slot": f"Q{MAX_QUESTION_GLOBAL}",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        generated_task_ids_max: set[str] = set()

        task_max = _construct_task(
            question_max,
            routing_result,
            (),
            (),
            generated_task_ids_max,
            "corr-id",
        )
        assert task_max.question_global == MAX_QUESTION_GLOBAL

        # Test below minimum invalid
        question_below = {
            "question_id": "Q-1",
            "question_global": -1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        generated_task_ids_below: set[str] = set()

        with pytest.raises(ValueError, match="question_global must be in range"):
            _construct_task(
                question_below,
                routing_result,
                (),
                (),
                generated_task_ids_below,
                "corr-id",
            )

        # Test above maximum invalid
        question_above = {
            "question_id": f"Q{MAX_QUESTION_GLOBAL+1}",
            "question_global": MAX_QUESTION_GLOBAL + 1,
            "dimension_id": "DIM01",
            "expected_elements": [],
        }
        generated_task_ids_above: set[str] = set()

        with pytest.raises(ValueError, match="question_global must be in range"):
            _construct_task(
                question_above,
                routing_result,
                (),
                (),
                generated_task_ids_above,
                "corr-id",
            )


class TestPhase7TaskIDGeneration:
    """Test task ID generation patterns and consistency."""

    def test_task_id_format_mqc_prefix(self):
        """Test task_id starts with MQC- prefix."""
        task = ExecutableTask(
            task_id="MQC-001_PA01",
            question_id="Q1",
            question_global=1,
            policy_area_id="PA01",
            dimension_id="DIM01",
            chunk_id="chunk_001",
            patterns=[],
            signals={},
            creation_timestamp="2024-01-01T00:00:00Z",
            expected_elements=[],
            metadata={},
        )
        assert task.task_id.startswith("MQC-")

    def test_task_id_format_zero_padded(self):
        """Test task_id has zero-padded question number."""
        test_cases = [
            (1, "MQC-001_PA01"),
            (10, "MQC-010_PA01"),
            (100, "MQC-100_PA01"),
            (999, "MQC-999_PA01"),
        ]

        for question_global, expected_prefix in test_cases:
            task = ExecutableTask(
                task_id=expected_prefix,
                question_id=f"Q{question_global}",
                question_global=question_global,
                policy_area_id="PA01",
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )
            assert task.task_id == expected_prefix

    def test_task_id_format_includes_policy_area(self):
        """Test task_id includes policy area ID."""
        test_cases = [
            ("PA01", "MQC-001_PA01"),
            ("PA05", "MQC-001_PA05"),
            ("PA10", "MQC-001_PA10"),
        ]

        for policy_area_id, expected_task_id in test_cases:
            task = ExecutableTask(
                task_id=expected_task_id,
                question_id="Q1",
                question_global=1,
                policy_area_id=policy_area_id,
                dimension_id="DIM01",
                chunk_id="chunk_001",
                patterns=[],
                signals={},
                creation_timestamp="2024-01-01T00:00:00Z",
                expected_elements=[],
                metadata={},
            )
            assert task.task_id == expected_task_id
            assert policy_area_id in task.task_id

    def test_construct_task_generates_consistent_task_id(self):
        """Test _construct_task generates consistent task_id from inputs."""
        question = {
            "question_id": "D2-Q25",
            "question_global": 75,
            "dimension_id": "DIM02",
            "base_slot": "D2-Q25",
            "cluster_id": "CL02",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result(policy_area_id="PA07")
        generated_task_ids: set[str] = set()

        task1 = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        # Reset and create again
        generated_task_ids2: set[str] = set()
        task2 = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids2,
            "corr-id",
        )

        assert task1.task_id == task2.task_id == "MQC-075_PA07"


class TestPhase7ProvenanceTracking:
    """Test provenance and metadata tracking in task construction."""

    def test_metadata_includes_base_slot(self):
        """Test metadata includes base_slot from question."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1-SLOT",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["base_slot"] == "D1-Q1-SLOT"

    def test_metadata_includes_cluster_id(self):
        """Test metadata includes cluster_id from question."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CLUSTER-ABC",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["cluster_id"] == "CLUSTER-ABC"

    def test_metadata_includes_correlation_id(self):
        """Test metadata includes correlation_id for tracing."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()
        correlation_id = "CORRELATION-XYZ-789"

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            correlation_id,
        )

        assert task.metadata["correlation_id"] == "CORRELATION-XYZ-789"

    def test_metadata_includes_document_position(self):
        """Test metadata includes document_position from routing_result."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result(document_position=(500, 750))
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["document_position"] == (500, 750)

    def test_metadata_tracks_pattern_counts(self):
        """Test metadata tracks original and filtered pattern counts."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        applicable_patterns = ({"p": "1"}, {"p": "2"}, {"p": "3"})
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            applicable_patterns,
            (),
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["original_pattern_count"] == 3
        assert task.metadata["filtered_pattern_count"] == 3

    def test_metadata_tracks_signal_counts(self):
        """Test metadata tracks original and resolved signal counts."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        resolved_signals = (
            {"signal_type": "s1", "v": 0.5},
            {"signal_type": "s2", "v": 0.7},
        )
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            resolved_signals,
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["original_signal_count"] == 2
        assert task.metadata["resolved_signal_count"] == 2

    def test_metadata_tracks_schema_element_count(self):
        """Test metadata tracks expected_elements count."""
        expected_elements = [
            {"type": "elem1"},
            {"type": "elem2"},
            {"type": "elem3"},
        ]
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": expected_elements,
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert task.metadata["schema_element_count"] == 3

    def test_metadata_includes_synchronizer_version(self):
        """Test metadata includes synchronizer version."""
        question = {
            "question_id": "D1-Q1",
            "question_global": 1,
            "dimension_id": "DIM01",
            "base_slot": "D1-Q1",
            "cluster_id": "CL01",
            "expected_elements": [],
        }
        routing_result = create_test_chunk_routing_result()
        generated_task_ids: set[str] = set()

        task = _construct_task(
            question,
            routing_result,
            (),
            (),
            generated_task_ids,
            "corr-id",
        )

        assert "synchronizer_version" in task.metadata
        assert isinstance(task.metadata["synchronizer_version"], str)
