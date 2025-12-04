"""Irrigation Synchronizer - Question→Chunk→Task→Plan Coordination.

This module implements the synchronization layer that maps questionnaire questions
to document chunks, generating an ExecutionPlan with 300 tasks (6 dimensions × 50
questions/dimension × 10 policy areas) for deterministic pipeline execution.

Architecture:
- IrrigationSynchronizer: Orchestrates chunk→question→task→plan flow
- ExecutionPlan: Immutable plan with deterministic plan_id and integrity_hash
- Task: Single unit of work (question + chunk + policy_area)
- Observability: Structured JSON logs with correlation_id tracking

Design Principles:
- Deterministic task generation (stable ordering, reproducible plan_id)
- Full observability (correlation_id propagates through all 10 phases)
- Prometheus metrics for synchronization health
- Blake3-based integrity hashing for plan verification
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any

from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.synchronization import ChunkMatrix

try:
    import blake3

    BLAKE3_AVAILABLE = True
except ImportError:
    BLAKE3_AVAILABLE = False

try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = logging.getLogger(__name__)

if PROMETHEUS_AVAILABLE:
    synchronization_duration = Histogram(
        "synchronization_duration_seconds",
        "Time spent building execution plan",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    )
    tasks_constructed = Counter(
        "synchronization_tasks_constructed_total",
        "Total number of tasks constructed",
        ["dimension", "policy_area"],
    )
    synchronization_failures = Counter(
        "synchronization_failures_total",
        "Total synchronization failures",
        ["error_type"],
    )
    synchronization_chunk_matches = Counter(
        "synchronization_chunk_matches_total",
        "Chunk routing match results",
        ["dimension", "policy_area", "status"],
    )
else:

    class DummyMetric:
        def time(self):
            class DummyContextManager:
                def __call__(self, func):
                    def wrapper(*args, **kwargs):
                        return func(*args, **kwargs)

                    return wrapper

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    pass

            return DummyContextManager()

        def labels(self, **kwargs):
            return self

        def inc(self, *args, **kwargs) -> None:
            pass

    synchronization_duration = DummyMetric()
    tasks_constructed = DummyMetric()
    synchronization_failures = DummyMetric()
    synchronization_chunk_matches = DummyMetric()


@dataclass(frozen=True)
class ChunkRoutingResult:
    """Immutable result of Phase 3 chunk routing verification.

    Contains validated chunk reference and extracted metadata for
    downstream task construction in Phases 4-7.
    """

    target_chunk: ChunkData
    chunk_id: str
    policy_area_id: str
    dimension_id: str
    text_content: str
    expected_elements: list[dict[str, Any]]
    document_position: tuple[int, int] | None


@dataclass(frozen=True)
class Task:
    """Single unit of work in the execution plan.

    Represents the mapping of one question to one chunk in a specific policy area.
    """

    task_id: str
    dimension: str
    question_id: str
    policy_area: str
    chunk_id: str
    chunk_index: int
    question_text: str


@dataclass(frozen=True)
class ExecutionPlan:
    """Immutable execution plan with deterministic identifiers.

    Contains all tasks to be executed, with cryptographic integrity verification.
    """

    plan_id: str
    tasks: tuple[Task, ...]
    chunk_count: int
    question_count: int
    integrity_hash: str
    created_at: str
    correlation_id: str

    def to_dict(self) -> dict[str, Any]:
        """Convert plan to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "tasks": [
                {
                    "task_id": t.task_id,
                    "dimension": t.dimension,
                    "question_id": t.question_id,
                    "policy_area": t.policy_area,
                    "chunk_id": t.chunk_id,
                    "chunk_index": t.chunk_index,
                    "question_text": t.question_text,
                }
                for t in self.tasks
            ],
            "chunk_count": self.chunk_count,
            "question_count": self.question_count,
            "integrity_hash": self.integrity_hash,
            "created_at": self.created_at,
            "correlation_id": self.correlation_id,
        }


class IrrigationSynchronizer:
    """Synchronizes questionnaire questions with document chunks.

    Generates deterministic execution plans mapping questions to chunks across
    all policy areas, with full observability and integrity verification.
    """

    def __init__(
        self,
        questionnaire: dict[str, Any],
        preprocessed_document: PreprocessedDocument | None = None,
        document_chunks: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize synchronizer with questionnaire and chunks.

        Args:
            questionnaire: Loaded questionnaire_monolith.json data
            preprocessed_document: PreprocessedDocument containing validated chunks
            document_chunks: Legacy list of document chunks (deprecated)

        Raises:
            ValueError: If chunk matrix validation fails or no chunks provided
        """
        self.questionnaire = questionnaire
        self.correlation_id = str(uuid.uuid4())
        self.question_count = self._count_questions()
        self.chunk_matrix: ChunkMatrix | None = None
        self.document_chunks: list[dict[str, Any]] | None = None

        if preprocessed_document is not None:
            try:
                self.chunk_matrix = ChunkMatrix(preprocessed_document)
                self.chunk_count = ChunkMatrix.EXPECTED_CHUNK_COUNT

                logger.info(
                    json.dumps(
                        {
                            "event": "irrigation_synchronizer_init",
                            "correlation_id": self.correlation_id,
                            "question_count": self.question_count,
                            "chunk_count": self.chunk_count,
                            "chunk_matrix_validated": True,
                            "mode": "preprocessed_document",
                            "timestamp": time.time(),
                        }
                    )
                )
            except ValueError as e:
                synchronization_failures.labels(
                    error_type="chunk_matrix_validation"
                ).inc()
                logger.error(
                    json.dumps(
                        {
                            "event": "irrigation_synchronizer_init_failed",
                            "correlation_id": self.correlation_id,
                            "error": str(e),
                            "error_type": "chunk_matrix_validation",
                            "timestamp": time.time(),
                        }
                    )
                )
                raise ValueError(
                    f"Chunk matrix validation failed during synchronizer initialization: {e}"
                ) from e
        elif document_chunks is not None:
            self.document_chunks = document_chunks
            self.chunk_count = len(document_chunks)

            logger.info(
                json.dumps(
                    {
                        "event": "irrigation_synchronizer_init",
                        "correlation_id": self.correlation_id,
                        "question_count": self.question_count,
                        "chunk_count": self.chunk_count,
                        "mode": "legacy_document_chunks",
                        "timestamp": time.time(),
                    }
                )
            )
        else:
            raise ValueError(
                "Either preprocessed_document or document_chunks must be provided"
            )

    def _count_questions(self) -> int:
        """Count total questions across all dimensions."""
        count = 0
        blocks = self.questionnaire.get("blocks", {})

        for dimension_key in ["D1", "D2", "D3", "D4", "D5", "D6"]:
            for i in range(1, 51):
                question_key = f"D{dimension_key[1]}_Q{i:02d}"
                if question_key in blocks:
                    count += 1

        return count

    def validate_chunk_routing(self, question: dict[str, Any]) -> ChunkRoutingResult:
        """Route chunk for question with Phase 3 multi-stage verification.

        This method implements P3.1-P3.10 of the irrigation synchronization
        specification. It extracts routing keys from the question, queries
        the chunk matrix, verifies consistency across multiple dimensions,
        and extracts chunk payload for downstream processing.

        Args:
            question: Question dictionary from questionnaire with routing keys
                Required keys: question_id, policy_area_id, dimension_id
                Optional keys: question_text, expected_elements, patterns, etc.

        Returns:
            ChunkRoutingResult with validated chunk and extracted metadata

        Raises:
            ValueError: If question missing required fields
            ValueError: If no chunk found for routing keys (synchronization failure)
            ValueError: If chunk routing keys inconsistent (corruption detected)
            ValueError: If chunk text empty or whitespace-only

        Example:
            >>> question = {
            ...     "question_id": "D1-Q01",
            ...     "policy_area_id": "PA05",
            ...     "dimension_id": "DIM03"
            ... }
            >>> result = synchronizer.validate_chunk_routing(question)
            >>> print(result.chunk_id)
            PA05-DIM03
        """
        question_id = question.get("question_id")
        if not question_id:
            raise ValueError(
                "Question missing required 'question_id' field. "
                "Cannot route chunk without question identifier."
            )

        policy_area_id = question.get("policy_area_id")
        if not policy_area_id:
            raise ValueError(
                f"Question {question_id} missing required 'policy_area_id' field. "
                "All questions must specify target policy area for chunk routing."
            )

        dimension_id = question.get("dimension_id")
        if not dimension_id:
            raise ValueError(
                f"Question {question_id} missing required 'dimension_id' field. "
                "All questions must specify target dimension for chunk routing."
            )

        lookup_key = (policy_area_id, dimension_id)

        logger.debug(
            json.dumps(
                {
                    "event": "chunk_routing_start",
                    "question_id": question_id,
                    "policy_area_id": policy_area_id,
                    "dimension_id": dimension_id,
                    "lookup_key": list(lookup_key),
                    "correlation_id": self.correlation_id,
                }
            )
        )

        try:
            target_chunk = self.chunk_matrix.get_chunk(policy_area_id, dimension_id)
        except KeyError as e:
            synchronization_chunk_matches.labels(
                dimension=dimension_id, policy_area=policy_area_id, status="failure"
            ).inc()

            raise ValueError(
                f"Synchronization Failure for MQC {question_id}: "
                f"PA={policy_area_id}, DIM={dimension_id}. "
                f"No corresponding chunk found in matrix. "
                f"This indicates incomplete chunk coverage - expected all combinations "
                f"of PA01-PA10 × DIM01-DIM06 to be present."
            ) from e

        if target_chunk.policy_area_id != policy_area_id:
            raise ValueError(
                f"Policy area mismatch for question {question_id}: "
                f"Routing key specifies PA={policy_area_id} but chunk has PA={target_chunk.policy_area_id}. "
                f"Chunk ID: {target_chunk.chunk_id}"
            )

        if target_chunk.dimension_id != dimension_id:
            raise ValueError(
                f"Dimension mismatch for question {question_id}: "
                f"Routing key specifies DIM={dimension_id} but chunk has DIM={target_chunk.dimension_id}. "
                f"Chunk ID: {target_chunk.chunk_id}"
            )

        expected_chunk_id = f"{policy_area_id}-{dimension_id}"
        if target_chunk.chunk_id != expected_chunk_id:
            raise ValueError(
                f"Chunk identity inconsistency for question {question_id}: "
                f"Expected chunk_id={expected_chunk_id} based on routing keys, "
                f"but chunk has chunk_id={target_chunk.chunk_id}"
            )

        text_content = target_chunk.text
        if not text_content or not text_content.strip():
            raise ValueError(
                f"Chunk {target_chunk.chunk_id} has empty or whitespace-only text. "
                f"Cannot process question {question_id} without chunk content."
            )

        expected_elements = getattr(target_chunk, "expected_elements", [])
        if expected_elements is None:
            expected_elements = []
        expected_elements = list(expected_elements)

        document_position = getattr(target_chunk, "document_position", None)
        if document_position is None and hasattr(target_chunk, "provenance"):
            provenance = target_chunk.provenance
            if provenance and hasattr(provenance, "span_in_page"):
                document_position = provenance.span_in_page

        synchronization_chunk_matches.labels(
            dimension=dimension_id, policy_area=policy_area_id, status="success"
        ).inc()

        logger.debug(
            json.dumps(
                {
                    "event": "chunk_routing_success",
                    "question_id": question_id,
                    "chunk_id": target_chunk.chunk_id,
                    "policy_area_id": policy_area_id,
                    "dimension_id": dimension_id,
                    "text_length": len(text_content),
                    "has_expected_elements": len(expected_elements) > 0,
                    "has_document_position": document_position is not None,
                    "correlation_id": self.correlation_id,
                    "timestamp": time.time(),
                }
            )
        )

        return ChunkRoutingResult(
            target_chunk=target_chunk,
            chunk_id=target_chunk.chunk_id,
            policy_area_id=policy_area_id,
            dimension_id=dimension_id,
            text_content=text_content,
            expected_elements=expected_elements,
            document_position=document_position,
        )

    def _extract_questions(self) -> list[dict[str, Any]]:
        """Extract all questions from questionnaire in deterministic order."""
        questions = []
        blocks = self.questionnaire.get("blocks", {})

        for dimension in range(1, 7):
            dim_key = f"D{dimension}"

            for q_num in range(1, 51):
                question_key = f"{dim_key}_Q{q_num:02d}"

                if question_key in blocks:
                    block = blocks[question_key]
                    questions.append(
                        {
                            "dimension": dim_key,
                            "question_id": question_key,
                            "question_num": q_num,
                            "question_text": block.get("question", ""),
                            "patterns": block.get("patterns", []),
                        }
                    )

        return questions

    def _compute_integrity_hash(self, tasks: list[Task]) -> str:
        """Compute Blake3 or SHA256 integrity hash of execution plan."""
        task_data = json.dumps(
            [
                {
                    "task_id": t.task_id,
                    "dimension": t.dimension,
                    "question_id": t.question_id,
                    "policy_area": t.policy_area,
                    "chunk_id": t.chunk_id,
                }
                for t in tasks
            ],
            sort_keys=True,
        ).encode("utf-8")

        if BLAKE3_AVAILABLE:
            return blake3.blake3(task_data).hexdigest()
        else:
            return hashlib.sha256(task_data).hexdigest()

    @synchronization_duration.time()
    def build_execution_plan(self) -> ExecutionPlan:
        """Build deterministic execution plan mapping questions to chunks.

        Uses validated chunk matrix if available, otherwise falls back to
        legacy document_chunks iteration mode.

        Returns:
            ExecutionPlan with deterministic plan_id and integrity_hash

        Raises:
            ValueError: If question data is invalid or chunk matrix lookup fails
        """
        if self.chunk_matrix is not None:
            return self._build_with_chunk_matrix()
        else:
            return self._build_with_legacy_chunks()

    def _build_with_chunk_matrix(self) -> ExecutionPlan:
        """Build execution plan using validated chunk matrix."""
        logger.info(
            json.dumps(
                {
                    "event": "build_execution_plan_start",
                    "correlation_id": self.correlation_id,
                    "question_count": self.question_count,
                    "chunk_count": self.chunk_count,
                    "mode": "chunk_matrix",
                    "phase": "synchronization_phase_0",
                }
            )
        )

        try:
            if self.question_count == 0:
                synchronization_failures.labels(error_type="empty_questions").inc()
                raise ValueError("No questions found in questionnaire")

            questions = self._extract_questions()
            policy_areas = ChunkMatrix.POLICY_AREAS
            dimensions = ChunkMatrix.DIMENSIONS

            tasks: list[Task] = []

            for question in questions:
                dimension_id = f"DIM{question['dimension'][1:].zfill(2)}"

                if dimension_id not in dimensions:
                    synchronization_failures.labels(
                        error_type="invalid_dimension"
                    ).inc()
                    raise ValueError(
                        f"Invalid dimension '{dimension_id}' for question "
                        f"'{question['question_id']}': must be one of {dimensions}"
                    )

                for policy_area in policy_areas:
                    try:
                        chunk = self.chunk_matrix.get_chunk(policy_area, dimension_id)

                        chunk_id = f"{chunk.policy_area_id}-{chunk.dimension_id}"

                        task_id = f"{question['question_id']}_{policy_area}_{chunk_id}"

                        task = Task(
                            task_id=task_id,
                            dimension=question["dimension"],
                            question_id=question["question_id"],
                            policy_area=policy_area,
                            chunk_id=chunk_id,
                            chunk_index=chunk.id,
                            question_text=question["question_text"],
                        )

                        tasks.append(task)

                        tasks_constructed.labels(
                            dimension=question["dimension"], policy_area=policy_area
                        ).inc()

                    except KeyError as e:
                        synchronization_failures.labels(
                            error_type="chunk_lookup_failure"
                        ).inc()
                        raise ValueError(
                            f"Failed to retrieve chunk for policy_area='{policy_area}', "
                            f"dimension='{dimension_id}', question='{question['question_id']}': {e}"
                        ) from e

            integrity_hash = self._compute_integrity_hash(tasks)

            plan_id = f"plan_{integrity_hash[:16]}"

            plan = ExecutionPlan(
                plan_id=plan_id,
                tasks=tuple(tasks),
                chunk_count=self.chunk_count,
                question_count=len(questions),
                integrity_hash=integrity_hash,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                correlation_id=self.correlation_id,
            )

            logger.info(
                json.dumps(
                    {
                        "event": "build_execution_plan_complete",
                        "correlation_id": self.correlation_id,
                        "plan_id": plan_id,
                        "task_count": len(tasks),
                        "chunk_count": self.chunk_count,
                        "question_count": len(questions),
                        "integrity_hash": integrity_hash,
                        "chunk_matrix_validated": True,
                        "mode": "chunk_matrix",
                        "phase": "synchronization_phase_complete",
                    }
                )
            )

            return plan

        except ValueError as e:
            synchronization_failures.labels(error_type="validation_failure").inc()
            logger.error(
                json.dumps(
                    {
                        "event": "build_execution_plan_error",
                        "correlation_id": self.correlation_id,
                        "error": str(e),
                        "error_type": "validation_failure",
                    }
                )
            )
            raise
        except Exception as e:
            synchronization_failures.labels(error_type=type(e).__name__).inc()
            logger.error(
                json.dumps(
                    {
                        "event": "build_execution_plan_error",
                        "correlation_id": self.correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
            )
            raise

    def _build_with_legacy_chunks(self) -> ExecutionPlan:
        """Build execution plan using legacy document_chunks list."""
        logger.info(
            json.dumps(
                {
                    "event": "build_execution_plan_start",
                    "correlation_id": self.correlation_id,
                    "question_count": self.question_count,
                    "chunk_count": self.chunk_count,
                    "mode": "legacy_chunks",
                    "phase": "synchronization_phase_0",
                }
            )
        )

        try:
            if not self.document_chunks:
                synchronization_failures.labels(error_type="empty_chunks").inc()
                raise ValueError("No document chunks provided")

            if self.question_count == 0:
                synchronization_failures.labels(error_type="empty_questions").inc()
                raise ValueError("No questions found in questionnaire")

            questions = self._extract_questions()
            policy_areas = [f"PA{i:02d}" for i in range(1, 11)]

            tasks: list[Task] = []

            for question in questions:
                for policy_area in policy_areas:
                    for chunk_idx, chunk in enumerate(self.document_chunks):
                        chunk_id = chunk.get("chunk_id", f"chunk_{chunk_idx:04d}")

                        task_id = f"{question['question_id']}_{policy_area}_{chunk_id}"

                        task = Task(
                            task_id=task_id,
                            dimension=question["dimension"],
                            question_id=question["question_id"],
                            policy_area=policy_area,
                            chunk_id=chunk_id,
                            chunk_index=chunk_idx,
                            question_text=question["question_text"],
                        )

                        tasks.append(task)

                        tasks_constructed.labels(
                            dimension=question["dimension"], policy_area=policy_area
                        ).inc()

            integrity_hash = self._compute_integrity_hash(tasks)

            plan_id = f"plan_{integrity_hash[:16]}"

            plan = ExecutionPlan(
                plan_id=plan_id,
                tasks=tuple(tasks),
                chunk_count=self.chunk_count,
                question_count=len(questions),
                integrity_hash=integrity_hash,
                created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                correlation_id=self.correlation_id,
            )

            logger.info(
                json.dumps(
                    {
                        "event": "build_execution_plan_complete",
                        "correlation_id": self.correlation_id,
                        "plan_id": plan_id,
                        "task_count": len(tasks),
                        "chunk_count": self.chunk_count,
                        "question_count": len(questions),
                        "integrity_hash": integrity_hash,
                        "mode": "legacy_chunks",
                        "phase": "synchronization_phase_complete",
                    }
                )
            )

            return plan

        except Exception as e:
            synchronization_failures.labels(error_type=type(e).__name__).inc()
            logger.error(
                json.dumps(
                    {
                        "event": "build_execution_plan_error",
                        "correlation_id": self.correlation_id,
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
            )
            raise


__all__ = [
    "IrrigationSynchronizer",
    "ExecutionPlan",
    "Task",
    "ChunkRoutingResult",
]
