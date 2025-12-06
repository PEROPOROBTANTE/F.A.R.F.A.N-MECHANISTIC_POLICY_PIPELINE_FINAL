"""
Phase 6: Schema Validation - Comprehensive Input Validation for Task Construction
==================================================================================

This module implements Phase 6 of the canonical pipeline:
    Raw Question/Chunk Data → Validated Schemas → Phase 7 Task Construction

Responsibilities:
-----------------
1. Validate question schema structure and field types
2. Validate chunk schema structure and field types
3. Enforce non-null constraints on mandatory fields
4. Validate data type correctness before downstream use
5. Check for missing required fields with explicit diagnostics
6. Ensure policy area and dimension ID consistency
7. Validate question_global range and format

Input Contract:
---------------
Phase5AggregationOutput (conceptual - from aggregation phase):
    - raw_questions: List[Dict[str, Any]]
    - raw_chunks: List[Dict[str, Any]]
    - aggregation_metadata: Dict[str, Any]

Output Contract (to Phase 7):
------------------------------
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
    - question_id: str (non-null, non-empty)
    - question_global: int (0-999)
    - dimension_id: str (non-null, non-empty)
    - policy_area_id: str (non-null, non-empty)
    - base_slot: str (non-null)
    - cluster_id: str (non-null)
    - patterns: List[Dict[str, Any]] (validated list type)
    - signals: Dict[str, Any] (validated dict type)
    - expected_elements: List[Dict[str, Any]] (validated list type)
    - metadata: Dict[str, Any] (validated dict type)

ValidatedChunkSchema:
    - chunk_id: str (non-null, non-empty)
    - policy_area_id: str (non-null, non-empty)
    - dimension_id: str (non-null, non-empty)
    - document_position: int (non-negative)
    - content: str (non-empty)
    - metadata: Dict[str, Any] (validated dict type)

Error Propagation Semantics:
-----------------------------
1. Schema validation failures prevent Phase 7 execution
2. Type mismatches are caught BEFORE Phase 7 receives data
3. Missing required fields are explicitly reported with field name
4. All errors are accumulated and returned in validation_errors list

Integration Points:
-------------------
Phase 5 → Phase 6:
    - Contract: Raw question and chunk dictionaries
    - Precondition: None (Phase 6 validates everything)
    - Error: Schema violations → schema_validation_passed=False

Phase 6 → Phase 7:
    - Contract: Phase6SchemaValidationOutput
    - Postcondition: schema_validation_passed must be True for Phase 7 to proceed
    - Error: If False, Phase 7 returns empty task list with propagated errors

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-19
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

PHASE6_VERSION = "1.0.0"
MAX_QUESTION_GLOBAL = 999


@dataclass
class ValidatedQuestionSchema:
    """Validated question schema output."""

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
    """Validated chunk schema output."""

    chunk_id: str
    policy_area_id: str
    dimension_id: str
    document_position: int
    content: str
    metadata: dict[str, Any]


@dataclass
class Phase6SchemaValidationOutput:
    """Output contract for Phase 6."""

    validated_questions: list[ValidatedQuestionSchema]
    validated_chunks: list[ValidatedChunkSchema]
    schema_validation_passed: bool
    validation_errors: list[str]
    validation_warnings: list[str]
    question_count: int
    chunk_count: int
    validation_timestamp: str
    phase6_version: str = PHASE6_VERSION


def _validate_question_schema(  # noqa: PLR0911, PLR0912, PLR0915
    question: dict[str, Any],
    index: int,
    errors: list[str],
    warnings: list[str],
) -> ValidatedQuestionSchema | None:
    """
    Validate a single question schema with explicit error handling.

    Validates fields in order:
    1. question_id: str (non-null, non-empty)
    2. question_global: int (0-999)
    3. dimension_id: str (non-null, non-empty)
    4. policy_area_id: str (non-null, non-empty)
    5. base_slot: str (non-null)
    6. cluster_id: str (non-null)
    7. patterns: List[Dict] (type validation)
    8. signals: Dict (type validation)
    9. expected_elements: List[Dict] (type validation)
    10. metadata: Dict (type validation)

    Args:
        question: Raw question dictionary
        index: Index in question list for error reporting
        errors: List to accumulate errors
        warnings: List to accumulate warnings

    Returns:
        ValidatedQuestionSchema or None if validation failed
    """
    context = f"question[{index}]"

    try:
        question_id = question["question_id"]
    except KeyError:
        errors.append(f"Field 'question_id' not found in {context}: KeyError")
        return None

    if not isinstance(question_id, str):
        errors.append(
            f"Field 'question_id' has invalid type in {context}: "
            f"expected str, got {type(question_id).__name__}"
        )
        return None

    if not question_id:
        errors.append(f"Field 'question_id' is empty string in {context}")
        return None

    try:
        question_global = question["question_global"]
    except KeyError:
        errors.append(f"Field 'question_global' not found in {context}: KeyError")
        return None

    if not isinstance(question_global, int):
        errors.append(
            f"Field 'question_global' has invalid type in {context}: "
            f"expected int, got {type(question_global).__name__}"
        )
        return None

    if not (0 <= question_global <= MAX_QUESTION_GLOBAL):
        errors.append(
            f"Field 'question_global' has invalid value in {context}: "
            f"{question_global} not in range [0, {MAX_QUESTION_GLOBAL}]"
        )
        return None

    try:
        dimension_id = question["dimension_id"]
    except KeyError:
        errors.append(f"Field 'dimension_id' not found in {context}: KeyError")
        return None

    if not isinstance(dimension_id, str):
        errors.append(
            f"Field 'dimension_id' has invalid type in {context}: "
            f"expected str, got {type(dimension_id).__name__}"
        )
        return None

    if not dimension_id:
        errors.append(f"Field 'dimension_id' is empty string in {context}")
        return None

    try:
        policy_area_id = question["policy_area_id"]
    except KeyError:
        errors.append(f"Field 'policy_area_id' not found in {context}: KeyError")
        return None

    if not isinstance(policy_area_id, str):
        errors.append(
            f"Field 'policy_area_id' has invalid type in {context}: "
            f"expected str, got {type(policy_area_id).__name__}"
        )
        return None

    if not policy_area_id:
        errors.append(f"Field 'policy_area_id' is empty string in {context}")
        return None

    try:
        base_slot = question["base_slot"]
    except KeyError:
        base_slot = ""
        warnings.append(f"Field 'base_slot' not found in {context}; using empty string")

    if not isinstance(base_slot, str):
        errors.append(
            f"Field 'base_slot' has invalid type in {context}: "
            f"expected str, got {type(base_slot).__name__}"
        )
        return None

    try:
        cluster_id = question["cluster_id"]
    except KeyError:
        cluster_id = ""
        warnings.append(
            f"Field 'cluster_id' not found in {context}; using empty string"
        )

    if not isinstance(cluster_id, str):
        errors.append(
            f"Field 'cluster_id' has invalid type in {context}: "
            f"expected str, got {type(cluster_id).__name__}"
        )
        return None

    try:
        patterns = question["patterns"]
    except KeyError:
        errors.append(f"Field 'patterns' not found in {context}: KeyError")
        return None

    if not isinstance(patterns, list):
        errors.append(
            f"Field 'patterns' has invalid type in {context}: "
            f"expected list, got {type(patterns).__name__}"
        )
        return None

    try:
        signals = question["signals"]
    except KeyError:
        errors.append(f"Field 'signals' not found in {context}: KeyError")
        return None

    if not isinstance(signals, dict):
        errors.append(
            f"Field 'signals' has invalid type in {context}: "
            f"expected dict, got {type(signals).__name__}"
        )
        return None

    try:
        expected_elements = question["expected_elements"]
    except KeyError:
        expected_elements = []
        warnings.append(
            f"Field 'expected_elements' not found in {context}; using empty list"
        )

    if not isinstance(expected_elements, list):
        errors.append(
            f"Field 'expected_elements' has invalid type in {context}: "
            f"expected list, got {type(expected_elements).__name__}"
        )
        return None

    try:
        metadata = question["metadata"]
    except KeyError:
        metadata = {}
        warnings.append(f"Field 'metadata' not found in {context}; using empty dict")

    if not isinstance(metadata, dict):
        errors.append(
            f"Field 'metadata' has invalid type in {context}: "
            f"expected dict, got {type(metadata).__name__}"
        )
        return None

    return ValidatedQuestionSchema(
        question_id=question_id,
        question_global=question_global,
        dimension_id=dimension_id,
        policy_area_id=policy_area_id,
        base_slot=base_slot,
        cluster_id=cluster_id,
        patterns=patterns,
        signals=signals,
        expected_elements=expected_elements,
        metadata=metadata,
    )


def _validate_chunk_schema(  # noqa: PLR0911, PLR0912
    chunk: dict[str, Any],
    index: int,
    errors: list[str],
    warnings: list[str],
) -> ValidatedChunkSchema | None:
    """
    Validate a single chunk schema with explicit error handling.

    Validates fields in order:
    1. chunk_id: str (non-null, non-empty)
    2. policy_area_id: str (non-null, non-empty)
    3. dimension_id: str (non-null, non-empty)
    4. document_position: int (non-negative)
    5. content: str (non-empty)
    6. metadata: Dict (type validation)

    Args:
        chunk: Raw chunk dictionary
        index: Index in chunk list for error reporting
        errors: List to accumulate errors
        warnings: List to accumulate warnings

    Returns:
        ValidatedChunkSchema or None if validation failed
    """
    context = f"chunk[{index}]"

    try:
        chunk_id = chunk["chunk_id"]
    except KeyError:
        errors.append(f"Field 'chunk_id' not found in {context}: KeyError")
        return None

    if not isinstance(chunk_id, str):
        errors.append(
            f"Field 'chunk_id' has invalid type in {context}: "
            f"expected str, got {type(chunk_id).__name__}"
        )
        return None

    if not chunk_id:
        errors.append(f"Field 'chunk_id' is empty string in {context}")
        return None

    try:
        policy_area_id = chunk["policy_area_id"]
    except KeyError:
        errors.append(f"Field 'policy_area_id' not found in {context}: KeyError")
        return None

    if not isinstance(policy_area_id, str):
        errors.append(
            f"Field 'policy_area_id' has invalid type in {context}: "
            f"expected str, got {type(policy_area_id).__name__}"
        )
        return None

    if not policy_area_id:
        errors.append(f"Field 'policy_area_id' is empty string in {context}")
        return None

    try:
        dimension_id = chunk["dimension_id"]
    except KeyError:
        errors.append(f"Field 'dimension_id' not found in {context}: KeyError")
        return None

    if not isinstance(dimension_id, str):
        errors.append(
            f"Field 'dimension_id' has invalid type in {context}: "
            f"expected str, got {type(dimension_id).__name__}"
        )
        return None

    if not dimension_id:
        errors.append(f"Field 'dimension_id' is empty string in {context}")
        return None

    try:
        document_position = chunk["document_position"]
    except KeyError:
        document_position = 0
        warnings.append(f"Field 'document_position' not found in {context}; using 0")

    if not isinstance(document_position, int):
        errors.append(
            f"Field 'document_position' has invalid type in {context}: "
            f"expected int, got {type(document_position).__name__}"
        )
        return None

    if document_position < 0:
        errors.append(
            f"Field 'document_position' has invalid value in {context}: "
            f"{document_position} must be non-negative"
        )
        return None

    try:
        content = chunk["content"]
    except KeyError:
        errors.append(f"Field 'content' not found in {context}: KeyError")
        return None

    if not isinstance(content, str):
        errors.append(
            f"Field 'content' has invalid type in {context}: "
            f"expected str, got {type(content).__name__}"
        )
        return None

    if not content:
        errors.append(f"Field 'content' is empty string in {context}")
        return None

    try:
        metadata = chunk["metadata"]
    except KeyError:
        metadata = {}
        warnings.append(f"Field 'metadata' not found in {context}; using empty dict")

    if not isinstance(metadata, dict):
        errors.append(
            f"Field 'metadata' has invalid type in {context}: "
            f"expected dict, got {type(metadata).__name__}"
        )
        return None

    return ValidatedChunkSchema(
        chunk_id=chunk_id,
        policy_area_id=policy_area_id,
        dimension_id=dimension_id,
        document_position=document_position,
        content=content,
        metadata=metadata,
    )


def phase6_schema_validation(
    raw_questions: list[dict[str, Any]],
    raw_chunks: list[dict[str, Any]],
) -> Phase6SchemaValidationOutput:
    """
    Execute Phase 6: Schema Validation.

    Validates all questions and chunks with explicit error handling for:
    - KeyError: Missing required fields
    - TypeError: Incorrect field types
    - ValueError: Invalid field values

    All validation occurs BEFORE returning to ensure Phase 7 receives
    clean, type-validated data.

    Args:
        raw_questions: List of raw question dictionaries
        raw_chunks: List of raw chunk dictionaries

    Returns:
        Phase6SchemaValidationOutput with validated schemas or error details
    """
    logger.info("Phase 6: Schema Validation started")

    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    validated_questions: list[ValidatedQuestionSchema] = []
    validated_chunks: list[ValidatedChunkSchema] = []

    if not isinstance(raw_questions, list):
        validation_errors.append(
            f"raw_questions has invalid type: expected list, got {type(raw_questions).__name__}"
        )
        raw_questions = []

    if not isinstance(raw_chunks, list):
        validation_errors.append(
            f"raw_chunks has invalid type: expected list, got {type(raw_chunks).__name__}"
        )
        raw_chunks = []

    logger.info(f"Validating {len(raw_questions)} questions")

    for index, question in enumerate(raw_questions):
        if not isinstance(question, dict):
            validation_errors.append(
                f"question[{index}] has invalid type: expected dict, got {type(question).__name__}"
            )
            continue

        validated_question = _validate_question_schema(
            question, index, validation_errors, validation_warnings
        )

        if validated_question:
            validated_questions.append(validated_question)

    logger.info(
        f"Validated {len(validated_questions)}/{len(raw_questions)} questions "
        f"(errors: {len([e for e in validation_errors if 'question' in e])})"
    )

    logger.info(f"Validating {len(raw_chunks)} chunks")

    for index, chunk in enumerate(raw_chunks):
        if not isinstance(chunk, dict):
            validation_errors.append(
                f"chunk[{index}] has invalid type: expected dict, got {type(chunk).__name__}"
            )
            continue

        validated_chunk = _validate_chunk_schema(
            chunk, index, validation_errors, validation_warnings
        )

        if validated_chunk:
            validated_chunks.append(validated_chunk)

    logger.info(
        f"Validated {len(validated_chunks)}/{len(raw_chunks)} chunks "
        f"(errors: {len([e for e in validation_errors if 'chunk' in e])})"
    )

    schema_validation_passed = len(validation_errors) == 0

    validation_timestamp = datetime.now(timezone.utc).isoformat()

    output = Phase6SchemaValidationOutput(
        validated_questions=validated_questions,
        validated_chunks=validated_chunks,
        schema_validation_passed=schema_validation_passed,
        validation_errors=validation_errors,
        validation_warnings=validation_warnings,
        question_count=len(validated_questions),
        chunk_count=len(validated_chunks),
        validation_timestamp=validation_timestamp,
    )

    logger.info(
        f"Phase 6: Schema Validation completed "
        f"(passed={schema_validation_passed}, "
        f"questions={len(validated_questions)}, chunks={len(validated_chunks)}, "
        f"errors={len(validation_errors)}, warnings={len(validation_warnings)})"
    )

    return output


__all__ = [
    "Phase6SchemaValidationOutput",
    "ValidatedQuestionSchema",
    "ValidatedChunkSchema",
    "phase6_schema_validation",
    "PHASE6_VERSION",
    "MAX_QUESTION_GLOBAL",
]
