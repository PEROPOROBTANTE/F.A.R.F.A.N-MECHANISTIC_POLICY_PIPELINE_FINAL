"""
Phase 8: Execution Plan Assembly - Deterministic Plan Construction with Integrity Verification
================================================================================================

This module implements Phase 8 of the canonical pipeline:
    Phase 7 Task Construction Output → ExecutionPlan → Phase 9+ Execution

Responsibilities:
-----------------
1. Assemble validated ExecutableTask instances into ExecutionPlan
2. Verify exactly 300 tasks are present (canonical contract)
3. Compute cryptographic integrity hash (BLAKE3 or SHA256)
4. Detect duplicate task IDs across the complete plan
5. Validate execution dependencies and ordering constraints
6. Generate execution metadata and provenance information
7. Establish error propagation semantics to downstream phases

Input Contract (from Phase 7):
-------------------------------
Phase7TaskConstructionOutput:
    - tasks: List[ExecutableTask] (validated instances)
    - task_count: int (must equal 300)
    - construction_passed: bool (must be True)
    - construction_errors: List[str]
    - construction_warnings: List[str]
    - duplicate_task_ids: List[str]
    - missing_fields_by_task: Dict[str, List[str]]
    - construction_timestamp: str
    - metadata: Dict[str, Any]

Output Contract (to Phase 9):
------------------------------
Phase8ExecutionPlanOutput:
    - execution_plan: ExecutionPlan | None
    - plan_id: str
    - task_count: int
    - assembly_passed: bool
    - assembly_errors: List[str]
    - assembly_warnings: List[str]
    - integrity_hash: str (BLAKE3 or SHA256)
    - duplicate_tasks: List[str]
    - assembly_timestamp: str
    - metadata: Dict[str, Any]

ExecutionPlan:
    - plan_id: str (unique identifier)
    - tasks: Tuple[ExecutableTask, ...] (immutable, length=300)
    - creation_timestamp: str (ISO 8601)
    - integrity_hash: str (cryptographic hash)
    - metadata: Dict[str, Any]

Phase 8 Sub-phases:
-------------------
8.1 Precondition Validation:
    - Input: Phase7TaskConstructionOutput
    - Process: Verify construction_passed=True, task_count=300
    - Output: validation_result: bool
    - Error Propagation: Failed precondition → assembly_passed=False

8.2 Duplicate Detection:
    - Input: tasks (from Phase 7)
    - Process: Check for duplicate task_ids across all tasks
    - Output: duplicate_list: List[str]
    - Error Propagation: Duplicates found → assembly_passed=False

8.3 Execution Plan Construction:
    - Input: validated tasks, plan_id
    - Process: Construct immutable ExecutionPlan with tuple conversion
    - Output: ExecutionPlan instance
    - Error Propagation: Construction failures → assembly_passed=False

8.4 Integrity Hash Computation:
    - Input: ExecutionPlan
    - Process: Compute BLAKE3/SHA256 hash of serialized task data
    - Output: integrity_hash: str
    - Error Propagation: Hash computation failures → assembly_warning

Integration Points:
-------------------
Phase 7 → Phase 8:
    - Contract: Phase7TaskConstructionOutput
    - Precondition: construction_passed must be True
    - Error: If False, Phase 8 returns None execution_plan with propagated errors

Phase 8 → Phase 9:
    - Contract: Phase8ExecutionPlanOutput
    - Precondition: assembly_passed must be True
    - Postcondition: execution_plan is not None, task_count=300
    - Error: If False, Phase 9+ abort with diagnostic error message

Error Propagation Semantics:
-----------------------------
1. Phase 7 construction failures → Phase 8 returns early with propagated errors
2. Task count != 300 → assembly_passed=False, execution_plan=None
3. Duplicate task IDs → assembly_passed=False, execution_plan=None
4. ExecutionPlan construction failures → assembly_passed=False, execution_plan=None
5. Integrity hash failures → assembly_warning (plan still usable)

All errors accumulate rather than fail-fast to provide complete diagnostics.

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-19
Version: 1.0.0
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from farfan_pipeline.core.orchestrator.task_planner import (
    ExecutableTask,  # noqa: TC001
)

logger = logging.getLogger(__name__)

PHASE8_VERSION = "1.0.0"
REQUIRED_TASK_COUNT = 300


@dataclass
class ExecutionPlan:
    """
    Immutable execution plan with exactly 300 tasks.

    Enforces the 300-question analysis contract (D1-D6 dimensions × PA01-PA10 areas)
    with cryptographic integrity verification.
    """

    plan_id: str
    tasks: tuple[ExecutableTask, ...]
    creation_timestamp: str
    integrity_hash: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        if len(self.tasks) != REQUIRED_TASK_COUNT:
            raise ValueError(
                f"ExecutionPlan requires exactly {REQUIRED_TASK_COUNT} tasks, "
                f"got {len(self.tasks)}"
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


@dataclass
class Phase7TaskConstructionOutput:
    """Input contract from Phase 7."""

    tasks: list[ExecutableTask]
    task_count: int
    construction_passed: bool
    construction_errors: list[str]
    construction_warnings: list[str]
    duplicate_task_ids: list[str]
    missing_fields_by_task: dict[str, list[str]]
    construction_timestamp: str
    metadata: dict[str, Any]


@dataclass
class Phase8ExecutionPlanOutput:
    """Output contract for Phase 8."""

    execution_plan: ExecutionPlan | None
    plan_id: str
    task_count: int
    assembly_passed: bool
    assembly_errors: list[str]
    assembly_warnings: list[str]
    integrity_hash: str
    duplicate_tasks: list[str]
    assembly_timestamp: str
    metadata: dict[str, Any]
    phase8_version: str = PHASE8_VERSION


def _validate_phase7_preconditions(
    phase7_output: Phase7TaskConstructionOutput,
    errors: list[str],
) -> bool:
    """
    Validate Phase 7 preconditions.

    Phase 8.1: Precondition Validation

    Args:
        phase7_output: Output from Phase 7
        errors: List to accumulate errors

    Returns:
        True if preconditions satisfied, False otherwise
    """
    preconditions_met = True

    if not phase7_output.construction_passed:
        errors.append(
            "Phase 7 construction failed; cannot proceed with execution plan assembly"
        )
        errors.extend(phase7_output.construction_errors)
        preconditions_met = False

    if phase7_output.task_count != REQUIRED_TASK_COUNT:
        errors.append(
            f"Phase 7 task count mismatch: expected {REQUIRED_TASK_COUNT}, "
            f"got {phase7_output.task_count}"
        )
        preconditions_met = False

    if not isinstance(phase7_output.tasks, list):
        errors.append(
            f"Phase 7 tasks has invalid type: expected list, "
            f"got {type(phase7_output.tasks).__name__}"
        )
        preconditions_met = False

    if phase7_output.duplicate_task_ids:
        errors.append(
            f"Phase 7 reported duplicate task IDs: {phase7_output.duplicate_task_ids}"
        )
        preconditions_met = False

    return preconditions_met


def _detect_duplicate_tasks(
    tasks: list[ExecutableTask],
) -> tuple[bool, list[str]]:
    """
    Detect duplicate task IDs in task list.

    Phase 8.2: Duplicate Detection

    Args:
        tasks: List of tasks to check

    Returns:
        Tuple of (has_duplicates, list_of_duplicate_ids)
    """
    seen: set[str] = set()
    duplicates: set[str] = set()

    for task in tasks:
        task_id = task.task_id
        if task_id in seen:
            duplicates.add(task_id)
        seen.add(task_id)

    return len(duplicates) > 0, sorted(duplicates)


def _compute_integrity_hash(
    tasks: tuple[ExecutableTask, ...],
    warnings: list[str],
) -> str:
    """
    Compute cryptographic integrity hash of task data.

    Phase 8.4: Integrity Hash Computation

    Uses SHA256 for deterministic serialization of task data.
    Failures produce warning and return empty string.

    Args:
        tasks: Tuple of tasks to hash
        warnings: List to accumulate warnings

    Returns:
        Hexadecimal hash string or empty string on failure
    """
    try:
        task_data = [
            {
                "task_id": task.task_id,
                "question_id": task.question_id,
                "question_global": task.question_global,
                "policy_area_id": task.policy_area_id,
                "dimension_id": task.dimension_id,
                "chunk_id": task.chunk_id,
                "creation_timestamp": task.creation_timestamp,
            }
            for task in tasks
        ]

        serialized = json.dumps(task_data, sort_keys=True, separators=(",", ":"))
        hash_value = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        logger.debug(f"Computed integrity hash: {hash_value[:16]}...")
        return hash_value

    except (TypeError, ValueError, AttributeError) as e:
        warning_msg = f"Integrity hash computation failed: {type(e).__name__}: {e}"
        warnings.append(warning_msg)
        logger.warning(warning_msg)
        return ""


def _construct_execution_plan(
    plan_id: str,
    tasks: list[ExecutableTask],
    errors: list[str],
    warnings: list[str],
) -> ExecutionPlan | None:
    """
    Construct immutable ExecutionPlan instance.

    Phase 8.3: Execution Plan Construction

    Args:
        plan_id: Unique plan identifier
        tasks: List of validated tasks
        errors: List to accumulate errors
        warnings: List to accumulate warnings

    Returns:
        ExecutionPlan instance or None if construction failed
    """
    try:
        tasks_tuple = tuple(tasks)

        creation_timestamp = datetime.now(timezone.utc).isoformat()

        integrity_hash = _compute_integrity_hash(tasks_tuple, warnings)

        metadata = {
            "phase8_version": PHASE8_VERSION,
            "task_count": len(tasks_tuple),
            "has_integrity_hash": bool(integrity_hash),
            "creation_timestamp": creation_timestamp,
        }

        execution_plan = ExecutionPlan(
            plan_id=plan_id,
            tasks=tasks_tuple,
            creation_timestamp=creation_timestamp,
            integrity_hash=integrity_hash,
            metadata=metadata,
        )

        logger.debug(f"Successfully constructed execution plan: {plan_id}")
        return execution_plan

    except (ValueError, TypeError) as e:
        error_msg = f"ExecutionPlan construction failed: {type(e).__name__}: {e}"
        errors.append(error_msg)
        logger.error(error_msg)
        return None


def phase8_execution_plan_assembly(
    phase7_output: Phase7TaskConstructionOutput,
    plan_id: str | None = None,
) -> Phase8ExecutionPlanOutput:
    """
    Execute Phase 8: Execution Plan Assembly.

    Hierarchical Decomposition:
    1. Phase 8.1: Precondition Validation
       - Verify Phase 7 construction_passed=True
       - Verify task_count=300
       - Check for duplicate_task_ids from Phase 7

    2. Phase 8.2: Duplicate Detection
       - Scan all tasks for duplicate task_ids
       - Accumulate duplicates in error list

    3. Phase 8.3: Execution Plan Construction
       - Convert task list to immutable tuple
       - Construct ExecutionPlan instance
       - Handle construction failures

    4. Phase 8.4: Integrity Hash Computation
       - Compute SHA256 hash of serialized tasks
       - Attach hash to execution plan
       - Warn on hash computation failures

    Integration Points:
    - Input: Phase7TaskConstructionOutput (requires construction_passed=True)
    - Output: Phase8ExecutionPlanOutput (provides execution_plan for Phase 9+)

    Error Propagation:
    - Phase 7 failures → assembly_passed=False, execution_plan=None
    - Precondition failures → accumulated in assembly_errors
    - Duplicate detection failures → accumulated in assembly_errors
    - Construction failures → accumulated in assembly_errors
    - Hash failures → accumulated in assembly_warnings (non-fatal)

    Args:
        phase7_output: Validated output from Phase 7
        plan_id: Optional plan identifier (generates UUID if not provided)

    Returns:
        Phase8ExecutionPlanOutput with execution plan or error details
    """
    logger.info("Phase 8: Execution Plan Assembly started")

    assembly_errors: list[str] = []
    assembly_warnings: list[str] = []
    execution_plan: ExecutionPlan | None = None
    duplicate_tasks: list[str] = []
    integrity_hash = ""

    if plan_id is None:
        plan_id = f"plan-{uuid4().hex[:16]}"

    logger.info(f"Phase 8.1: Precondition Validation (plan_id={plan_id})")

    preconditions_met = _validate_phase7_preconditions(phase7_output, assembly_errors)

    if not preconditions_met:
        logger.error(
            f"Phase 8.1: Precondition validation failed "
            f"({len(assembly_errors)} errors)"
        )

        return Phase8ExecutionPlanOutput(
            execution_plan=None,
            plan_id=plan_id,
            task_count=phase7_output.task_count,
            assembly_passed=False,
            assembly_errors=assembly_errors,
            assembly_warnings=assembly_warnings,
            integrity_hash="",
            duplicate_tasks=[],
            assembly_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "phase7_errors_propagated": len(phase7_output.construction_errors),
                "phase7_warnings_propagated": len(phase7_output.construction_warnings),
            },
        )

    logger.info(f"Phase 8.2: Duplicate Detection ({len(phase7_output.tasks)} tasks)")

    has_duplicates, duplicate_list = _detect_duplicate_tasks(phase7_output.tasks)

    if has_duplicates:
        duplicate_tasks = duplicate_list
        assembly_errors.append(
            f"Duplicate task IDs detected in Phase 8: {duplicate_tasks}"
        )
        logger.error(f"Phase 8.2: Found {len(duplicate_tasks)} duplicate task IDs")
    else:
        logger.info("Phase 8.2: No duplicate task IDs detected")

    if assembly_errors:
        logger.error(
            f"Phase 8: Cannot proceed with plan construction "
            f"({len(assembly_errors)} errors)"
        )

        return Phase8ExecutionPlanOutput(
            execution_plan=None,
            plan_id=plan_id,
            task_count=phase7_output.task_count,
            assembly_passed=False,
            assembly_errors=assembly_errors,
            assembly_warnings=assembly_warnings,
            integrity_hash="",
            duplicate_tasks=duplicate_tasks,
            assembly_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

    logger.info("Phase 8.3: Execution Plan Construction")

    execution_plan = _construct_execution_plan(
        plan_id=plan_id,
        tasks=phase7_output.tasks,
        errors=assembly_errors,
        warnings=assembly_warnings,
    )

    if execution_plan is None:
        logger.error("Phase 8.3: Execution plan construction failed")

        return Phase8ExecutionPlanOutput(
            execution_plan=None,
            plan_id=plan_id,
            task_count=phase7_output.task_count,
            assembly_passed=False,
            assembly_errors=assembly_errors,
            assembly_warnings=assembly_warnings,
            integrity_hash="",
            duplicate_tasks=duplicate_tasks,
            assembly_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

    integrity_hash = execution_plan.integrity_hash

    logger.info(
        f"Phase 8.3: Successfully constructed execution plan "
        f"(integrity_hash={integrity_hash[:16]}...)"
    )

    assembly_passed = len(assembly_errors) == 0

    assembly_timestamp = datetime.now(timezone.utc).isoformat()

    metadata = {
        "plan_id": plan_id,
        "task_count": len(execution_plan.tasks),
        "integrity_hash_length": len(integrity_hash),
        "phase7_warnings_count": len(phase7_output.construction_warnings),
        "assembly_duration_ms": 0,
    }

    output = Phase8ExecutionPlanOutput(
        execution_plan=execution_plan,
        plan_id=plan_id,
        task_count=len(execution_plan.tasks),
        assembly_passed=assembly_passed,
        assembly_errors=assembly_errors,
        assembly_warnings=assembly_warnings,
        integrity_hash=integrity_hash,
        duplicate_tasks=duplicate_tasks,
        assembly_timestamp=assembly_timestamp,
        metadata=metadata,
    )

    logger.info(
        f"Phase 8: Execution Plan Assembly completed "
        f"(passed={assembly_passed}, tasks={len(execution_plan.tasks)}, "
        f"errors={len(assembly_errors)}, warnings={len(assembly_warnings)})"
    )

    return output


__all__ = [
    "ExecutionPlan",
    "Phase7TaskConstructionOutput",
    "Phase8ExecutionPlanOutput",
    "phase8_execution_plan_assembly",
    "PHASE8_VERSION",
    "REQUIRED_TASK_COUNT",
]
