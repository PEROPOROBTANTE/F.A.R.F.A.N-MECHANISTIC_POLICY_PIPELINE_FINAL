"""
Core immutable data models for execution plan management.

Provides frozen dataclasses for task and execution plan representation with
deterministic integrity verification and strict immutability guarantees.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_TASK_COUNT = 300

logger = logging.getLogger(__name__)


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


class ExecutionPlanManager:
    """
    Manager for execution plan persistence with atomic index updates.

    Provides archival operations with transactional integrity and rollback
    support for plan storage operations.
    """

    def __init__(self, storage_dir: Path, index_file: Path | None = None) -> None:
        """
        Initialize ExecutionPlanManager with storage paths.

        Args:
            storage_dir: Directory for storing execution plan files
            index_file: Optional path to index file (defaults to storage_dir/plans.jsonl)
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = (
            Path(index_file) if index_file else self.storage_dir / "plans.jsonl"
        )

    def _archive_to_storage(
        self, plan: ExecutionPlan, correlation_id: str | None = None
    ) -> ExecutionPlan:
        """
        Archive execution plan with atomic index update and transactional rollback.

        Implements atomic write operation with three-phase commit:
        1. Write plan file to storage
        2. Append index entry to JSON Lines file
        3. Verify file integrity

        Rollback triggers:
        - If index write fails: delete plan file via storage_path.unlink()
        - If file verification fails: remove index entry

        Args:
            plan: ExecutionPlan instance to archive
            correlation_id: Optional correlation ID for tracking

        Returns:
            Unmodified ExecutionPlan instance for immediate execution or disposal

        Raises:
            ValueError: If plan archival fails
            OSError: If file system operations fail
        """
        created_at = datetime.now(timezone.utc).isoformat()
        task_count = len(plan.tasks)
        integrity_hash = plan.compute_integrity_hash()
        correlation_id_value = correlation_id or "unknown"

        storage_filename = f"{plan.plan_id}_{created_at.replace(':', '-')}.json"
        storage_path = self.storage_dir / storage_filename

        try:
            plan_data = {
                "plan_id": plan.plan_id,
                "tasks": [
                    {
                        "task_id": task.task_id,
                        "micro_question_context": task.micro_question_context,
                        "target_chunk": task.target_chunk,
                        "applicable_patterns": list(task.applicable_patterns),
                        "resolved_signals": list(task.resolved_signals),
                        "creation_timestamp": task.creation_timestamp,
                        "synchronizer_version": task.synchronizer_version,
                    }
                    for task in plan.tasks
                ],
                "metadata": plan.metadata,
                "created_at": created_at,
                "integrity_hash": integrity_hash,
                "correlation_id": correlation_id_value,
            }

            storage_path.write_text(json.dumps(plan_data, indent=2), encoding="utf-8")

        except OSError as e:
            logger.error(
                json.dumps(
                    {
                        "event": "execution_plan_archive_failed",
                        "plan_id": plan.plan_id,
                        "error": str(e),
                        "phase": "plan_file_write",
                        "correlation_id": correlation_id_value,
                    }
                )
            )
            raise ValueError(
                f"Failed to write plan file for {plan.plan_id}: {e}"
            ) from e

        index_entry = {
            "plan_id": plan.plan_id,
            "storage_path": str(storage_path),
            "created_at": created_at,
            "task_count": task_count,
            "integrity_hash": integrity_hash,
            "correlation_id": correlation_id_value,
        }

        try:
            with self.index_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(index_entry) + "\n")

        except OSError as e:
            try:
                storage_path.unlink()
                logger.warning(
                    json.dumps(
                        {
                            "event": "execution_plan_archive_rollback",
                            "plan_id": plan.plan_id,
                            "reason": "index_write_failed",
                            "rollback_action": "plan_file_deleted",
                            "correlation_id": correlation_id_value,
                        }
                    )
                )
            except OSError as unlink_error:
                logger.error(
                    json.dumps(
                        {
                            "event": "execution_plan_archive_rollback_failed",
                            "plan_id": plan.plan_id,
                            "error": str(unlink_error),
                            "correlation_id": correlation_id_value,
                        }
                    )
                )

            logger.error(
                json.dumps(
                    {
                        "event": "execution_plan_archive_failed",
                        "plan_id": plan.plan_id,
                        "error": str(e),
                        "phase": "index_write",
                        "correlation_id": correlation_id_value,
                    }
                )
            )
            raise ValueError(
                f"Failed to write index entry for {plan.plan_id}: {e}"
            ) from e

        try:
            if not storage_path.exists():
                raise ValueError(f"Plan file verification failed: {storage_path}")

            file_size = storage_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"Plan file is empty: {storage_path}")

        except (OSError, ValueError) as e:
            try:
                self._remove_index_entry(plan.plan_id)
                logger.warning(
                    json.dumps(
                        {
                            "event": "execution_plan_archive_rollback",
                            "plan_id": plan.plan_id,
                            "reason": "file_verification_failed",
                            "rollback_action": "index_entry_removed",
                            "correlation_id": correlation_id_value,
                        }
                    )
                )
            except Exception as rollback_error:
                logger.error(
                    json.dumps(
                        {
                            "event": "execution_plan_archive_rollback_failed",
                            "plan_id": plan.plan_id,
                            "error": str(rollback_error),
                            "correlation_id": correlation_id_value,
                        }
                    )
                )

            logger.error(
                json.dumps(
                    {
                        "event": "execution_plan_archive_failed",
                        "plan_id": plan.plan_id,
                        "error": str(e),
                        "phase": "file_verification",
                        "correlation_id": correlation_id_value,
                    }
                )
            )
            raise ValueError(f"File verification failed for {plan.plan_id}: {e}") from e

        logger.info(
            json.dumps(
                {
                    "event": "execution_plan_archived",
                    "plan_id": plan.plan_id,
                    "storage_path": str(storage_path),
                    "created_at": created_at,
                    "task_count": task_count,
                    "integrity_hash": integrity_hash,
                    "correlation_id": correlation_id_value,
                }
            )
        )

        return plan

    def _remove_index_entry(self, plan_id: str) -> None:
        """
        Remove index entry for given plan_id.

        Rewrites index file excluding the entry with matching plan_id.

        Args:
            plan_id: Plan ID to remove from index
        """
        if not self.index_file.exists():
            return

        lines = []
        try:
            with self.index_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
        except OSError as e:
            logger.error(f"Failed to read index file for removal: {e}")
            raise

        filtered_lines = []
        for line in lines:
            try:
                entry = json.loads(line.strip())
                if entry.get("plan_id") != plan_id:
                    filtered_lines.append(line)
            except json.JSONDecodeError:
                filtered_lines.append(line)

        try:
            with self.index_file.open("w", encoding="utf-8") as f:
                f.writelines(filtered_lines)
        except OSError as e:
            logger.error(f"Failed to rewrite index file: {e}")
            raise
