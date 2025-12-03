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
        patterns: List of pattern dictionaries with 'policy_area_id' field
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
            ValueError: If no chunk exists for the question's coordinates,
                       with descriptive message including question_id
        """
        try:
            return chunk_matrix.get_chunk(
                question.policy_area_id, question.dimension_id
            )
        except ValueError as e:
            raise ValueError(
                f"Failed to match chunk for question_id='{question.question_id}': {e}"
            ) from e

    def _filter_patterns(
        self, question: Question, target_pa_id: str
    ) -> tuple[dict[str, Any], ...]:
        """
        Filter patterns to only those matching target policy area.

        Iterates question.patterns and validates every pattern has 'policy_area_id'
        field (raising ValueError if missing). Filters to only patterns matching
        target_pa_id with tuple return type enforcing immutability. Logs warning
        when zero patterns match but does not fail.

        Args:
            question: Question containing patterns to filter
            target_pa_id: Target policy area ID to filter for

        Returns:
            Immutable tuple of patterns matching target_pa_id

        Raises:
            ValueError: If any pattern is missing 'policy_area_id' field
        """
        filtered: list[dict[str, Any]] = []

        for idx, pattern in enumerate(question.patterns):
            if "policy_area_id" not in pattern:
                raise ValueError(
                    f"Pattern at index {idx} for question_id='{question.question_id}' "
                    f"is missing required 'policy_area_id' field"
                )

            if pattern["policy_area_id"] == target_pa_id:
                filtered.append(pattern)

        if len(filtered) == 0:
            logger.warning(
                f"Zero patterns matched target_pa_id='{target_pa_id}' for "
                f"question_id='{question.question_id}'"
            )

        return tuple(filtered)
