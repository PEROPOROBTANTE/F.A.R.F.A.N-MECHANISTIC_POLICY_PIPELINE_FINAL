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
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.signals import SignalRegistry

from farfan_pipeline.core.orchestrator.task_planner import ExecutableTask
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

    def _resolve_signals_for_question(
        self,
        question: dict[str, Any],
        target_chunk: ChunkData,
        signal_registry: SignalRegistry | None,
    ) -> tuple[Any, ...]:
        """Phase 5: Resolve signals for question and chunk.

        Queries the signal registry for all signals required by the question,
        validates that all required signals are present, and returns an
        immutable tuple of Signal objects.

        Args:
            question: Question dict with signal_requirements
            target_chunk: Target chunk from Phase 3 routing
            signal_registry: Registry for signal resolution

        Returns:
            Immutable tuple of Signal objects

        Raises:
            ValueError: When signal_registry is None or required signals are missing
        """
        if signal_registry is None:
            raise ValueError("SignalRegistry is required for Phase 5 signal resolution")

        question_id = question.get("question_id", "UNKNOWN")
        signal_requirements = question.get("signal_requirements", {})

        if not isinstance(signal_requirements, dict):
            signal_requirements = {}

        required_types = (
            set(signal_requirements.keys()) if signal_requirements else set()
        )

        if not required_types:
            logger.debug(
                json.dumps(
                    {
                        "event": "signal_resolution_skipped",
                        "question_id": question_id,
                        "reason": "no_signal_requirements",
                        "correlation_id": self.correlation_id,
                    }
                )
            )
            return ()

        try:
            from farfan_pipeline.core.orchestrator.signal_resolution import (
                Chunk,
                _resolve_signals,
            )
            from farfan_pipeline.core.orchestrator.signal_resolution import (
                Question as SignalQuestion,
            )

            chunk_for_resolution = Chunk(
                chunk_id=target_chunk.chunk_id
                or f"{target_chunk.policy_area_id}-{target_chunk.dimension_id}",
                text=target_chunk.text,
            )

            question_for_resolution = SignalQuestion(
                question_id=question_id,
                signal_requirements=required_types,
            )

            resolved_signals = _resolve_signals(
                chunk=chunk_for_resolution,
                question=question_for_resolution,
                signal_registry=signal_registry,
            )

            logger.debug(
                json.dumps(
                    {
                        "event": "signal_resolution_success",
                        "question_id": question_id,
                        "chunk_id": chunk_for_resolution.chunk_id,
                        "required_count": len(required_types),
                        "resolved_count": len(resolved_signals),
                        "correlation_id": self.correlation_id,
                    }
                )
            )

            return resolved_signals

        except ImportError as e:
            raise ValueError(
                f"Signal resolution dependencies not available: {e}"
            ) from e

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

    def _validate_schema_compatibility(
        self,
        question: dict[str, Any],
        routing_result: ChunkRoutingResult,
        correlation_id: str,
    ) -> None:
        """Phase 6: Validate schema compatibility between question and chunk.

        Extracts expected_elements from both question and chunk routing result,
        validates type compatibility and structure consistency, and raises
        exceptions if schema incompatibilities are detected. Acts as a fail-fast
        gate preventing task construction when schema validation fails.

        Args:
            question: Question dictionary from questionnaire
            routing_result: ChunkRoutingResult from Phase 3
            correlation_id: Correlation ID for tracking

        Raises:
            TypeError: If either schema has invalid type (not list, dict, or None)
            ValueError: If schemas have heterogeneous types, list length mismatch,
                       or dict key set mismatch, or if question["question_global"] is missing
        """
        question_id = question.get("question_id", "UNKNOWN")
        question_global = question.get("question_global")

        if question_global is None:
            raise ValueError("question_global is required")

        if not isinstance(question_global, int):
            raise ValueError(
                f"question_global must be an integer, got {type(question_global).__name__}"
            )

        if not (0 <= question_global <= 999):
            raise ValueError(
                f"question_global must be between 0 and 999 inclusive, got {question_global}"
            )

        provisional_task_id = (
            f"MQC-{question_global:03d}_{routing_result.policy_area_id}"
        )
        chunk_id = routing_result.chunk_id

        question_schema = question.get("expected_elements")
        chunk_schema = routing_result.expected_elements

        self._validate_expected_elements_types(
            provisional_task_id,
            question_schema,
            chunk_schema,
            question_id,
            chunk_id,
            correlation_id,
        )

        logger.debug(
            json.dumps(
                {
                    "event": "schema_validation_success",
                    "question_id": question_id,
                    "chunk_id": chunk_id,
                    "provisional_task_id": provisional_task_id,
                    "correlation_id": correlation_id,
                }
            )
        )

    def _validate_expected_elements_types(
        self,
        provisional_task_id: str,  # noqa: ARG002
        question_schema: Any,  # noqa: ANN401
        chunk_schema: Any,  # noqa: ANN401
        question_id: str,
        chunk_id: str,  # noqa: ARG002
        correlation_id: str,
    ) -> None:
        """Validate expected_elements type compatibility and structure.

        Performs type classification on both schema values by checking if each is
        None via identity test, then list via isinstance check, then dict via
        isinstance check, with any other type classified as invalid. Validates
        type homogeneity, length equality for lists, and key set equality for dicts.

        Args:
            provisional_task_id: Task ID for error reporting
            question_schema: expected_elements from question
            chunk_schema: expected_elements from chunk
            question_id: Question identifier for error messages
            chunk_id: Chunk identifier for error messages
            correlation_id: Correlation ID for distributed tracing

        Raises:
            TypeError: If either schema has invalid type (not list, dict, or None)
            ValueError: If schemas have heterogeneous types, list length mismatch,
                       or dict key set mismatch
        """

        def _classify_type(value: Any) -> str:  # noqa: ANN401
            if value is None:
                return "none"
            elif isinstance(value, list):
                return "list"
            elif isinstance(value, dict):
                return "dict"
            else:
                return "invalid"

        question_type = _classify_type(question_schema)
        chunk_type = _classify_type(chunk_schema)

        if question_type == "invalid":
            raise TypeError(
                f"Schema validation failure for question {question_id}: "
                f"expected_elements from question has invalid type "
                f"{type(question_schema).__name__}, expected list|dict|None "
                f"[correlation_id={correlation_id}]"
            )

        if chunk_type == "invalid":
            raise TypeError(
                f"Schema validation failure for question {question_id}: "
                f"expected_elements from chunk has invalid type "
                f"{type(chunk_schema).__name__}, expected list|dict|None "
                f"[correlation_id={correlation_id}]"
            )

        if question_type == "none" and chunk_type == "none":
            return

        if (
            question_type != "none"
            and chunk_type != "none"
            and question_type != chunk_type
        ):
            raise ValueError(
                f"Schema validation failure: heterogeneous types "
                f"(question has {question_type}, chunk has {chunk_type}) "
                f"[correlation_id={correlation_id}]"
            )

        if question_type == "list" and chunk_type == "list":
            question_len = len(question_schema)
            chunk_len = len(chunk_schema)
            if question_len != chunk_len:
                raise ValueError(
                    f"Schema validation failure for question {question_id}: "
                    f"expected_elements list length mismatch "
                    f"(question has {question_len}, chunk has {chunk_len}) "
                    f"[correlation_id={correlation_id}]"
                )

            self._validate_element_compatibility(
                question_schema,
                chunk_schema,
                question_id,
                chunk_id,
                correlation_id,
            )

        if question_type == "dict" and chunk_type == "dict":
            question_keys = set(question_schema.keys())
            chunk_keys = set(chunk_schema.keys())
            if question_keys != chunk_keys:
                missing_in_chunk = question_keys - chunk_keys
                extra_in_chunk = chunk_keys - question_keys
                details = []
                if missing_in_chunk:
                    details.append(f"missing in chunk: {sorted(missing_in_chunk)}")
                if extra_in_chunk:
                    details.append(f"extra in chunk: {sorted(extra_in_chunk)}")
                raise ValueError(
                    f"Schema validation failure for question {question_id}: "
                    f"expected_elements dict key mismatch ({', '.join(details)}) "
                    f"[correlation_id={correlation_id}]"
                )

        if question_schema is not None and chunk_schema is None:
            logger.info(
                json.dumps(
                    {
                        "event": "schema_asymmetry_detected",
                        "question_id": question_id,
                        "chunk_id": chunk_id,
                        "question_schema_type": question_type,
                        "chunk_schema_type": "none",
                        "message": "Question specifies required elements but chunk provides no schema",
                        "validation_status": "compatible_via_constraint_relaxation",
                        "correlation_id": self.correlation_id,
                    }
                )
            )

    def _validate_element_compatibility(
        self,
        question_elements: list[dict[str, Any]],
        chunk_elements: list[dict[str, Any]],
        question_id: str,
        chunk_id: str,
        correlation_id: str,
    ) -> int:
        """Phase 6.3: Validate semantic compatibility of expected_elements.

        Performs element-by-element semantic validation with type field equality,
        asymmetric required field implication (q_required implies c_required),
        and minimum field threshold ordering (c_min >= q_min).

        Args:
            question_elements: List of expected element dicts from question
            chunk_elements: List of expected element dicts from chunk
            question_id: Question identifier for error messages
            chunk_id: Chunk identifier for error messages
            correlation_id: Correlation ID for distributed tracing

        Returns:
            Count of validated elements

        Raises:
            ValueError: If type field mismatch, required field implication violated,
                       or minimum threshold ordering violated
        """
        if len(question_elements) != len(chunk_elements):
            raise ValueError(
                f"Element count mismatch for question {question_id}: "
                f"question has {len(question_elements)} elements, "
                f"chunk has {len(chunk_elements)} elements "
                f"[correlation_id={correlation_id}]"
            )

        validated_count = 0

        for idx, (q_elem, c_elem) in enumerate(
            zip(question_elements, chunk_elements, strict=True)
        ):
            if not isinstance(q_elem, dict):
                raise ValueError(
                    f"Element at index {idx} in question {question_id} is not a dict "
                    f"[correlation_id={correlation_id}]"
                )

            if not isinstance(c_elem, dict):
                raise ValueError(
                    f"Element at index {idx} in chunk {chunk_id} is not a dict "
                    f"[correlation_id={correlation_id}]"
                )

            q_type = q_elem.get("type")
            c_type = c_elem.get("type")

            if q_type != c_type:
                raise ValueError(
                    f"Type field mismatch at index {idx} for question {question_id}: "
                    f"question type='{q_type}', chunk type='{c_type}' "
                    f"[correlation_id={correlation_id}]"
                )

            q_required = q_elem.get("required", False)
            c_required = c_elem.get("required", False)

            if q_required and not c_required:
                raise ValueError(
                    f"Required field implication violated at index {idx} for question {question_id}: "
                    f"question requires element type '{q_type}' but chunk does not "
                    f"[correlation_id={correlation_id}]"
                )

            q_min = q_elem.get("minimum")
            c_min = c_elem.get("minimum")

            if q_min is not None and c_min is not None and c_min < q_min:
                raise ValueError(
                    f"Minimum threshold ordering violated at index {idx} for question {question_id}: "
                    f"chunk minimum ({c_min}) < question minimum ({q_min}) for type '{q_type}' "
                    f"[correlation_id={correlation_id}]"
                )

            if q_min is not None and c_min is None:
                raise ValueError(
                    f"Minimum field asymmetry at index {idx} for question {question_id}: "
                    f"question specifies minimum={q_min} but chunk has no minimum for type '{q_type}' "
                    f"[correlation_id={correlation_id}]"
                )

            validated_count += 1

        logger.debug(
            json.dumps(
                {
                    "event": "element_compatibility_validation_success",
                    "question_id": question_id,
                    "chunk_id": chunk_id,
                    "validated_count": validated_count,
                    "correlation_id": correlation_id,
                }
            )
        )

        return validated_count

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
            "synchronizer_version": "2.0.0",
            "correlation_id": self.correlation_id,
            "original_pattern_count": len(applicable_patterns),
            "original_signal_count": len(resolved_signals),
            "filtered_pattern_count": len(patterns_list),
            "resolved_signal_count": len(signals_dict),
            "schema_element_count": len(expected_elements_list),
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

    def _assemble_execution_plan(self, executable_tasks: list[ExecutableTask]) -> None:
        """Phase 8.1.1: Validate execution plan for duplicate task identifiers.

        Extracts all task IDs, detects duplicates using set-based comparison,
        and raises ValueError with deterministic error reporting when duplicates
        are found. Serves as defense-in-depth detection of questionnaire data
        corruption or potential concurrency issues.

        Args:
            executable_tasks: List of ExecutableTask objects to validate

        Raises:
            ValueError: When duplicate task identifiers are detected, with message
                       containing count and sorted list of duplicates
        """
        from collections import Counter

        task_ids = [t.task_id for t in executable_tasks]
        unique_count = len(set(task_ids))

        if unique_count < len(task_ids):
            duplicate_list = sorted(
                [task_id for task_id, count in Counter(task_ids).items() if count > 1]
            )
            raise ValueError(
                f"Execution plan assembly failure: found {len(task_ids) - unique_count} "
                f"duplicate task identifiers; duplicates are {duplicate_list}"
            )

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

                    resolved_signals = self._resolve_signals_for_question(
                        question,
                        routing_result.target_chunk,
                        self.signal_registry,
                    )

                    self._validate_schema_compatibility(
                        question, routing_result, self.correlation_id
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

            self._assemble_execution_plan(tasks)

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
            plan_id = f"plan_{integrity_hash[:16]}"

            plan = ExecutionPlan(
                plan_id=plan_id,
                tasks=tuple(legacy_tasks),
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


__all__ = [
    "IrrigationSynchronizer",
    "ExecutionPlan",
    "Task",
    "ChunkRoutingResult",
    "SignalRegistry",
]
