import logging
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from types import MappingProxyType, UnionType
from typing import Any, Protocol, Union, get_type_hints

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ChunkRoutingResult:
    policy_area_id: str
    chunk_id: str
    expected_elements: list[Any]


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
    patterns: tuple[dict[str, Any], ...]
    signals: MappingProxyType[str, Any]
    creation_timestamp: str
    expected_elements: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    metadata: MappingProxyType[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    context: MicroQuestionContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.patterns, tuple):
            object.__setattr__(self, "patterns", tuple(self.patterns))
        if not isinstance(self.signals, MappingProxyType):
            object.__setattr__(self, "signals", MappingProxyType(dict(self.signals)))
        if not isinstance(self.expected_elements, tuple):
            object.__setattr__(self, "expected_elements", tuple(self.expected_elements))
        if not isinstance(self.metadata, MappingProxyType):
            object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

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
    q_elements = question.get("expected_elements", [])
    c_elements = chunk.get("expected_elements", [])

    if q_elements != c_elements:
        raise ValueError(
            f"Schema mismatch for question {question.get('question_id', 'UNKNOWN')}:\n"
            f"Question schema: {q_elements}\n"
            f"Chunk schema: {c_elements}"
        )

    if not isinstance(q_elements, list) or not isinstance(c_elements, list):
        return

    if len(q_elements) != len(c_elements):
        return

    for q_elem, c_elem in zip(q_elements, c_elements, strict=True):
        if not isinstance(q_elem, dict) or not isinstance(c_elem, dict):
            continue

        q_required = q_elem.get("required", False)
        c_required = c_elem.get("required", False)

        if not ((not q_required) or c_required):
            element_type = q_elem.get("type", "UNKNOWN")
            raise ValueError(
                f"Required-field implication violation for question {question.get('question_id', 'UNKNOWN')}: "
                f"element type '{element_type}' is required in question but not in chunk"
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

    patterns = list(applicable_patterns)
    signals = {signal.signal_type: signal for signal in resolved_signals}
    creation_timestamp = datetime.now(timezone.utc).isoformat()
    expected_elements = routing_result.expected_elements

    context = MicroQuestionContext(
        task_id=task_id,
        question_id=question.get("question_id", ""),
        question_global=question_global,
        policy_area_id=routing_result.policy_area_id,
        dimension_id=question.get("dimension_id", ""),
        chunk_id=routing_result.chunk_id,
        base_slot=question.get("base_slot", ""),
        cluster_id=question.get("cluster_id", ""),
        patterns=applicable_patterns,
        signals=signals,
        expected_elements=tuple(expected_elements),
        signal_requirements=question.get("signal_requirements", {}),
        creation_timestamp=creation_timestamp,
    )

    assembled_fields = {
        "task_id": task_id,
        "question_id": question.get("question_id", ""),
        "question_global": question_global,
        "policy_area_id": routing_result.policy_area_id,
        "dimension_id": question.get("dimension_id", ""),
        "chunk_id": routing_result.chunk_id,
        "patterns": tuple(patterns),
        "signals": MappingProxyType(signals),
        "creation_timestamp": creation_timestamp,
        "expected_elements": tuple(expected_elements),
        "metadata": MappingProxyType(
            {
                "base_slot": question.get("base_slot", ""),
                "cluster_id": question.get("cluster_id", ""),
                "correlation_id": correlation_id,
            }
        ),
        "context": context,
    }

    type_hints = get_type_hints(ExecutableTask)

    for dataclass_field in fields(ExecutableTask):
        field_name = dataclass_field.name
        field_type = type_hints.get(field_name, dataclass_field.type)

        is_optional = (
            hasattr(field_type, "__origin__")
            and field_type.__origin__ is Union
            and type(None) in field_type.__args__
        ) or (
            isinstance(field_type, UnionType)
            and type(None) in getattr(field_type, "__args__", ())
        )

        if not is_optional:
            field_value = assembled_fields.get(field_name)
            if field_value is None:
                raise ValueError(
                    f"Mandatory field '{field_name}' cannot be None for task {task_id}"
                )

    task = ExecutableTask(**assembled_fields)

    logger.debug(
        "Task constructed",
        extra={
            "task_id": task.task_id,
            "question_id": task.question_id,
            "question_global": task.question_global,
            "policy_area_id": task.policy_area_id,
            "chunk_id": task.chunk_id,
            "correlation_id": correlation_id,
        },
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

    if not isinstance(question_global, int) or not (0 <= question_global <= 999):
        raise ValueError(
            f"Invalid question_global: {question_global}. "
            f"Must be an integer in range 0-999."
        )

    policy_area_id = routing_result.policy_area_id

    if question_global is None:
        raise ValueError("question_global is required")

    if not isinstance(question_global, int):
        raise ValueError(
            f"question_global must be an integer, got {type(question_global).__name__}"
        )

    if not (0 <= question_global <= 999):
        raise ValueError(
            f"question_global must be between 0 and 999 inclusive, got {question_global}"
        )

    task_id = f"MQC-{question_global:03d}_{policy_area_id}"

    if task_id in generated_task_ids:
        question_id = question.get("question_id", "")
        raise ValueError(
            f"Duplicate task_id detected: {task_id} for question {question_id}"
        )

    generated_task_ids.add(task_id)

    creation_timestamp = datetime.now(timezone.utc).isoformat()

    context = MicroQuestionContext(
        task_id=task_id,
        question_id=question.get("question_id", ""),
        question_global=question_global,
        policy_area_id=policy_area_id,
        dimension_id=question.get("dimension_id", ""),
        chunk_id=chunk.get("id", ""),
        base_slot=question.get("base_slot", ""),
        cluster_id=question.get("cluster_id", ""),
        patterns=tuple(patterns),
        signals=signals,
        expected_elements=tuple(question.get("expected_elements", [])),
        signal_requirements=question.get("signal_requirements", {}),
        creation_timestamp=creation_timestamp,
    )

    expected_elements = question.get("expected_elements", [])
    expected_elements_tuple = (
        tuple(expected_elements)
        if isinstance(expected_elements, list)
        else expected_elements
    )
    patterns_tuple = tuple(patterns) if isinstance(patterns, list) else patterns

    task = ExecutableTask(
        task_id=task_id,
        question_id=question.get("question_id", ""),
        question_global=question_global,
        policy_area_id=policy_area_id,
        dimension_id=question.get("dimension_id", ""),
        chunk_id=chunk.get("id", ""),
        patterns=patterns_tuple,
        signals=(
            MappingProxyType(signals)
            if not isinstance(signals, MappingProxyType)
            else signals
        ),
        creation_timestamp=creation_timestamp,
        expected_elements=expected_elements_tuple,
        metadata=MappingProxyType(
            {
                "base_slot": question.get("base_slot", ""),
                "cluster_id": question.get("cluster_id", ""),
            }
        ),
        context=context,
    )

    return task


def extract_expected_elements(context: MicroQuestionContext) -> list[dict[str, Any]]:
    return [
        dict(elem) if isinstance(elem, dict) else elem
        for elem in context.expected_elements
    ]


def extract_signal_requirements(context: MicroQuestionContext) -> dict[str, Any]:
    if isinstance(context.signal_requirements, MappingProxyType):
        return dict(context.signal_requirements)
    if isinstance(context.signal_requirements, dict):
        return context.signal_requirements
    return {}


def sort_micro_question_contexts(
    contexts: list[MicroQuestionContext],
) -> list[MicroQuestionContext]:
    return sorted(
        contexts,
        key=lambda ctx: (
            ctx.dimension_id,
            ctx.policy_area_id,
            ctx.question_global,
        ),
    )


def _validate_cross_task(plan: list[ExecutableTask]) -> None:
    chunk_usage: dict[str, int] = {}
    policy_area_usage: dict[str, int] = {}

    for task in plan:
        chunk_id = task.chunk_id
        chunk_usage[chunk_id] = chunk_usage.get(chunk_id, 0) + 1

        policy_area_id = task.policy_area_id
        policy_area_usage[policy_area_id] = policy_area_usage.get(policy_area_id, 0) + 1

    for chunk_id, count in chunk_usage.items():
        if count != EXPECTED_TASKS_PER_CHUNK:
            logger.warning(
                f"Chunk usage deviation: chunk {chunk_id} used {count} times "
                f"(expected {EXPECTED_TASKS_PER_CHUNK})"
            )

    for policy_area_id, count in policy_area_usage.items():
        if count != EXPECTED_TASKS_PER_POLICY_AREA:
            logger.warning(
                f"Policy area usage deviation: {policy_area_id} used {count} times "
                f"(expected {EXPECTED_TASKS_PER_POLICY_AREA})"
            )
