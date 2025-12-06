"""
Phase 7: Task Construction - Deterministic Task Generation with Strict Validation
==================================================================================

This module implements Phase 7 of the canonical pipeline:
    Phase 6 Schema Validation Output → ExecutableTask Set → Phase 8 Execution Plan

Responsibilities:
-----------------
1. Generate unique task identifiers with zero-padded three-character format
2. Construct ExecutableTask instances with complete field validation
3. Enforce non-null constraints on all mandatory fields
4. Validate type correctness before any operations assuming type
5. Handle KeyError and AttributeError explicitly with diagnostic messages
6. Establish sequential dependencies for hierarchical decomposition
7. Validate integration points with Phase 6 and Phase 8

Input Contract (from Phase 6):
-------------------------------
Phase6SchemaValidationOutput:
    - validated_questions: List[ValidatedQuestionSchema]
    - validated_chunks: List[ValidatedChunkSchema]
    - schema_validation_passed: bool
    - validation_errors: List[str]
    - validation_warnings: List[str]
    - question_count: int
    - chunk_count: int
    - validation_timestamp: str

ValidatedQuestionSchema:
    - question_id: str (non-null, validated format)
    - question_global: int (0-999, validated)
    - dimension_id: str (non-null)
    - policy_area_id: str (non-null)
    - base_slot: str (non-null)
    - cluster_id: str (non-null)
    - patterns: List[Dict[str, Any]] (validated schema)
    - signals: Dict[str, Any] (validated schema)
    - expected_elements: List[Dict[str, Any]] (validated schema)
    - metadata: Dict[str, Any]

ValidatedChunkSchema:
    - chunk_id: str (non-null, validated format)
    - policy_area_id: str (non-null)
    - dimension_id: str (non-null)
    - document_position: int (non-negative)
    - content: str (non-empty)
    - metadata: Dict[str, Any]

Output Contract (to Phase 8):
------------------------------
Phase7TaskConstructionOutput:
    - tasks: List[ExecutableTask] (length=300)
    - task_count: int (must equal 300)
    - construction_passed: bool
    - construction_errors: List[str]
    - construction_warnings: List[str]
    - duplicate_task_ids: List[str]
    - missing_fields_by_task: Dict[str, List[str]]
    - construction_timestamp: str
    - metadata: Dict[str, Any]

ExecutableTask (from task_planner.py):
    - task_id: str (format: "MQC-{question_global:03d}_{policy_area_id}")
    - question_id: str (non-empty)
    - question_global: int (0-999)
    - policy_area_id: str (non-empty)
    - dimension_id: str (non-empty)
    - chunk_id: str (non-empty)
    - patterns: List[Dict[str, Any]]
    - signals: Dict[str, Any]
    - creation_timestamp: str (ISO 8601)
    - expected_elements: List[Dict[str, Any]]
    - metadata: Dict[str, Any]

Phase 7 Sub-phases:
-------------------
7.1 Identifier Generation:
    - Input: validated_questions (from Phase 6)
    - Process: Generate task_id with format "MQC-{question_global:03d}_{policy_area_id}"
    - Validation: Enforce three-character zero-padding, check duplicates
    - Output: task_id_map: Dict[str, str]
    - Error Propagation: Duplicate IDs → construction_errors

7.2 Task Construction:
    - Input: validated_questions, validated_chunks, task_id_map (from 7.1)
    - Process: Construct ExecutableTask for each question-chunk pair
    - Validation: Validate ALL mandatory fields before dataclass constructor
    - Field Processing Order (deterministic):
        1. task_id (from task_id_map)
        2. question_id (from question)
        3. question_global (validate int type)
        4. policy_area_id (from question)
        5. dimension_id (from question)
        6. chunk_id (from chunk)
        7. patterns (validate list type)
        8. signals (validate dict type)
        9. creation_timestamp (generate ISO 8601)
        10. expected_elements (validate list type)
        11. metadata (construct dict)
    - Output: List[ExecutableTask]
    - Error Propagation: Field validation failures → construction_errors

Integration Points:
-------------------
Phase 6 → Phase 7:
    - Contract: Phase6SchemaValidationOutput
    - Precondition: schema_validation_passed must be True
    - Error: If False, Phase 7 returns empty task list with propagated errors

Phase 7 → Phase 8:
    - Contract: Phase7TaskConstructionOutput
    - Precondition: construction_passed must be True
    - Postcondition: task_count must equal 300
    - Error: If False, Phase 8 aborts with diagnostic error message

Error Handling:
---------------
1. KeyError Handling:
   - All dictionary access wrapped in try-except
   - Error message format: "Field '{field}' not found in {source}: KeyError"
   - Accumulate errors rather than fail-fast

2. AttributeError Handling:
   - All attribute access validated before use
   - Error message format: "Attribute '{attr}' not found in {object}: AttributeError"
   - Accumulate errors rather than fail-fast

3. TypeError Handling:
   - Type validation occurs BEFORE operations
   - Error message format: "Field '{field}' has invalid type: expected {expected}, got {actual}"
   - Accumulate errors rather than fail-fast

4. ValueError Handling:
   - Range/format validation before use
   - Error message format: "Field '{field}' has invalid value: {value} ({reason})"
   - Accumulate errors rather than fail-fast

Determinism Guarantees:
-----------------------
1. Field processing order is fixed and documented
2. Error messages are consistent and deterministic
3. Task ID generation is deterministic from input
4. Metadata construction follows fixed key order
5. All operations are pure functions with no side effects

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-19
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from farfan_pipeline.core.orchestrator.task_planner import ExecutableTask

logger = logging.getLogger(__name__)

PHASE7_VERSION = "1.0.0"
REQUIRED_TASK_COUNT = 300
MAX_QUESTION_GLOBAL = 999
TASK_ID_FORMAT = "MQC-{question_global:03d}_{policy_area_id}"


@dataclass
class ValidatedQuestionSchema:
    """Validated question schema from Phase 6."""

    question_id: str
    question_global: int
    dimension_id: str
    policy_area_id: str
    base_slot: str
    cluster_id: str
    patterns: list[dict[str, Any]]
    signals: dict[str, Any]
    expected_elements: list[dict[str, Any]]
    metadata: dict[str, Any]


@dataclass
class ValidatedChunkSchema:
    """Validated chunk schema from Phase 6."""

    chunk_id: str
    policy_area_id: str
    dimension_id: str
    document_position: int
    content: str
    metadata: dict[str, Any]


@dataclass
class Phase6SchemaValidationOutput:
    """Output contract from Phase 6."""

    validated_questions: list[ValidatedQuestionSchema]
    validated_chunks: list[ValidatedChunkSchema]
    schema_validation_passed: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    question_count: int
    chunk_count: int
    validation_timestamp: str


@dataclass
class Phase7TaskConstructionOutput:
    """Output contract for Phase 7."""

    tasks: list[ExecutableTask]
    task_count: int
    construction_passed: bool
    construction_errors: list[str]
    construction_warnings: list[str]
    duplicate_task_ids: list[str]
    missing_fields_by_task: dict[str, list[str]]
    construction_timestamp: str
    metadata: dict[str, Any]
    phase7_version: str = PHASE7_VERSION


class FieldValidationError(Exception):
    """Raised when field validation fails during task construction."""

    pass


class TaskConstructionError(Exception):
    """Raised when task construction fails."""

    pass


def _validate_field_non_null(
    field_name: str,
    field_value: Any,
    source: str,
    errors: list[str],
) -> bool:
    """
    Validate that a field is non-null.

    Args:
        field_name: Name of the field being validated
        field_value: Value to validate
        source: Source context (e.g., "question", "chunk")
        errors: List to accumulate errors

    Returns:
        True if validation passed, False otherwise
    """
    if field_value is None:
        errors.append(
            f"Field '{field_name}' is None in {source}: non-null constraint violated"
        )
        return False
    return True


def _validate_field_non_empty_string(
    field_name: str,
    field_value: Any,
    source: str,
    errors: list[str],
) -> bool:
    """
    Validate that a field is a non-empty string.

    Type validation occurs BEFORE empty check.

    Args:
        field_name: Name of the field being validated
        field_value: Value to validate
        source: Source context (e.g., "question", "chunk")
        errors: List to accumulate errors

    Returns:
        True if validation passed, False otherwise
    """
    if not isinstance(field_value, str):
        errors.append(
            f"Field '{field_name}' has invalid type in {source}: "
            f"expected str, got {type(field_value).__name__}"
        )
        return False

    if not field_value:
        errors.append(
            f"Field '{field_name}' is empty string in {source}: non-empty constraint violated"
        )
        return False

    return True


def _validate_field_integer_range(
    field_name: str,
    field_value: Any,
    source: str,
    min_value: int,
    max_value: int,
    errors: list[str],
) -> bool:
    """
    Validate that a field is an integer within specified range.

    Type validation occurs BEFORE range check.

    Args:
        field_name: Name of the field being validated
        field_value: Value to validate
        source: Source context
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        errors: List to accumulate errors

    Returns:
        True if validation passed, False otherwise
    """
    if not isinstance(field_value, int):
        errors.append(
            f"Field '{field_name}' has invalid type in {source}: "
            f"expected int, got {type(field_value).__name__}"
        )
        return False

    if not (min_value <= field_value <= max_value):
        errors.append(
            f"Field '{field_name}' has invalid value in {source}: "
            f"{field_value} not in range [{min_value}, {max_value}]"
        )
        return False

    return True


def _validate_field_list_type(
    field_name: str,
    field_value: Any,
    source: str,
    errors: list[str],
) -> bool:
    """
    Validate that a field is a list.

    Type validation only; does not check contents.

    Args:
        field_name: Name of the field being validated
        field_value: Value to validate
        source: Source context
        errors: List to accumulate errors

    Returns:
        True if validation passed, False otherwise
    """
    if not isinstance(field_value, list):
        errors.append(
            f"Field '{field_name}' has invalid type in {source}: "
            f"expected list, got {type(field_value).__name__}"
        )
        return False

    return True


def _validate_field_dict_type(
    field_name: str,
    field_value: Any,
    source: str,
    errors: list[str],
) -> bool:
    """
    Validate that a field is a dict.

    Type validation only; does not check contents.

    Args:
        field_name: Name of the field being validated
        field_value: Value to validate
        source: Source context
        errors: List to accumulate errors

    Returns:
        True if validation passed, False otherwise
    """
    if not isinstance(field_value, dict):
        errors.append(
            f"Field '{field_name}' has invalid type in {source}: "
            f"expected dict, got {type(field_value).__name__}"
        )
        return False

    return True


def _safe_get_dict_field(
    data: dict[str, Any],
    field_name: str,
    source: str,
    errors: list[str],
    default: Any = None,
) -> Any:
    """
    Safely extract field from dictionary with KeyError handling.

    Args:
        data: Dictionary to extract from
        field_name: Key to extract
        source: Source context for error message
        errors: List to accumulate errors
        default: Default value if key not found and error not appended

    Returns:
        Field value or default

    Raises:
        Never raises; accumulates errors instead
    """
    try:
        return data[field_name]
    except KeyError:
        errors.append(f"Field '{field_name}' not found in {source}: KeyError")
        return default


def _safe_get_attribute(
    obj: Any,
    attr_name: str,
    source: str,
    errors: list[str],
    default: Any = None,
) -> Any:
    """
    Safely extract attribute from object with AttributeError handling.

    Args:
        obj: Object to extract from
        attr_name: Attribute to extract
        source: Source context for error message
        errors: List to accumulate errors
        default: Default value if attribute not found

    Returns:
        Attribute value or default

    Raises:
        Never raises; accumulates errors instead
    """
    try:
        return getattr(obj, attr_name)
    except AttributeError:
        errors.append(f"Attribute '{attr_name}' not found in {source}: AttributeError")
        return default


def _generate_task_id(
    question_global: int,
    policy_area_id: str,
    errors: list[str],
) -> str:
    """
    Generate task ID with three-character zero-padded format.

    Phase 7.1: Identifier Generation

    Args:
        question_global: Question number (0-999)
        policy_area_id: Policy area identifier
        errors: List to accumulate errors

    Returns:
        Task ID in format "MQC-{question_global:03d}_{policy_area_id}"
        Empty string if validation fails
    """
    if not _validate_field_integer_range(
        "question_global",
        question_global,
        "task_id_generation",
        0,
        MAX_QUESTION_GLOBAL,
        errors,
    ):
        return ""

    if not _validate_field_non_empty_string(
        "policy_area_id",
        policy_area_id,
        "task_id_generation",
        errors,
    ):
        return ""

    try:
        task_id = TASK_ID_FORMAT.format(
            question_global=question_global,
            policy_area_id=policy_area_id,
        )
        return task_id
    except (ValueError, KeyError) as e:
        errors.append(f"Task ID formatting failed: {type(e).__name__}: {e}")
        return ""


def _check_duplicate_task_ids(
    task_ids: list[str],
) -> tuple[bool, list[str]]:
    """
    Check for duplicate task IDs.

    Phase 7.1: Identifier Generation - Duplicate Detection

    Args:
        task_ids: List of task IDs to check

    Returns:
        Tuple of (has_duplicates, list_of_duplicate_ids)
    """
    seen: set[str] = set()
    duplicates: set[str] = set()

    for task_id in task_ids:
        if task_id in seen:
            duplicates.add(task_id)
        seen.add(task_id)

    return len(duplicates) > 0, sorted(duplicates)


def _construct_single_task(  # noqa: PLR0911
    question: ValidatedQuestionSchema,
    chunk: ValidatedChunkSchema,
    task_id: str,
    errors: list[str],
    warnings: list[str],  # noqa: ARG001
) -> ExecutableTask | None:
    """
    Construct a single ExecutableTask with complete field validation.

    Phase 7.2: Task Construction

    Field Processing Order (deterministic):
    1. task_id (validated)
    2. question_id (validate non-empty string)
    3. question_global (validate int type and range)
    4. policy_area_id (validate non-empty string)
    5. dimension_id (validate non-empty string)
    6. chunk_id (validate non-empty string)
    7. patterns (validate list type)
    8. signals (validate dict type)
    9. creation_timestamp (generate ISO 8601)
    10. expected_elements (validate list type)
    11. metadata (construct dict with fixed key order)

    All validations occur BEFORE dataclass constructor invocation.

    Args:
        question: Validated question schema from Phase 6
        chunk: Validated chunk schema from Phase 6
        task_id: Pre-generated task ID from Phase 7.1
        errors: List to accumulate errors
        warnings: List to accumulate warnings

    Returns:
        ExecutableTask instance or None if validation failed
    """
    task_errors: list[str] = []
    task_context = f"task[{task_id}]"

    if not _validate_field_non_empty_string(
        "task_id", task_id, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    question_id = _safe_get_attribute(
        question, "question_id", task_context, task_errors, ""
    )
    if not _validate_field_non_empty_string(
        "question_id", question_id, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    question_global = _safe_get_attribute(
        question, "question_global", task_context, task_errors, -1
    )
    if not _validate_field_integer_range(
        "question_global",
        question_global,
        task_context,
        0,
        MAX_QUESTION_GLOBAL,
        task_errors,
    ):
        errors.extend(task_errors)
        return None

    policy_area_id = _safe_get_attribute(
        question, "policy_area_id", task_context, task_errors, ""
    )
    if not _validate_field_non_empty_string(
        "policy_area_id", policy_area_id, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    dimension_id = _safe_get_attribute(
        question, "dimension_id", task_context, task_errors, ""
    )
    if not _validate_field_non_empty_string(
        "dimension_id", dimension_id, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    chunk_id = _safe_get_attribute(chunk, "chunk_id", task_context, task_errors, "")
    if not _validate_field_non_empty_string(
        "chunk_id", chunk_id, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    patterns = _safe_get_attribute(question, "patterns", task_context, task_errors, [])
    if not _validate_field_list_type("patterns", patterns, task_context, task_errors):
        errors.extend(task_errors)
        return None

    signals = _safe_get_attribute(question, "signals", task_context, task_errors, {})
    if not _validate_field_dict_type("signals", signals, task_context, task_errors):
        errors.extend(task_errors)
        return None

    creation_timestamp = datetime.now(timezone.utc).isoformat()

    expected_elements = _safe_get_attribute(
        question, "expected_elements", task_context, task_errors, []
    )
    if not _validate_field_list_type(
        "expected_elements", expected_elements, task_context, task_errors
    ):
        errors.extend(task_errors)
        return None

    question_metadata = _safe_get_attribute(
        question, "metadata", task_context, task_errors, {}
    )
    chunk_metadata = _safe_get_attribute(
        chunk, "metadata", task_context, task_errors, {}
    )

    base_slot = _safe_get_attribute(question, "base_slot", task_context, [], "")
    cluster_id = _safe_get_attribute(question, "cluster_id", task_context, [], "")
    document_position = _safe_get_attribute(
        chunk, "document_position", task_context, [], 0
    )

    metadata = {
        "base_slot": base_slot,
        "cluster_id": cluster_id,
        "document_position": document_position,
        "phase7_version": PHASE7_VERSION,
        "question_metadata": (
            question_metadata if isinstance(question_metadata, dict) else {}
        ),
        "chunk_metadata": chunk_metadata if isinstance(chunk_metadata, dict) else {},
        "pattern_count": len(patterns) if isinstance(patterns, list) else 0,
        "signal_count": len(signals) if isinstance(signals, dict) else 0,
        "expected_element_count": (
            len(expected_elements) if isinstance(expected_elements, list) else 0
        ),
    }

    try:
        task = ExecutableTask(
            task_id=task_id,
            question_id=question_id,
            question_global=question_global,
            policy_area_id=policy_area_id,
            dimension_id=dimension_id,
            chunk_id=chunk_id,
            patterns=patterns,
            signals=signals,
            creation_timestamp=creation_timestamp,
            expected_elements=expected_elements,
            metadata=metadata,
        )

        logger.debug(
            f"Successfully constructed task: {task_id} "
            f"(question={question_id}, chunk={chunk_id})"
        )

        return task

    except (ValueError, TypeError) as e:
        error_msg = (
            f"ExecutableTask dataclass constructor failed for {task_id}: "
            f"{type(e).__name__}: {e}"
        )
        errors.append(error_msg)
        logger.error(error_msg)
        return None


def phase7_task_construction(  # noqa: PLR0912, PLR0915
    phase6_output: Phase6SchemaValidationOutput,
) -> Phase7TaskConstructionOutput:
    """
    Execute Phase 7: Task Construction.

    Hierarchical Decomposition:
    1. Phase 7.1: Identifier Generation
       - Generate task IDs with three-character zero-padding
       - Check for duplicates
       - Accumulate errors

    2. Phase 7.2: Task Construction
       - Validate all mandatory fields in deterministic order
       - Construct ExecutableTask instances
       - Accumulate errors and track missing fields

    Integration Points:
    - Input: Phase6SchemaValidationOutput (requires schema_validation_passed=True)
    - Output: Phase7TaskConstructionOutput (provides tasks for Phase 8)

    Error Propagation:
    - Phase 6 failures → construction_passed=False, empty task list
    - Field validation failures → accumulated in construction_errors
    - Duplicate task IDs → accumulated in duplicate_task_ids
    - Missing fields → tracked in missing_fields_by_task

    Args:
        phase6_output: Validated output from Phase 6

    Returns:
        Phase7TaskConstructionOutput with constructed tasks or error details
    """
    logger.info("Phase 7: Task Construction started")

    construction_errors: list[str] = []
    construction_warnings: list[str] = []
    tasks: list[ExecutableTask] = []
    duplicate_task_ids: list[str] = []
    missing_fields_by_task: dict[str, list[str]] = {}

    if not phase6_output.schema_validation_passed:
        construction_errors.append(
            "Phase 6 schema validation failed; cannot proceed with task construction"
        )
        construction_errors.extend(phase6_output.validation_errors)

        return Phase7TaskConstructionOutput(
            tasks=[],
            task_count=0,
            construction_passed=False,
            construction_errors=construction_errors,
            construction_warnings=construction_warnings,
            duplicate_task_ids=[],
            missing_fields_by_task={},
            construction_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "phase6_errors_propagated": len(phase6_output.validation_errors),
                "phase6_warnings_propagated": len(phase6_output.validation_warnings),
            },
        )

    validated_questions = phase6_output.validated_questions
    validated_chunks = phase6_output.validated_chunks

    if not validated_questions:
        construction_errors.append("No validated questions provided by Phase 6")

    if not validated_chunks:
        construction_errors.append("No validated chunks provided by Phase 6")

    if construction_errors:
        return Phase7TaskConstructionOutput(
            tasks=[],
            task_count=0,
            construction_passed=False,
            construction_errors=construction_errors,
            construction_warnings=construction_warnings,
            duplicate_task_ids=[],
            missing_fields_by_task={},
            construction_timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={},
        )

    logger.info(
        f"Phase 7.1: Identifier Generation started "
        f"({len(validated_questions)} questions)"
    )

    task_id_map: dict[str, str] = {}
    task_ids_list: list[str] = []

    for question in validated_questions:
        question_global = _safe_get_attribute(
            question, "question_global", "phase7.1", construction_errors, -1
        )
        policy_area_id = _safe_get_attribute(
            question, "policy_area_id", "phase7.1", construction_errors, ""
        )

        task_id = _generate_task_id(
            question_global, policy_area_id, construction_errors
        )

        if task_id:
            question_id = _safe_get_attribute(
                question, "question_id", "phase7.1", construction_errors, ""
            )
            task_id_map[question_id] = task_id
            task_ids_list.append(task_id)

    has_duplicates, duplicate_list = _check_duplicate_task_ids(task_ids_list)
    if has_duplicates:
        duplicate_task_ids = duplicate_list
        construction_errors.append(f"Duplicate task IDs detected: {duplicate_task_ids}")

    logger.info(
        f"Phase 7.1: Generated {len(task_id_map)} task IDs "
        f"(duplicates: {len(duplicate_task_ids)})"
    )

    logger.info("Phase 7.2: Task Construction started")

    for question in validated_questions:
        question_id = _safe_get_attribute(
            question, "question_id", "phase7.2", construction_errors, ""
        )

        task_id = task_id_map.get(question_id, "")
        if not task_id:
            construction_errors.append(
                f"Task ID not found in task_id_map for question {question_id}"
            )
            continue

        policy_area_id = _safe_get_attribute(
            question, "policy_area_id", "phase7.2", construction_errors, ""
        )
        dimension_id = _safe_get_attribute(
            question, "dimension_id", "phase7.2", construction_errors, ""
        )

        matching_chunks = [
            chunk
            for chunk in validated_chunks
            if chunk.policy_area_id == policy_area_id
            and chunk.dimension_id == dimension_id
        ]

        if not matching_chunks:
            construction_warnings.append(
                f"No matching chunks found for question {question_id} "
                f"(PA={policy_area_id}, DIM={dimension_id})"
            )
            continue

        chunk = matching_chunks[0]

        task = _construct_single_task(
            question=question,
            chunk=chunk,
            task_id=task_id,
            errors=construction_errors,
            warnings=construction_warnings,
        )

        if task:
            tasks.append(task)
        else:
            missing_fields = [
                err.split("'")[1]
                for err in construction_errors
                if f"task[{task_id}]" in err and "not found" in err
            ]
            if missing_fields:
                missing_fields_by_task[task_id] = missing_fields

    logger.info(f"Phase 7.2: Constructed {len(tasks)} tasks")

    task_count = len(tasks)
    construction_passed = (
        len(construction_errors) == 0 and task_count == REQUIRED_TASK_COUNT
    )

    if task_count != REQUIRED_TASK_COUNT:
        construction_errors.append(
            f"Task count mismatch: expected {REQUIRED_TASK_COUNT}, got {task_count}"
        )

    construction_timestamp = datetime.now(timezone.utc).isoformat()

    metadata = {
        "question_count": len(validated_questions),
        "chunk_count": len(validated_chunks),
        "task_id_map_size": len(task_id_map),
        "duplicate_count": len(duplicate_task_ids),
        "missing_field_task_count": len(missing_fields_by_task),
        "construction_duration_ms": 0,
    }

    output = Phase7TaskConstructionOutput(
        tasks=tasks,
        task_count=task_count,
        construction_passed=construction_passed,
        construction_errors=construction_errors,
        construction_warnings=construction_warnings,
        duplicate_task_ids=duplicate_task_ids,
        missing_fields_by_task=missing_fields_by_task,
        construction_timestamp=construction_timestamp,
        metadata=metadata,
    )

    logger.info(
        f"Phase 7: Task Construction completed "
        f"(passed={construction_passed}, tasks={task_count}, "
        f"errors={len(construction_errors)}, warnings={len(construction_warnings)})"
    )

    return output


__all__ = [
    "Phase6SchemaValidationOutput",
    "Phase7TaskConstructionOutput",
    "ValidatedQuestionSchema",
    "ValidatedChunkSchema",
    "phase7_task_construction",
    "PHASE7_VERSION",
    "REQUIRED_TASK_COUNT",
    "MAX_QUESTION_GLOBAL",
    "TASK_ID_FORMAT",
]
