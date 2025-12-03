"""
Immutable micro-question context model and deterministic ordering helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True, slots=True)
class MicroQuestionContext:
    """
    Canonical identity and routing metadata for a micro question.
    """

    policy_area_id: str
    question_global: int
    question_id: str = ""
    dimension_id: str | None = None
    base_slot: str | None = None
    cluster_id: str | None = None
    contract_version: str | None = None
    text: str | None = None


def sort_micro_question_contexts(
    questions: Iterable[MicroQuestionContext],
) -> list[MicroQuestionContext]:
    """
    Return micro-question contexts deterministically sorted by policy area then global id.
    """
    return sorted(questions, key=lambda q: (q.policy_area_id, q.question_global))


__all__ = ["MicroQuestionContext", "sort_micro_question_contexts"]
