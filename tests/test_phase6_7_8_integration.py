"""
Integration Tests for Phase 6-7-8 Pipeline
===========================================

Tests the complete flow:
Phase 6 (Schema Validation) → Phase 7 (Task Construction) → Phase 8 (Execution Plan)

Verifies:
1. Successful end-to-end integration with valid data
2. Error propagation from Phase 6 → Phase 7 → Phase 8
3. Field validation and type checking
4. Duplicate detection across phases
5. Non-null constraint enforcement
6. Deterministic identifier generation
7. Integrity hash computation
"""

import pytest
from typing import Any

from src.farfan_pipeline.core.phases.phase6_schema_validation import (
    phase6_schema_validation,
    Phase6SchemaValidationOutput,
    PHASE6_VERSION,
)
from src.farfan_pipeline.core.phases.phase7_task_construction import (
    phase7_task_construction,
    Phase7TaskConstructionOutput,
    PHASE7_VERSION,
    TASK_ID_FORMAT,
)
from src.farfan_pipeline.core.phases.phase8_execution_plan import (
    phase8_execution_plan_assembly,
    Phase8ExecutionPlanOutput,
    PHASE8_VERSION,
)


def create_valid_question(index: int) -> dict[str, Any]:
    """Create a valid question for testing."""
    return {
        "question_id": f"Q{index:03d}",
        "question_global": index,
        "dimension_id": f"D{(index % 6) + 1}",
        "policy_area_id": f"PA{(index % 10) + 1:02d}",
        "base_slot": f"slot_{index}",
        "cluster_id": f"cluster_{index % 4}",
        "patterns": [{"type": "regex", "value": "test.*"}],
        "signals": {"signal_type": "evidence", "strength": 0.8},
        "expected_elements": [{"type": "text", "required": True}],
        "metadata": {"source": "test"},
    }


def create_valid_chunk(index: int) -> dict[str, Any]:
    """Create a valid chunk for testing."""
    return {
        "chunk_id": f"chunk_{index:03d}",
        "policy_area_id": f"PA{(index % 10) + 1:02d}",
        "dimension_id": f"D{(index % 6) + 1}",
        "document_position": index,
        "content": f"Test content for chunk {index}",
        "metadata": {"page": index // 10},
    }


class TestPhase6SchemaValidation:
    """Test Phase 6 schema validation functionality."""

    def test_valid_questions_and_chunks(self):
        """Test successful validation with valid data."""
        questions = [create_valid_question(i) for i in range(10)]
        chunks = [create_valid_chunk(i) for i in range(10)]

        result = phase6_schema_validation(questions, chunks)

        assert result.schema_validation_passed
        assert len(result.validation_errors) == 0
        assert result.question_count == 10
        assert result.chunk_count == 10
        assert len(result.validated_questions) == 10
        assert len(result.validated_chunks) == 10
        assert result.phase6_version == PHASE6_VERSION

    def test_missing_required_field_question(self):
        """Test error handling for missing required field in question."""
        questions = [{"question_id": "Q001"}]
        chunks = []

        result = phase6_schema_validation(questions, chunks)

        assert not result.schema_validation_passed
        assert len(result.validation_errors) > 0
        assert any("question_global" in err for err in result.validation_errors)
        assert any("KeyError" in err for err in result.validation_errors)

    def test_invalid_type_question_global(self):
        """Test error handling for invalid type."""
        question = create_valid_question(0)
        question["question_global"] = "not_an_int"

        result = phase6_schema_validation([question], [])

        assert not result.schema_validation_passed
        assert any("invalid type" in err for err in result.validation_errors)
        assert any("expected int" in err for err in result.validation_errors)

    def test_out_of_range_question_global(self):
        """Test error handling for out-of-range value."""
        question = create_valid_question(0)
        question["question_global"] = 1000

        result = phase6_schema_validation([question], [])

        assert not result.schema_validation_passed
        assert any("not in range" in err for err in result.validation_errors)

    def test_empty_string_field(self):
        """Test error handling for empty string in required field."""
        question = create_valid_question(0)
        question["question_id"] = ""

        result = phase6_schema_validation([question], [])

        assert not result.schema_validation_passed
        assert any("empty string" in err for err in result.validation_errors)

    def test_missing_chunk_content(self):
        """Test error handling for missing chunk content."""
        chunks = [{"chunk_id": "chunk_001"}]

        result = phase6_schema_validation([], chunks)

        assert not result.schema_validation_passed
        assert any("content" in err for err in result.validation_errors)
        assert any("KeyError" in err for err in result.validation_errors)


class TestPhase7TaskConstruction:
    """Test Phase 7 task construction functionality."""

    def test_successful_task_construction(self):
        """Test successful task construction with valid Phase 6 output."""
        questions = [create_valid_question(i) for i in range(5)]
        chunks = [create_valid_chunk(i) for i in range(5)]

        phase6_output = phase6_schema_validation(questions, chunks)
        assert phase6_output.schema_validation_passed

        phase7_output = phase7_task_construction(phase6_output)

        assert phase7_output.construction_passed
        assert len(phase7_output.construction_errors) == 0
        assert phase7_output.task_count == 5
        assert len(phase7_output.tasks) == 5
        assert phase7_output.phase7_version == PHASE7_VERSION

    def test_task_id_format(self):
        """Test task ID generation with zero-padded format."""
        questions = [create_valid_question(i) for i in range(3)]
        chunks = [create_valid_chunk(i) for i in range(3)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)

        assert phase7_output.construction_passed

        for i, task in enumerate(phase7_output.tasks):
            expected_id = TASK_ID_FORMAT.format(
                question_global=i,
                policy_area_id=f"PA{(i % 10) + 1:02d}"
            )
            assert task.task_id == expected_id
            assert len(task.task_id.split("-")[1].split("_")[0]) == 3

    def test_phase6_failure_propagation(self):
        """Test error propagation when Phase 6 fails."""
        phase6_output = Phase6SchemaValidationOutput(
            validated_questions=[],
            validated_chunks=[],
            schema_validation_passed=False,
            validation_errors=["Phase 6 test error"],
            validation_warnings=[],
            question_count=0,
            chunk_count=0,
            validation_timestamp="2025-01-19T00:00:00Z",
        )

        phase7_output = phase7_task_construction(phase6_output)

        assert not phase7_output.construction_passed
        assert len(phase7_output.construction_errors) > 0
        assert any("Phase 6" in err for err in phase7_output.construction_errors)
        assert phase7_output.task_count == 0
        assert len(phase7_output.tasks) == 0

    def test_duplicate_task_id_detection(self):
        """Test duplicate task ID detection."""
        questions = [
            create_valid_question(0),
            create_valid_question(0),
        ]
        chunks = [create_valid_chunk(0)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)

        assert not phase7_output.construction_passed
        assert len(phase7_output.duplicate_task_ids) > 0
        assert any("Duplicate" in err for err in phase7_output.construction_errors)

    def test_missing_field_tracking(self):
        """Test tracking of missing fields by task."""
        from src.farfan_pipeline.core.phases.phase7_task_construction import (
            ValidatedQuestionSchema,
            ValidatedChunkSchema,
            Phase6SchemaValidationOutput,
        )

        question = ValidatedQuestionSchema(
            question_id="",
            question_global=0,
            dimension_id="D1",
            policy_area_id="PA01",
            base_slot="slot_0",
            cluster_id="cluster_0",
            patterns=[],
            signals={},
            expected_elements=[],
            metadata={},
        )

        chunk = ValidatedChunkSchema(
            chunk_id="chunk_000",
            policy_area_id="PA01",
            dimension_id="D1",
            document_position=0,
            content="test",
            metadata={},
        )

        phase6_output = Phase6SchemaValidationOutput(
            validated_questions=[question],
            validated_chunks=[chunk],
            schema_validation_passed=True,
            validation_errors=[],
            validation_warnings=[],
            question_count=1,
            chunk_count=1,
            validation_timestamp="2025-01-19T00:00:00Z",
        )

        phase7_output = phase7_task_construction(phase6_output)

        assert not phase7_output.construction_passed
        assert any("empty string" in err for err in phase7_output.construction_errors)


class TestPhase8ExecutionPlanAssembly:
    """Test Phase 8 execution plan assembly functionality."""

    def test_successful_plan_assembly(self):
        """Test successful execution plan assembly."""
        questions = [create_valid_question(i) for i in range(10)]
        chunks = [create_valid_chunk(i) for i in range(10)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)

        assert phase7_output.construction_passed

        phase8_output = phase8_execution_plan_assembly(phase7_output)

        assert phase8_output.assembly_passed
        assert phase8_output.execution_plan is not None
        assert phase8_output.task_count == 10
        assert len(phase8_output.assembly_errors) == 0
        assert phase8_output.integrity_hash != ""
        assert len(phase8_output.integrity_hash) == 64
        assert phase8_output.phase8_version == PHASE8_VERSION

    def test_phase7_failure_propagation(self):
        """Test error propagation when Phase 7 fails."""
        phase7_output = Phase7TaskConstructionOutput(
            tasks=[],
            task_count=0,
            construction_passed=False,
            construction_errors=["Phase 7 test error"],
            construction_warnings=[],
            duplicate_task_ids=[],
            missing_fields_by_task={},
            construction_timestamp="2025-01-19T00:00:00Z",
            metadata={},
        )

        phase8_output = phase8_execution_plan_assembly(phase7_output)

        assert not phase8_output.assembly_passed
        assert phase8_output.execution_plan is None
        assert len(phase8_output.assembly_errors) > 0
        assert any("Phase 7" in err for err in phase8_output.assembly_errors)

    def test_integrity_hash_determinism(self):
        """Test that integrity hash is deterministic."""
        questions = [create_valid_question(i) for i in range(5)]
        chunks = [create_valid_chunk(i) for i in range(5)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)

        phase8_output1 = phase8_execution_plan_assembly(phase7_output)
        phase8_output2 = phase8_execution_plan_assembly(phase7_output)

        assert phase8_output1.integrity_hash == phase8_output2.integrity_hash

    def test_execution_plan_immutability(self):
        """Test that execution plan tasks are immutable tuple."""
        questions = [create_valid_question(i) for i in range(5)]
        chunks = [create_valid_chunk(i) for i in range(5)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)
        phase8_output = phase8_execution_plan_assembly(phase7_output)

        assert phase8_output.execution_plan is not None
        assert isinstance(phase8_output.execution_plan.tasks, tuple)

        with pytest.raises(AttributeError):
            phase8_output.execution_plan.tasks.append(None)


class TestPhase6_7_8_Integration:
    """Integration tests for the complete Phase 6-7-8 pipeline."""

    def test_end_to_end_success(self):
        """Test successful end-to-end pipeline execution."""
        questions = [create_valid_question(i) for i in range(20)]
        chunks = [create_valid_chunk(i) for i in range(20)]

        phase6_output = phase6_schema_validation(questions, chunks)
        assert phase6_output.schema_validation_passed

        phase7_output = phase7_task_construction(phase6_output)
        assert phase7_output.construction_passed

        phase8_output = phase8_execution_plan_assembly(phase7_output)
        assert phase8_output.assembly_passed
        assert phase8_output.execution_plan is not None

    def test_error_cascade_from_phase6(self):
        """Test that errors cascade correctly from Phase 6 through Phase 8."""
        questions = [{"invalid": "data"}]
        chunks = []

        phase6_output = phase6_schema_validation(questions, chunks)
        assert not phase6_output.schema_validation_passed

        phase7_output = phase7_task_construction(phase6_output)
        assert not phase7_output.construction_passed

        phase8_output = phase8_execution_plan_assembly(phase7_output)
        assert not phase8_output.assembly_passed
        assert phase8_output.execution_plan is None

    def test_deterministic_processing_order(self):
        """Test that processing order is deterministic."""
        questions = [create_valid_question(i) for i in range(10)]
        chunks = [create_valid_chunk(i) for i in range(10)]

        run1_phase6 = phase6_schema_validation(questions, chunks)
        run1_phase7 = phase7_task_construction(run1_phase6)
        run1_phase8 = phase8_execution_plan_assembly(run1_phase7)

        run2_phase6 = phase6_schema_validation(questions, chunks)
        run2_phase7 = phase7_task_construction(run2_phase6)
        run2_phase8 = phase8_execution_plan_assembly(run2_phase7)

        assert len(run1_phase7.tasks) == len(run2_phase7.tasks)
        for task1, task2 in zip(run1_phase7.tasks, run2_phase7.tasks):
            assert task1.task_id == task2.task_id
            assert task1.question_global == task2.question_global

        assert run1_phase8.integrity_hash == run2_phase8.integrity_hash

    def test_metadata_propagation(self):
        """Test that metadata is properly propagated through phases."""
        questions = [create_valid_question(i) for i in range(5)]
        chunks = [create_valid_chunk(i) for i in range(5)]

        phase6_output = phase6_schema_validation(questions, chunks)
        phase7_output = phase7_task_construction(phase6_output)
        phase8_output = phase8_execution_plan_assembly(phase7_output)

        assert phase7_output.metadata["question_count"] == 5
        assert phase7_output.metadata["chunk_count"] == 5

        assert phase8_output.metadata["task_count"] == 5
        assert "integrity_hash_length" in phase8_output.metadata
