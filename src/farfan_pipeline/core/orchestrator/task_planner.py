from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.irrigation_synchronizer import (
        ChunkRoutingResult,
    )

logger = logging.getLogger(__name__)

EXPECTED_TASKS_PER_CHUNK = 5
EXPECTED_TASKS_PER_POLICY_AREA = 30
MAX_QUESTION_GLOBAL = 999


class RoutingResult(Protocol):
    """Protocol for routing result objects that provide policy_area_id."""

    policy_area_id: str


def _freeze_immutable(obj: Any) -> Any:  # noqa: ANN401
    if isinstance(obj, dict):
        return MappingProxyType({k: _freeze_immutable(v) for k, v in obj.items()})
    if isinstance(obj, list | tuple):
        return tuple(_freeze_immutable(x) for x in obj)
    if isinstance(obj, set):
        return frozenset(_freeze_immutable(x) for x in obj)
    return obj


@dataclass(frozen=True, slots=True)
class MicroQuestionContext:
    task_id: str
    question_id: str
    question_global: int
    policy_area_id: str
    dimension_id: str
    chunk_id: str
    base_slot: str
    cluster_id: str
    patterns: tuple[Any, ...]
    signals: Any
    expected_elements: tuple[Any, ...]
    signal_requirements: Any
    creation_timestamp: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "patterns", tuple(self.patterns))
        object.__setattr__(self, "signals", _freeze_immutable(self.signals))
        object.__setattr__(self, "expected_elements", tuple(self.expected_elements))
        object.__setattr__(
            self, "signal_requirements", _freeze_immutable(self.signal_requirements)
        )


@dataclass(frozen=True, slots=True)
class ExecutableTask:
    task_id: str
    question_id: str
    question_global: int
    policy_area_id: str
    dimension_id: str
    chunk_id: str
    patterns: list[dict[str, Any]]
    signals: dict[str, Any]
    creation_timestamp: str
    expected_elements: list[dict[str, Any]]
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.task_id:
            raise ValueError("task_id cannot be empty")
        if not self.question_id:
            raise ValueError("question_id cannot be empty")
        if not isinstance(self.question_global, int):
            raise ValueError(
                f"question_global must be an integer, got {type(self.question_global).__name__}"
            )
        if not (0 <= self.question_global <= MAX_QUESTION_GLOBAL):
            raise ValueError(
                f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}, got {self.question_global}"
            )
        if not self.policy_area_id:
            raise ValueError("policy_area_id cannot be empty")
        if not self.dimension_id:
            raise ValueError("dimension_id cannot be empty")
        if not self.chunk_id:
            raise ValueError("chunk_id cannot be empty")
        if not self.creation_timestamp:
            raise ValueError("creation_timestamp cannot be empty")


def _validate_element_compatibility(  # noqa: PLR0912
    provisional_task_id: str,
    question_schema: list[dict[str, Any]] | dict[str, Any],
    chunk_schema: list[dict[str, Any]] | dict[str, Any],
    common_type_class: type,  # noqa: ARG001
) -> int:
    validated_count = 0

    if isinstance(question_schema, list) and isinstance(chunk_schema, list):
        for idx, (q_elem, c_elem) in enumerate(
            zip(question_schema, chunk_schema, strict=True)
        ):
            if q_elem.get("type") is None:
                raise ValueError(
                    f"Task {provisional_task_id}: Question element at index {idx} "
                    f"has missing type field"
                )
            if c_elem.get("type") is None:
                raise ValueError(
                    f"Task {provisional_task_id}: Chunk element at index {idx} "
                    f"has missing type field"
                )

            if q_elem["type"] != c_elem["type"]:
                raise ValueError(
                    f"Task {provisional_task_id}: Type mismatch at index {idx}: "
                    f"question type '{q_elem['type']}' != chunk type '{c_elem['type']}'"
                )

            q_required = q_elem.get("required", False)
            c_required = c_elem.get("required", False)
            if q_required and not c_required:
                raise ValueError(
                    f"Task {provisional_task_id}: Required field mismatch at index {idx}: "
                    f"question requires element but chunk marks it optional"
                )

            q_minimum = q_elem.get("minimum", 0)
            c_minimum = c_elem.get("minimum", 0)
            if c_minimum < q_minimum:
                raise ValueError(
                    f"Task {provisional_task_id}: Threshold mismatch at index {idx}: "
                    f"chunk minimum ({c_minimum}) is lower than question minimum ({q_minimum})"
                )

            validated_count += 1

    elif isinstance(question_schema, dict) and isinstance(chunk_schema, dict):
        sorted_keys = sorted(set(question_schema.keys()) & set(chunk_schema.keys()))
        for key in sorted_keys:
            q_elem = question_schema[key]
            c_elem = chunk_schema[key]

            if q_elem.get("type") is None:
                raise ValueError(
                    f"Task {provisional_task_id}: Question element '{key}' "
                    f"has missing type field"
                )
            if c_elem.get("type") is None:
                raise ValueError(
                    f"Task {provisional_task_id}: Chunk element '{key}' "
                    f"has missing type field"
                )

            if q_elem["type"] != c_elem["type"]:
                raise ValueError(
                    f"Task {provisional_task_id}: Type mismatch for key '{key}': "
                    f"question type '{q_elem['type']}' != chunk type '{c_elem['type']}'"
                )

            q_required = q_elem.get("required", False)
            c_required = c_elem.get("required", False)
            if q_required and not c_required:
                raise ValueError(
                    f"Task {provisional_task_id}: Required field mismatch for key '{key}': "
                    f"question requires element but chunk marks it optional"
                )

            q_minimum = q_elem.get("minimum", 0)
            c_minimum = c_elem.get("minimum", 0)
            if c_minimum < q_minimum:
                raise ValueError(
                    f"Task {provisional_task_id}: Threshold mismatch for key '{key}': "
                    f"chunk minimum ({c_minimum}) is lower than question minimum ({q_minimum})"
                )

            validated_count += 1

    return validated_count


def _validate_schema(question: dict[str, Any], chunk: dict[str, Any]) -> None:
    """Validate schema compatibility between question and chunk expected_elements.

    Performs shallow equality check and validates semantic constraints:
    - Asymmetric required field implication: if question element is required,
      chunk element must also be required
    - Minimum threshold ordering: chunk minimum must be >= question minimum

    Args:
        question: Question dict with expected_elements field
        chunk: Chunk dict with expected_elements field

    Raises:
        ValueError: If schema mismatch, required field implication violation,
                   or minimum threshold ordering violation detected
    """
    question_id = question.get("question_id", "UNKNOWN")
    q_elements = question.get("expected_elements", [])
    c_elements = chunk.get("expected_elements", [])

    if q_elements != c_elements:
        raise ValueError(
            f"Schema mismatch for question {question_id}: "
            f"expected_elements differ between question and chunk.\n"
            f"Question schema: {q_elements}\n"
            f"Chunk schema: {c_elements}"
        )

    if not isinstance(q_elements, list) or not isinstance(c_elements, list):
        return

    if len(q_elements) != len(c_elements):
        return

    for idx, (q_elem, c_elem) in enumerate(zip(q_elements, c_elements, strict=True)):
        if not isinstance(q_elem, dict) or not isinstance(c_elem, dict):
            continue

        q_required = q_elem.get("required", False)
        c_required = c_elem.get("required", False)

        if q_required and not c_required:
            element_type = q_elem.get("type", f"element_at_index_{idx}")
            raise ValueError(
                f"Required-field implication violation for question {question_id}: "
                f"element type '{element_type}' at index {idx} is required in question "
                f"but marked as optional in chunk"
            )

        q_minimum = q_elem.get("minimum", 0)
        c_minimum = c_elem.get("minimum", 0)

        if isinstance(q_minimum, (int, float)) and isinstance(c_minimum, (int, float)):
            if c_minimum < q_minimum:
                element_type = q_elem.get("type", f"element_at_index_{idx}")
                raise ValueError(
                    f"Minimum threshold ordering violation for question {question_id}: "
                    f"element type '{element_type}' at index {idx} has "
                    f"chunk minimum ({c_minimum}) < question minimum ({q_minimum})"
                )


def _construct_task(
    question: dict[str, Any],
    routing_result: ChunkRoutingResult,
    applicable_patterns: tuple[Any, ...],
    resolved_signals: tuple[Any, ...],
    generated_task_ids: set[str],
    correlation_id: str,
) -> ExecutableTask:
    question_id = question.get("question_id", "UNKNOWN")
    question_global = question.get("question_global")

    if question_global is None:
        raise ValueError(
            f"Task construction failure for {question_id}: "
            "question_global field missing or None"
        )

    if not isinstance(question_global, int):
        raise ValueError(
            f"Task construction failure for {question_id}: "
            f"question_global must be an integer, got {type(question_global).__name__}"
        )

    if not (0 <= question_global <= MAX_QUESTION_GLOBAL):
        raise ValueError(
            f"Task construction failure for {question_id}: "
            f"question_global must be in range 0-{MAX_QUESTION_GLOBAL}, got {question_global}"
        )

    task_id = f"MQC-{question_global:03d}_{routing_result.policy_area_id}"

    if task_id in generated_task_ids:
        raise ValueError(f"Duplicate task_id detected: {task_id}")

    generated_task_ids.add(task_id)

    patterns_list = (
        list(applicable_patterns)
        if not isinstance(applicable_patterns, list)
        else applicable_patterns
    )

    signals_dict = {}
    for signal in resolved_signals:
        if isinstance(signal, dict) and "signal_type" in signal:
            signals_dict[signal["signal_type"]] = signal
        elif hasattr(signal, "signal_type"):
            signals_dict[signal.signal_type] = signal

    expected_elements = question.get("expected_elements", [])
    expected_elements_list = (
        list(expected_elements) if isinstance(expected_elements, list | tuple) else []
    )

    document_position = routing_result.document_position

    metadata = {
        "base_slot": question.get("base_slot", ""),
        "cluster_id": question.get("cluster_id", ""),
        "document_position": document_position,
        "synchronizer_version": "2.0.0",
        "correlation_id": correlation_id,
        "original_pattern_count": len(applicable_patterns),
        "original_signal_count": len(resolved_signals),
        "filtered_pattern_count": len(patterns_list),
        "resolved_signal_count": len(signals_dict),
        "schema_element_count": len(expected_elements_list),
    }

    creation_timestamp = datetime.now(timezone.utc).isoformat()

    dimension_id = (
        routing_result.dimension_id
        if routing_result.dimension_id
        else question.get("dimension_id", "")
    )

    try:
        task = ExecutableTask(
            task_id=task_id,
            question_id=question.get("question_id", ""),
            question_global=question_global,
            policy_area_id=routing_result.policy_area_id,
            dimension_id=dimension_id,
            chunk_id=routing_result.chunk_id,
            patterns=patterns_list,
            signals=signals_dict,
            creation_timestamp=creation_timestamp,
            expected_elements=expected_elements_list,
            metadata=metadata,
        )
    except TypeError as e:
        raise ValueError(
            f"Task construction failed for {task_id}: dataclass validation error - {e}"
        ) from e

    logger.debug(
        f"Constructed task: task_id={task_id}, question_id={question_id}, "
        f"chunk_id={routing_result.chunk_id}, pattern_count={len(patterns_list)}, "
        f"signal_count={len(signals_dict)}"
    )

    return task


def _construct_task_legacy(
    question: dict[str, Any],
    chunk: dict[str, Any],
    patterns: list[dict[str, Any]],
    signals: dict[str, Any],
    generated_task_ids: set[str],
    routing_result: RoutingResult,
) -> ExecutableTask:
    question_global = question.get("question_global")

    if not isinstance(question_global, int) or not (
        0 <= question_global <= MAX_QUESTION_GLOBAL
    ):
        raise ValueError(
            f"Invalid question_global: {question_global}. "
            f"Must be an integer in range 0-{MAX_QUESTION_GLOBAL}."
        )

    policy_area_id = routing_result.policy_area_id

    if question_global is None:
        raise ValueError("question_global is required")

    if not isinstance(question_global, int):
        raise ValueError(
            f"question_global must be an integer, got {type(question_global).__name__}"
        )

    if not (0 <= question_global <= MAX_QUESTION_GLOBAL):
        raise ValueError(
            f"question_global must be between 0 and {MAX_QUESTION_GLOBAL} inclusive, got {question_global}"
        )

    task_id = f"MQC-{question_global:03d}_{policy_area_id}"

    if task_id in generated_task_ids:
        question_id = question.get("question_id", "")
        raise ValueError(
            f"Duplicate task_id detected: {task_id} for question {question_id}"
        )

    generated_task_ids.add(task_id)

    creation_timestamp = datetime.now(timezone.utc).isoformat()

    expected_elements = question.get("expected_elements", [])
    expected_elements_list = (
        list(expected_elements) if isinstance(expected_elements, list | tuple) else []
    )
    patterns_list = list(patterns) if isinstance(patterns, list | tuple) else []

    signals_dict = dict(signals) if isinstance(signals, dict) else {}

    metadata = {
        "base_slot": question.get("base_slot", ""),
        "cluster_id": question.get("cluster_id", ""),
        "document_position": None,
        "synchronizer_version": "2.0.0",
        "correlation_id": "",
        "original_pattern_count": len(patterns_list),
        "original_signal_count": len(signals_dict),
        "filtered_pattern_count": len(patterns_list),
        "resolved_signal_count": len(signals_dict),
        "schema_element_count": len(expected_elements_list),
    }

    try:
        task = ExecutableTask(
            task_id=task_id,
            question_id=question.get("question_id", ""),
            question_global=question_global,
            policy_area_id=policy_area_id,
            dimension_id=question.get("dimension_id", ""),
            chunk_id=chunk.get("id", ""),
            patterns=patterns_list,
            signals=signals_dict,
            creation_timestamp=creation_timestamp,
            expected_elements=expected_elements_list,
            metadata=metadata,
        )
    except TypeError as e:
        raise ValueError(
            f"Task construction failed for {task_id}: dataclass validation error - {e}"
        ) from e

    return task
