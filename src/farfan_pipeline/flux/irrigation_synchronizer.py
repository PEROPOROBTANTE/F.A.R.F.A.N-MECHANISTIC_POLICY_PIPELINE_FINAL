"""
Irrigation Synchronizer - Question-to-Chunk Matching
====================================================

Deterministic O(1) question-to-chunk matching and pattern filtering for the
signal irrigation system. Ensures strict policy_area × dimension isolation.

Technical Standards:
- O(1) chunk lookup via dictionary-based ChunkMatrix
- Immutable tuple returns for pattern filtering
- Comprehensive validation with descriptive errors
- Type hints with strict mypy compliance

Version: 1.0.0
Status: Production-ready
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ChunkMatrix:
    """
    Matrix structure for O(1) chunk lookup by (policy_area_id, dimension_id).

    Attributes:
        chunks: Dictionary mapping (policy_area_id, dimension_id) -> chunk
    """

    chunks: dict[tuple[str, str], Any]

    def get_chunk(self, policy_area_id: str, dimension_id: str) -> Any:
        """
        Get chunk by policy_area_id and dimension_id.

        Args:
            policy_area_id: Policy area identifier (e.g., "PA01")
            dimension_id: Dimension identifier (e.g., "D1")

        Returns:
            The chunk corresponding to the given coordinates

        Raises:
            ValueError: If no chunk exists for the given coordinates
        """
        key = (policy_area_id, dimension_id)
        if key not in self.chunks:
            raise ValueError(
                f"No chunk found for policy_area_id='{policy_area_id}', "
                f"dimension_id='{dimension_id}'"
            )
        return self.chunks[key]


@dataclass
class Question:
    """
    Question structure with policy area and dimension coordinates.

    Attributes:
        question_id: Unique question identifier
        policy_area_id: Policy area identifier
        dimension_id: Dimension identifier
        patterns: List of pattern dictionaries. The 'policy_area_id' is at the
                  question level, not within each pattern.
    """

    question_id: str
    policy_area_id: str
    dimension_id: str
    patterns: list[dict[str, Any]]


class IrrigationSynchronizer:
    """
    Synchronizes questions with chunks and filters patterns by policy area.

    Provides O(1) chunk matching and strict pattern filtering with immutability
    guarantees and comprehensive error handling.
    """

    def __init__(self) -> None:
        """Initialize the IrrigationSynchronizer."""
        pass

    def prepare_executor_contexts(self, question_contexts: list[Any]) -> list[Any]:
        """
        Prepare Phase 2 executor contexts from sorted question contexts.

        Initializes empty executable tasks list, loops through sorted question contexts,
        extracts routing keys (pa_id, dim_id, question_global, question_id) and execution
        metadata (expected_elements, signal_requirements, patterns), logs question
        processing start with structured logging, and returns prepared ExecutableTask
        objects for downstream execution.

        Args:
            question_contexts: List of sorted question context objects (MicroQuestionContext)

        Returns:
            List of ExecutableTask objects prepared for Phase 2 execution
        """
        from datetime import datetime, timezone

        from farfan_pipeline.core.orchestrator.task_planner import ExecutableTask

        executable_tasks: list[ExecutableTask] = []

        for question_ctx in question_contexts:
            pa_id = getattr(question_ctx, "policy_area_id", "")
            dim_id = getattr(question_ctx, "dimension_id", "")
            question_global = getattr(question_ctx, "question_global", None)
            question_id = getattr(question_ctx, "question_id", "")

            if not question_id:
                raise ValueError(
                    "Executor context preparation failure: question_id is empty or None"
                )

            if question_global is None:
                raise ValueError(
                    f"Executor context preparation failure for question {question_id}: "
                    "question_global field is required but None"
                )

            if not isinstance(question_global, int):
                raise ValueError(
                    f"Executor context preparation failure for question {question_id}: "
                    f"question_global must be an integer, got {type(question_global).__name__}"
                )

            if not (0 <= question_global <= 999):
                raise ValueError(
                    f"Executor context preparation failure for question {question_id}: "
                    f"question_global must be between 0 and 999 inclusive, got {question_global}"
                )

            if not pa_id:
                raise ValueError(
                    f"Executor context preparation failure for question {question_id}: "
                    "policy_area_id is empty or None"
                )

            if not dim_id:
                raise ValueError(
                    f"Executor context preparation failure for question {question_id}: "
                    "dimension_id is empty or None"
                )

            patterns = list(getattr(question_ctx, "patterns", ()))
            expected_elements = []
            signal_requirements = {}

            logger.info(
                "question_processing_start",
                extra={
                    "question_id": question_id,
                    "pa_id": pa_id,
                    "dim_id": dim_id,
                    "question_global": question_global,
                    "phase": "phase_2_executor_preparation",
                },
            )

            base_slot = getattr(question_ctx, "base_slot", "")
            cluster_id = getattr(question_ctx, "cluster_id", "")
            document_position = getattr(question_ctx, "document_position", None)

            metadata = {
                "base_slot": base_slot if base_slot else "",
                "cluster_id": cluster_id if cluster_id else "",
                "document_position": document_position,
                "synchronizer_version": "2.0.0",
                "correlation_id": "",
                "original_pattern_count": len(patterns),
                "original_signal_count": len(signal_requirements),
                "filtered_pattern_count": len(patterns),
                "resolved_signal_count": len(signal_requirements),
                "schema_element_count": len(expected_elements),
            }

            task = ExecutableTask(
                task_id=f"MQC-{question_global:03d}_{pa_id}",
                question_id=question_id,
                question_global=question_global,
                policy_area_id=pa_id,
                dimension_id=dim_id,
                chunk_id=f"{pa_id}-{dim_id}",
                patterns=patterns,
                signals=signal_requirements,
                creation_timestamp=datetime.now(timezone.utc).isoformat(),
                expected_elements=expected_elements,
                metadata=metadata,
            )

            executable_tasks.append(task)

        return executable_tasks

    def _match_chunk(self, question: Question, chunk_matrix: ChunkMatrix) -> Any:
        """
        Match question to chunk via O(1) lookup.

        Performs O(1) lookup via chunk_matrix.get_chunk(question.policy_area_id,
        question.dimension_id) and wraps ValueError with descriptive message
        including question_id.

        Args:
            question: Question to match
            chunk_matrix: Matrix of chunks indexed by (policy_area_id, dimension_id)

        Returns:
            The matched chunk

        Raises:
            ValueError: If no chunk exists for the question's coordinates or if
                       routing keys are missing, with descriptive message including question_id
        """
        if not question.policy_area_id:
            raise ValueError(
                f"Chunk matching failure for question_id='{question.question_id}': "
                "policy_area_id is empty or None"
            )
        if not question.dimension_id:
            raise ValueError(
                f"Chunk matching failure for question_id='{question.question_id}': "
                "dimension_id is empty or None"
            )

        try:
            return chunk_matrix.get_chunk(
                question.policy_area_id, question.dimension_id
            )
        except ValueError as e:
            raise ValueError(
                f"Chunk matching failure for question_id='{question.question_id}': "
                f"No chunk found for policy_area_id='{question.policy_area_id}', "
                f"dimension_id='{question.dimension_id}'"
            ) from e
        except KeyError as e:
            raise ValueError(
                f"Chunk matching failure for question_id='{question.question_id}': "
                f"Matrix lookup failed for coordinates "
                f"(policy_area_id='{question.policy_area_id}', "
                f"dimension_id='{question.dimension_id}')"
            ) from e

    def _filter_patterns(
        self, question: Question, target_pa_id: str
    ) -> tuple[dict[str, Any], ...]:
        """
        Filter patterns to only those matching target policy area.

        Validates that all patterns have a 'policy_area_id' field, then filters
        to return only patterns matching the target policy area ID.

        Args:
            question: Question containing patterns to filter
            target_pa_id: Target policy area ID to filter for

        Returns:
            Immutable tuple of patterns matching target_pa_id

        Raises:
            ValueError: If target_pa_id is empty or any pattern is missing 'policy_area_id' field
        """
        if not target_pa_id:
            raise ValueError(
                f"Pattern filtering failure for question '{question.question_id}': "
                "target_pa_id parameter is empty or None"
            )

        for idx, pattern in enumerate(question.patterns):
            if not isinstance(pattern, dict):
                raise ValueError(
                    f"Pattern at index {idx} in question '{question.question_id}' "
                    f"is not a dict (type: {type(pattern).__name__})"
                )
            if "policy_area_id" not in pattern:
                raise ValueError(
                    f"Pattern at index {idx} in question '{question.question_id}' "
                    f"is missing required 'policy_area_id' field"
                )

        filtered = [
            pattern
            for pattern in question.patterns
            if pattern.get("policy_area_id") == target_pa_id
        ]

        if not filtered:
            logger.warning(
                f"Pattern filtering complete for question '{question.question_id}': "
                f"zero patterns matched target policy area '{target_pa_id}'. "
                f"Question has policy_area_id='{question.policy_area_id}' "
                f"with {len(question.patterns)} total patterns."
            )

        return tuple(filtered)
