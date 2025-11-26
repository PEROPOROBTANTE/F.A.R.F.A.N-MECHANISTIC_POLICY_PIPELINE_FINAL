"""
Types for Phase 2 (Microquestions)
==================================

This module defines the canonical data structures for the output of
Phase 2, which involves processing the PreprocessedDocument to generate
a series of microquestions and their answers.

These types are used by the PhaseOrchestrator to validate and record
the results of the core orchestrator's execution.

Author: F.A.R.F.A.N Architecture Team
Date: 2025-11-21
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Tuple


@dataclass
class Phase2QuestionResult:
    """
    Represents the result for a single microquestion generated
    and answered during Phase 2.
    """

    base_slot: str
    question_id: str
    question_global: int | None
    policy_area_id: str | None = None
    dimension_id: str | None = None
    cluster_id: str | None = None
    evidence: dict[str, Any] | None = None
    validation: dict[str, Any] | None = None
    trace: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    human_readable_output: str | None = None  # Added for v3 contracts


@dataclass
class Phase2Result:
    """
    Represents the complete output of Phase 2, containing all
    the generated microquestions.
    """

    questions: List[Phase2QuestionResult]


def _extract_questions(result: Any) -> tuple[List[Any] | None, list[str]]:
    """Normalize Phase 2 result into a list of question dicts if possible."""
    errors: list[str] = []
    if result is None:
        errors.append("Phase 2 returned no data")
        return None, errors

    if isinstance(result, dict) and "questions" in result:
        questions = result.get("questions")
    elif hasattr(result, "questions"):
        questions = getattr(result, "questions")
    else:
        errors.append("Phase 2 result missing 'questions'")
        return None, errors

    if not isinstance(questions, list):
        errors.append("Phase 2 questions must be a list")
        return None, errors

    return questions, errors


def validate_phase2_result(result: Any) -> Tuple[bool, list[str], List[dict[str, Any]] | None]:
    """
    Validate the structure of a Phase 2 result.

    Returns:
        Tuple of (is_valid, errors, normalized_questions)
    """
    questions, errors = _extract_questions(result)
    if questions is None:
        return False, errors, None

    if len(questions) == 0:
        errors.append("Phase 2 questions list is empty or missing")
        return False, errors, questions

    normalized: list[dict[str, Any]] = []
    for idx, q in enumerate(questions):
        if not isinstance(q, dict):
            errors.append(f"Question {idx} must be a dict")
            continue

        required_keys = ["base_slot", "question_id", "question_global", "evidence", "validation"]
        missing = [key for key in required_keys if q.get(key) is None]
        if missing:
            errors.append(f"Question {idx} missing keys: {', '.join(missing)}")

        normalized.append(q)

    return len(errors) == 0, errors, normalized


__all__ = [
    "Phase2QuestionResult",
    "Phase2Result",
    "validate_phase2_result",
]
