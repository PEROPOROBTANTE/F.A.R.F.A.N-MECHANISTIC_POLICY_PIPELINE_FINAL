"""Core orchestrator classes, data models, and execution engine.

This module contains the fundamental building blocks for orchestration:
- Data models (PreprocessedDocument, Evidence, PhaseResult, etc.)
- Abort signaling (AbortSignal, AbortRequested)
- Resource management (ResourceLimits, PhaseInstrumentation)
- Method execution (MethodExecutor)
- Orchestrator (the main 11-phase orchestration engine)

The Orchestrator is the sole owner of the provider; processors and executors
receive pre-prepared data.
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import logging
import os
import statistics
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Literal, ParamSpec, TypedDict, TypeVar

from ...analysis.recommendation_engine import RecommendationEngine
from ...processing.aggregation import (
    AreaPolicyAggregator,
    AreaScore,
    ClusterAggregator,
    ClusterScore,
    DimensionAggregator,
    DimensionScore,
    MacroAggregator,
    MacroScore,
    ScoredResult,
)

from .arg_router import ArgRouterError, ArgumentValidationError, ExtendedArgRouter
from .calibration_registry import resolve_calibration
from .class_registry import ClassRegistryError, build_class_registry
from ..dependency_lockdown import get_dependency_lockdown
from .versions import CALIBRATION_VERSION

if TYPE_CHECKING:
    from document_ingestion import PreprocessedDocument as IngestionPreprocessedDocument

logger = logging.getLogger(__name__)

# Environment-configurable expectations for validation
EXPECTED_QUESTION_COUNT = int(os.getenv("EXPECTED_QUESTION_COUNT", "305"))
EXPECTED_METHOD_COUNT = int(os.getenv("EXPECTED_METHOD_COUNT", "416"))
PHASE_TIMEOUT_DEFAULT = int(os.getenv("PHASE_TIMEOUT_SECONDS", "300"))


class PhaseTimeoutError(RuntimeError):
    """Raised when a phase exceeds its timeout."""
    
    def __init__(self, phase_id: int | str, phase_name: str, timeout_s: float):
        self.phase_id = phase_id
        self.phase_name = phase_name
        self.timeout_s = timeout_s
        super().__init__(
            f"Phase {phase_id} ({phase_name}) timed out after {timeout_s}s"
        )


# ParamSpec and TypeVar for execute_phase_with_timeout
P = ParamSpec("P")
T = TypeVar("T")


async def execute_phase_with_timeout(
    phase_id: int,
    phase_name: str,
    coro: Callable[P, T] | None = None,
    *varargs: P.args,
    handler: Callable[P, T] | None = None,  # Legacy parameter for backward compatibility
    args: tuple | None = None,  # Legacy parameter for backward compatibility
    timeout_s: float = 300.0,
    **kwargs: P.kwargs,
) -> T:
    """Execute an async phase with timeout and comprehensive logging.
    
    Args:
        phase_id: Numeric phase identifier
        phase_name: Human-readable phase name
        coro: Coroutine/callable to execute (preferred)
        *varargs: Positional arguments for coro (when using positional style)
        handler: Legacy alias for coro (for backward compatibility)
        args: Legacy parameter for positional arguments (for backward compatibility)
        timeout_s: Timeout in seconds (default: 300.0)
        **kwargs: Keyword arguments for coro
        
    Returns:
        Result from coro
        
    Raises:
        PhaseTimeoutError: If execution exceeds timeout_s
        Exception: Any exception raised by coro
        ValueError: If neither coro nor handler is provided
    """
    # Support both coro and handler (legacy) parameter names
    target = coro or handler
    if target is None:
        raise ValueError("Either 'coro' or 'handler' must be provided")
    
    # Support both varargs (*args in signature) and args kwarg (legacy)
    call_args = varargs if varargs else (args or ())
    
    start = time.perf_counter()
    logger.info(
        "phase_execution_started",
        extra={"phase_id": phase_id, "phase_name": phase_name, "timeout_s": timeout_s},
    )
    try:
        result = await asyncio.wait_for(target(*call_args, **kwargs), timeout=timeout_s)
        elapsed = time.perf_counter() - start
        logger.info(
            "phase_execution_completed",
            extra={
                "phase_id": phase_id,
                "phase_name": phase_name,
                "elapsed_s": elapsed,
                "timeout_s": timeout_s,
                "time_remaining_s": timeout_s - elapsed,
            },
        )
        return result
    except asyncio.TimeoutError as exc:
        elapsed = time.perf_counter() - start
        logger.error(
            "phase_execution_timeout",
            extra={
                "phase_id": phase_id,
                "phase_name": phase_name,
                "elapsed_s": elapsed,
                "timeout_s": timeout_s,
                "exceeded_by_s": elapsed - timeout_s,
            },
        )
        raise PhaseTimeoutError(phase_id, phase_name, timeout_s) from exc
    except asyncio.CancelledError:
        elapsed = time.perf_counter() - start
        logger.warning(
            "phase_execution_cancelled",
            extra={
                "phase_id": phase_id,
                "phase_name": phase_name,
                "elapsed_s": elapsed,
            },
        )
        raise  # Re-raise to propagate cancellation
    except Exception as exc:
        elapsed = time.perf_counter() - start
        logger.error(
            "phase_execution_error",
            extra={
                "phase_id": phase_id,
                "phase_name": phase_name,
                "elapsed_s": elapsed,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True,
        )
        raise


def _normalize_monolith_for_hash(monolith: dict | MappingProxyType) -> dict:
    """Normalize monolith for hash computation and JSON serialization.
    
    Converts MappingProxyType to dict recursively to ensure:
    1. JSON serialization doesn't fail
    2. Hash computation is consistent
    
    Args:
        monolith: Monolith data (may be MappingProxyType or dict)
        
    Returns:
        Normalized dict suitable for hashing and JSON serialization
        
    Raises:
        RuntimeError: If normalization fails or produces inconsistent results
    """
    if isinstance(monolith, MappingProxyType):
        monolith = dict(monolith)
    
    # Deep-convert nested mapping proxies if they exist
    def _convert(obj: Any) -> Any:
        if isinstance(obj, MappingProxyType):
            obj = dict(obj)
        if isinstance(obj, dict):
            return {k: _convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_convert(v) for v in obj]
        return obj
    
    normalized = _convert(monolith)
    
    # Verify normalization is idempotent
    try:
        # Test that we can serialize it
        json.dumps(normalized, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Monolith normalization failed: {exc}") from exc
    
    return normalized


class MacroScoreDict(TypedDict):
    """Typed container for macro score evaluation results."""
    macro_score: MacroScore
    macro_score_normalized: float
    cluster_scores: list[ClusterScore]


@dataclass
class ClusterScoreData:
    """Type-safe cluster score data for macro evaluation."""
    id: str
    score: float
    normalized_score: float


@dataclass
class MacroEvaluation:
    """Type-safe macro evaluation result.
    
    This replaces polymorphic dict/object handling with a strict contract.
    All downstream consumers must treat macro scores as this type.
    """
    macro_score: float
    macro_score_normalized: float
    clusters: list[ClusterScoreData]


@dataclass(frozen=True)
class ChunkData:
    """Single semantic chunk from SPC (Smart Policy Chunks).
    
    Preserves chunk structure and metadata from the ingestion pipeline,
    enabling chunk-aware executor routing and scoped processing.
    """
    id: int
    text: str
    chunk_type: Literal["diagnostic", "activity", "indicator", "resource", "temporal", "entity"]
    sentences: list[int]  # Global sentence IDs in this chunk
    tables: list[int]     # Global table IDs in this chunk
    start_pos: int
    end_pos: int
    confidence: float
    edges_out: list[int] = field(default_factory=list)  # Chunk IDs this connects to
    edges_in: list[int] = field(default_factory=list)   # Chunk IDs connecting to this


@dataclass
class PreprocessedDocument:
    """Orchestrator representation of a processed document.

    This is the normalized document format used internally by the orchestrator.
    It can be constructed from ingestion payloads or created directly.
    
    New in SPC exploitation: Preserves chunk structure when processing_mode='chunked',
    enabling chunk-aware executor routing and reducing redundant processing.
    """
    document_id: str
    raw_text: str
    sentences: list[Any]
    tables: list[Any]
    metadata: dict[str, Any]
    
    # NEW CHUNK FIELDS for SPC exploitation
    chunks: list[ChunkData] = field(default_factory=list)
    chunk_index: dict[str, int] = field(default_factory=dict)  # Fast lookup: entity_id → chunk_id
    chunk_graph: dict[str, Any] = field(default_factory=dict)  # Exposed graph structure
    processing_mode: Literal["flat", "chunked"] = "flat"  # Mode flag for backward compatibility

    def __post_init__(self) -> None:
        """Validate document fields after initialization.
        
        Raises:
            ValueError: If raw_text is empty or whitespace-only
        """
        if not self.raw_text or not self.raw_text.strip():
            raise ValueError(
                "PreprocessedDocument cannot have empty raw_text. "
                "Use PreprocessedDocument.ensure() to create from SPC pipeline."
            )

    @staticmethod
    def _dataclass_to_dict(value: Any) -> Any:
        """Convert a dataclass to a dictionary if applicable."""
        if is_dataclass(value):
            return asdict(value)
        return value

    @classmethod
    def ensure(
        cls, document: Any, *, document_id: str | None = None, use_spc_ingestion: bool = True
    ) -> PreprocessedDocument:
        """Normalize arbitrary ingestion payloads into orchestrator documents.
        
        Args:
            document: Document to normalize (PreprocessedDocument or CanonPolicyPackage)
            document_id: Optional document ID override
            use_spc_ingestion: Must be True (SPC is now the only supported ingestion method)
            
        Returns:
            PreprocessedDocument instance
            
        Raises:
            ValueError: If use_spc_ingestion is False
            TypeError: If document type is not supported
        """
        # Enforce SPC-only ingestion
        if not use_spc_ingestion:
            raise ValueError(
                "SPC ingestion is now required. Set use_spc_ingestion=True or remove the parameter. "
                "Legacy ingestion methods (document_ingestion module) are no longer supported."
            )
        
        # Reject class types - only accept instances
        if isinstance(document, type):
            class_name = getattr(document, '__name__', str(document))
            raise TypeError(
                f"Expected document instance, got class type '{class_name}'. "
                "Pass an instance of the document, not the class itself."
            )

        if isinstance(document, cls):
            return document

        # Check for SPC (Smart Policy Chunks) ingestion - canonical phase-one
        # Documents must have chunk_graph attribute (from CanonPolicyPackage)
        if hasattr(document, "chunk_graph"):
            # Validate chunk_graph exists and is not empty
            chunk_graph = getattr(document, "chunk_graph", None)
            if chunk_graph is None:
                raise ValueError(
                    "Document has chunk_graph attribute but it is None. "
                    "Ensure SPC ingestion pipeline completed successfully."
                )
            
            # Validate chunk_graph has chunks
            if not hasattr(chunk_graph, 'chunks') or not chunk_graph.chunks:
                raise ValueError(
                    "Document chunk_graph is empty. "
                    "Ensure SPC ingestion pipeline completed successfully and extracted chunks."
                )
            
            try:
                from saaaaaa.utils.spc_adapter import SPCAdapter
                adapter = SPCAdapter()
                preprocessed = adapter.to_preprocessed_document(document, document_id=document_id)
                
                # Comprehensive SPC ingestion validation
                validation_results = []
                
                # Validate raw_text
                if not preprocessed.raw_text or not preprocessed.raw_text.strip():
                    raise ValueError(
                        "SPC ingestion produced empty document. "
                        "Check that the source document contains extractable text."
                    )
                text_length = len(preprocessed.raw_text)
                validation_results.append(f"raw_text: {text_length} chars")
                
                # Validate sentences extracted
                sentence_count = len(preprocessed.sentences) if preprocessed.sentences else 0
                if sentence_count == 0:
                    logger.warning("SPC ingestion produced zero sentences - document may be malformed")
                validation_results.append(f"sentences: {sentence_count}")
                
                # Validate chunk_graph exists
                chunk_count = preprocessed.metadata.get("chunk_count", 0)
                validation_results.append(f"chunks: {chunk_count}")
                
                # Log successful validation
                logger.info(f"SPC ingestion validation passed: {', '.join(validation_results)}")
                
                return preprocessed
            except ImportError as e:
                raise ImportError(
                    "SPC ingestion requires spc_adapter module. "
                    "Ensure saaaaaa.utils.spc_adapter is available."
                ) from e
            except ValueError:
                # Re-raise ValueError directly (e.g., empty document validation)
                raise
            except Exception as e:
                raise TypeError(
                    f"Failed to adapt SPC document: {e}. "
                    "Ensure document is a valid CanonPolicyPackage instance from SPC pipeline."
                ) from e

        raise TypeError(
            "Unsupported preprocessed document payload. "
            f"Expected PreprocessedDocument or CanonPolicyPackage with chunk_graph, got {type(document)!r}. "
            "Documents must be processed through the SPC ingestion pipeline first."
        )

@dataclass
class Evidence:
    """Evidence container for orchestrator results."""
    modality: str
    elements: list[Any] = field(default_factory=list)
    raw_results: dict[str, Any] = field(default_factory=dict)

class AbortRequested(RuntimeError):
    """Raised when an abort signal is triggered during orchestration."""

class AbortSignal:
    """Thread-safe abort signal shared across orchestration phases."""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._reason: str | None = None
        self._timestamp: datetime | None = None

    def abort(self, reason: str) -> None:
        """Trigger an abort with a reason and timestamp."""
        if not reason:
            reason = "Abort requested"
        with self._lock:
            if not self._event.is_set():
                self._event.set()
                self._reason = reason
                self._timestamp = datetime.utcnow()

    def is_aborted(self) -> bool:
        """Check whether abort has been triggered."""
        return self._event.is_set()

    def get_reason(self) -> str | None:
        """Return the abort reason if set."""
        with self._lock:
            return self._reason

    def get_timestamp(self) -> datetime | None:
        """Return the abort timestamp if set."""
        with self._lock:
            return self._timestamp

    def reset(self) -> None:
        """Clear the abort signal."""
        with self._lock:
            self._event.clear()
            self._reason = None
            self._timestamp = None

class ResourceLimits:
    """Runtime resource guard with adaptive worker prediction."""

    def __init__(
        self,
        max_memory_mb: float | None = 4096.0,
        max_cpu_percent: float = 85.0,
        max_workers: int = 32,
        min_workers: int = 4,
        hard_max_workers: int = 64,
        history: int = 120,
    ) -> None:
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.min_workers = max(1, min_workers)
        self.hard_max_workers = max(self.min_workers, hard_max_workers)
        self._max_workers = max(self.min_workers, min(max_workers, self.hard_max_workers))
        self._usage_history: deque[dict[str, float]] = deque(maxlen=history)
        self._semaphore: asyncio.Semaphore | None = None
        self._semaphore_limit = self._max_workers
        self._async_lock: asyncio.Lock | None = None
        self._psutil = None
        self._psutil_process = None
        try:  # pragma: no cover - optional dependency
            import psutil  # type: ignore[import-untyped]

            self._psutil = psutil
            self._psutil_process = psutil.Process(os.getpid())
        except Exception:  # pragma: no cover - psutil missing
            self._psutil = None
            self._psutil_process = None

    @property
    def max_workers(self) -> int:
        """Return the current worker budget."""
        return self._max_workers

    def attach_semaphore(self, semaphore: asyncio.Semaphore) -> None:
        """Attach an asyncio semaphore for budget control."""
        self._semaphore = semaphore
        self._semaphore_limit = self._max_workers

    async def apply_worker_budget(self) -> int:
        """Apply the current worker budget to the semaphore."""
        if self._semaphore is None:
            return self._max_workers

        if self._async_lock is None:
            self._async_lock = asyncio.Lock()

        async with self._async_lock:
            desired = self._max_workers
            current = self._semaphore_limit
            if desired > current:
                for _ in range(desired - current):
                    self._semaphore.release()
            elif desired < current:
                reduction = current - desired
                for _ in range(reduction):
                    await self._semaphore.acquire()
            self._semaphore_limit = desired
            return self._max_workers

    def _record_usage(self, usage: dict[str, float]) -> None:
        """Record resource usage and predict worker budget."""
        self._usage_history.append(usage)
        self._predict_worker_budget()

    def _predict_worker_budget(self) -> None:
        """Adjust worker budget based on recent resource usage."""
        if len(self._usage_history) < 5:
            return

        cpu_vals = [entry["cpu_percent"] for entry in self._usage_history]
        mem_vals = [entry["memory_percent"] for entry in self._usage_history]
        recent_cpu = cpu_vals[-5:]
        recent_mem = mem_vals[-5:]
        avg_cpu = statistics.mean(recent_cpu)
        avg_mem = statistics.mean(recent_mem)

        new_budget = self._max_workers
        if self.max_cpu_percent and avg_cpu > self.max_cpu_percent * 0.95 or self.max_memory_mb and avg_mem > 90.0:
            new_budget = max(self.min_workers, self._max_workers - 1)
        elif avg_cpu < self.max_cpu_percent * 0.6 and avg_mem < 70.0:
            new_budget = min(self.hard_max_workers, self._max_workers + 1)

        self._max_workers = max(self.min_workers, min(new_budget, self.hard_max_workers))

    def check_memory_exceeded(
        self, usage: dict[str, float] | None = None
    ) -> tuple[bool, dict[str, float]]:
        """Check if memory limit has been exceeded."""
        usage = usage or self.get_resource_usage()
        exceeded = False
        if self.max_memory_mb is not None:
            exceeded = usage.get("rss_mb", 0.0) > self.max_memory_mb
        return exceeded, usage

    def check_cpu_exceeded(
        self, usage: dict[str, float] | None = None
    ) -> tuple[bool, dict[str, float]]:
        """Check if CPU limit has been exceeded."""
        usage = usage or self.get_resource_usage()
        exceeded = False
        if self.max_cpu_percent:
            exceeded = usage.get("cpu_percent", 0.0) > self.max_cpu_percent
        return exceeded, usage

    def get_resource_usage(self) -> dict[str, float]:
        """Capture current resource usage metrics."""
        timestamp = datetime.utcnow().isoformat()
        cpu_percent = 0.0
        memory_percent = 0.0
        rss_mb = 0.0

        if self._psutil:
            try:  # pragma: no cover - psutil branch
                cpu_percent = float(self._psutil.cpu_percent(interval=None))
                virtual_memory = self._psutil.virtual_memory()
                memory_percent = float(virtual_memory.percent)
                if self._psutil_process is not None:
                    rss_mb = float(self._psutil_process.memory_info().rss / (1024 * 1024))
            except Exception:
                cpu_percent = 0.0
        else:
            try:
                load1, _, _ = os.getloadavg()
                cpu_percent = float(min(100.0, load1 * 100))
            except OSError:
                cpu_percent = 0.0
            try:
                import resource

                usage_info = resource.getrusage(resource.RUSAGE_SELF)
                rss_mb = float(usage_info.ru_maxrss / 1024)
            except Exception:
                rss_mb = 0.0

        usage = {
            "timestamp": timestamp,
            "cpu_percent": cpu_percent,
            "memory_percent": memory_percent,
            "rss_mb": rss_mb,
            "worker_budget": float(self._max_workers),
        }
        self._record_usage(usage)
        return usage

    def get_usage_history(self) -> list[dict[str, float]]:
        """Return the recorded usage history."""
        return list(self._usage_history)

class PhaseInstrumentation:
    """Collects granular telemetry for each orchestration phase."""

    def __init__(
        self,
        phase_id: int,
        name: str,
        items_total: int | None = None,
        snapshot_interval: int = 10,
        resource_limits: ResourceLimits | None = None,
    ) -> None:
        self.phase_id = phase_id
        self.name = name
        self.items_total = items_total or 0
        self.snapshot_interval = max(1, snapshot_interval)
        self.resource_limits = resource_limits
        self.items_processed = 0
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.warnings: list[dict[str, Any]] = []
        self.errors: list[dict[str, Any]] = []
        self.resource_snapshots: list[dict[str, Any]] = []
        self.latencies: list[float] = []
        self.anomalies: list[dict[str, Any]] = []

    def start(self, items_total: int | None = None) -> None:
        """Mark the start of phase execution."""
        if items_total is not None:
            self.items_total = items_total
        self.start_time = time.perf_counter()

    def increment(self, count: int = 1, latency: float | None = None) -> None:
        """Increment processed item count and optionally record latency."""
        self.items_processed += count
        if latency is not None:
            self.latencies.append(latency)
            self._detect_latency_anomaly(latency)
        if self.resource_limits and self.should_snapshot():
            self.capture_resource_snapshot()

    def should_snapshot(self) -> bool:
        """Determine if a resource snapshot should be captured."""
        if self.items_total == 0:
            return False
        if self.items_processed == 0:
            return False
        return self.items_processed % self.snapshot_interval == 0

    def capture_resource_snapshot(self) -> None:
        """Capture a resource usage snapshot."""
        if not self.resource_limits:
            return
        snapshot = self.resource_limits.get_resource_usage()
        snapshot["items_processed"] = self.items_processed
        self.resource_snapshots.append(snapshot)

    def record_warning(self, category: str, message: str, **extra: Any) -> None:
        """Record a warning during phase execution."""
        entry = {
            "category": category,
            "message": message,
            **extra,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.warnings.append(entry)

    def record_error(self, category: str, message: str, **extra: Any) -> None:
        """Record an error during phase execution."""
        entry = {
            "category": category,
            "message": message,
            **extra,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.errors.append(entry)

    def _detect_latency_anomaly(self, latency: float) -> None:
        """Detect latency anomalies using statistical thresholds."""
        if len(self.latencies) < 5:
            return
        mean_latency = statistics.mean(self.latencies)
        std_latency = statistics.pstdev(self.latencies) or 0.0
        threshold = mean_latency + (3 * std_latency)
        if std_latency and latency > threshold:
            self.anomalies.append(
                {
                    "type": "latency_spike",
                    "latency": latency,
                    "mean": mean_latency,
                    "std": std_latency,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

    def complete(self) -> None:
        """Mark the end of phase execution."""
        self.end_time = time.perf_counter()

    def duration_ms(self) -> float | None:
        """Return the phase duration in milliseconds."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time) * 1000.0

    def progress(self) -> float | None:
        """Return the progress fraction (0.0 to 1.0)."""
        if not self.items_total:
            return None
        return min(1.0, self.items_processed / float(self.items_total))

    def throughput(self) -> float | None:
        """Return items processed per second."""
        if self.start_time is None:
            return None
        elapsed = (
            (time.perf_counter() - self.start_time)
            if self.end_time is None
            else (self.end_time - self.start_time)
        )
        if not elapsed:
            return None
        return self.items_processed / elapsed

    def latency_histogram(self) -> dict[str, float | None]:
        """Return latency percentiles."""
        if not self.latencies:
            return {"p50": None, "p95": None, "p99": None}
        sorted_latencies = sorted(self.latencies)

        def percentile(p: float) -> float:
            if not sorted_latencies:
                return 0.0
            k = (len(sorted_latencies) - 1) * (p / 100.0)
            f = int(k)
            c = min(f + 1, len(sorted_latencies) - 1)
            if f == c:
                return sorted_latencies[int(k)]
            d0 = sorted_latencies[f] * (c - k)
            d1 = sorted_latencies[c] * (k - f)
            return d0 + d1

        return {
            "p50": percentile(50.0),
            "p95": percentile(95.0),
            "p99": percentile(99.0),
        }

    def build_metrics(self) -> dict[str, Any]:
        """Build a metrics summary dictionary."""
        return {
            "phase_id": self.phase_id,
            "name": self.name,
            "duration_ms": self.duration_ms(),
            "items_processed": self.items_processed,
            "items_total": self.items_total,
            "progress": self.progress(),
            "throughput": self.throughput(),
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "resource_snapshots": list(self.resource_snapshots),
            "latency_histogram": self.latency_histogram(),
            "anomalies": list(self.anomalies),
        }

@dataclass
class PhaseResult:
    """Result of a single orchestration phase."""
    success: bool
    phase_id: str
    data: Any
    error: Exception | None
    duration_ms: float
    mode: str
    aborted: bool = False

@dataclass
class MicroQuestionRun:
    """Result of executing a single micro-question."""
    question_id: str
    question_global: int
    base_slot: str
    metadata: dict[str, Any]
    evidence: Evidence | None
    error: str | None = None
    duration_ms: float | None = None
    aborted: bool = False

@dataclass
class ScoredMicroQuestion:
    """Scored micro-question result."""
    question_id: str
    question_global: int
    base_slot: str
    score: float | None
    normalized_score: float | None
    quality_level: str | None
    evidence: Evidence | None
    scoring_details: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

class MethodExecutor:
    """Execute catalog methods using ArgRouter and class registry.

    This executor builds the class registry, instantiates all required classes,
    and delegates signature/kwargs handling to ArgRouter. No hardcoded logic.
    """

    def __init__(
        self, 
        dispatcher: Any | None = None, 
        calibrations: dict[str, Any] | None = None,
        signal_registry: Any | None = None,
    ) -> None:
        # Build the class registry
        self.degraded_mode = False
        self.degraded_reasons: list[str] = []
        self.signal_registry = signal_registry
        
        try:
            registry = build_class_registry()
        except (ClassRegistryError, ModuleNotFoundError, ImportError) as exc:
            self.degraded_mode = True
            reason = f"Class registry incomplete: {exc}"
            self.degraded_reasons.append(reason)
            logger.warning("DEGRADED MODE: %s", reason)
            registry = {}

        if calibrations is None:
            # DEPRECATION: No longer loading from YAML
            # Calibrations are now internal in calibration_registry.py
            # Leaving this logic in place only for backward compatibility during transition
            logger.info(
                "Calibration loading from YAML is deprecated. "
                "Using internal calibration_registry.CALIBRATIONS instead."
            )
            calibrations = {}  # Empty dict - YAML calibrations no longer supported

        self.raw_calibrations = calibrations  # Will be empty dict after migration
        self.calibrations = self._map_calibrations_to_classes(calibrations)  # Will be empty dict
        
        # Add calibration metadata for traceability
        self.calibration_version = CALIBRATION_VERSION
        self.calibration_hash = "n/a"  # Placeholder - hash function removed

        # Instantiate all classes
        self.instances: dict[str, Any] = {}
        ontology_instance = None

        for class_name, cls in registry.items():
            try:
                # Special handling for MunicipalOntology - shared instance
                if class_name == "MunicipalOntology":
                    ontology_instance = cls()
                    self.instances[class_name] = ontology_instance
                # Classes that need ontology
                elif class_name in ("SemanticAnalyzer", "PerformanceAnalyzer", "TextMiningEngine"):
                    if ontology_instance is not None:
                        self.instances[class_name] = cls(ontology_instance)
                    else:
                        logger.warning(
                            "Cannot instantiate %s: MunicipalOntology not available", class_name
                        )
                # PolicyTextProcessor needs ProcessorConfig
                elif class_name == "PolicyTextProcessor":
                    try:
                        from policy_processor import ProcessorConfig
                        calibration_payload = self.calibrations.get(class_name)
                        if calibration_payload is not None and self._supports_parameter(cls, "calibration"):
                            self.instances[class_name] = cls(ProcessorConfig(), calibration=calibration_payload)
                        else:
                            self.instances[class_name] = cls(ProcessorConfig())
                    except ImportError:
                        logger.warning("Cannot instantiate PolicyTextProcessor: ProcessorConfig unavailable")
                else:
                    # Standard instantiation
                    calibration_payload = self.calibrations.get(class_name)
                    if calibration_payload is not None and self._supports_parameter(cls, "calibration"):
                        self.instances[class_name] = cls(calibration=calibration_payload)
                    else:
                        self.instances[class_name] = cls()
            except Exception as exc:
                logger.error("Failed to instantiate %s: %s", class_name, exc)

        # Create ExtendedArgRouter with the registry for enhanced validation and metrics
        self._router = ExtendedArgRouter(registry)
        
        # Check for critical degradation
        if len(self.instances) == 0 and len(registry) > 0:
            self.degraded_mode = True
            reason = "All class instantiations failed"
            self.degraded_reasons.append(reason)
            logger.error("CRITICAL DEGRADATION: %s", reason)

    def _map_calibrations_to_classes(self, calibrations: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Map legacy YAML calibrations to classes.
        
        NOTE: This method is deprecated and will always return an empty dict
        since calibrations parameter is always {} (YAML loading disabled).
        Kept for backward compatibility during transition period.
        """
        # Legacy YAML calibration mapping - no longer used
        # calibrations is always {} since YAML loading was deprecated
        return {}

    @staticmethod
    def _supports_parameter(callable_obj: Any, parameter_name: str) -> bool:
        try:
            signature = inspect.signature(callable_obj)
        except (TypeError, ValueError):  # pragma: no cover - builtins / C extensions
            return False
        return parameter_name in signature.parameters

    def execute(self, class_name: str, method_name: str, **kwargs: Any) -> Any:
        """Execute a method from the catalog.

        Args:
            class_name: Name of the class
            method_name: Name of the method to execute
            **kwargs: Keyword arguments to pass to the method

        Returns:
            The method's return value

        Raises:
            ArgRouterError: If routing fails
            AttributeError: If method doesn't exist
            RuntimeError: If calibration is missing or placeholder
        """
        # Fail-fast calibration enforcement
        calib = resolve_calibration(class_name, method_name)
        if calib is None:
            raise RuntimeError(f"No calibration registered for {class_name}.{method_name}")
        if calib.is_default_like():
            raise RuntimeError(f"Placeholder calibration detected for {class_name}.{method_name}")
        
        instance = self.instances.get(class_name)
        if not instance:
            logger.warning("No instance available for class %s", class_name)
            return None

        try:
            method = getattr(instance, method_name)
        except AttributeError:
            logger.error("Class %s has no method %s", class_name, method_name)
            raise

        try:
            args, routed_kwargs = self._router.route(class_name, method_name, dict(kwargs))
            return method(*args, **routed_kwargs)
        except (ArgRouterError, ArgumentValidationError):
            logger.exception("Argument routing failed for %s.%s", class_name, method_name)
            raise
        except Exception:
            logger.exception("Method execution failed for %s.%s", class_name, method_name)
            raise

    def get_routing_metrics(self) -> dict[str, Any]:
        """Get routing metrics from ExtendedArgRouter.
        
        Returns:
            Dict with routing statistics including:
            - total_routes: Total number of routes processed
            - special_routes_hit: Count of special route invocations
            - validation_errors: Count of validation failures
            - silent_drops_prevented: Count of silent parameter drops prevented
        """
        if hasattr(self._router, 'get_metrics'):
            return self._router.get_metrics()
        return {}

def validate_phase_definitions(phase_list: list[tuple[int, str, str, str]], orchestrator_class: type) -> None:
    """Validate phase definitions for structural coherence.
    
    This is a hard gate: if phase definitions are broken, the orchestrator cannot start.
    No "limited mode" is allowed when the base schema is corrupted.
    
    Args:
        phase_list: List of phase tuples (id, mode, handler, label)
        orchestrator_class: Orchestrator class to check for handler methods
        
    Raises:
        RuntimeError: If phase definitions are invalid
    """
    if not phase_list:
        raise RuntimeError("FASES cannot be empty - no phases defined for orchestration")
    
    # Extract phase IDs
    phase_ids = [phase[0] for phase in phase_list]
    
    # Check for duplicate phase IDs
    seen_ids = set()
    for phase_id in phase_ids:
        if phase_id in seen_ids:
            raise RuntimeError(
                f"Duplicate phase ID {phase_id} in FASES definition. "
                "Phase IDs must be unique."
            )
        seen_ids.add(phase_id)
    
    # Check that IDs are contiguous starting from 0
    # For performance: check sorted and validate range
    if phase_ids != sorted(phase_ids):
        raise RuntimeError(
            f"Phase IDs must be sorted in ascending order. Got {phase_ids}"
        )
    if phase_ids[0] != 0:
        raise RuntimeError(
            f"Phase IDs must start from 0. Got first ID: {phase_ids[0]}"
        )
    if phase_ids[-1] != len(phase_list) - 1:
        raise RuntimeError(
            f"Phase IDs must be contiguous from 0 to {len(phase_list) - 1}. "
            f"Got highest ID: {phase_ids[-1]}"
        )
    
    # Validate each phase
    valid_modes = {"sync", "async"}
    for phase_id, mode, handler_name, label in phase_list:
        # Validate mode
        if mode not in valid_modes:
            raise RuntimeError(
                f"Phase {phase_id} ({label}): invalid mode '{mode}'. "
                f"Mode must be one of {valid_modes}"
            )
        
        # Validate handler exists as method in orchestrator
        if not hasattr(orchestrator_class, handler_name):
            raise RuntimeError(
                f"Phase {phase_id} ({label}): handler method '{handler_name}' "
                f"does not exist in {orchestrator_class.__name__}"
            )
        
        # Validate handler is callable
        handler = getattr(orchestrator_class, handler_name, None)
        if not callable(handler):
            raise RuntimeError(
                f"Phase {phase_id} ({label}): handler '{handler_name}' "
                f"is not callable"
            )


class Orchestrator:
    """Robust 11-phase orchestrator with abort support and resource control.

    The Orchestrator owns the provider and prepares all data for processors
    and executors. It executes 11 phases synchronously or asynchronously,
    with full instrumentation and abort capability.
    """

    FASES: list[tuple[int, str, str, str]] = [
        (0, "sync", "_load_configuration", "FASE 0 - Validación de Configuración"),
        (1, "sync", "_ingest_document", "FASE 1 - Ingestión de Documento"),
        (2, "async", "_execute_micro_questions_async", "FASE 2 - Micro Preguntas"),
        (3, "async", "_score_micro_results_async", "FASE 3 - Scoring Micro"),
        (4, "async", "_aggregate_dimensions_async", "FASE 4 - Agregación Dimensiones"),
        (5, "async", "_aggregate_policy_areas_async", "FASE 5 - Agregación Áreas"),
        (6, "sync", "_aggregate_clusters", "FASE 6 - Agregación Clústeres"),
        (7, "sync", "_evaluate_macro", "FASE 7 - Evaluación Macro"),
        (8, "async", "_generate_recommendations", "FASE 8 - Recomendaciones"),
        (9, "sync", "_assemble_report", "FASE 9 - Ensamblado de Reporte"),
        (10, "async", "_format_and_export", "FASE 10 - Formateo y Exportación"),
    ]

    PHASE_ITEM_TARGETS: dict[int, int] = {
        0: 1,
        1: 1,
        2: 300,
        3: 300,
        4: 60,
        5: 10,
        6: 4,
        7: 1,
        8: 1,
        9: 1,
        10: 1,
    }

    PHASE_OUTPUT_KEYS: dict[int, str] = {
        0: "config",
        1: "document",
        2: "micro_results",
        3: "scored_results",
        4: "dimension_scores",
        5: "policy_area_scores",
        6: "cluster_scores",
        7: "macro_result",
        8: "recommendations",
        9: "report",
        10: "export_payload",
    }

    PHASE_ARGUMENT_KEYS: dict[int, list[str]] = {
        1: ["pdf_path", "config"],
        2: ["document", "config"],
        3: ["micro_results", "config"],
        4: ["scored_results", "config"],
        5: ["dimension_scores", "config"],
        6: ["policy_area_scores", "config"],
        7: ["cluster_scores", "config"],
        8: ["macro_result", "config"],
        9: ["recommendations", "config"],
        10: ["report", "config"],
    }

    # Phase timeout configuration (in seconds)
    PHASE_TIMEOUTS: dict[int, float] = {
        0: 60,     # Configuration validation
        1: 120,    # Document ingestion
        2: 600,    # Micro questions (300 items)
        3: 300,    # Scoring micro
        4: 180,    # Dimension aggregation
        5: 120,    # Policy area aggregation
        6: 60,     # Cluster aggregation
        7: 60,     # Macro evaluation
        8: 120,    # Recommendations
        9: 60,     # Report assembly
        10: 120,   # Format and export
    }

    # Score normalization constant
    PERCENTAGE_SCALE: int = 100

    def __init__(
        self,
        catalog: dict[str, Any] | None = None,
        monolith: dict[str, Any] | None = None,
        questionnaire: "CanonicalQuestionnaire | None" = None,
        method_map: dict[str, Any] | None = None,
        schema: dict[str, Any] | None = None,
        catalog_path: str | None = None,
        monolith_path: str | None = None,
        method_map_path: str | None = None,
        schema_path: str | None = None,
        resource_limits: ResourceLimits | None = None,
        resource_snapshot_interval: int = 10,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            catalog: Pre-loaded method catalog data (preferred, I/O-free)
            monolith: DEPRECATED - Use questionnaire parameter instead
            questionnaire: Pre-loaded CanonicalQuestionnaire (PREFERRED, I/O-free, type-safe)
            method_map: Pre-loaded method-class mapping data (preferred, I/O-free)
            schema: Pre-loaded questionnaire schema data (preferred, I/O-free)
            catalog_path: Legacy path to method catalog JSON (deprecated, triggers I/O)
            monolith_path: Legacy path to questionnaire monolith JSON (deprecated, triggers I/O)
            method_map_path: Legacy path to method-class mapping JSON (deprecated, triggers I/O)
            schema_path: Legacy path to questionnaire schema (deprecated, triggers I/O)
            resource_limits: Resource limit configuration
            resource_snapshot_interval: Interval for resource snapshots

        Note:
            QUESTIONNAIRE INTEGRITY ENFORCEMENT:
            - Prefer 'questionnaire' parameter (CanonicalQuestionnaire) for type safety
            - The 'monolith' parameter is deprecated (accepts dict for backward compatibility)
            - For I/O-free initialization, use factory.py to load data
            - Passing path parameters triggers I/O and is deprecated
        """
        # ========================================================================
        # QUESTIONNAIRE INTEGRITY ENFORCEMENT
        # ========================================================================
        # Import CanonicalQuestionnaire for type checking
        from .questionnaire import CanonicalQuestionnaire

        # Handle questionnaire parameter (preferred) vs monolith (deprecated)
        if questionnaire is not None and monolith is not None:
            raise ValueError(
                "Cannot specify both 'questionnaire' and 'monolith' parameters. "
                "Use 'questionnaire' (CanonicalQuestionnaire) for type safety."
            )

        if questionnaire is not None:
            # Type-safe path: CanonicalQuestionnaire already validated
            if not isinstance(questionnaire, CanonicalQuestionnaire):
                raise TypeError(
                    f"questionnaire must be CanonicalQuestionnaire, got {type(questionnaire).__name__}"
                )
            self._canonical_questionnaire = questionnaire
            self._monolith_data = dict(questionnaire.data)  # Extract mutable dict for internal use
            logger.info(
                "orchestrator_initialized_with_canonical_questionnaire",
                sha256=questionnaire.sha256[:16] + "...",
                question_count=questionnaire.total_question_count,
                version=questionnaire.version,
            )
        elif monolith is not None:
            # Legacy path: dict provided (deprecated)
            import warnings
            warnings.warn(
                "Orchestrator 'monolith' parameter is deprecated. "
                "Use 'questionnaire' parameter with CanonicalQuestionnaire instead. "
                "Load via: from saaaaaa.core.orchestrator.questionnaire import load_questionnaire",
                DeprecationWarning,
                stacklevel=2
            )
            self._canonical_questionnaire = None
            self._monolith_data = monolith
            logger.warning(
                "orchestrator_initialized_with_legacy_dict",
                version=monolith.get("version", "unknown"),
            )
            # Validate structure of legacy dict
            from .questionnaire import _validate_questionnaire_structure
            try:
                _validate_questionnaire_structure(monolith)
            except (ValueError, TypeError) as e:
                raise RuntimeError(
                    f"Questionnaire structure validation failed: {e}. "
                    "Cannot start orchestrator with corrupt questionnaire."
                ) from e
        else:
            # Neither provided - will need to load later
            self._canonical_questionnaire = None
            self._monolith_data = None

        # Store other pre-loaded data
        self._catalog_data = catalog
        self._method_map_data = method_map
        self._schema_data = schema

        # ========================================================================
        # PROMPT_SCHEMA_GATES_ENFORCER: Validate phase definitions at startup
        # No limited mode allowed - if schema is broken, orchestrator cannot start
        # ========================================================================
        validate_phase_definitions(self.FASES, self.__class__)

        # ========================================================================
        # DEPRECATION WARNINGS for path parameters
        # Path parameters trigger I/O and are deprecated in favor of pre-loaded data
        # ========================================================================
        import warnings

        path_params = {
            "catalog_path": (
                catalog_path,
                "Use 'catalog' parameter with pre-loaded data instead. "
                "Load via: from saaaaaa.core.orchestrator.factory import build_processor",
            ),
            "monolith_path": (
                monolith_path,
                "Use 'questionnaire' parameter with CanonicalQuestionnaire instead. "
                "Load via: from saaaaaa.core.orchestrator.questionnaire import load_questionnaire",
            ),
            "method_map_path": (
                method_map_path,
                "Use 'method_map' parameter with pre-loaded data instead. "
                "Load via: from saaaaaa.core.orchestrator.factory import build_processor",
            ),
            "schema_path": (
                schema_path,
                "Use 'schema' parameter with pre-loaded data instead. "
                "Load via: from saaaaaa.core.orchestrator.factory import build_processor",
            ),
        }

        for param_name, (param_value, message) in path_params.items():
            if param_value is not None:
                warnings.warn(
                    f"Orchestrator '{param_name}' parameter is DEPRECATED. {message}",
                    DeprecationWarning,
                    stacklevel=2,
                )

        # Store paths for backward compatibility (but deprecated)
        self.catalog_path = self._resolve_path(catalog_path) if catalog_path else None
        self.monolith_path = self._resolve_path(monolith_path) if monolith_path else None
        self.method_map_path = self._resolve_path(method_map_path) if method_map_path else None
        self.schema_path = self._resolve_path(schema_path) if schema_path else None
        self.resource_limits = resource_limits or ResourceLimits()
        self.resource_snapshot_interval = max(1, resource_snapshot_interval)

        # Load catalog from pre-loaded data (I/O-free path)
        if self._catalog_data is not None:
            self.catalog = self._catalog_data
        else:
            # No data provided - will need to load later or fail
            # This allows construction without I/O but requires data to be set before use
            self.catalog = None
        
        # ========================================================================
        # PROMPT_NONEMPTY_EXECUTION_GRAPH_ENFORCER: Validate catalog is non-empty
        # Cannot proceed with empty catalog
        # ========================================================================
        if self.catalog is not None:
            if not self.catalog:
                raise RuntimeError(
                    "Method catalog is empty - cannot run pipeline. "
                    "A non-empty catalog is required for orchestration."
                )
            # Check if catalog has methods attribute/key
            catalog_methods = None
            if isinstance(self.catalog, dict):
                catalog_methods = self.catalog.get("methods")
            elif hasattr(self.catalog, "methods"):
                catalog_methods = getattr(self.catalog, "methods", None)
            
            if catalog_methods is not None and not catalog_methods:
                raise RuntimeError(
                    "Method catalog.methods is empty - cannot run pipeline. "
                    "At least one method must be registered in the catalog."
                )

        self.executor = MethodExecutor()
        
        # ========================================================================
        # PROMPT_NONEMPTY_EXECUTION_GRAPH_ENFORCER: Validate MethodExecutor.instances is non-empty
        # No "limited mode" when instances registry is empty
        # ========================================================================
        if not self.executor.instances:
            raise RuntimeError(
                "MethodExecutor.instances is empty - no executable methods registered. "
                "Cannot start orchestration without method instances. "
                "Check that class registry is properly configured."
            )
        
        self.calibrations: dict[str, Any] = getattr(self.executor, "raw_calibrations", {})

        # Import executors from the executors module
        from . import executors

        self.executors = {
            "D1-Q1": executors.D1Q1_Executor,
            "D1-Q2": executors.D1Q2_Executor,
            "D1-Q3": executors.D1Q3_Executor,
            "D1-Q4": executors.D1Q4_Executor,
            "D1-Q5": executors.D1Q5_Executor,
            "D2-Q1": executors.D2Q1_Executor,
            "D2-Q2": executors.D2Q2_Executor,
            "D2-Q3": executors.D2Q3_Executor,
            "D2-Q4": executors.D2Q4_Executor,
            "D2-Q5": executors.D2Q5_Executor,
            "D3-Q1": executors.D3Q1_Executor,
            "D3-Q2": executors.D3Q2_Executor,
            "D3-Q3": executors.D3Q3_Executor,
            "D3-Q4": executors.D3Q4_Executor,
            "D3-Q5": executors.D3Q5_Executor,
            "D4-Q1": executors.D4Q1_Executor,
            "D4-Q2": executors.D4Q2_Executor,
            "D4-Q3": executors.D4Q3_Executor,
            "D4-Q4": executors.D4Q4_Executor,
            "D4-Q5": executors.D4Q5_Executor,
            "D5-Q1": executors.D5Q1_Executor,
            "D5-Q2": executors.D5Q2_Executor,
            "D5-Q3": executors.D5Q3_Executor,
            "D5-Q4": executors.D5Q4_Executor,
            "D5-Q5": executors.D5Q5_Executor,
            "D6-Q1": executors.D6Q1_Executor,
            "D6-Q2": executors.D6Q2_Executor,
            "D6-Q3": executors.D6Q3_Executor,
            "D6-Q4": executors.D6Q4_Executor,
            "D6-Q5": executors.D6Q5_Executor,
        }

        self.abort_signal = AbortSignal()
        self.phase_results: list[PhaseResult] = []
        self._phase_instrumentation: dict[int, PhaseInstrumentation] = {}
        self._phase_status: dict[int, str] = {
            phase_id: "not_started" for phase_id, *_ in self.FASES
        }
        self._phase_outputs: dict[int, Any] = {}
        self._context: dict[str, Any] = {}
        self._start_time: float | None = None

        # Initialize dependency lockdown enforcement
        self.dependency_lockdown = get_dependency_lockdown()
        logger.info(
            f"Orchestrator dependency mode: {self.dependency_lockdown.get_mode_description()}"
        )

        # Initialize RecommendationEngine for 3-level recommendations
        # Get questionnaire provider for dependency injection (shared by all init paths)
        try:
            from . import get_questionnaire_provider
            questionnaire_provider = get_questionnaire_provider()
        except Exception as e:
            logger.warning(f"Failed to get questionnaire provider: {e}")
            questionnaire_provider = None
        
        # Note: Passing orchestrator=self is safe here because RecommendationEngine
        # only stores the reference in __init__ and doesn't access orchestrator
        # attributes during initialization. The orchestrator is fully set up at
        # this point (all required attributes initialized above).
        try:
            # Try to load enhanced rules first (v2.0), fallback to v1.0
            try:
                self.recommendation_engine = RecommendationEngine(
                    rules_path="config/recommendation_rules_enhanced.json",
                    schema_path="rules/recommendation_rules_enhanced.schema.json",
                    questionnaire_provider=questionnaire_provider,
                    orchestrator=self
                )
                logger.info("RecommendationEngine initialized with enhanced v2.0 rules")
            except Exception as e_enhanced:
                logger.info(f"Enhanced rules not available ({e_enhanced}), falling back to v1.0")
                self.recommendation_engine = RecommendationEngine(
                    rules_path="config/recommendation_rules.json",
                    schema_path="rules/recommendation_rules.schema.json",
                    questionnaire_provider=questionnaire_provider,
                    orchestrator=self
                )
                logger.info("RecommendationEngine initialized with v1.0 rules")
        except Exception as e:
            logger.warning(f"Failed to initialize RecommendationEngine: {e}")
            self.recommendation_engine = None

    def _resolve_path(self, path: str | None) -> str | None:
        """Resolve a relative or absolute path, searching multiple candidate locations."""
        if path is None:
            return None

        candidates = [path]
        if not os.path.isabs(path):
            base_dir = os.path.dirname(__file__)
            candidates.append(os.path.join(base_dir, path))
            candidates.append(os.path.join(os.getcwd(), path))
            if not path.startswith("rules"):
                candidates.append(os.path.join(os.getcwd(), "rules", "METODOS", path))

        for candidate in candidates:
            if candidate and os.path.exists(candidate):
                return candidate

        return path

    def _get_phase_timeout(self, phase_id: int) -> float:
        """Get timeout for a specific phase."""
        return self.PHASE_TIMEOUTS.get(phase_id, 300.0)  # Default 5 minutes

    def process_development_plan(
            self, pdf_path: str, preprocessed_document: Any | None = None
    ) -> list[PhaseResult]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            raise RuntimeError("process_development_plan() debe ejecutarse fuera de un loop asyncio activo")
        return asyncio.run(
            self.process_development_plan_async(
                pdf_path, preprocessed_document=preprocessed_document
            )
        )

    async def process(self, preprocessed_document: Any) -> list[PhaseResult]:
        """
        DEPRECATED ALIAS for process_development_plan_async().

        This method exists ONLY for backward compatibility with code
        that incorrectly assumed Orchestrator had a .process() method.

        Use process_development_plan_async() instead.

        Args:
            preprocessed_document: PreprocessedDocument to process

        Returns:
            List of phase results

        Raises:
            DeprecationWarning: This method is deprecated
        """
        import warnings
        warnings.warn(
            "Orchestrator.process() is deprecated. "
            "Use process_development_plan_async(pdf_path, preprocessed_document=...) instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Extract pdf_path from preprocessed_document if available
        pdf_path = getattr(preprocessed_document, 'source_path', None)
        if pdf_path is None:
            # Try to get from metadata
            metadata = getattr(preprocessed_document, 'metadata', {})
            pdf_path = metadata.get('source_path', 'unknown.pdf')

        return await self.process_development_plan_async(
            pdf_path=str(pdf_path),
            preprocessed_document=preprocessed_document
        )

    async def process_development_plan_async(
            self, pdf_path: str, preprocessed_document: Any | None = None
    ) -> list[PhaseResult]:
        self.reset_abort()
        self.phase_results = []
        self._phase_instrumentation = {}
        self._phase_outputs = {}
        self._context = {"pdf_path": pdf_path}
        if preprocessed_document is not None:
            self._context["preprocessed_override"] = preprocessed_document
        self._phase_status = {phase_id: "not_started" for phase_id, *_ in self.FASES}
        self._start_time = time.perf_counter()

        for phase_id, mode, handler_name, phase_label in self.FASES:
            self._ensure_not_aborted()
            handler = getattr(self, handler_name)
            instrumentation = PhaseInstrumentation(
                phase_id=phase_id,
                name=phase_label,
                items_total=self.PHASE_ITEM_TARGETS.get(phase_id),
                snapshot_interval=self.resource_snapshot_interval,
                resource_limits=self.resource_limits,
            )
            instrumentation.start(items_total=self.PHASE_ITEM_TARGETS.get(phase_id))
            self._phase_instrumentation[phase_id] = instrumentation
            self._phase_status[phase_id] = "running"

            args = [self._context[key] for key in self.PHASE_ARGUMENT_KEYS.get(phase_id, [])]

            success = False
            data: Any = None
            error: Exception | None = None
            try:
                if mode == "sync":
                    data = handler(*args)
                else:
                    # Use centralized execute_phase_with_timeout
                    data = await execute_phase_with_timeout(
                        phase_id,
                        phase_label,
                        handler,
                        *args,
                        timeout_s=self._get_phase_timeout(phase_id),
                    )
                success = True
            except PhaseTimeoutError as exc:
                error = exc
                success = False
                instrumentation.record_error("timeout", str(exc))
                self.request_abort(f"Fase {phase_id} timed out: {exc}")
            except AbortRequested as exc:
                error = exc
                success = False
                instrumentation.record_warning("abort", str(exc))
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.exception("Fase %s falló", phase_label)
                error = exc
                success = False
                instrumentation.record_error("exception", str(exc))
                self.request_abort(f"Fase {phase_id} falló: {exc}")
            finally:
                instrumentation.complete()

            aborted = self.abort_signal.is_aborted()
            duration_ms = instrumentation.duration_ms() or 0.0
            phase_result = PhaseResult(
                success=success and not aborted,
                phase_id=str(phase_id),
                data=data,
                error=error,
                duration_ms=duration_ms,
                mode=mode,
                aborted=aborted,
            )
            self.phase_results.append(phase_result)

            if success and not aborted:
                self._phase_outputs[phase_id] = data
                out_key = self.PHASE_OUTPUT_KEYS.get(phase_id)
                if out_key:
                    self._context[out_key] = data
                self._phase_status[phase_id] = "completed"
            elif aborted:
                self._phase_status[phase_id] = "aborted"
                break
            else:
                self._phase_status[phase_id] = "failed"
                break

        return self.phase_results

    def get_processing_status(self) -> dict[str, Any]:
        if self._start_time is None:
            status = "not_started"
            elapsed = 0.0
            completed_flag = False
        else:
            aborted = self.abort_signal.is_aborted()
            status = "aborted" if aborted else "running"
            elapsed = time.perf_counter() - self._start_time
            completed_flag = all(state == "completed" for state in self._phase_status.values()) and not aborted

        completed = sum(1 for state in self._phase_status.values() if state == "completed")
        total = len(self.FASES)
        overall_progress = completed / total if total else 0.0

        phase_progress = {
            str(phase_id): instr.progress()
            for phase_id, instr in self._phase_instrumentation.items()
        }

        resource_usage = self.resource_limits.get_resource_usage() if self._start_time else {}

        return {
            "status": status,
            "overall_progress": overall_progress,
            "phase_progress": phase_progress,
            "elapsed_time_s": elapsed,
            "resource_usage": resource_usage,
            "abort_status": self.abort_signal.is_aborted(),
            "abort_reason": self.abort_signal.get_reason(),
            "completed": completed_flag,
        }

    def get_phase_metrics(self) -> dict[str, Any]:
        return {
            str(phase_id): instr.build_metrics()
            for phase_id, instr in self._phase_instrumentation.items()
        }

    async def monitor_progress_async(self, poll_interval: float = 2.0):
        while True:
            status = self.get_processing_status()
            yield status
            if status["status"] != "running":
                break
            await asyncio.sleep(poll_interval)

    def abort_handler(self, reason: str) -> None:
        self.request_abort(reason)

    def request_abort(self, reason: str) -> None:
        """Request orchestration to abort with a specific reason."""
        self.abort_signal.abort(reason)
        logger.warning(f"Abort requested: {reason}")

    def reset_abort(self) -> None:
        """Reset the abort signal to allow new orchestration runs."""
        self.abort_signal.reset()
        logger.debug("Abort signal reset")

    def _ensure_not_aborted(self) -> None:
        """Check if orchestration has been aborted and raise exception if so."""
        if self.abort_signal.is_aborted():
            reason = self.abort_signal.get_reason() or "Unknown reason"
            raise AbortRequested(f"Orchestration aborted: {reason}")

    def health_check(self) -> dict[str, Any]:
        usage = self.resource_limits.get_resource_usage()
        cpu_headroom = max(0.0, self.resource_limits.max_cpu_percent - usage.get("cpu_percent", 0.0))
        mem_headroom = max(0.0, (self.resource_limits.max_memory_mb or 0.0) - usage.get("rss_mb", 0.0))
        score = max(0.0, min(100.0, (cpu_headroom / max(1.0, self.resource_limits.max_cpu_percent)) * 50.0))
        if self.resource_limits.max_memory_mb:
            score += max(0.0, min(50.0, (mem_headroom / max(1.0, self.resource_limits.max_memory_mb)) * 50.0))
        score = min(100.0, score)
        if self.abort_signal.is_aborted():
            score = min(score, 20.0)
        return {"score": score, "resource_usage": usage, "abort": self.abort_signal.is_aborted()}

    def get_system_health(self) -> dict[str, Any]:
        """
        Comprehensive system health check.
        
        Returns health status with component checks for:
        - Method executor
        - Questionnaire provider (if available)
        - Resource limits and usage
        
        Returns:
            Dict with overall status ('healthy', 'degraded', 'unhealthy')
            and component-specific health information
        """
        health = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }

        # Check method executor
        try:
            executor_health = {
                'instances_loaded': len(self.executor.instances),
                'calibrations_loaded': len(self.executor.calibrations),
                'status': 'healthy'
            }
            health['components']['method_executor'] = executor_health
        except Exception as e:
            health['status'] = 'unhealthy'
            health['components']['method_executor'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check questionnaire provider (if available)
        try:
            from . import get_questionnaire_provider
            provider = get_questionnaire_provider()
            questionnaire_health = {
                'has_data': provider.has_data(),
                'status': 'healthy' if provider.has_data() else 'unhealthy'
            }
            health['components']['questionnaire_provider'] = questionnaire_health
            
            if not provider.has_data():
                health['status'] = 'degraded'
        except Exception as e:
            health['status'] = 'unhealthy'
            health['components']['questionnaire_provider'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check resource limits
        try:
            usage = self.resource_limits.get_resource_usage()
            resource_health = {
                'cpu_percent': usage.get('cpu_percent', 0),
                'memory_mb': usage.get('rss_mb', 0),
                'worker_budget': usage.get('worker_budget', 0),
                'status': 'healthy'
            }
            
            # Warning thresholds
            if usage.get('cpu_percent', 0) > 80:
                resource_health['status'] = 'degraded'
                resource_health['warning'] = 'High CPU usage'
                health['status'] = 'degraded'
            
            if usage.get('rss_mb', 0) > 3500:  # Near 4GB limit
                resource_health['status'] = 'degraded'
                resource_health['warning'] = 'High memory usage'
                health['status'] = 'degraded'
            
            health['components']['resources'] = resource_health
        except Exception as e:
            health['status'] = 'unhealthy'
            health['components']['resources'] = {
                'status': 'unhealthy',
                'error': str(e)
            }

        # Check abort status
        if self.abort_signal.is_aborted():
            health['status'] = 'unhealthy'
            health['abort_reason'] = self.abort_signal.get_reason()

        return health

    def export_metrics(self) -> dict[str, Any]:
        """
        Export all metrics for monitoring.
        
        Returns:
            Dict containing:
            - timestamp: Current UTC timestamp
            - phase_metrics: Metrics for all phases
            - resource_usage: Resource usage history
            - abort_status: Current abort status
            - phase_status: Status of all phases
        """
        abort_timestamp = self.abort_signal.get_timestamp()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'phase_metrics': self.get_phase_metrics(),
            'resource_usage': self.resource_limits.get_usage_history(),
            'abort_status': {
                'is_aborted': self.abort_signal.is_aborted(),
                'reason': self.abort_signal.get_reason(),
                'timestamp': abort_timestamp.isoformat() if abort_timestamp else None,
            },
            'phase_status': dict(self._phase_status),
        }

    def _load_configuration(self) -> dict[str, Any]:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[0]
        start = time.perf_counter()

        # Use pre-loaded monolith data (I/O-free path)
        if self._monolith_data is not None:
            # Normalize monolith for hash and serialization (handles MappingProxyType)
            monolith = _normalize_monolith_for_hash(self._monolith_data)
            
            # Stable, content-based hash for reproducibility
            monolith_hash = hashlib.sha256(
                json.dumps(monolith, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
        else:
            raise ValueError(
                "No monolith data available. Use saaaaaa.core.orchestrator.factory to load "
                "data and pass via monolith parameter for I/O-free initialization."
            )

        micro_questions: list[dict[str, Any]] = monolith["blocks"].get("micro_questions", [])
        meso_questions: list[dict[str, Any]] = monolith["blocks"].get("meso_questions", [])
        macro_question: dict[str, Any] = monolith["blocks"].get("macro_question", {})

        question_total = len(micro_questions) + len(meso_questions) + (1 if macro_question else 0)
        if question_total != EXPECTED_QUESTION_COUNT:
            logger.warning("Question count mismatch: expected %s, got %s", EXPECTED_QUESTION_COUNT, question_total)
            instrumentation.record_error("integrity", f"Conteo de preguntas inesperado: {question_total}", expected=EXPECTED_QUESTION_COUNT, found=question_total)

        structure_report = self._validate_contract_structure(monolith, instrumentation)

        method_summary: dict[str, Any] = {}
        # Use pre-loaded method_map data (I/O-free path)
        if self._method_map_data is not None:
            method_map = self._method_map_data
            
            # ========================================================================
            # PROMPT_NONEMPTY_EXECUTION_GRAPH_ENFORCER: Validate method_map is non-empty
            # Cannot route methods with empty map
            # ========================================================================
            if not method_map:
                raise RuntimeError(
                    "Method map is empty - cannot route methods. "
                    "A non-empty method map is required for orchestration."
                )
            
            summary = method_map.get("summary", {})
            total_methods = summary.get("total_methods")
            if total_methods != EXPECTED_METHOD_COUNT:
                logger.warning("Method count mismatch: expected %s, got %s", EXPECTED_METHOD_COUNT, total_methods)
                instrumentation.record_error(
                    "catalog",
                    "Total de métodos inesperado",
                    expected=EXPECTED_METHOD_COUNT,
                    found=total_methods,
                )
            method_summary = {
                "total_methods": total_methods,
                "metadata": summary,
            }

        schema_report: dict[str, Any] = {"errors": []}
        # Use pre-loaded schema data (I/O-free path)
        if self._schema_data is not None:
            try:  # pragma: no cover - optional dependency
                import jsonschema

                schema = self._schema_data

                validator = jsonschema.Draft202012Validator(schema)
                schema_errors = [
                    {
                        "path": list(error.path),
                        "message": error.message,
                    }
                    for error in validator.iter_errors(monolith)
                ]
                schema_report["errors"] = schema_errors
                if schema_errors:
                    instrumentation.record_error(
                        "schema",
                        f"Validation errors: {len(schema_errors)}",
                        count=len(schema_errors),
                    )
            except ImportError:
                logger.warning("jsonschema not installed, skipping schema validation")

        duration = time.perf_counter() - start
        instrumentation.increment(latency=duration)

        config = {
            "catalog": self.catalog,
            "monolith": monolith,
            "monolith_sha256": monolith_hash,
            "micro_questions": micro_questions,
            "meso_questions": meso_questions,
            "macro_question": macro_question,
            "structure_report": structure_report,
            "method_summary": method_summary,
            "schema_report": schema_report,
        }

        return config

    def _validate_contract_structure(self, monolith: dict[str, Any], instrumentation: PhaseInstrumentation) -> dict[
        str, Any]:
        micro_questions = monolith["blocks"].get("micro_questions", [])
        base_slots = {question.get("base_slot") for question in micro_questions}
        modalities = {question.get("scoring_modality") for question in micro_questions}
        expected_modalities = {"TYPE_A", "TYPE_B", "TYPE_C", "TYPE_D", "TYPE_E", "TYPE_F"}

        if len(base_slots) != 30:
            instrumentation.record_error(
                "structure",
                "Cantidad de slots base inválida",
                expected=30,
                found=len(base_slots),
            )

        missing_modalities = expected_modalities - modalities
        if missing_modalities:
            instrumentation.record_error(
                "structure",
                "Modalidades faltantes",
                missing=sorted(missing_modalities),
            )

        slot_area_map: dict[str, str] = {}
        area_cluster_map: dict[str, str] = {}
        for question in micro_questions:
            slot = question.get("base_slot")
            area = question.get("policy_area_id")
            cluster = question.get("cluster_id")
            if slot and area:
                previous = slot_area_map.setdefault(slot, area)
                if previous != area:
                    instrumentation.record_error(
                        "structure",
                        "Asignación de área inconsistente",
                        base_slot=slot,
                        previous=previous,
                        current=area,
                    )
            if area and cluster:
                previous_cluster = area_cluster_map.setdefault(area, cluster)
                if previous_cluster != cluster:
                    instrumentation.record_error(
                        "structure",
                        "Área asignada a múltiples clústeres",
                        area=area,
                        previous=previous_cluster,
                        current=cluster,
                    )

        return {
            "base_slots": sorted(base_slots),
            "modalities": sorted(modalities),
            "slot_area_map": slot_area_map,
            "area_cluster_map": area_cluster_map,
        }

    def _ingest_document(self, pdf_path: str, config: dict[str, Any]) -> PreprocessedDocument:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[1]
        start = time.perf_counter()

        document_id = os.path.splitext(os.path.basename(pdf_path))[0] or "doc_1"
        override_payload = self._context.get("preprocessed_override")
        if override_payload is not None:
            try:
                preprocessed = PreprocessedDocument.ensure(
                    override_payload, document_id=document_id, use_spc_ingestion=True
                )
            except TypeError as exc:
                instrumentation.record_error(
                    "ingestion", "Documento preprocesado incompatible", reason=str(exc)
                )
                raise
        else:
            error_msg = (
                "No preprocessed document provided. Ingestion must be performed externally. "
                f"Use process_development_plan_async(pdf_path='{pdf_path}', preprocessed_document=<doc>) "
                "where <doc> is a PreprocessedDocument from SPC ingestion pipeline."
            )
            instrumentation.record_error(
                "ingestion", "Missing preprocessed document", reason=error_msg
            )
            raise ValueError(error_msg)

        # Validate that the document is not empty
        if not preprocessed.raw_text or not preprocessed.raw_text.strip():
            error_msg = "Empty document after ingestion - raw_text is empty or whitespace-only"
            instrumentation.record_error(
                "ingestion", "Empty document", reason=error_msg
            )
            raise ValueError(error_msg)
        
        # Log ingestion metrics and validate chunk count
        chunk_count = preprocessed.metadata.get("chunk_count", 0)
        if chunk_count == 0:
            error_msg = "No chunks extracted from document - chunk_count is 0"
            instrumentation.record_error(
                "ingestion", "No chunks", reason=error_msg
            )
            raise ValueError(error_msg)
        
        text_length = len(preprocessed.raw_text)
        sentence_count = len(preprocessed.sentences) if preprocessed.sentences else 0
        adapter_source = preprocessed.metadata.get("adapter_source", "unknown")
        
        # Store ingestion information for verification manifest
        ingestion_info = {
            "method": "SPC",  # Only SPC is supported
            "chunk_count": chunk_count,
            "text_length": text_length,
            "sentence_count": sentence_count,
            "adapter_source": adapter_source,
            "chunk_strategy": preprocessed.metadata.get("chunk_strategy", "semantic"),
        }
        if "chunk_overlap" in preprocessed.metadata:
            ingestion_info["chunk_overlap"] = preprocessed.metadata["chunk_overlap"]
        
        # Store in context for manifest generation
        if hasattr(self, "_context"):
            self._context["ingestion_info"] = ingestion_info
        
        logger.info(
            f"Document ingested successfully: document_id={document_id}, "
            f"method=SPC, text_length={text_length}, chunk_count={chunk_count}, "
            f"sentence_count={sentence_count}"
        )

        duration = time.perf_counter() - start
        instrumentation.increment(latency=duration)
        return preprocessed

    async def _execute_micro_questions_async(
            self,
            document: PreprocessedDocument,
            config: dict[str, Any],
    ) -> list[MicroQuestionRun]:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[2]
        micro_questions = config.get("micro_questions", [])
        instrumentation.items_total = len(micro_questions)
        ordered_questions: list[dict[str, Any]] = []
        
        # NEW: Initialize chunk router for chunk-aware execution
        chunk_routes: dict[int, Any] = {}
        if document.processing_mode == "chunked" and document.chunks:
            try:
                from saaaaaa.core.orchestrator.chunk_router import ChunkRouter
                router = ChunkRouter()
                
                # Route chunks to executors
                for chunk in document.chunks:
                    route = router.route_chunk(chunk)
                    if not route.skip_reason:
                        chunk_routes[chunk.id] = route
                
                logger.info(
                    f"Chunk-aware execution enabled: routed {len(chunk_routes)} chunks "
                    f"from {len(document.chunks)} total chunks"
                )
            except ImportError:
                logger.warning("ChunkRouter not available, falling back to flat mode")
                chunk_routes = {}

        questions_by_slot: dict[str, deque] = {}
        for question in micro_questions:
            slot = question.get("base_slot")
            questions_by_slot.setdefault(slot, deque()).append(question)

        slots = sorted(questions_by_slot.keys())
        while True:
            added = False
            for slot in slots:
                queue = questions_by_slot.get(slot)
                if queue:
                    ordered_questions.append(queue.popleft())
                    added = True
            if not added:
                break

        semaphore = asyncio.Semaphore(self.resource_limits.max_workers)
        self.resource_limits.attach_semaphore(semaphore)

        circuit_breakers: dict[str, dict[str, Any]] = {
            slot: {"failures": 0, "open": False}
            for slot in self.executors
        }

        results: list[MicroQuestionRun] = []
        
        # NEW: Track chunk execution metrics
        execution_metrics = {
            "chunk_executions": 0,  # Actual chunk-level executions
            "full_doc_executions": 0,  # Fallback full document executions
            "total_chunks_processed": 0,  # Total chunks that could have been processed
        }

        async def process_question(question: dict[str, Any]) -> MicroQuestionRun:
            await self.resource_limits.apply_worker_budget()
            async with semaphore:
                self._ensure_not_aborted()
                question_id = question.get("question_id", "")
                question_global = int(question.get("question_global", 0))
                base_slot = question.get("base_slot", "")
                metadata = {
                    key: question.get(key)
                    for key in (
                        "question_id",
                        "question_global",
                        "base_slot",
                        "dimension_id",
                        "policy_area_id",
                        "cluster_id",
                        "scoring_modality",
                        "expected_elements",
                    )
                }

                circuit = circuit_breakers.setdefault(base_slot, {"failures": 0, "open": False})
                if circuit.get("open"):
                    instrumentation.record_warning(
                        "circuit_breaker",
                        "Circuit breaker abierto, pregunta omitida",
                        base_slot=base_slot,
                        question_id=question_id,
                    )
                    instrumentation.increment()
                    return MicroQuestionRun(
                        question_id=question_id,
                        question_global=question_global,
                        base_slot=base_slot,
                        metadata=metadata,
                        evidence=None,
                        error="circuit_breaker_open",
                        aborted=False,
                    )

                usage = self.resource_limits.get_resource_usage()
                mem_exceeded, usage = self.resource_limits.check_memory_exceeded(usage)
                cpu_exceeded, usage = self.resource_limits.check_cpu_exceeded(usage)
                if mem_exceeded:
                    instrumentation.record_warning("resource", "Límite de memoria excedido", usage=usage)
                if cpu_exceeded:
                    instrumentation.record_warning("resource", "Límite de CPU excedido", usage=usage)

                executor_class = self.executors.get(base_slot)
                start_time = time.perf_counter()
                evidence: Evidence | None = None
                error_message: str | None = None

                if not executor_class:
                    error_message = f"Ejecutor no definido para {base_slot}"
                    instrumentation.record_error("executor", error_message, base_slot=base_slot)
                else:
                    try:
                        executor_instance = executor_class(self.executor)
                        
                        # NEW: Chunk-aware execution
                        if chunk_routes and document.processing_mode == "chunked":
                            # Find chunks relevant to this base_slot
                            relevant_chunk_ids = [
                                chunk_id for chunk_id, route in chunk_routes.items()
                                if base_slot in route.executor_class or route.executor_class == base_slot
                            ]
                            
                            if relevant_chunk_ids:
                                # Track metrics
                                execution_metrics["chunk_executions"] += len(relevant_chunk_ids)
                                execution_metrics["total_chunks_processed"] += len(relevant_chunk_ids)
                                
                                # Execute on relevant chunks only
                                chunk_evidences = []
                                for chunk_id in relevant_chunk_ids:
                                    try:
                                        # Call execute_chunk if available, otherwise fall back to execute
                                        if hasattr(executor_instance, 'execute_chunk'):
                                            chunk_evidence = await asyncio.to_thread(
                                                executor_instance.execute_chunk, document, chunk_id
                                            )
                                        else:
                                            # Fallback: execute on full document
                                            chunk_evidence = await asyncio.to_thread(
                                                executor_instance.execute, document, self.executor
                                            )
                                        if chunk_evidence:
                                            chunk_evidences.append(chunk_evidence)
                                    except Exception as chunk_exc:
                                        logger.warning(
                                            f"Chunk {chunk_id} execution failed for {base_slot}: {chunk_exc}"
                                        )
                                
                                # Aggregate chunk results
                                if chunk_evidences:
                                    # Use first evidence as base, merge others
                                    evidence = chunk_evidences[0]
                                    # Simple aggregation: combine matches/claims if available
                                    if len(chunk_evidences) > 1 and hasattr(evidence, 'matches'):
                                        all_matches = []
                                        for chunk_ev in chunk_evidences:
                                            if hasattr(chunk_ev, 'matches') and chunk_ev.matches:
                                                all_matches.extend(chunk_ev.matches)
                                        evidence.matches = all_matches
                                else:
                                    evidence = None
                            else:
                                # No relevant chunks for this slot, execute on full document
                                execution_metrics["full_doc_executions"] += 1
                                evidence = await asyncio.to_thread(
                                    executor_instance.execute, document, self.executor
                                )
                        else:
                            # Flat mode or no chunk routes - use original behavior
                            execution_metrics["full_doc_executions"] += 1
                            evidence = await asyncio.to_thread(
                                executor_instance.execute, document, self.executor
                            )
                        
                        circuit["failures"] = 0
                    except Exception as exc:  # pragma: no cover - dependencias externas
                        circuit["failures"] += 1
                        error_message = str(exc)
                        instrumentation.record_error(
                            "micro_question",
                            error_message,
                            base_slot=base_slot,
                            question_id=question_id,
                        )
                        if circuit["failures"] >= 3:
                            circuit["open"] = True
                            instrumentation.record_warning(
                                "circuit_breaker",
                                "Circuit breaker activado",
                                base_slot=base_slot,
                            )

                duration = time.perf_counter() - start_time
                instrumentation.increment(latency=duration)
                if instrumentation.items_processed % 10 == 0:
                    instrumentation.record_warning(
                        "progress",
                        "Progreso de micro preguntas",
                        processed=instrumentation.items_processed,
                        total=instrumentation.items_total,
                    )

                return MicroQuestionRun(
                    question_id=question_id,
                    question_global=question_global,
                    base_slot=base_slot,
                    metadata=metadata,
                    evidence=evidence,
                    error=error_message,
                    duration_ms=duration * 1000.0,
                    aborted=self.abort_signal.is_aborted(),
                )

        tasks = [asyncio.create_task(process_question(question)) for question in ordered_questions]

        try:
            for task in asyncio.as_completed(tasks):
                result = await task
                results.append(result)
                if self.abort_signal.is_aborted():
                    raise AbortRequested(self.abort_signal.get_reason() or "Abort requested")
        except AbortRequested:
            for task in tasks:
                task.cancel()
            raise
        
        # Log chunk execution metrics
        if chunk_routes and document.processing_mode == "chunked":
            total_possible = len(micro_questions) * len(document.chunks)
            actual_executed = execution_metrics["chunk_executions"] + execution_metrics["full_doc_executions"]
            savings_pct = ((total_possible - actual_executed) / max(total_possible, 1)) * 100 if total_possible > 0 else 0
            
            logger.info(
                f"Chunk execution metrics: {execution_metrics['chunk_executions']} chunk-scoped, "
                f"{execution_metrics['full_doc_executions']} full-doc, "
                f"{total_possible} total possible, "
                f"savings: {savings_pct:.1f}%"
            )
            
            # Store metrics for verification manifest
            if not hasattr(self, '_execution_metrics'):
                self._execution_metrics = {}
            self._execution_metrics['phase_2'] = {
                'chunk_executions': execution_metrics['chunk_executions'],
                'full_doc_executions': execution_metrics['full_doc_executions'],
                'total_possible_executions': total_possible,
                'actual_executions': actual_executed,
                'savings_percent': savings_pct,
            }

        return results

    async def _score_micro_results_async(
            self,
            micro_results: list[MicroQuestionRun],
            config: dict[str, Any],
    ) -> list[ScoredMicroQuestion]:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[3]
        instrumentation.items_total = len(micro_results)

        # Import from the flat scoring.py module file
        import importlib.util
        from pathlib import Path
        scoring_file_path = Path(__file__).parent.parent.parent / "analysis" / "scoring.py"
        spec = importlib.util.spec_from_file_location("scoring_flat", scoring_file_path)
        scoring_flat = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scoring_flat)
        ScoringEvidence = scoring_flat.Evidence
        MicroQuestionScorer = scoring_flat.MicroQuestionScorer
        ScoringModality = scoring_flat.ScoringModality

        scorer = MicroQuestionScorer()
        results: list[ScoredMicroQuestion] = []
        semaphore = asyncio.Semaphore(self.resource_limits.max_workers)
        self.resource_limits.attach_semaphore(semaphore)

        async def score_item(item: MicroQuestionRun) -> ScoredMicroQuestion:
            async with semaphore:
                await self.resource_limits.apply_worker_budget()
                self._ensure_not_aborted()
                start = time.perf_counter()

                modality_value = item.metadata.get("scoring_modality", "TYPE_A")
                try:
                    modality = ScoringModality(modality_value)
                except Exception:
                    modality = ScoringModality.TYPE_A

                if item.error or not item.evidence:
                    instrumentation.record_warning(
                        "scoring",
                        "Evidencia ausente para scoring",
                        question_id=item.question_id,
                        error=item.error,
                    )
                    instrumentation.increment(latency=time.perf_counter() - start)
                    return ScoredMicroQuestion(
                        question_id=item.question_id,
                        question_global=item.question_global,
                        base_slot=item.base_slot,
                        score=None,
                        normalized_score=None,
                        quality_level=None,
                        evidence=item.evidence,
                        metadata=item.metadata,
                        error=item.error or "missing_evidence",
                    )

                # Handle evidence as either dict or dataclass
                if isinstance(item.evidence, dict):
                    elements_found = item.evidence.get("elements", [])
                    raw_results = item.evidence.get("raw_results", {})
                else:
                    elements_found = getattr(item.evidence, "elements", [])
                    raw_results = getattr(item.evidence, "raw_results", {})
                
                scoring_evidence = ScoringEvidence(
                    elements_found=elements_found,
                    confidence_scores=raw_results.get("confidence_scores", []),
                    semantic_similarity=raw_results.get("semantic_similarity"),
                    pattern_matches=raw_results.get("pattern_matches", {}),
                    metadata=raw_results,
                )

                try:
                    scored = await asyncio.to_thread(
                        scorer.apply_scoring_modality,
                        item.question_id,
                        item.question_global,
                        modality,
                        scoring_evidence,
                    )
                    duration = time.perf_counter() - start
                    instrumentation.increment(latency=duration)
                    return ScoredMicroQuestion(
                        question_id=scored.question_id,
                        question_global=scored.question_global,
                        base_slot=item.base_slot,
                        score=scored.raw_score,
                        normalized_score=scored.normalized_score,
                        quality_level=scored.quality_level.value,
                        evidence=item.evidence,
                        scoring_details=scored.scoring_details,
                        metadata=item.metadata,
                    )
                except Exception as exc:  # pragma: no cover - dependencia externa
                    instrumentation.record_error(
                        "scoring",
                        str(exc),
                        question_id=item.question_id,
                    )
                    duration = time.perf_counter() - start
                    instrumentation.increment(latency=duration)
                    return ScoredMicroQuestion(
                        question_id=item.question_id,
                        question_global=item.question_global,
                        base_slot=item.base_slot,
                        score=None,
                        normalized_score=None,
                        quality_level=None,
                        evidence=item.evidence,
                        metadata=item.metadata,
                        error=str(exc),
                    )

        tasks = [asyncio.create_task(score_item(item)) for item in micro_results]
        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)
            if self.abort_signal.is_aborted():
                raise AbortRequested(self.abort_signal.get_reason() or "Abort requested")

        return results

    async def _aggregate_dimensions_async(
            self,
            scored_results: list[ScoredMicroQuestion],
            config: dict[str, Any],
    ) -> list[DimensionScore]:
        """Aggregate micro question scores into dimension scores using DimensionAggregator.

        Args:
            scored_results: List of scored micro questions
            config: Configuration dict containing monolith

        Returns:
            List of DimensionScore objects with full validation and diagnostics
        """
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[4]

        # Get monolith from config
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith in config for dimension aggregation")
            return []

        # Initialize dimension aggregator
        aggregator = DimensionAggregator(monolith, abort_on_insufficient=False)

        # Convert ScoredMicroQuestion to ScoredResult
        converted_results: list[ScoredResult] = []
        for item in scored_results:
            if item.score is None or item.metadata is None:
                continue
            converted_results.append(
                ScoredResult(
                    question_global=item.question_global,
                    base_slot=item.base_slot,
                    policy_area=item.metadata.get("policy_area_id", ""),
                    dimension=item.metadata.get("dimension_id", ""),
                    score=item.score,
                    quality_level=item.quality_level or "INSUFICIENTE",
                    evidence=asdict(item.evidence) if item.evidence and is_dataclass(item.evidence) else (item.evidence if isinstance(item.evidence, dict) else {}),
                    raw_results=item.scoring_details,
                )
            )

        # Group by dimension and area
        dimension_map: dict[tuple[str, str], list[ScoredResult]] = {}
        for result in converted_results:
            key = (result.dimension, result.policy_area)
            dimension_map.setdefault(key, []).append(result)

        instrumentation.items_total = len(dimension_map)
        dimension_scores: list[DimensionScore] = []

        # Aggregate each dimension
        for (dimension_id, area_id), items in dimension_map.items():
            self._ensure_not_aborted()
            await asyncio.sleep(0)
            start = time.perf_counter()

            try:
                dim_score = aggregator.aggregate_dimension(
                    dimension_id=dimension_id,
                    area_id=area_id,
                    scored_results=items,
                    weights=None  # Use equal weights by default
                )
                dimension_scores.append(dim_score)
            except Exception as e:
                logger.error(f"Failed to aggregate dimension {dimension_id}/{area_id}: {e}")

            instrumentation.increment(latency=time.perf_counter() - start)

        return dimension_scores

    async def _aggregate_policy_areas_async(
            self,
            dimension_scores: list[DimensionScore],
            config: dict[str, Any],
    ) -> list[AreaScore]:
        """Aggregate dimension scores into policy area scores using AreaPolicyAggregator.

        Args:
            dimension_scores: List of DimensionScore objects
            config: Configuration dict containing monolith

        Returns:
            List of AreaScore objects with full validation and diagnostics
        """
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[5]

        # Get monolith from config
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith in config for area aggregation")
            return []

        # Initialize area aggregator
        aggregator = AreaPolicyAggregator(monolith, abort_on_insufficient=False)

        # Group dimension scores by area
        areas: dict[str, list[DimensionScore]] = {}
        for score in dimension_scores:
            area_id = score.area_id
            if area_id:
                areas.setdefault(area_id, []).append(score)

        instrumentation.items_total = len(areas)
        area_scores: list[AreaScore] = []

        # Aggregate each area
        for area_id, scores in areas.items():
            self._ensure_not_aborted()
            await asyncio.sleep(0)
            start = time.perf_counter()

            try:
                area_score = aggregator.aggregate_area(
                    area_id=area_id,
                    dimension_scores=scores
                )
                area_scores.append(area_score)
            except Exception as e:
                logger.error(f"Failed to aggregate area {area_id}: {e}")

            instrumentation.increment(latency=time.perf_counter() - start)

        return area_scores

    def _aggregate_clusters(
            self,
            policy_area_scores: list[AreaScore],
            config: dict[str, Any],
    ) -> list[ClusterScore]:
        """Aggregate policy area scores into cluster scores using ClusterAggregator.

        Args:
            policy_area_scores: List of AreaScore objects
            config: Configuration dict containing monolith

        Returns:
            List of ClusterScore objects with full validation and diagnostics
        """
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[6]

        # Get monolith from config
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith in config for cluster aggregation")
            return []

        # Initialize cluster aggregator
        aggregator = ClusterAggregator(monolith, abort_on_insufficient=False)

        # Get cluster definitions from monolith
        clusters = monolith["blocks"]["niveles_abstraccion"]["clusters"]

        instrumentation.items_total = len(clusters)
        cluster_scores: list[ClusterScore] = []

        # Aggregate each cluster
        for cluster_def in clusters:
            self._ensure_not_aborted()
            start = time.perf_counter()
            cluster_id = cluster_def["cluster_id"]

            try:
                cluster_score = aggregator.aggregate_cluster(
                    cluster_id=cluster_id,
                    area_scores=policy_area_scores,
                    weights=None  # Use equal weights by default
                )
                cluster_scores.append(cluster_score)
            except Exception as e:
                logger.error(f"Failed to aggregate cluster {cluster_id}: {e}")

            instrumentation.increment(latency=time.perf_counter() - start)

        return cluster_scores

    def _evaluate_macro(self, cluster_scores: list[ClusterScore], config: dict[str, Any]) -> MacroScoreDict:
        """Evaluate macro level using MacroAggregator.

        Args:
            cluster_scores: List of ClusterScore objects from FASE 6
            config: Configuration dict containing monolith

        Returns:
            MacroScoreDict with macro_score, macro_score_normalized, and cluster_scores
        """
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[7]
        start = time.perf_counter()

        # Get monolith from config
        monolith = config.get("monolith")
        if not monolith:
            logger.error("No monolith in config for macro evaluation")
            macro_score = MacroScore(
                score=0.0,
                quality_level="INSUFICIENTE",
                cross_cutting_coherence=0.0,
                systemic_gaps=[],
                strategic_alignment=0.0,
                cluster_scores=[],
                validation_passed=False,
                validation_details={"error": "No monolith", "type": "config"}
            )
            result: MacroScoreDict = {
                "macro_score": macro_score,
                "macro_score_normalized": 0.0,
                "cluster_scores": cluster_scores,
            }
            return result

        # Initialize macro aggregator
        aggregator = MacroAggregator(monolith, abort_on_insufficient=False)

        # Extract area_scores and dimension_scores from cluster_scores
        area_scores: list[AreaScore] = []
        dimension_scores: list[DimensionScore] = []

        for cluster in cluster_scores:
            area_scores.extend(cluster.area_scores)
            for area in cluster.area_scores:
                dimension_scores.extend(area.dimension_scores)

        # Remove duplicates (in case areas appear in multiple clusters)
        seen_areas = set()
        unique_areas = []
        for area in area_scores:
            if area.area_id not in seen_areas:
                seen_areas.add(area.area_id)
                unique_areas.append(area)

        seen_dims = set()
        unique_dims = []
        for dim in dimension_scores:
            key = (dim.dimension_id, dim.area_id)
            if key not in seen_dims:
                seen_dims.add(key)
                unique_dims.append(dim)

        # Evaluate macro
        try:
            macro_score = aggregator.evaluate_macro(
                cluster_scores=cluster_scores,
                area_scores=unique_areas,
                dimension_scores=unique_dims
            )
        except Exception as e:
            logger.error(f"Failed to evaluate macro: {e}")
            macro_score = MacroScore(
                score=0.0,
                quality_level="INSUFICIENTE",
                cross_cutting_coherence=0.0,
                systemic_gaps=[],
                strategic_alignment=0.0,
                cluster_scores=cluster_scores,
                validation_passed=False,
                validation_details={"error": str(e), "type": "exception"}
            )

        instrumentation.increment(latency=time.perf_counter() - start)
        # macro_score is already normalized to 0-1 range from averaging cluster scores
        # Extract the score field from the MacroScore object with explicit float conversion
        macro_score_normalized = float(macro_score.score) if isinstance(macro_score, MacroScore) else float(macro_score)

        result: MacroScoreDict = {
            "macro_score": macro_score,
            "macro_score_normalized": macro_score_normalized,
            "cluster_scores": cluster_scores,
        }
        return result

    async def _generate_recommendations(
            self,
            macro_result: dict[str, Any],
            config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate recommendations at MICRO, MESO, and MACRO levels using RecommendationEngine.

        This phase connects to the orchestrator's 3-level flux:
        - MICRO: Uses scored question results from phase 3
        - MESO: Uses cluster aggregations from phase 6
        - MACRO: Uses macro evaluation from phase 7

        Args:
            macro_result: Macro evaluation results from phase 7
            config: Configuration dictionary

        Returns:
            Dictionary with MICRO, MESO, and MACRO recommendations
        """
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[8]
        start = time.perf_counter()

        await asyncio.sleep(0)

        # If RecommendationEngine is not available, return empty recommendations
        if self.recommendation_engine is None:
            logger.warning("RecommendationEngine not available, returning empty recommendations")
            recommendations = {
                "MICRO": {"level": "MICRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MESO": {"level": "MESO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MACRO": {"level": "MACRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "macro_score": macro_result.get("macro_score"),
            }
            instrumentation.increment(latency=time.perf_counter() - start)
            return recommendations

        try:
            # ========================================================================
            # MICRO LEVEL: Transform scored results to PA-DIM scores
            # ========================================================================
            micro_scores: dict[str, float] = {}
            scored_results = self._context.get('scored_results', [])

            # Group by policy area and dimension to calculate average scores
            pa_dim_groups: dict[str, list[float]] = {}
            for result in scored_results:
                if hasattr(result, 'metadata') and result.metadata:
                    pa_id = result.metadata.get('policy_area_id')
                    dim_id = result.metadata.get('dimension_id')
                    score = result.normalized_score

                    if pa_id and dim_id and score is not None:
                        key = f"{pa_id}-{dim_id}"
                        if key not in pa_dim_groups:
                            pa_dim_groups[key] = []
                        pa_dim_groups[key].append(score)

            # Calculate average for each PA-DIM combination
            for key, scores in pa_dim_groups.items():
                if scores:
                    micro_scores[key] = sum(scores) / len(scores)

            logger.info(f"Extracted {len(micro_scores)} MICRO PA-DIM scores for recommendations")

            # ========================================================================
            # MESO LEVEL: Transform cluster scores
            # ========================================================================
            cluster_data: dict[str, Any] = {}
            cluster_scores = self._context.get('cluster_scores', [])

            for cluster in cluster_scores:
                cluster_id = cluster.get('cluster_id')
                cluster_score = cluster.get('score')
                areas = cluster.get('areas', [])

                if cluster_id and cluster_score is not None:
                    # cluster_score is already normalized to 0-1 range from aggregation
                    normalized_cluster_score = cluster_score

                    # Calculate variance across areas in this cluster using normalized scores
                    # area scores are already normalized to 0-1 range from aggregation
                    valid_area_scores = [
                        (area, area.get('score'))
                        for area in areas
                        if area.get('score') is not None
                    ]
                    normalized_area_values = [score for _, score in valid_area_scores]
                    variance = (
                        statistics.variance(normalized_area_values)
                        if len(normalized_area_values) > 1
                        else 0.0
                    )

                    # Find weakest policy area in cluster
                    weakest_area = (
                        min(valid_area_scores, key=lambda item: item[1])
                        if valid_area_scores
                        else None
                    )
                    weak_pa = weakest_area[0].get('area_id') if weakest_area else None

                    cluster_data[cluster_id] = {
                        'score': normalized_cluster_score * self.PERCENTAGE_SCALE,  # 0-100 scale
                        'variance': variance,
                        'weak_pa': weak_pa
                    }

            logger.info(f"Extracted {len(cluster_data)} MESO cluster metrics for recommendations")

            # ========================================================================
            # MACRO LEVEL: Transform macro evaluation
            # ========================================================================
            macro_score = macro_result.get('macro_score')
            macro_score_normalized = macro_result.get('macro_score_normalized')

            # macro_score is already normalized to 0-1 range
            # Extract the score value if macro_score is a MacroScore object
            if macro_score is not None and macro_score_normalized is None:
                macro_score_normalized = macro_score.score if isinstance(macro_score, MacroScore) else macro_score

            # Extract numeric value from macro_score_normalized (may be dict/object)
            macro_score_numeric = None
            if macro_score_normalized is not None:
                if isinstance(macro_score_normalized, dict):
                    macro_score_numeric = macro_score_normalized.get('score')
                elif hasattr(macro_score_normalized, 'score'):
                    try:
                        macro_score_numeric = macro_score_normalized.score
                    except (AttributeError, TypeError) as e:
                        logger.warning(f"Failed to extract score attribute: {e}")
                        macro_score_numeric = None
                else:
                    # Already a numeric value
                    macro_score_numeric = macro_score_normalized
                
                # Validate that extracted value is numeric
                if macro_score_numeric is not None and not isinstance(macro_score_numeric, (int, float)):
                    logger.warning(
                        f"Expected numeric macro_score, got {type(macro_score_numeric).__name__}: {macro_score_numeric!r}"
                    )
                    macro_score_numeric = None

            # Determine macro band based on score
            macro_band = 'INSUFICIENTE'
            if macro_score_numeric is not None:
                scaled_score = float(macro_score_numeric) * self.PERCENTAGE_SCALE
                if scaled_score >= 75:
                    macro_band = 'SATISFACTORIO'
                elif scaled_score >= 55:
                    macro_band = 'ACEPTABLE'
                elif scaled_score >= 35:
                    macro_band = 'DEFICIENTE'

            # Find clusters below target (< 55%)
            # cluster scores are already normalized to 0-1 range
            clusters_below_target = []
            for cluster in cluster_scores:
                cluster_id = cluster.get('cluster_id')
                cluster_score = cluster.get('score', 0)
                if cluster_score is not None and cluster_score * self.PERCENTAGE_SCALE < 55:
                    clusters_below_target.append(cluster_id)

            # Calculate overall variance
            # cluster scores are already normalized to 0-1 range
            normalized_cluster_scores = [
                c.get('score')
                for c in cluster_scores
                if c.get('score') is not None
            ]
            overall_variance = (
                statistics.variance(normalized_cluster_scores)
                if len(normalized_cluster_scores) > 1
                else 0.0
            )

            variance_alert = 'BAJA'
            if overall_variance >= 0.18:
                variance_alert = 'ALTA'
            elif overall_variance >= 0.08:
                variance_alert = 'MODERADA'

            # Find priority micro gaps (lowest scoring PA-DIM combinations)
            sorted_micro = sorted(micro_scores.items(), key=lambda x: x[1])
            priority_micro_gaps = [k for k, v in sorted_micro[:5] if v < 0.55]

            macro_data = {
                'macro_band': macro_band,
                'clusters_below_target': clusters_below_target,
                'variance_alert': variance_alert,
                'priority_micro_gaps': priority_micro_gaps,
                'macro_score_percentage': (
                    float(macro_score_numeric) * self.PERCENTAGE_SCALE if macro_score_numeric is not None else None
                )
            }

            logger.info(f"Macro band: {macro_band}, Clusters below target: {len(clusters_below_target)}")

            # ========================================================================
            # GENERATE RECOMMENDATIONS AT ALL 3 LEVELS
            # ========================================================================
            context = {
                'generated_at': datetime.utcnow().isoformat(),
                'macro_score': macro_score
            }

            recommendation_sets = self.recommendation_engine.generate_all_recommendations(
                micro_scores=micro_scores,
                cluster_data=cluster_data,
                macro_data=macro_data,
                context=context
            )

            # Convert RecommendationSet objects to dictionaries
            recommendations = {
                level: rec_set.to_dict() for level, rec_set in recommendation_sets.items()
            }
            recommendations['macro_score'] = macro_score
            recommendations['macro_score_normalized'] = macro_score_normalized

            logger.info(
                f"Generated recommendations: "
                f"MICRO={len(recommendation_sets['MICRO'].recommendations)}, "
                f"MESO={len(recommendation_sets['MESO'].recommendations)}, "
                f"MACRO={len(recommendation_sets['MACRO'].recommendations)}"
            )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}", exc_info=True)
            recommendations = {
                "MICRO": {"level": "MICRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MESO": {"level": "MESO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "MACRO": {"level": "MACRO", "recommendations": [], "generated_at": datetime.utcnow().isoformat()},
                "macro_score": macro_result.get("macro_score"),
                "error": str(e)
            }

        instrumentation.increment(latency=time.perf_counter() - start)
        return recommendations

    def _assemble_report(self, recommendations: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[9]
        start = time.perf_counter()

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations": recommendations,
            "metadata": {
                "monolith_sha256": config.get("monolith_sha256"),
                "method_summary": config.get("method_summary"),
            },
        }

        instrumentation.increment(latency=time.perf_counter() - start)
        return report

    async def _format_and_export(self, report: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
        self._ensure_not_aborted()
        instrumentation = self._phase_instrumentation[10]
        start = time.perf_counter()

        await asyncio.sleep(0)
        export_payload = {
            "report": report,
            "phase_metrics": self.get_phase_metrics(),
            "completed_at": datetime.utcnow().isoformat(),
        }

        instrumentation.increment(latency=time.perf_counter() - start)
        return export_payload


def describe_pipeline_shape(
    monolith: dict[str, Any] | None = None,
    executor_instances: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe the actual pipeline shape from live data.
    
    Computes phase count, question count, and executor count from real data
    instead of using hard-coded constants.
    
    Args:
        monolith: Questionnaire monolith (if available)
        executor_instances: MethodExecutor.instances dict (if available)
        
    Returns:
        Dict with actual pipeline metrics
    """
    shape: dict[str, Any] = {
        "phases": len(Orchestrator.FASES),
    }
    
    if monolith:
        micro_questions = monolith.get("blocks", {}).get("micro_questions", [])
        meso_questions = monolith.get("blocks", {}).get("meso_questions", [])
        macro_question = monolith.get("blocks", {}).get("macro_question", {})
        question_total = len(micro_questions) + len(meso_questions) + (1 if macro_question else 0)
        shape["expected_micro_questions"] = question_total
    
    if executor_instances:
        shape["registered_executors"] = len(executor_instances)
    
    return shape

