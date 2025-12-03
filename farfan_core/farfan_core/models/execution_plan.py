"""
Core immutable data models for execution plan management.

Provides frozen dataclasses for task and execution plan representation with
deterministic integrity verification and strict immutability guarantees.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

REQUIRED_TASK_COUNT = 300


@dataclass(frozen=True)
class ExecutableTask:
    """
    Immutable task representation for execution planning.

    Enforces immutability through frozen=True and tuple-based collections
    to ensure deterministic execution and provenance tracking.
    """

    task_id: str
    micro_question_context: str
    target_chunk: str
    applicable_patterns: tuple[str, ...]
    resolved_signals: tuple[str, ...]
    creation_timestamp: float
    synchronizer_version: str


@dataclass(frozen=True)
class ExecutionPlan:
    """
    Immutable execution plan containing exactly 300 tasks.

    Enforces the 300-question analysis contract (D1-D6 dimensions × PA01-PA10 areas)
    with duplicate detection and cryptographic integrity verification.
    """

    plan_id: str
    tasks: tuple[ExecutableTask, ...]
    metadata: dict[str, Any] = field(default_factory=dict)  # type: ignore[misc]

    def __post_init__(self) -> None:
        if len(self.tasks) != REQUIRED_TASK_COUNT:
            raise ValueError(
                f"ExecutionPlan requires exactly {REQUIRED_TASK_COUNT} tasks, got {len(self.tasks)}"
            )

        task_ids = [task.task_id for task in self.tasks]
        if len(task_ids) != len(set(task_ids)):
            seen: set[str] = set()
            duplicates: set[str] = set()
            for task_id in task_ids:
                if task_id in seen:
                    duplicates.add(task_id)
                seen.add(task_id)
            raise ValueError(
                f"ExecutionPlan contains duplicate task_ids: {sorted(duplicates)}"
            )

    def compute_integrity_hash(self) -> str:
        """
        Compute deterministic SHA256 hash of serialized task list.

        Returns:
            Hexadecimal SHA256 hash string of JSON-serialized tasks.
        """
        task_data = [
            {
                "task_id": task.task_id,
                "micro_question_context": task.micro_question_context,
                "target_chunk": task.target_chunk,
                "applicable_patterns": list(task.applicable_patterns),
                "resolved_signals": list(task.resolved_signals),
                "creation_timestamp": task.creation_timestamp,
                "synchronizer_version": task.synchronizer_version,
            }
            for task in self.tasks
        ]

        serialized = json.dumps(task_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
