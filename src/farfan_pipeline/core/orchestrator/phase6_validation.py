"""Phase 6: Schema Validation Pipeline - Four Subphase Architecture.

This module implements Phase 6 as a complete validation pipeline with four subphases:

Phase 6.1: Classification & Extraction
    - Extracts question_global via bracket notation (question["question_global"])
    - Extracts expected_elements via get method with None handling
    - Classifies types using isinstance checks in None-list-dict-invalid order
    - Stores classification tuple before any iteration occurs

Phase 6.2: Structural Validation
    - Checks invalid types first with human-readable type names
    - Enforces homogeneity allowing None compatibility
    - Validates list length equality and dict key set equality
    - Uses symmetric difference computation for dict key validation
    - Returns silently on dual-None without logging

Phase 6.3: Semantic Validation
    - Iterates deterministically via enumerate-zip for lists and sorted keys for dicts
    - Extracts type-required-minimum fields with get defaults
    - Implements asymmetric required implication as not-q-or-c boolean expression
    - Enforces c-min-greater-equal-q-min threshold ordering
    - Returns validated element count

Phase 6.4: Orchestrator
    - Invokes structural then semantic layers in sequence
    - Captures element count return value
    - Emits debug log with has_required_fields and has_minimum_thresholds computed
      via any-element-iteration
    - Logs info warning for None chunk schema with non-None question schema
    - Integrates into build_with_chunk_matrix loop after Phase 5 before construct_task
    - Allows TypeError-ValueError propagation to outer handler without try-except wrapping

Architecture:
    Phase 6.1 → Phase 6.2 → Phase 6.3 → Phase 6.4
    (Sequential root) (Structural) (Semantic) (Synchronization barrier)

Parallelization:
    - Phase 6.1: Sequential root (extracts and classifies)
    - Phase 6.2-6.3: Concurrency potential (independent validation layers)
    - Phase 6.4: Synchronization barrier (aggregates results)
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_QUESTION_GLOBAL = 999


def _classify_expected_elements_type(value: Any) -> str:  # noqa: ANN401
    """Phase 6.1: Classify expected_elements type using isinstance checks.

    Performs type classification in None-list-dict-invalid order via identity
    test for None, then isinstance checks for list and dict, with any other
    type classified as invalid.

    Args:
        value: Value to classify (expected_elements from question or chunk)

    Returns:
        Type classification string: "none", "list", "dict", or "invalid"

    Classification Order:
        1. None via identity test (value is None)
        2. list via isinstance(value, list)
        3. dict via isinstance(value, dict)
        4. invalid for all other types
    """
    if value is None:
        return "none"
    elif isinstance(value, list):
        return "list"
    elif isinstance(value, dict):
        return "dict"
    else:
        return "invalid"


def _extract_and_classify_schemas(
    question: dict[str, Any],
    chunk_expected_elements: list[dict[str, Any]] | dict[str, Any] | None,
    question_id: str,
) -> tuple[int, Any, Any, str, str]:  # noqa: ANN401
    """Phase 6.1: Extract question_global and expected_elements, classify types.

    Extracts question_global via bracket notation (question["question_global"])
    and expected_elements via get method with None default. Classifies both
    schema types and stores classification tuple before any iteration occurs.

    Args:
        question: Question dictionary from questionnaire
        chunk_expected_elements: expected_elements from chunk routing result
        question_id: Question identifier for error reporting

    Returns:
        Tuple of (question_global, question_schema, chunk_schema,
                 question_type, chunk_type)

    Raises:
        ValueError: If question_global is missing, invalid type, or out of range
    """
    # Extract question_global via bracket notation
    try:
        question_global = question["question_global"]
    except KeyError as e:
        raise ValueError(
            f"Schema validation failure for question {question_id}: "
            "question_global field is required but missing"
        ) from e

    # Validate question_global
    if not isinstance(question_global, int):
        raise ValueError(
            f"Schema validation failure for question {question_id}: "
            f"question_global must be an integer, got {type(question_global).__name__}"
        )

    if not (0 <= question_global <= MAX_QUESTION_GLOBAL):
        raise ValueError(
            f"Schema validation failure for question {question_id}: "
            f"question_global must be between 0 and {MAX_QUESTION_GLOBAL} inclusive, got {question_global}"
        )

    # Extract expected_elements via get method with None handling
    question_schema = question.get("expected_elements")
    chunk_schema = chunk_expected_elements

    # Classify types using isinstance checks in None-list-dict-invalid order
    question_type = _classify_expected_elements_type(question_schema)
    chunk_type = _classify_expected_elements_type(chunk_schema)

    # Store classification tuple before any iteration occurs
    return question_global, question_schema, chunk_schema, question_type, chunk_type


def _validate_structural_compatibility(
    question_schema: Any,  # noqa: ANN401
    chunk_schema: Any,  # noqa: ANN401
    question_type: str,
    chunk_type: str,
    question_id: str,
    correlation_id: str,
) -> None:
    """Phase 6.2: Validate structural compatibility with type homogeneity checks.

    Checks invalid types first with human-readable type names, enforces
    homogeneity allowing None compatibility, validates list length equality
    and dict key set equality with symmetric difference computation, and
    returns silently on dual-None without logging.

    Args:
        question_schema: expected_elements from question
        chunk_schema: expected_elements from chunk
        question_type: Classified type of question schema
        chunk_type: Classified type of chunk schema
        question_id: Question identifier for error messages
        correlation_id: Correlation ID for distributed tracing

    Raises:
        TypeError: If either schema has invalid type (not list, dict, or None)
        ValueError: If schemas have heterogeneous types (not allowing None),
                   list length mismatch, or dict key set mismatch

    Returns:
        None (returns silently on dual-None or successful validation)
    """
    # Check invalid types first with human-readable type names
    if question_type == "invalid":
        raise TypeError(
            f"Schema validation failure for question {question_id}: "
            f"expected_elements from question has invalid type "
            f"{type(question_schema).__name__}, expected list, dict, or None "
            f"[correlation_id={correlation_id}]"
        )

    if chunk_type == "invalid":
        raise TypeError(
            f"Schema validation failure for question {question_id}: "
            f"expected_elements from chunk has invalid type "
            f"{type(chunk_schema).__name__}, expected list, dict, or None "
            f"[correlation_id={correlation_id}]"
        )

    # Return silently on dual-None without logging
    if question_type == "none" and chunk_type == "none":
        return

    # Enforce homogeneity allowing None compatibility
    # None is compatible with any type, but non-None types must match
    if question_type not in ("none", chunk_type) and chunk_type != "none":
        raise ValueError(
            f"Schema validation failure for question {question_id}: "
            f"heterogeneous types detected (question has {question_type}, "
            f"chunk has {chunk_type}) [correlation_id={correlation_id}]"
        )

    # Validate list length equality
    if question_type == "list" and chunk_type == "list":
        question_len = len(question_schema)
        chunk_len = len(chunk_schema)
        if question_len != chunk_len:
            raise ValueError(
                f"Schema validation failure for question {question_id}: "
                f"list length mismatch (question has {question_len} elements, "
                f"chunk has {chunk_len} elements) [correlation_id={correlation_id}]"
            )

    # Validate dict key set equality with symmetric difference computation
    if question_type == "dict" and chunk_type == "dict":
        question_keys = set(question_schema.keys())
        chunk_keys = set(chunk_schema.keys())

        # Compute symmetric difference
        symmetric_diff = question_keys ^ chunk_keys

        if symmetric_diff:
            missing_in_chunk = question_keys - chunk_keys
            extra_in_chunk = chunk_keys - question_keys

            details = []
            if missing_in_chunk:
                details.append(f"missing in chunk: {sorted(missing_in_chunk)}")
            if extra_in_chunk:
                details.append(f"extra in chunk: {sorted(extra_in_chunk)}")

            raise ValueError(
                f"Schema validation failure for question {question_id}: "
                f"dict key set mismatch ({', '.join(details)}) "
                f"[correlation_id={correlation_id}]"
            )


def _validate_semantic_constraints(
    question_schema: Any,  # noqa: ANN401
    chunk_schema: Any,  # noqa: ANN401
    question_type: str,
    chunk_type: str,
    provisional_task_id: str,
    question_id: str,
    chunk_id: str,
    correlation_id: str,
) -> int:
    """Phase 6.3: Validate semantic constraints and return validated element count.

    Iterates deterministically via enumerate-zip for lists and sorted keys for
    dicts, extracts type-required-minimum fields with get defaults, implements
    asymmetric required implication as not-q-or-c boolean expression, enforces
    c-min-greater-equal-q-min threshold ordering, and returns validated element
    count.

    Args:
        question_schema: expected_elements from question
        chunk_schema: expected_elements from chunk
        question_type: Classified type of question schema
        chunk_type: Classified type of chunk schema
        provisional_task_id: Task ID for error reporting
        question_id: Question identifier for error messages
        chunk_id: Chunk identifier for error messages
        correlation_id: Correlation ID for distributed tracing

    Returns:
        Validated element count (number of elements validated)

    Raises:
        ValueError: If required field implication violated or threshold ordering violated

    Semantic Constraints:
        - Asymmetric required implication: not q_required or c_required
        - Threshold ordering: c_minimum >= q_minimum
    """
    validated_count = 0

    # Iterate deterministically via enumerate-zip for lists
    if question_type == "list" and chunk_type == "list":
        for idx, (q_elem, c_elem) in enumerate(
            zip(question_schema, chunk_schema, strict=True)
        ):
            if not isinstance(q_elem, dict) or not isinstance(c_elem, dict):
                continue

            # Extract type-required-minimum fields with get defaults
            element_type = q_elem.get("type", f"element_at_index_{idx}")
            q_required = q_elem.get("required", False)
            c_required = c_elem.get("required", False)
            q_minimum = q_elem.get("minimum", 0)
            c_minimum = c_elem.get("minimum", 0)

            # Implement asymmetric required implication as not-q-or-c boolean expression
            if q_required and not c_required:
                raise ValueError(
                    f"Task {provisional_task_id}: Required field implication violation "
                    f"at index {idx}: element type '{element_type}' is required in "
                    f"question but marked as optional in chunk "
                    f"[question_id={question_id}, chunk_id={chunk_id}, "
                    f"correlation_id={correlation_id}]"
                )

            # Enforce c-min-greater-equal-q-min threshold ordering
            if (
                isinstance(q_minimum, int | float)
                and isinstance(c_minimum, int | float)
                and c_minimum < q_minimum
            ):
                raise ValueError(
                    f"Task {provisional_task_id}: Threshold ordering violation "
                    f"at index {idx}: element type '{element_type}' has chunk "
                    f"minimum ({c_minimum}) < question minimum ({q_minimum}) "
                    f"[question_id={question_id}, chunk_id={chunk_id}, "
                    f"correlation_id={correlation_id}]"
                )

            validated_count += 1

    # Iterate deterministically via sorted keys for dicts
    elif question_type == "dict" and chunk_type == "dict":
        common_keys = set(question_schema.keys()) & set(chunk_schema.keys())

        for key in sorted(common_keys):
            q_elem = question_schema[key]
            c_elem = chunk_schema[key]

            if not isinstance(q_elem, dict) or not isinstance(c_elem, dict):
                continue

            # Extract type-required-minimum fields with get defaults
            element_type = q_elem.get("type", key)
            q_required = q_elem.get("required", False)
            c_required = c_elem.get("required", False)
            q_minimum = q_elem.get("minimum", 0)
            c_minimum = c_elem.get("minimum", 0)

            # Implement asymmetric required implication as not-q-or-c boolean expression
            if q_required and not c_required:
                raise ValueError(
                    f"Task {provisional_task_id}: Required field implication violation "
                    f"for key '{key}': element type '{element_type}' is required in "
                    f"question but marked as optional in chunk "
                    f"[question_id={question_id}, chunk_id={chunk_id}, "
                    f"correlation_id={correlation_id}]"
                )

            # Enforce c-min-greater-equal-q-min threshold ordering
            if (
                isinstance(q_minimum, int | float)
                and isinstance(c_minimum, int | float)
                and c_minimum < q_minimum
            ):
                raise ValueError(
                    f"Task {provisional_task_id}: Threshold ordering violation "
                    f"for key '{key}': element type '{element_type}' has chunk "
                    f"minimum ({c_minimum}) < question minimum ({q_minimum}) "
                    f"[question_id={question_id}, chunk_id={chunk_id}, "
                    f"correlation_id={correlation_id}]"
                )

            validated_count += 1

    return validated_count


def validate_phase6_schema_compatibility(
    question: dict[str, Any],
    chunk_expected_elements: list[dict[str, Any]] | dict[str, Any] | None,
    chunk_id: str,
    policy_area_id: str,
    correlation_id: str,
) -> int:
    """Phase 6.4: Orchestrator - Coordinate complete validation pipeline.

    Invokes structural then semantic layers in sequence, captures element count
    return value, emits debug log with has_required_fields and has_minimum_thresholds
    computed via any-element-iteration, logs info warning for None chunk schema
    with non-None question schema, and allows TypeError-ValueError propagation
    to outer handler without try-except wrapping.

    This is the main entry point for Phase 6 validation, designed to integrate
    into the build_with_chunk_matrix loop after Phase 5 (signal resolution) and
    before construct_task.

    Args:
        question: Question dictionary from questionnaire
        chunk_expected_elements: expected_elements from chunk routing result
        chunk_id: Chunk identifier for logging
        policy_area_id: Policy area identifier for task ID construction
        correlation_id: Correlation ID for distributed tracing

    Returns:
        Validated element count (number of elements validated)

    Raises:
        TypeError: If either schema has invalid type (propagated from Phase 6.2)
        ValueError: If validation fails (propagated from Phase 6.1, 6.2, or 6.3)

    Integration Point:
        Called within build_with_chunk_matrix loop:
        1. After Phase 5: Signal resolution completes
        2. Before construct_task: Task construction begins
        3. No try-except wrapper: Exceptions propagate to outer handler

    Orchestration Flow:
        Phase 6.1: Extract and classify schemas
        Phase 6.2: Validate structural compatibility
        Phase 6.3: Validate semantic constraints (if both schemas non-None)
        Phase 6.4: Emit debug logs and return validated count
    """
    question_id = question.get("question_id", "UNKNOWN")

    # Phase 6.1: Classification & Extraction
    (
        question_global,
        question_schema,
        chunk_schema,
        question_type,
        chunk_type,
    ) = _extract_and_classify_schemas(question, chunk_expected_elements, question_id)

    # Construct provisional task ID for error reporting
    provisional_task_id = f"MQC-{question_global:03d}_{policy_area_id}"

    # Phase 6.2: Structural Validation
    _validate_structural_compatibility(
        question_schema,
        chunk_schema,
        question_type,
        chunk_type,
        question_id,
        correlation_id,
    )

    # Phase 6.3: Semantic Validation (if both schemas non-None)
    validated_count = 0
    if question_schema is not None and chunk_schema is not None:
        validated_count = _validate_semantic_constraints(
            question_schema,
            chunk_schema,
            question_type,
            chunk_type,
            provisional_task_id,
            question_id,
            chunk_id,
            correlation_id,
        )

    # Phase 6.4: Emit debug log with has_required_fields and has_minimum_thresholds
    # Compute via any-element-iteration
    has_required_fields = False
    has_minimum_thresholds = False

    if question_schema is not None:
        if isinstance(question_schema, list):
            has_required_fields = any(
                elem.get("required", False)
                for elem in question_schema
                if isinstance(elem, dict)
            )
            has_minimum_thresholds = any(
                "minimum" in elem for elem in question_schema if isinstance(elem, dict)
            )
        elif isinstance(question_schema, dict):
            has_required_fields = any(
                elem.get("required", False)
                for elem in question_schema.values()
                if isinstance(elem, dict)
            )
            has_minimum_thresholds = any(
                "minimum" in elem
                for elem in question_schema.values()
                if isinstance(elem, dict)
            )

    logger.debug(
        f"Phase 6 validation complete: question_id={question_id}, "
        f"chunk_id={chunk_id}, provisional_task_id={provisional_task_id}, "
        f"validated_count={validated_count}, "
        f"has_required_fields={has_required_fields}, "
        f"has_minimum_thresholds={has_minimum_thresholds}, "
        f"question_type={question_type}, chunk_type={chunk_type}, "
        f"correlation_id={correlation_id}"
    )

    # Log info warning for None chunk schema with non-None question schema
    if question_schema is not None and chunk_schema is None:
        logger.info(
            f"Schema asymmetry detected: question_id={question_id}, "
            f"chunk_id={chunk_id}, question_schema_type={question_type}, "
            f"chunk_schema_type=none, message='Question specifies required elements "
            f"but chunk provides no schema', "
            f"validation_status='compatible_via_constraint_relaxation', "
            f"correlation_id={correlation_id}"
        )

    return validated_count


__all__ = [
    "validate_phase6_schema_compatibility",
    "_extract_and_classify_schemas",
    "_validate_structural_compatibility",
    "_validate_semantic_constraints",
    "_classify_expected_elements_type",
]
