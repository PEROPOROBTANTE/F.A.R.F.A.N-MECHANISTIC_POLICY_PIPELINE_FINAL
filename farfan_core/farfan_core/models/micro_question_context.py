"""
Immutable micro-question context model and deterministic ordering helper.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class MicroQuestionContext:
    """
    Canonical identity and routing metadata for a micro question.
    """

    policy_area_id: str
    dimension_id: str
    question_global: int
    question_id: str = ""
    base_slot: str | None = None
    cluster_id: str | None = None
    contract_version: str | None = None
    text: str | None = None
    patterns: tuple[dict[str, Any], ...] = ()

    def __post_init__(self) -> None:
        if not self.policy_area_id:
            raise ValueError("policy_area_id is required for MicroQuestionContext")
        if not self.dimension_id:
            raise ValueError("dimension_id is required for MicroQuestionContext")
        if self.question_global <= 0:
            raise ValueError("question_global must be a positive integer")
        normalized_patterns = tuple(self.patterns)
        object.__setattr__(self, "patterns", normalized_patterns)
        for pattern in normalized_patterns:
            pa_in_pattern = pattern.get("policy_area_id")
            if pa_in_pattern is None:
                raise ValueError("patterns entries must include policy_area_id")
            if pa_in_pattern != self.policy_area_id:
                raise ValueError(
                    f"Pattern policy_area_id {pa_in_pattern!r} "
                    f"does not match context policy_area_id {self.policy_area_id!r}"
                )


def sort_micro_question_contexts(
    questions: Iterable[MicroQuestionContext],
) -> list[MicroQuestionContext]:
    """
    Return micro-question contexts deterministically sorted by policy area then global id.
    """
    return sorted(questions, key=lambda q: (q.policy_area_id, q.question_global))


__all__ = ["MicroQuestionContext", "sort_micro_question_contexts"]
