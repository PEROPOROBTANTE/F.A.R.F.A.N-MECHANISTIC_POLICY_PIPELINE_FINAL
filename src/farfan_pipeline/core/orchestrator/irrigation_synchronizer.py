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
import statistics
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.signals import SignalRegistry

from farfan_pipeline.core.orchestrator.task_planner import ExecutableTask
from farfan_pipeline.core.orchestrator.phase6_validation import (
    validate_phase6_schema_compatibility,
)
from farfan_pipeline.core.types import ChunkData, PreprocessedDocument
from farfan_pipeline.synchronization import ChunkMatrix

try:
    from farfan_pipeline.core.orchestrator.signals import (
        SignalRegistry as _SignalRegistry,
    )
except ImportError:
    _SignalRegistry = None  # type: ignore

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

SHA256_HEX_DIGEST_LENGTH = 64

SKEW_THRESHOLD_CV = 0.3

class SignalRegistry(Protocol):
    """Protocol for signal registry implementations.

    Defines the interface that signal registries must implement for
    use with IrrigationSynchronizer signal resolution.
    """

    def get_signals_for_chunk(
        self, chunk: ChunkData, requirements: list[str]
    ) -> list[Any]:
        """Get signals for a chunk matching the given requirements.

        Args:
            chunk: Target chunk to get signals for
            requirements: List of required signal types

        Returns:
            List of signals, each with signal_id, signal_type, and content fields
        """
        ...


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
        "Total chunk routing matches during synchronization",
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

SHA256_HEX_DIGEST_LENGTH = 64


@dataclass(frozen=True)
class ChunkRoutingResult:
    """Result of Phase 3 chunk routing verification.

    Contains validated chunk reference and extracted metadata for task construction.
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


@dataclass
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
    metadata: dict[str, Any] = field(default_factory=dict)

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
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionPlan:
        """Reconstruct ExecutionPlan from dictionary.

        Args:
            data: Dictionary representation of ExecutionPlan

        Returns:
            ExecutionPlan instance reconstructed from dictionary
        """
        tasks = tuple(
            Task(
                task_id=t["task_id"],
                dimension=t["dimension"],
                question_id=t["question_id"],
                policy_area=t["policy_area"],
                chunk_id=t["chunk_id"],
                chunk_index=t["chunk_index"],
                question_text=t["question_text"],
            )
            for t in data["tasks"]
        )

        return cls(
            plan_id=data["plan_id"],
            tasks=tasks,
            chunk_count=data["chunk_count"],
            question_count=data["question_count"],
            integrity_hash=data["integrity_hash"],
            created_at=data["created_at"],
            correlation_id=data["correlation_id"],
        )


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
        signal_registry: SignalRegistry | None = None,
    ) -> None:
        """Initialize synchronizer with questionnaire and chunks.

        Args:
            questionnaire: Loaded questionnaire_monolith.json data
            preprocessed_document: PreprocessedDocument containing validated chunks
            document_chunks: Legacy list of document chunks (deprecated)
            signal_registry: SignalRegistry for Phase 5 signal resolution (initialized if None)

        Raises:
            ValueError: If chunk matrix validation fails or no chunks provided
        """
        self.questionnaire = questionnaire
        self.correlation_id = str(uuid.uuid4())
        self.question_count = self._count_questions()
        self.chunk_matrix: ChunkMatrix | None = None
        self.document_chunks: list[dict[str, Any]] | None = None

        if signal_registry is None and _SignalRegistry is not None:
            self.signal_registry: SignalRegistry | None = _SignalRegistry()
        else:
            self.signal_registry = signal_registry

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
        """Phase 3: Validate chunk routing and extract metadata.

        Verifies that a chunk exists in the matrix for the question's routing keys,
        validates chunk consistency, and extracts metadata for task construction.

        Args:
            question: Question dict with routing keys (policy_area_id, dimension_id)

        Returns:
            ChunkRoutingResult with validated chunk and extracted metadata

        Raises:
            ValueError: If chunk not found or validation fails
        """
        question_id = question.get("question_id", "UNKNOWN")
        policy_area_id = question.get("policy_area_id")
        dimension_id = question.get("dimension_id")

        if not policy_area_id:
            raise ValueError(
                f"Question {question_id} missing required field: policy_area_id"
            )

        if not dimension_id:
            raise ValueError(
                f"Question {question_id} missing required field: dimension_id"
            )

        try:
            target_chunk = self.chunk_matrix.get_chunk(policy_area_id, dimension_id)

            chunk_id = target_chunk.chunk_id or f"{policy_area_id}-{dimension_id}"

            if not target_chunk.text or not target_chunk.text.strip():
                raise ValueError(
                    f"Chunk {chunk_id} has empty text content for question {question_id}"
                )

            if (
                target_chunk.policy_area_id
                and target_chunk.policy_area_id != policy_area_id
            ):
                raise ValueError(
                    f"Chunk routing key mismatch for {question_id}: "
                    f"question policy_area={policy_area_id} but chunk has {target_chunk.policy_area_id}"
                )

            if target_chunk.dimension_id and target_chunk.dimension_id != dimension_id:
                raise ValueError(
                    f"Chunk routing key mismatch for {question_id}: "
                    f"question dimension={dimension_id} but chunk has {target_chunk.dimension_id}"
                )

            expected_elements = question.get("expected_elements", [])

            document_position = None
            if target_chunk.start_pos is not None and target_chunk.end_pos is not None:
                document_position = (target_chunk.start_pos, target_chunk.end_pos)

            synchronization_chunk_matches.labels(
                dimension=dimension_id, policy_area=policy_area_id, status="success"
            ).inc()

            logger.debug(
                json.dumps(
                    {
                        "event": "chunk_routing_success",
                        "question_id": question_id,
                        "chunk_id": chunk_id,
                        "policy_area_id": policy_area_id,
                        "dimension_id": dimension_id,
                        "text_length": len(target_chunk.text),
                        "has_expected_elements": len(expected_elements) > 0,
                        "has_document_position": document_position is not None,
                        "correlation_id": self.correlation_id,
                    }
                )
            )

            return ChunkRoutingResult(
                target_chunk=target_chunk,
                chunk_id=chunk_id,
                policy_area_id=policy_area_id,
                dimension_id=dimension_id,
                text_content=target_chunk.text,
                expected_elements=expected_elements,
                document_position=document_position,
            )

        except KeyError as e:
            synchronization_chunk_matches.labels(
                dimension=dimension_id, policy_area=policy_area_id, status="failure"
            ).inc()

            error_msg = (
                f"Synchronization Failure for MQC {question_id}: "
                f"PA={policy_area_id}, DIM={dimension_id}. "
                f"No corresponding chunk found in matrix."
            )

            logger.error(
                json.dumps(
                    {
                        "event": "chunk_routing_failure",
                        "question_id": question_id,
                        "policy_area_id": policy_area_id,
                        "dimension_id": dimension_id,
                        "error": error_msg,
                        "correlation_id": self.correlation_id,
                    }
                )
            )

            raise ValueError(error_msg) from e

    def _extract_questions(self) -> list[dict[str, Any]]:
        """Extract all questions from questionnaire in deterministic order."""
        questions = []
        blocks = self.questionnaire.get("blocks", {})

        for dimension in range(1, 7):
            dim_key = f"D{dimension}"
            dimension_id = f"DIM{dimension:02d}"

            for q_num in range(1, 51):
                question_key = f"{dim_key}_Q{q_num:02d}"

                if question_key in blocks:
                    block = blocks[question_key]
                    questions.append(
                        {
                            "dimension": dim_key,
                            "question_id": question_key,
                            "question_num": q_num,
                            "question_global": block.get("question_global", 0),
                            "question_text": block.get("question", ""),
                            "policy_area_id": block.get("policy_area_id"),
                            "dimension_id": dimension_id,
                            "patterns": block.get("patterns", []),
                            "expected_elements": block.get("expected_elements", []),
                            "signal_requirements": block.get("signal_requirements", {}),
                        }
                    )

        questions.sort(key=lambda q: (q["dimension_id"], q["question_id"]))

        return questions

    def _filter_patterns(
        self,
        patterns: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        policy_area_id: str,
    ) -> tuple[dict[str, Any], ...]:
        """Filter patterns by policy_area_id using strict equality.

        Filters patterns to include only those where pattern.policy_area_id == policy_area_id
        (strict equality). Patterns lacking a policy_area_id attribute are excluded.

        Args:
            patterns: Iterable of pattern objects (typically dicts with optional policy_area_id)
            policy_area_id: Policy area ID string (e.g., "PA01") to filter by

        Returns:
            Immutable tuple of filtered pattern dicts. Returns empty tuple if no patterns match.

        Filtering Rules:
            - Strict equality: pattern.policy_area_id == policy_area_id
            - Exclude patterns without policy_area_id attribute
            - Result is immutable (tuple)
        """
        included = []
        excluded = []
        included_ids = []
        excluded_ids = []

        for pattern in patterns:
            pattern_id = (
                pattern.get("id", "UNKNOWN") if isinstance(pattern, dict) else "UNKNOWN"
            )

            if isinstance(pattern, dict) and "policy_area_id" in pattern:
                if pattern["policy_area_id"] == policy_area_id:
                    included.append(pattern)
                    included_ids.append(pattern_id)
                else:
                    excluded.append(pattern)
                    excluded_ids.append(pattern_id)
            else:
                excluded.append(pattern)
                excluded_ids.append(pattern_id)

        total_count = len(included) + len(excluded)

        logger.info(
            json.dumps(
                {
                    "event": "IrrigationSynchronizer._filter_patterns",
                    "total": total_count,
                    "included": len(included),
                    "excluded": len(excluded),
                    "included_ids": included_ids,
                    "excluded_ids": excluded_ids,
                    "policy_area_id": policy_area_id,
                    "correlation_id": self.correlation_id,
                }
            )
        )

        return tuple(included)

    def _construct_task(
        self,
        question: dict[str, Any],
        routing_result: ChunkRoutingResult,
        applicable_patterns: tuple[dict[str, Any], ...],
        resolved_signals: tuple[Any, ...],
        generated_task_ids: set[str],
    ) -> ExecutableTask:
        """Construct ExecutableTask from question and routing result.

        Extracts all fields from validated inputs, converts tuples to lists for patterns,
        builds signals dict keyed by signal_type, generates creation_timestamp, populates
        metadata with all required keys, validates all mandatory fields are non-None, and
        catches TypeError from dataclass validation to re-raise as ValueError.

        Args:
            question: Question dict from questionnaire
            routing_result: Validated routing result from Phase 3
            applicable_patterns: Filtered tuple of patterns applicable to the routed policy area
            resolved_signals: Resolved signals tuple from Phase 5
            generated_task_ids: Set of task IDs generated in current synchronization run

        Returns:
            ExecutableTask ready for execution

        Raises:
            ValueError: If duplicate task_id is detected or required fields are missing/invalid
        """
        # Phase 7.1: Validate and extract question_global
        question_global = question.get("question_global")
        if question_global is None:
            raise ValueError("question_global field is required but missing")
        if not isinstance(question_global, int):
            raise ValueError(
                f"question_global must be an integer, got {type(question_global).__name__}"
            )

        # Phase 7.1: Construct task_id from validated question_global
        task_id = f"MQC-{question_global:03d}_{routing_result.policy_area_id}"

        if task_id in generated_task_ids:
            raise ValueError(f"Duplicate task_id detected: {task_id}")

        generated_task_ids.add(task_id)

        # Field extraction in declaration order for validation priority
        # Extract question_id with bracket notation and KeyError conversion
        try:
            question_id = question["question_id"]
        except KeyError as e:
            raise ValueError("question_id field is required but missing") from e

        # Assign question_global (already validated above)
        # Extract routing fields via attribute access (guaranteed by ChunkRoutingResult schema)
        policy_area_id = routing_result.policy_area_id
        dimension_id = routing_result.dimension_id
        chunk_id = routing_result.chunk_id

        expected_elements_list = list(routing_result.expected_elements)
        document_position = routing_result.document_position

        patterns_list = list(applicable_patterns)

        signals_dict: dict[str, Any] = {}
        for signal in resolved_signals:
            if isinstance(signal, dict) and "signal_type" in signal:
                signals_dict[signal["signal_type"]] = signal
            elif hasattr(signal, "signal_type"):
                signals_dict[signal.signal_type] = signal

        from datetime import datetime, timezone

        creation_timestamp = datetime.now(timezone.utc).isoformat()

        metadata = {
            "document_position": document_position,
            "synchronizer_version": "1.0.0",
            "correlation_id": self.correlation_id,
            "original_pattern_count": len(applicable_patterns),
            "original_signal_count": len(resolved_signals),
        }

        if task_id is None or not task_id:
            raise ValueError("Task construction failure: task_id is None or empty")
        if question_id is None or not question_id:
            raise ValueError("Task construction failure: question_id is None or empty")
        if question_global is None:
            raise ValueError("Task construction failure: question_global is None")
        if policy_area_id is None or not policy_area_id:
            raise ValueError(
                "Task construction failure: policy_area_id is None or empty"
            )
        if dimension_id is None or not dimension_id:
            raise ValueError("Task construction failure: dimension_id is None or empty")
        if chunk_id is None or not chunk_id:
            raise ValueError("Task construction failure: chunk_id is None or empty")
        if creation_timestamp is None or not creation_timestamp:
            raise ValueError(
                "Task construction failure: creation_timestamp is None or empty"
            )

        try:
            task = ExecutableTask(
                task_id=task_id,
                question_id=question_id,
                question_global=question_global,
                policy_area_id=policy_area_id,
                dimension_id=dimension_id,
                chunk_id=chunk_id,
                patterns=patterns_list,
                signals=signals_dict,
                creation_timestamp=creation_timestamp,
                expected_elements=expected_elements_list,
                metadata=metadata,
            )
        except TypeError as e:
            raise ValueError(
                f"Task construction failed for {task_id}: dataclass validation error - {e}"
            ) from e

        logger.debug(
            f"Constructed task: task_id={task_id}, question_id={question_id}, "
            f"chunk_id={chunk_id}, pattern_count={len(patterns_list)}, "
            f"signal_count={len(signals_dict)}"
        )

        return task

    def _assemble_execution_plan(
        self,
        executable_tasks: list[ExecutableTask],
        questions: list[dict[str, Any]],
        correlation_id: str,  # noqa: ARG002
    ) -> tuple[list[ExecutableTask], str]:
        """Phase 8: Assemble execution plan with validation and deterministic ordering.

        Performs four-phase assembly process:
        - Phase 8.1: Pre-assembly validation (duplicate detection, count validation)
        - Phase 8.2: Deterministic task ordering (lexicographic by task_id)
        - Phase 8.3: Plan identifier computation (SHA256 of deterministic JSON)
        - Phase 8.4: Plan identifier validation (format and length checks)

        Validates that task count matches question count and that no duplicate
        task identifiers exist. Then sorts tasks lexicographically by task_id to ensure
        deterministic plan identifier generation across runs. Computes plan_id by
        encoding deterministic JSON serialization (sort_keys=True, compact separators)
        to UTF-8 bytes, computing SHA256 hash, and validating result matches expected
        64-character lowercase hexadecimal format.

        Args:
            executable_tasks: List of constructed ExecutableTask objects
            questions: List of question dictionaries
            correlation_id: Correlation ID for tracing

        Returns:
            Tuple of (sorted list of ExecutableTask objects, plan_id string)

        Raises:
            ValueError: If task count doesn't match question count, duplicates exist,
                       or plan_id validation fails
            RuntimeError: When sorting operation corrupts task list length
        """
        from collections import Counter

        question_count = len(questions)
        task_count = len(executable_tasks)

        if task_count != question_count:
            raise ValueError(
                f"Execution plan assembly failure: expected {question_count} tasks "
                f"but constructed {task_count}; task construction loop corrupted"
            )

        task_ids = [t.task_id for t in executable_tasks]
        unique_count = len(set(task_ids))

        if unique_count != len(task_ids):
            counter = Counter(task_ids)
            duplicates = [task_id for task_id, count in counter.items() if count > 1]
            duplicate_count = len(task_ids) - unique_count

            raise ValueError(
                f"Execution plan assembly failure: found {duplicate_count} duplicate "
                f"task identifiers; duplicates are {sorted(duplicates)}"
            )

        sorted_tasks = sorted(executable_tasks, key=lambda t: t.task_id)

        if len(sorted_tasks) != len(executable_tasks):
            raise RuntimeError(
                f"Task ordering corruption detected: sorted task count {len(sorted_tasks)} "
                f"does not match input task count {len(executable_tasks)}"
            )

        task_serialization = [
            {
                "task_id": t.task_id,
                "question_id": t.question_id,
                "question_global": t.question_global,
                "policy_area_id": t.policy_area_id,
                "dimension_id": t.dimension_id,
                "chunk_id": t.chunk_id,
            }
            for t in sorted_tasks
        ]

        json_bytes = json.dumps(
            task_serialization, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        plan_id = hashlib.sha256(json_bytes).hexdigest()

        if len(plan_id) != SHA256_HEX_DIGEST_LENGTH:
            raise ValueError(
                f"Plan identifier validation failure: expected length {SHA256_HEX_DIGEST_LENGTH} but got {len(plan_id)}; "
                "SHA256 implementation may be compromised or monkey-patched"
            )

        if not all(c in "0123456789abcdef" for c in plan_id):
            raise ValueError(
                "Plan identifier validation failure: expected lowercase hexadecimal but got "
                "characters outside '0123456789abcdef' set; SHA256 implementation may be "
                "compromised or monkey-patched"
            )

        return sorted_tasks, plan_id

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

    def _construct_execution_plan_phase_8_4(
        self,
        sorted_tasks: list[Task],
        plan_id: str,
        chunk_count: int,
        question_count: int,
        integrity_hash: str,
    ) -> ExecutionPlan:
        """Phase 8.4: ExecutionPlan dataclass construction.

        Constructs the final execution artifact from the sorted task list produced in
        Phase 8.2, converting sorted_tasks to an immutable tuple, constructing a
        metadata dictionary with generation_timestamp (UTC ISO 8601),
        synchronizer_version "2.0.0", chunk_count from the chunk matrix,
        question_count and task_count, invoking the ExecutionPlan constructor with
        plan_id from Phase 8.3 and tasks_tuple with metadata_dict as keyword arguments,
        wrapping the constructor call in try-except to catch TypeError from dataclass
        validation and re-raise as ValueError with context-specific message, then
        verifying task order preservation by checking that all adjacent task_id pairs
        maintain lexicographic ordering and raising ValueError if any violation is
        detected before emitting an info-level structured log event and returning the
        constructed ExecutionPlan instance.

        Args:
            sorted_tasks: List of Task objects sorted by task_id (from Phase 8.2)
            plan_id: Plan identifier string (from Phase 8.3)
            chunk_count: Number of chunks in the document
            question_count: Number of questions in the questionnaire
            integrity_hash: Blake3 or SHA256 hash of the task list

        Returns:
            ExecutionPlan instance with validated task ordering

        Raises:
            ValueError: If dataclass validation fails or task ordering is violated
        """
        tasks_tuple = tuple(sorted_tasks)

        metadata_dict = {
            "generation_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "synchronizer_version": "2.0.0",
            "chunk_count": chunk_count,
            "question_count": question_count,
            "task_count": len(tasks_tuple),
        }

        try:
            plan = ExecutionPlan(
                plan_id=plan_id,
                tasks=tasks_tuple,
                chunk_count=metadata_dict["chunk_count"],
                question_count=metadata_dict["question_count"],
                integrity_hash=integrity_hash,
                created_at=metadata_dict["generation_timestamp"],
                correlation_id=self.correlation_id,
            )
        except TypeError as e:
            raise ValueError(
                f"ExecutionPlan dataclass construction failed: {e}. "
                f"Constructor validation rejected arguments (plan_id={plan_id}, "
                f"task_count={len(tasks_tuple)}, chunk_count={chunk_count}, "
                f"question_count={question_count})"
            ) from e

        for i in range(len(tasks_tuple) - 1):
            current_task_id = tasks_tuple[i].task_id
            next_task_id = tasks_tuple[i + 1].task_id

            if current_task_id >= next_task_id:
                raise ValueError(
                    f"Task order preservation violation detected at index {i}: "
                    f"task_id '{current_task_id}' >= task_id '{next_task_id}'. "
                    f"Expected strict lexicographic ordering maintained after Phase 8.2 sort."
                )

        logger.info(
            json.dumps(
                {
                    "event": "execution_plan_phase_8_4_complete",
                    "plan_id": plan_id,
                    "task_count": len(tasks_tuple),
                    "chunk_count": chunk_count,
                    "question_count": question_count,
                    "integrity_hash": integrity_hash,
                    "synchronizer_version": metadata_dict["synchronizer_version"],
                    "generation_timestamp": metadata_dict["generation_timestamp"],
                    "correlation_id": self.correlation_id,
                    "phase": "execution_plan_construction_phase_8_4",
                }
            )
        )

        return plan

    def _validate_cross_task_cardinality(
        self, plan: ExecutionPlan, questions: list[dict[str, Any]]
    ) -> None:
        """Validate cross-task cardinality and log task distribution statistics.

        Extracts unique chunk IDs from execution plan tasks, computes expected
        reference counts by filtering questions for matching policy_area_id and
        dimension_id (parsed from chunk_id), compares actual task counts per chunk
        against expected counts, and emits warning-level logs for mismatches.

        Also collects chunk usage statistics (mean, median, min, max) across all
        unique chunks, policy area task distribution mapping, and dimension coverage
        validation, culminating in a single info-level log entry with complete
        observability into task distribution patterns.

        Args:
            plan: ExecutionPlan containing all constructed tasks
            questions: List of original question dictionaries

        Raises:
            None - Discrepancies emit warnings but do not raise exceptions since
                   they may reflect legitimate sparse coverage rather than errors
        """
        unique_chunks: set[str] = set()
        chunk_task_counts: dict[str, int] = {}

        for task in plan.tasks:
            chunk_id = task.chunk_id
            unique_chunks.add(chunk_id)
            chunk_task_counts[chunk_id] = chunk_task_counts.get(chunk_id, 0) + 1

        for chunk_id, actual_count in chunk_task_counts.items():
            try:
                parts = chunk_id.split("-")
                if len(parts) >= 2:
                    policy_area_id = parts[0]
                    dimension_id = parts[1]

                    expected_count = sum(
                        1
                        for q in questions
                        if q.get("policy_area_id") == policy_area_id
                        and q.get("dimension_id") == dimension_id
                    )

                    if actual_count != expected_count:
                        logger.warning(
                            json.dumps(
                                {
                                    "event": "cross_task_cardinality_mismatch",
                                    "chunk_id": chunk_id,
                                    "policy_area_id": policy_area_id,
                                    "dimension_id": dimension_id,
                                    "expected_count": expected_count,
                                    "actual_count": actual_count,
                                    "correlation_id": self.correlation_id,
                                    "timestamp": time.time(),
                                }
                            )
                        )
            except (IndexError, ValueError) as e:
                logger.warning(
                    json.dumps(
                        {
                            "event": "chunk_id_parse_error",
                            "chunk_id": chunk_id,
                            "error": str(e),
                            "correlation_id": self.correlation_id,
                            "timestamp": time.time(),
                        }
                    )
                )

        chunk_counts = list(chunk_task_counts.values())
        chunk_usage_stats: dict[str, float] = {}

        if chunk_counts:
            chunk_usage_stats = {
                "mean": statistics.mean(chunk_counts),
                "median": statistics.median(chunk_counts),
                "min": float(min(chunk_counts)),
                "max": float(max(chunk_counts)),
            }

        tasks_per_policy_area: dict[str, int] = {}
        for task in plan.tasks:
            try:
                parts = task.chunk_id.split("-")
                if len(parts) >= 1:
                    policy_area_id = parts[0]
                    tasks_per_policy_area[policy_area_id] = (
                        tasks_per_policy_area.get(policy_area_id, 0) + 1
                    )
            except (IndexError, ValueError):
                pass

        tasks_per_dimension: dict[str, int] = {}
        for task in plan.tasks:
            try:
                parts = task.chunk_id.split("-")
                if len(parts) >= 2:
                    dimension_id = parts[1]
                    tasks_per_dimension[dimension_id] = (
                        tasks_per_dimension.get(dimension_id, 0) + 1
                    )
            except (IndexError, ValueError):
                pass

        logger.info(
            json.dumps(
                {
                    "event": "cross_task_cardinality_validation_complete",
                    "total_unique_chunks": len(unique_chunks),
                    "tasks_per_policy_area": tasks_per_policy_area,
                    "tasks_per_dimension": tasks_per_dimension,
                    "chunk_usage_stats": chunk_usage_stats,
                    "correlation_id": self.correlation_id,
                    "timestamp": time.time(),
                }
            )
        )

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
        """Build execution plan using validated chunk matrix.

        Orchestrates Phases 2-7 of irrigation synchronization:
        - Phase 2: Question extraction
        - Phase 3: Chunk routing (OBJECTIVE 3 INTEGRATION)
        - Phase 4: Pattern filtering (policy_area_id-based filtering)
        - Phase 5: Signal resolution (future)
        - Phase 6: Schema validation (future)
        - Phase 7: Task construction

        Returns:
            ExecutionPlan with validated tasks

        Raises:
            ValueError: On routing failures, validation errors
        """
        logger.info(
            json.dumps(
                {
                    "event": "task_construction_start",
                    "correlation_id": self.correlation_id,
                    "question_count": self.question_count,
                    "chunk_count": self.chunk_count,
                    "mode": "chunk_matrix",
                    "phase": "synchronization_phase_2",
                    "timestamp": time.time(),
                }
            )
        )

        try:
            if self.question_count == 0:
                synchronization_failures.labels(error_type="empty_questions").inc()
                raise ValueError(
                    "No questions extracted from questionnaire. "
                    "Cannot build tasks with empty question set."
                )

            questions = self._extract_questions()

            if not questions:
                raise ValueError(
                    "No questions extracted from questionnaire. "
                    "Cannot build tasks with empty question set."
                )

            tasks: list[ExecutableTask] = []
            routing_successes = 0
            routing_failures = 0
            generated_task_ids: set[str] = set()

            for idx, question in enumerate(questions, start=1):
                question_id = question.get("question_id", f"UNKNOWN_{idx}")
                policy_area_id = question.get("policy_area_id", "UNKNOWN")
                dimension_id = question.get("dimension_id", "UNKNOWN")
                chunk_id = "UNKNOWN"

                try:
                    routing_result = self.validate_chunk_routing(question)
                    routing_successes += 1
                    chunk_id = routing_result.chunk_id

                    patterns_raw = question.get("patterns", [])
                    applicable_patterns = self._filter_patterns(
                        patterns_raw, routing_result.policy_area_id
                    )

                    # Phase 5 validation: Ensure signal_registry initialized
                    if self.signal_registry is None:
                        raise ValueError(
                            f"SignalRegistry required for Phase 5 signal resolution "
                            f"but not initialized for question {question_id}"
                        )

                    resolved_signals = self._resolve_signals_for_question(
                        question,
                        routing_result.target_chunk,
                        self.signal_registry,
                    )

                    # Phase 6: Schema validation (four subphase pipeline)
                    # Validates structural compatibility and semantic constraints
                    # Allows TypeError/ValueError to propagate to outer handler
                    validate_phase6_schema_compatibility(
                        question=question,
                        chunk_expected_elements=routing_result.expected_elements,
                        chunk_id=routing_result.chunk_id,
                        policy_area_id=routing_result.policy_area_id,
                        correlation_id=self.correlation_id,
                    )

                    task = self._construct_task(
                        question,
                        routing_result,
                        applicable_patterns,
                        resolved_signals,
                        generated_task_ids,
                    )
                    tasks.append(task)

                    if idx % 50 == 0:
                        logger.info(
                            json.dumps(
                                {
                                    "event": "task_construction_progress",
                                    "tasks_completed": idx,
                                    "total_questions": len(questions),
                                    "progress_pct": round(
                                        100 * idx / len(questions), 2
                                    ),
                                    "correlation_id": self.correlation_id,
                                }
                            )
                        )

                except (ValueError, TypeError) as e:
                    routing_failures += 1

                    logger.error(
                        json.dumps(
                            {
                                "event": "task_construction_failure",
                                "error_event": "routing_or_signal_failure",
                                "question_id": question_id,
                                "question_index": idx,
                                "policy_area_id": policy_area_id,
                                "dimension_id": dimension_id,
                                "chunk_id": chunk_id,
                                "error_type": type(e).__name__,
                                "error_message": str(e),
                                "correlation_id": self.correlation_id,
                                "timestamp": time.time(),
                            }
                        ),
                        exc_info=True,
                    )

                    raise

            expected_task_count = len(questions)
            actual_task_count = len(tasks)

            if actual_task_count != expected_task_count:
                raise ValueError(
                    f"Task count mismatch: Expected {expected_task_count} tasks "
                    f"but constructed {actual_task_count}. "
                    f"Routing successes: {routing_successes}, failures: {routing_failures}"
                )

            tasks, plan_id = self._assemble_execution_plan(
                tasks, questions, self.correlation_id
            )

            logger.info(
                json.dumps(
                    {
                        "event": "task_construction_complete",
                        "total_tasks": actual_task_count,
                        "routing_successes": routing_successes,
                        "routing_failures": routing_failures,
                        "success_rate": round(
                            100 * routing_successes / max(expected_task_count, 1), 2
                        ),
                        "correlation_id": self.correlation_id,
                        "timestamp": time.time(),
                    }
                )
            )

            legacy_tasks = []
            for task in tasks:
                legacy_task = Task(
                    task_id=task.task_id,
                    dimension=task.dimension_id,
                    question_id=task.question_id,
                    policy_area=task.policy_area_id,
                    chunk_id=task.chunk_id,
                    chunk_index=0,
                    question_text="",
                )
                legacy_tasks.append(legacy_task)

            integrity_hash = self._compute_integrity_hash(legacy_tasks)

            plan = self._construct_execution_plan_phase_8_4(
                sorted_tasks=legacy_tasks,
                plan_id=plan_id,
                chunk_count=self.chunk_count,
                question_count=len(questions),
                integrity_hash=integrity_hash,
            )

            self._validate_cross_task_cardinality(plan, questions)

            logger.info(
                json.dumps(
                    {
                        "event": "build_execution_plan_complete",
                        "correlation_id": self.correlation_id,
                        "plan_id": plan_id,
                        "task_count": len(legacy_tasks),
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

            sorted_tasks = sorted(tasks, key=lambda t: t.task_id)

            if len(sorted_tasks) != len(tasks):
                raise RuntimeError(
                    f"Task ordering corruption detected: sorted task count {len(sorted_tasks)} "
                    f"does not match input task count {len(tasks)}"
                )

            task_serialization = [
                {
                    "task_id": t.task_id,
                    "question_id": t.question_id,
                    "dimension": t.dimension,
                    "policy_area": t.policy_area,
                    "chunk_id": t.chunk_id,
                }
                for t in sorted_tasks
            ]

            json_bytes = json.dumps(
                task_serialization, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")

            plan_id = hashlib.sha256(json_bytes).hexdigest()

            if len(plan_id) != SHA256_HEX_DIGEST_LENGTH:
                raise ValueError(
                    f"Plan identifier validation failure: expected length {SHA256_HEX_DIGEST_LENGTH} but got {len(plan_id)}; "
                    "SHA256 implementation may be compromised or monkey-patched"
                )

            if not all(c in "0123456789abcdef" for c in plan_id):
                raise ValueError(
                    "Plan identifier validation failure: expected lowercase hexadecimal but got "
                    "characters outside '0123456789abcdef' set; SHA256 implementation may be "
                    "compromised or monkey-patched"
                )

            integrity_hash = self._compute_integrity_hash(sorted_tasks)

            plan = self._construct_execution_plan_phase_8_4(
                sorted_tasks=sorted_tasks,
                plan_id=plan_id,
                chunk_count=self.chunk_count,
                question_count=len(questions),
                integrity_hash=integrity_hash,
            )

            self._validate_cross_task_cardinality(plan, questions)

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

    def _validate_cross_task_contamination(self, execution_plan: ExecutionPlan) -> None:
        """Build traceability mappings for task-chunk relationship queries.

        Constructs two bidirectional dictionaries enabling efficient task-chunk
        relationship queries and stores them in ExecutionPlan metadata:
        - task_chunk_mapping: Maps each task_id to its chunk_id (one-to-one)
        - chunk_task_mapping: Maps each chunk_id to list of task_ids (one-to-many)

        Args:
            execution_plan: ExecutionPlan to enrich with traceability mappings

        Returns:
            None (modifies execution_plan.metadata in place)
        """
        task_chunk_mapping = {t.task_id: t.chunk_id for t in execution_plan.tasks}

        chunk_task_mapping: dict[str, list[str]] = {}
        for t in execution_plan.tasks:
            chunk_task_mapping.setdefault(t.chunk_id, []).append(t.task_id)

        execution_plan.metadata["task_chunk_mapping"] = task_chunk_mapping
        execution_plan.metadata["chunk_task_mapping"] = chunk_task_mapping

    def _resolve_signals_for_question(
        self,
        question: dict[str, Any],
        target_chunk: ChunkData,
        signal_registry: SignalRegistry,
    ) -> tuple[Any, ...]:
        """Resolve signals for a question from registry.

        Performs signal resolution with comprehensive validation:
        - Normalizes signal_requirements to empty list if missing/None
        - Calls signal_registry.get_signals_for_chunk with requirements
        - Validates return type is list (raises TypeError if None)
        - Validates each signal has required fields (signal_id, signal_type, content)
        - Detects missing required signals (HARD STOP with ValueError)
        - Detects and warns about duplicate signal types
        - Returns immutable tuple of resolved signals

        Args:
            question: Question dict with signal_requirements field
            target_chunk: Target ChunkData for signal resolution
            signal_registry: Registry implementing get_signals_for_chunk(chunk, requirements)

        Returns:
            Immutable tuple of resolved signals

        Raises:
            TypeError: If signal_registry returns non-list type
            ValueError: If signal missing required field or required signals not found
        """
        question_id = question.get("question_id", "UNKNOWN")
        chunk_id = getattr(target_chunk, "chunk_id", "UNKNOWN")

        # Normalize signal_requirements to empty list if missing or None
        signal_requirements = question.get("signal_requirements")
        if signal_requirements is None:
            signal_requirements = []
        elif not isinstance(signal_requirements, list):
            # If it's a dict or other type, extract as list if possible
            if isinstance(signal_requirements, dict):
                signal_requirements = list(signal_requirements.keys())
            else:
                signal_requirements = []

        # Call signal_registry.get_signals_for_chunk
        resolved_signals = signal_registry.get_signals_for_chunk(
            target_chunk, signal_requirements
        )

        # Validate return is list type (raise TypeError if None)
        if resolved_signals is None:
            raise TypeError(
                f"SignalRegistry returned {type(None).__name__} for question {question_id} "
                f"chunk {chunk_id}, expected list"
            )

        if not isinstance(resolved_signals, list):
            raise TypeError(
                f"SignalRegistry returned {type(resolved_signals).__name__} for question {question_id} "
                f"chunk {chunk_id}, expected list"
            )

        # Validate each signal has required fields
        required_fields = ["signal_id", "signal_type", "content"]
        for i, signal in enumerate(resolved_signals):
            for field in required_fields:
                # Try both attribute and dict access
                has_field = False
                try:
                    if hasattr(signal, field):
                        getattr(signal, field)
                        has_field = True
                except (AttributeError, KeyError):
                    pass

                if not has_field:
                    try:
                        if isinstance(signal, dict) and field in signal:
                            has_field = True
                    except (TypeError, KeyError):
                        pass

                if not has_field:
                    raise ValueError(
                        f"Signal at index {i} missing field {field} for question {question_id}"
                    )

        # Extract signal_types into set
        signal_types = set()
        for signal in resolved_signals:
            # Try attribute access first, then dict access
            signal_type = None
            try:
                if hasattr(signal, "signal_type"):
                    signal_type = signal.signal_type
            except AttributeError:
                pass

            if signal_type is None:
                try:
                    if isinstance(signal, dict):
                        signal_type = signal["signal_type"]
                except (KeyError, TypeError):
                    pass

            if signal_type is not None:
                signal_types.add(signal_type)

        # Compute missing signals
        requirements_set = set(signal_requirements) if signal_requirements else set()
        missing_signals = requirements_set - signal_types

        # Raise ValueError if non-empty (HARD STOP)
        if missing_signals:
            missing_sorted = sorted(missing_signals)
            raise ValueError(
                f"Synchronization Failure for MQC {question_id}: "
                f"Missing required signals {missing_sorted} for chunk {chunk_id}"
            )

        # Detect duplicates
        if len(resolved_signals) > len(signal_types):
            # Find duplicate types for logging
            type_counts: dict[Any, int] = {}
            for signal in resolved_signals:
                signal_type = None
                try:
                    if hasattr(signal, "signal_type"):
                        signal_type = signal.signal_type
                except AttributeError:
                    pass

                if signal_type is None:
                    try:
                        if isinstance(signal, dict):
                            signal_type = signal["signal_type"]
                    except (KeyError, TypeError):
                        pass

                if signal_type is not None:
                    type_counts[signal_type] = type_counts.get(signal_type, 0) + 1

            duplicate_types = [t for t, count in type_counts.items() if count > 1]

            logger.warning(
                "signal_resolution_duplicates",
                extra={
                    "question_id": question_id,
                    "chunk_id": chunk_id,
                    "correlation_id": self.correlation_id,
                    "duplicate_types": duplicate_types,
                },
            )

        # Emit success log
        logger.debug(
            "signal_resolution_success",
            extra={
                "question_id": question_id,
                "chunk_id": chunk_id,
                "correlation_id": self.correlation_id,
                "resolved_count": len(resolved_signals),
                "required_count": len(signal_requirements),
                "signal_types": list(signal_types),
            },
        )

        # Return tuple for immutability
        return tuple(resolved_signals)

    def _serialize_and_verify_plan(self, plan: ExecutionPlan) -> str:
        """Serialize ExecutionPlan and verify round-trip integrity.

        Serializes the execution plan to JSON, deserializes it back, reconstructs
        an ExecutionPlan instance, and validates that plan_id and task count match
        the original to ensure serialization is lossless.

        Args:
            plan: ExecutionPlan instance to serialize and verify

        Returns:
            Validated serialized JSON string ready for persistent storage

        Raises:
            ValueError: If plan_id mismatch or task count mismatch detected
        """
        plan_dict = plan.to_dict()
        serialized_json = json.dumps(plan_dict, sort_keys=True, separators=(",", ":"))

        deserialized_dict = json.loads(serialized_json)
        reconstructed_plan = ExecutionPlan.from_dict(deserialized_dict)

        if reconstructed_plan.plan_id != plan.plan_id:
            raise ValueError(
                f"Serialization verification failed: plan_id mismatch "
                f"(original={plan.plan_id}, reconstructed={reconstructed_plan.plan_id})"
            )

        original_task_count = len(plan.tasks)
        reconstructed_task_count = len(reconstructed_plan.tasks)

        if reconstructed_task_count != original_task_count:
            raise ValueError(
                f"Serialization verification failed: task count mismatch "
                f"(original={original_task_count}, reconstructed={reconstructed_task_count})"
            )

        return serialized_json

    def _archive_to_storage(
        self,
        serialized_json: str,
        execution_plan: ExecutionPlan,
        base_dir: Path,
    ) -> ExecutionPlan:
        """Archive execution plan to storage with atomic index update and rollback.

        Constructs storage path as base_dir / 'execution_plans' / f'{plan_id}.json',
        writes serialized JSON with verification, and atomically updates index with
        rollback logic for orphaned files.

        Args:
            serialized_json: Serialized JSON string of execution plan
            execution_plan: ExecutionPlan instance to archive
            base_dir: Base directory path for storage

        Returns:
            Original ExecutionPlan instance unchanged

        Raises:
            ValueError: If write fails (re-raised from IOError)
            IOError: If write verification fails (content mismatch)
        """
        plan_id = execution_plan.plan_id
        storage_path = base_dir / "execution_plans" / f"{plan_id}.json"

        try:
            storage_path.parent.mkdir(parents=True, exist_ok=True)
        except IOError as e:
            raise ValueError(
                f"Failed to create parent directories for plan_id={plan_id}, "
                f"storage_path={storage_path}: {e}"
            ) from e

        try:
            storage_path.write_text(serialized_json, encoding="utf-8")
        except IOError as e:
            raise ValueError(
                f"Failed to write execution plan for plan_id={plan_id}, "
                f"storage_path={storage_path}: {e}"
            ) from e

        try:
            read_content = storage_path.read_text(encoding="utf-8")
            if read_content != serialized_json:
                storage_path.unlink()
                raise IOError(
                    f"Write verification failed for plan_id={plan_id}, "
                    f"storage_path={storage_path}: content mismatch after write"
                )
        except IOError as e:
            if storage_path.exists():
                storage_path.unlink()
            raise

        index_path = base_dir / "execution_plans" / "index.jsonl"
        index_entry = {
            "plan_id": plan_id,
            "storage_path": str(storage_path),
            "created_at": execution_plan.created_at,
            "task_count": len(execution_plan.tasks),
            "integrity_hash": execution_plan.integrity_hash,
            "correlation_id": execution_plan.correlation_id,
        }

        try:
            with open(index_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(index_entry) + "\n")
        except IOError as e:
            if storage_path.exists():
                storage_path.unlink()
            raise ValueError(
                f"Failed to update index for plan_id={plan_id}, "
                f"storage_path={storage_path}: {e}"
            ) from e

        logger.info(
            "execution_plan_archived",
            extra={
                "event": "execution_plan_archived",
                "plan_id": plan_id,
                "storage_path": str(storage_path),
                "task_count": len(execution_plan.tasks),
                "integrity_hash": execution_plan.integrity_hash,
                "correlation_id": execution_plan.correlation_id,
                "created_at": execution_plan.created_at,
            },
        )

        return execution_plan


__all__ = [
    "IrrigationSynchronizer",
    "ExecutionPlan",
    "Task",
    "ChunkRoutingResult",
    "SignalRegistry",
]
