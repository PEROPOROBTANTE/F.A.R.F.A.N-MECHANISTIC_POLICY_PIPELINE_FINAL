"""
Unit tests for execution plan immutable data models.
"""

import time
from dataclasses import FrozenInstanceError

import pytest

from farfan_core.farfan_core.models.execution_plan import (
    REQUIRED_TASK_COUNT,
    ExecutableTask,
    ExecutionPlan,
)

SHA256_HEX_LENGTH = 64


class TestExecutableTaskImmutability:
    """Test suite for ExecutableTask immutability guarantees."""

    def test_executable_task_immutability(self) -> None:
        """Verify FrozenInstanceError on modification attempts."""
        task = ExecutableTask(
            task_id="T001",
            micro_question_context="Does policy address climate change?",
            target_chunk="chunk_001",
            applicable_patterns=("pattern_A", "pattern_B"),
            resolved_signals=("signal_X", "signal_Y"),
            creation_timestamp=time.time(),
            synchronizer_version="v1.0.0",
        )

        with pytest.raises(FrozenInstanceError):
            task.task_id = "T002"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            task.micro_question_context = "Modified context"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            task.target_chunk = "chunk_002"  # type: ignore[misc]

        with pytest.raises(FrozenInstanceError):
            task.creation_timestamp = time.time()  # type: ignore[misc]

    def test_tuple_fields_are_immutable(self) -> None:
        """Verify tuple fields cannot be modified."""
        task = ExecutableTask(
            task_id="T001",
            micro_question_context="Test context",
            target_chunk="chunk_001",
            applicable_patterns=("pattern_A", "pattern_B"),
            resolved_signals=("signal_X",),
            creation_timestamp=time.time(),
            synchronizer_version="v1.0.0",
        )

        with pytest.raises((AttributeError, TypeError)):
            task.applicable_patterns[0] = "modified"  # type: ignore[index]

        with pytest.raises((AttributeError, TypeError)):
            task.resolved_signals.append("signal_Z")  # type: ignore[attr-defined]


class TestExecutionPlanTaskCount:
    """Test suite for 300-task enforcement."""

    def test_execution_plan_rejects_wrong_task_count(self) -> None:
        """Verify ValueError for non-300 task counts."""
        tasks_299 = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
            for i in range(299)
        )

        with pytest.raises(ValueError, match="requires exactly 300 tasks, got 299"):
            ExecutionPlan(plan_id="PLAN_299", tasks=tasks_299)

        tasks_301 = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
            for i in range(301)
        )

        with pytest.raises(ValueError, match="requires exactly 300 tasks, got 301"):
            ExecutionPlan(plan_id="PLAN_301", tasks=tasks_301)

    def test_execution_plan_accepts_exactly_300_tasks(self) -> None:
        """Verify acceptance of exactly 300 tasks."""
        tasks_300 = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        plan = ExecutionPlan(plan_id="PLAN_300", tasks=tasks_300)
        assert len(plan.tasks) == REQUIRED_TASK_COUNT
        assert plan.plan_id == "PLAN_300"


class TestExecutionPlanDuplicateDetection:
    """Test suite for duplicate task_id detection."""

    def test_execution_plan_rejects_duplicate_task_ids(self) -> None:
        """Verify ValueError for duplicate task_ids."""
        tasks_with_duplicates = []
        for i in range(298):
            tasks_with_duplicates.append(
                ExecutableTask(
                    task_id=f"T{i:03d}",
                    micro_question_context=f"Question {i}",
                    target_chunk=f"chunk_{i:03d}",
                    applicable_patterns=("pattern_A",),
                    resolved_signals=("signal_X",),
                    creation_timestamp=time.time(),
                    synchronizer_version="v1.0.0",
                )
            )

        tasks_with_duplicates.append(
            ExecutableTask(
                task_id="T000",
                micro_question_context="Duplicate question",
                target_chunk="chunk_dup1",
                applicable_patterns=("pattern_B",),
                resolved_signals=("signal_Y",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
        )

        tasks_with_duplicates.append(
            ExecutableTask(
                task_id="T001",
                micro_question_context="Another duplicate",
                target_chunk="chunk_dup2",
                applicable_patterns=("pattern_C",),
                resolved_signals=("signal_Z",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
        )

        with pytest.raises(
            ValueError, match=r"contains duplicate task_ids.*\['T000', 'T001'\]"
        ):
            ExecutionPlan(plan_id="PLAN_DUP", tasks=tuple(tasks_with_duplicates))

    def test_execution_plan_accepts_unique_task_ids(self) -> None:
        """Verify acceptance of all unique task_ids."""
        tasks_unique = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        plan = ExecutionPlan(plan_id="PLAN_UNIQUE", tasks=tasks_unique)
        task_ids = {task.task_id for task in plan.tasks}
        assert len(task_ids) == REQUIRED_TASK_COUNT


class TestExecutionPlanIntegrityHash:
    """Test suite for integrity hash computation."""

    def test_execution_plan_integrity_hash_is_deterministic(self) -> None:
        """Verify hash determinism across multiple computations."""
        tasks = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A", "pattern_B"),
                resolved_signals=("signal_X", "signal_Y"),
                creation_timestamp=1234567890.0 + i,
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        plan = ExecutionPlan(plan_id="PLAN_HASH", tasks=tasks)

        hash1 = plan.compute_integrity_hash()
        hash2 = plan.compute_integrity_hash()
        hash3 = plan.compute_integrity_hash()

        assert hash1 == hash2 == hash3
        assert len(hash1) == SHA256_HEX_LENGTH
        assert all(c in "0123456789abcdef" for c in hash1)

    def test_different_task_order_produces_different_hash(self) -> None:
        """Verify hash changes with task ordering."""
        base_tasks = [
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=1234567890.0,
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        ]

        plan1 = ExecutionPlan(plan_id="PLAN_ORDER1", tasks=tuple(base_tasks))
        plan2 = ExecutionPlan(
            plan_id="PLAN_ORDER2",
            tasks=tuple(reversed(base_tasks)),
        )

        hash1 = plan1.compute_integrity_hash()
        hash2 = plan2.compute_integrity_hash()

        assert hash1 != hash2

    def test_different_task_content_produces_different_hash(self) -> None:
        """Verify hash changes with task content modifications."""
        tasks1 = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context="Context A",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=1234567890.0,
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        tasks2 = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context="Context B",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=1234567890.0,
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        plan1 = ExecutionPlan(plan_id="PLAN_CONTENT1", tasks=tasks1)
        plan2 = ExecutionPlan(plan_id="PLAN_CONTENT2", tasks=tasks2)

        hash1 = plan1.compute_integrity_hash()
        hash2 = plan2.compute_integrity_hash()

        assert hash1 != hash2

    def test_hash_is_sha256_format(self) -> None:
        """Verify hash conforms to SHA256 format."""
        tasks = tuple(
            ExecutableTask(
                task_id=f"T{i:03d}",
                micro_question_context=f"Question {i}",
                target_chunk=f"chunk_{i:03d}",
                applicable_patterns=("pattern_A",),
                resolved_signals=("signal_X",),
                creation_timestamp=time.time(),
                synchronizer_version="v1.0.0",
            )
            for i in range(300)
        )

        plan = ExecutionPlan(plan_id="PLAN_SHA256", tasks=tasks)
        integrity_hash = plan.compute_integrity_hash()

        assert isinstance(integrity_hash, str)
        assert len(integrity_hash) == SHA256_HEX_LENGTH
        int(integrity_hash, 16)
