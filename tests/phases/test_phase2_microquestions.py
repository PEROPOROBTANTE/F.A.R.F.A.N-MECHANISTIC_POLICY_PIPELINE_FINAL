"""Test Phase 2: Microquestions Execution

Tests Phase 2 question generation and validation.
"""
import pytest
from farfan_pipeline.core.phases.phase2_types import (
    Phase2QuestionResult, Phase2Result, validate_phase2_result
)


class TestPhase2Contract:
    """Test Phase 2 result validation."""

    def test_phase2_result_structure(self):
        """Test Phase2Result has questions list."""
        question = Phase2QuestionResult(
            base_slot="D1Q1", question_id="q1", question_global=1,
            policy_area_id="PA01", dimension_id="DIM01",
            evidence={}, validation={}, trace={}
        )
        result = Phase2Result(questions=[question])
        assert len(result.questions) == 1

    def test_validate_phase2_result_success(self):
        """Test validation succeeds for valid Phase 2 result."""
        result_data = {
            "questions": [
                {
                    "base_slot": "D1Q1", "question_id": "q1", "question_global": 1,
                    "evidence": {}, "validation": {}
                }
            ]
        }
        is_valid, errors, normalized = validate_phase2_result(result_data)
        assert is_valid
        assert len(errors) == 0
        assert len(normalized) == 1

    def test_validate_phase2_result_empty_questions(self):
        """Test validation fails for empty questions list."""
        result_data = {"questions": []}
        is_valid, errors, normalized = validate_phase2_result(result_data)
        assert not is_valid
        assert any("empty" in err.lower() for err in errors)

    def test_validate_phase2_result_missing_questions(self):
        """Test validation fails for missing questions field."""
        result_data = {}
        is_valid, errors, normalized = validate_phase2_result(result_data)
        assert not is_valid
        assert any("missing" in err.lower() for err in errors)
