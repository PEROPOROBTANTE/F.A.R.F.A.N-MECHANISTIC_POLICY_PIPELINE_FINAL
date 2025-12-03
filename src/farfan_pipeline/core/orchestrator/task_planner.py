import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

EXPECTED_TASKS_PER_CHUNK = 5
EXPECTED_TASKS_PER_POLICY_AREA = 30


@dataclass
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
    expected_elements: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def _validate_schema(question: dict[str, Any], chunk: dict[str, Any]) -> None:
    q_elements = question.get("expected_elements", [])
    c_elements = chunk.get("expected_elements", [])

    if q_elements != c_elements:
        raise ValueError(
            f"Schema mismatch for question {question.get('question_id', 'UNKNOWN')}:\n"
            f"Question schema: {q_elements}\n"
            f"Chunk schema: {c_elements}"
        )


def _construct_task(
    question: dict[str, Any],
    chunk: dict[str, Any],
    patterns: list[dict[str, Any]],
    signals: dict[str, Any],
    generated_ids: set[str],
) -> ExecutableTask:
    question_global = question.get("question_global")
    policy_area_id = question.get("policy_area_id")

    task_id = f"MQC-{question_global:03d}_{policy_area_id}"

    if task_id in generated_ids:
        raise ValueError(f"Duplicate task_id detected: {task_id}")

    generated_ids.add(task_id)

    task = ExecutableTask(
        task_id=task_id,
        question_id=question.get("question_id", ""),
        question_global=question_global,
        policy_area_id=policy_area_id,
        dimension_id=question.get("dimension_id", ""),
        chunk_id=chunk.get("id", ""),
        patterns=patterns,
        signals=signals,
        creation_timestamp=datetime.now(timezone.utc).isoformat(),
        expected_elements=question.get("expected_elements", []),
        metadata={
            "base_slot": question.get("base_slot", ""),
            "cluster_id": question.get("cluster_id", ""),
        },
    )

    return task


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
