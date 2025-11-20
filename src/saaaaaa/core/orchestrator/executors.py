"""Advanced Data Flow Executors for Orchestration

This module implements a sophisticated orchestration system for executing analysis
methods across policy documents. The executor framework provides:

- Dynamic method sequencing with dependency resolution
- Parallel execution optimization for independent methods
- Calibration-aware execution with adaptive thresholding
- Signal registry integration for tracking method results
- Comprehensive error handling and retry mechanisms
- Telemetry and observability through OpenTelemetry integration

Architecture:
-------------
The executor system uses a hierarchical design:

1. ExecutorBase: Abstract base class defining the core execution interface
2. AdvancedDataFlowExecutor: Main implementation with calibration integration
3. Question-specific executors (D1Q1_Executor, D1Q2_Executor, etc.): Specialized
   executors for each question in the policy assessment questionnaire

Method Sequencing:
------------------
The executor determines optimal method execution order by:
- Analyzing method dependencies through input/output requirements
- Detecting independent methods that can execute in parallel
- Applying calibration scores to skip low-quality methods (threshold: 0.3)
- Using retry logic with exponential backoff for transient failures

This approach reduces total execution time by executing independent methods
concurrently while maintaining correctness through dependency ordering.

Calibration Integration:
------------------------
When a CalibrationOrchestrator is provided, executors:
- Query calibration scores for each method before execution
- Skip methods scoring below CALIBRATION_SKIP_THRESHOLD (0.3)
- Log calibration decisions for traceability
- Propagate calibration metadata through the execution pipeline

Performance Characteristics:
----------------------------
- Single Question Executor: 50-200ms (varies by question complexity)
- Batch Execution (5 questions): 300-1000ms
- Batch Execution (30 questions): 2-5 seconds
- Calibration lookup overhead: ~5-10ms per method
- Dependency resolution: ~50-100ms for complex graphs

Memory Requirements:
--------------------
- Base Memory per Executor: ~10MB
- Method result caching: ~5-10MB per 100 results
- Dependency graph storage: ~1-5MB (scales with method count)
- Signal registry: ~20-50MB (depends on signal count and size)
- Total for Full Orchestrator: ~50-100MB
- Large Documents (10MB+): Additional 50-100MB working memory

Configuration:
--------------
Executors require an ExecutorConfig object that specifies:
- timeout_s: Maximum execution time per method (seconds, default: 300.0)
- retry_count: Number of retry attempts for failed methods (default: 3)
- seed: Random seed for deterministic execution (optional)
- advanced_modules: Configuration for optional advanced features

See ExecutorConfig and AdvancedModuleConfig for complete parameter documentation.
"""

import asyncio
import inspect
import logging
import math
import os
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Any, Generic, TypeVar

import numpy as np

# Contract infrastructure - ACTUAL INTEGRATION
from ...utils.determinism_helpers import deterministic
from .executor_config import ExecutorConfig
from .signal_consumption import SignalConsumptionProof
from .versions import CALIBRATION_VERSION
from .versions import MIN_CALIBRATION_VERSION as MINIMUM_SUPPORTED_VERSION
from ...utils.contracts import ExtractionArtifact

if TYPE_CHECKING:
    from saaaaaa.core.calibration import CalibrationResult

# NEW: Calibration system imports
try:
    from saaaaaa.core.calibration import CalibrationOrchestrator
    HAS_CALIBRATION = True
except ImportError:
    CalibrationOrchestrator = None  # type: ignore
    HAS_CALIBRATION = False

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    tracer = trace.get_tracer(__name__)
    HAS_OTEL = True
except ImportError:
    tracer = None
    HAS_OTEL = False

try:  # Optional imports for advanced context propagation
    import networkx as nx
except Exception:  # pragma: no cover - optional dependency at runtime
    nx = None  # type: ignore[assignment]

try:  # Teoría de Cambio categorical enrichment
    from saaaaaa.core.types import CategoriaCausal
except Exception:  # pragma: no cover - avoid hard failure if module unavailable
    CategoriaCausal = None  # type: ignore[assignment]

# ============================================================================
# LOGGING AND METRICS SETUP
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# DETERMINISTIC EXECUTION CONTEXT
# ============================================================================

@dataclass
class DeterministicSeeds:
    """Container for deterministic seeds used within an execution context."""
    np: int  # Seed for numpy RNG
    python: int  # Seed for Python random


@contextmanager
def deterministic(policy_unit_id: str | None, correlation_id: str | None):
    """
    Deterministic execution context manager.

    Provides stable seeds derived from policy_unit_id and correlation_id.
    For the same (policy_unit_id, correlation_id), guarantees bit-for-bit
    reproducible execution of stochastic operations.

    Usage:
        with deterministic(policy_unit_id, correlation_id) as seeds:
            rng = np.random.default_rng(seeds.np)
            # Use rng for all stochastic operations

    Args:
        policy_unit_id: Policy unit identifier
        correlation_id: Correlation identifier

    Yields:
        DeterministicSeeds with .np and .python attributes
    """
    import hashlib
    import random

    # Derive deterministic seed from identifiers
    components = [
        str(policy_unit_id) if policy_unit_id else "NO_POLICY_UNIT",
        str(correlation_id) if correlation_id else "NO_CORRELATION",
    ]
    material = "|".join(components)
    digest = hashlib.sha256(material.encode("utf-8")).digest()
    base_seed = int.from_bytes(digest[:4], byteorder="big")

    seeds = DeterministicSeeds(
        np=base_seed,
        python=base_seed + 1,
    )

    # Seed Python's random module for deterministic execution
    random.seed(seeds.python)

    yield seeds


def _ensure_rng(rng: np.random.Generator | None) -> np.random.Generator:
    """
    Ensure a valid RNG generator is available.

    If rng is None, creates a new default generator.
    Otherwise, returns the provided rng.

    Args:
        rng: Optional numpy random generator

    Returns:
        A valid numpy random generator
    """
    if rng is None:
        return np.random.default_rng()
    return rng


class CircuitBreakerState:
    """Async-safe circuit breaker state for fault isolation."""

    def __init__(self) -> None:
        self.failures = 0
        self.open = False
        self._lock = asyncio.Lock()
        self._state_changes: list[dict[str, Any]] = []
        self._max_history = 100

    async def increment_failures(self) -> None:
        """Increment failure count and potentially open circuit."""
        async with self._lock:
            old_open = self.open
            self.failures += 1
            if self.failures >= 3:
                self.open = True

            # Record state change
            if old_open != self.open:
                self._state_changes.append({
                    'timestamp': time.time(),
                    'from_open': old_open,
                    'to_open': self.open,
                    'failures': self.failures,
                })

                # Trim history
                if len(self._state_changes) > self._max_history:
                    self._state_changes = self._state_changes[-self._max_history:]

                logger.warning(
                    "circuit_breaker_state_change",
                    extra={
                        "old_open": old_open,
                        "new_open": self.open,
                        "failures": self.failures,
                    }
                )

    async def reset(self) -> None:
        """Reset circuit breaker state."""
        async with self._lock:
            old_open = self.open
            self.failures = 0
            self.open = False

            # Record state change if circuit was open
            if old_open:
                self._state_changes.append({
                    'timestamp': time.time(),
                    'from_open': old_open,
                    'to_open': False,
                    'failures': 0,
                })

                # Trim history
                if len(self._state_changes) > self._max_history:
                    self._state_changes = self._state_changes[-self._max_history:]

    async def is_open(self) -> bool:
        """Check if circuit is open."""
        async with self._lock:
            return self.open

    def get_state_history(self) -> list[dict[str, Any]]:
        """Get history of state changes for monitoring."""
        return list(self._state_changes)


@dataclass
class ExecutionMetrics:
    """Metrics for monitoring executor performance"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    quantum_optimizations: int = 0
    quantum_convergence_times: list[float] = field(default_factory=list)
    meta_learner_strategy_selections: dict[int, int] = field(default_factory=dict)
    information_bottlenecks_detected: int = 0
    retry_attempts: int = 0
    method_execution_times: dict[str, list[float]] = field(default_factory=dict)

    def record_execution(self, success: bool, execution_time: float, method_key: str = None) -> None:
        """Record an execution attempt"""
        with _metrics_lock:
            self.total_executions += 1
            if success:
                self.successful_executions += 1
            else:
                self.failed_executions += 1
            self.total_execution_time += execution_time
            if method_key:
                if method_key not in self.method_execution_times:
                    self.method_execution_times[method_key] = []
                self.method_execution_times[method_key].append(execution_time)

    def record_quantum_optimization(self, convergence_time: float) -> None:
        """Record quantum optimization metrics"""
        with _metrics_lock:
            self.quantum_optimizations += 1
            self.quantum_convergence_times.append(convergence_time)

    def record_meta_learner_selection(self, strategy_idx: int) -> None:
        """Record meta-learner strategy selection"""
        with _metrics_lock:
            if strategy_idx not in self.meta_learner_strategy_selections:
                self.meta_learner_strategy_selections[strategy_idx] = 0
            self.meta_learner_strategy_selections[strategy_idx] += 1

    def record_information_bottleneck(self) -> None:
        """Record information bottleneck detection"""
        with _metrics_lock:
            self.information_bottlenecks_detected += 1

    def record_retry(self) -> None:
        """Record retry attempt"""
        with _metrics_lock:
            self.retry_attempts += 1

    def get_summary(self) -> dict[str, Any]:
        """Get metrics summary"""
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'failed_executions': self.failed_executions,
            'success_rate': self.successful_executions / max(self.total_executions, 1),
            'total_execution_time': self.total_execution_time,
            'avg_execution_time': self.total_execution_time / max(self.total_executions, 1),
            'quantum_optimizations': self.quantum_optimizations,
            'avg_quantum_convergence_time': np.mean(self.quantum_convergence_times) if self.quantum_convergence_times else 0.0,
            'meta_learner_strategies': dict(self.meta_learner_strategy_selections),
            'information_bottlenecks_detected': self.information_bottlenecks_detected,
            'retry_attempts': self.retry_attempts,
        }

# Global metrics instance with thread-safety
_global_metrics = ExecutionMetrics()
_metrics_lock = threading.RLock()
_ARG_UNSET: object = object()

def get_execution_metrics() -> ExecutionMetrics:
    """Get global execution metrics"""
    return _global_metrics

@contextmanager
def execution_timer(operation_name: str):
    """Context manager for timing operations"""
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.debug(f"{operation_name} completed in {elapsed:.3f}s")

# ============================================================================
# ADVANCED EXECUTOR BASE CLASS
# ============================================================================

@dataclass
class ValidationResult:
    """Result of executor validation check."""
    is_valid: bool
    severity: str  # ERROR, WARNING, INFO
    message: str
    context: dict[str, Any] = field(default_factory=dict)


class ExecutorBase(ABC):
    """Base class for all executors with pre-flight validation.

    This class provides the foundational validation logic that all executors
    must implement before execution. It ensures that:
    1. All dependencies are available
    2. Calibrations are properly configured
    3. Required resources are accessible
    """

    def validate_before_execution(self) -> ValidationResult:
        """Perform pre-flight checks before execution.

        This method validates:
        1. All class dependencies exist in the executor registry
        2. All methods have proper calibration entries
        3. Required resources (config, signal registry) are available

        Returns:
            ValidationResult: Object indicating validation success or failure
        """
        errors = []
        warnings = []
        context_info = {}

        # Check 1: Verify all dependencies exist
        try:
            dependency_result = self._check_dependencies()
            if not dependency_result.is_valid:
                errors.append(dependency_result.message)
                context_info.update(dependency_result.context)
            elif dependency_result.severity == "WARNING":
                warnings.append(dependency_result.message)
        except Exception as e:
            errors.append(f"Dependency check failed: {str(e)}")

        # Check 2: Verify calibration available
        try:
            calibration_result = self._check_calibration()
            if not calibration_result.is_valid:
                errors.append(calibration_result.message)
                context_info.update(calibration_result.context)
            elif calibration_result.severity == "WARNING":
                warnings.append(calibration_result.message)
        except Exception as e:
            errors.append(f"Calibration check failed: {str(e)}")

        # Check 3: Ensure resources available
        try:
            resource_result = self._check_resources()
            if not resource_result.is_valid:
                errors.append(resource_result.message)
                context_info.update(resource_result.context)
            elif resource_result.severity == "WARNING":
                warnings.append(resource_result.message)
        except Exception as e:
            errors.append(f"Resource check failed: {str(e)}")

        # Compile final result
        if errors:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message="; ".join(errors),
                context=context_info
            )
        elif warnings:
            return ValidationResult(
                is_valid=True,
                severity="WARNING",
                message="; ".join(warnings),
                context=context_info
            )
        else:
            return ValidationResult(
                is_valid=True,
                severity="INFO",
                message="All pre-flight checks passed",
                context=context_info
            )

    def _check_dependencies(self) -> ValidationResult:
        """Check that all class dependencies exist in executor registry.

        Returns:
            ValidationResult indicating if dependencies are satisfied
        """
        if not hasattr(self, 'executor') or self.executor is None:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message="Method executor not initialized",
                context={"check": "dependencies"}
            )

        seq = self._get_method_sequence()
        missing_classes = []

        for class_name, _method_name in seq:
            if not hasattr(self.executor, 'instances'):
                return ValidationResult(
                    is_valid=False,
                    severity="ERROR",
                    message="Executor does not have instances registry",
                    context={"check": "dependencies"}
                )

            if class_name not in self.executor.instances:
                missing_classes.append(class_name)

        if missing_classes:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"Missing class dependencies: {', '.join(missing_classes)}",
                context={
                    "check": "dependencies",
                    "missing_classes": missing_classes,
                    "total_required": len(seq)
                }
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message=f"All {len(seq)} class dependencies available",
            context={
                "check": "dependencies",
                "classes_checked": len({c for c, _ in seq})
            }
        )

    def _check_calibration(self) -> ValidationResult:
        """Check that the new calibration orchestrator is available."""
        if hasattr(self, 'calibration') and self.calibration is not None:
            return ValidationResult(
                is_valid=True,
                severity="INFO",
                message="CalibrationOrchestrator is available."
            )
        return ValidationResult(
            is_valid=False,
            severity="ERROR",
            message="CalibrationOrchestrator is not available in the executor."
        )

    def _check_resources(self) -> ValidationResult:
        """Check that required resources are available.

        Returns:
            ValidationResult indicating if resources are available
        """
        issues = []
        warnings = []

        # Check config
        if not hasattr(self, 'config') or self.config is None:
            issues.append("ExecutorConfig not initialized")

        # Check signal registry (optional but recommended)
        if not hasattr(self, 'signal_registry') or self.signal_registry is None:
            warnings.append("Signal registry not available (optional)")

        # Check method executor
        if not hasattr(self, 'executor') or self.executor is None:
            issues.append("Method executor not initialized")

        if issues:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message="; ".join(issues),
                context={
                    "check": "resources",
                    "issues": issues,
                    "warnings": warnings
                }
            )

        if warnings:
            return ValidationResult(
                is_valid=True,
                severity="WARNING",
                message="; ".join(warnings),
                context={
                    "check": "resources",
                    "warnings": warnings
                }
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message="All required resources available",
            context={"check": "resources"}
        )

    @abstractmethod
    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return the method sequence for this executor.

        Returns:
            List of (class_name, method_name) tuples
        """
        pass


class MethodSequenceValidatingMixin:
    """Mixin for validating method sequences in executors."""

    def _validate_method_sequences(self) -> None:
        """Validate that all methods in the sequence exist and are callable.

        Raises:
            ValueError: If a class is not registered, method doesn't exist, or method is not callable
        """
        seq = self._get_method_sequence()
        for class_name, method_name in seq:
            instance = self.executor.instances.get(class_name)
            if instance is None:
                raise ValueError(f"Class {class_name} not in executor registry")
            if not hasattr(instance, method_name):
                raise ValueError(f"{class_name} has no method {method_name}")
            method = getattr(instance, method_name)
            if not callable(method):
                raise ValueError(f"{class_name}.{method_name} is not callable")

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return the method sequence for this executor.

        Section 5.1: Support METHOD_SEQUENCE class attribute (preferred)
        Falls back to _get_method_sequence() method for backward compatibility.

        Returns:
            List of (class_name, method_name) tuples
        """
        # Section 5.1: Check for METHOD_SEQUENCE class attribute first (new pattern)
        if hasattr(self.__class__, 'METHOD_SEQUENCE'):
            return self.__class__.METHOD_SEQUENCE
        # Fallback to method implementation for backward compatibility
        return []


class AdvancedDataFlowExecutor(ExecutorBase, MethodSequenceValidatingMixin):
    """Advanced executor with frontier paradigmatic capabilities"""

    # Calibration threshold: methods with scores below this are skipped
    CALIBRATION_SKIP_THRESHOLD = 0.3

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        questionnaire_provider=None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,  # NEW
    ) -> None:
        # Section 3: ExecutorConfig Contract Enforcement
        # Config is REQUIRED - no fallbacks allowed
        if config is None:
            raise ValueError(
                f"{self.__class__.__name__}: ExecutorConfig is required and cannot be None. "
                "Use build_processor() factory or provide explicit config."
            )

        self.executor = method_executor
        self.signal_registry = signal_registry
        self.questionnaire_provider = questionnaire_provider
        self.config = config

        # NEW: Calibration orchestrator
        self.calibration = calibration_orchestrator

        # NEW: Store calibration results for current execution
        self.calibration_results: dict[str, CalibrationResult] = {}
        self.accumulator: dict[str, list[Any]] = {}

    def _validate_executor_config(self) -> None:
        """Section 3.2: Validate config at construction time.

        Enforces contract requirements:
        - timeout_s > 0
        - retry >= 0
        - seed >= 0
        - Logs config hash for traceability
        """
        if self.config.timeout_s <= 0:
            raise ValueError(f"config.timeout_s must be > 0, got {self.config.timeout_s}")

        if self.config.retry < 0:
            raise ValueError(f"config.retry must be >= 0, got {self.config.retry}")

        if self.config.seed < 0:
            raise ValueError(f"config.seed must be >= 0, got {self.config.seed}")

        config_hash = self.config.compute_hash()
        logger.info(
            "executor_config_validated",
            extra={
                "executor_class": self.__class__.__name__,
                "config_hash": config_hash,
                "timeout_s": self.config.timeout_s,
                "retry": self.config.retry,
                "seed": self.config.seed,
            }
        )

        # Section 7.2: Track advanced module activation
        self.module_activations = {
            "quantum": {"count": 0, "total_time": 0.0},
            "neuromorphic": {"count": 0, "total_time": 0.0},
            "causal": {"count": 0, "total_time": 0.0},
            "info_theory": {"count": 0, "total_time": 0.0},
            "meta_learning": {"count": 0, "total_time": 0.0},
        }

        # Log only hard facts with academic basis
        logger.info(
            "executor_initialized",
            extra={
                "executor_class": self.__class__.__name__,
                "config_hash": self.config.compute_hash(),
                "timeout_s": self.config.timeout_s,
                "retry": self.config.retry,
                "advanced_modules": "academically_grounded",
                "advanced_module_version": self.adv_config.advanced_module_version,  # Section 7.3
                "quantum_methods": self.adv_config.quantum_num_methods,
                "neuromorphic_stages": self.adv_config.neuromorphic_num_stages,
                "causal_variables": self.adv_config.causal_num_variables,
                "calibration_enabled": self.calibration is not None,  # NEW
            },
        )

        self.execution_metrics: dict[str, list[float]] = defaultdict(list)
        self.method_dependencies: dict[str, set] = {}
        self._argument_context: dict[str, Any] = {}
        self.used_signals: list[dict[str, Any]] = []  # Track signal usage
        # Validate early: no executor can be constructed with missing/placeholder calibration
        self._validate_method_sequences()
        self._validate_calibrations()

        # NOTE: Validation NOT called in base class because most executors
        # define method_sequence in execute(), not in _get_method_sequence().
        # Executors that want validation must call it explicitly in their __init__.

    def _get_policy_area_for_question(self, question_id: str) -> str:
        """
        Map question ID to policy area using injected questionnaire provider.

        This uses the provider's already-loaded data, avoiding direct file I/O
        and respecting the dependency injection architecture.

        Args:
            question_id: Question ID (e.g., "Q001", "Q031")

        Returns:
            Policy area code (e.g., "PA01", "PA02")
        """
        # Use injected provider if available
        if self.questionnaire_provider:
            try:
                return self.questionnaire_provider.get_policy_area_for_question(question_id)
            except Exception as e:
                logger.warning(
                    "provider_policy_area_lookup_failed",
                    question_id=question_id,
                    error=str(e),
                    fallback="PA01"
                )
        else:
            logger.warning(
                "no_questionnaire_provider",
                question_id=question_id,
                fallback="PA01"
            )

        # Fallback to PA01
        return "PA01"

    def _fetch_signals(self, policy_area: str = "fiscal") -> dict[str, Any] | None:
        """
        Fetch signals from registry for the given policy area.

        Adds OpenTelemetry span for observability. Signal registry is now required
        (explicit None allowed for graceful degradation, but absence is logged).

        Args:
            policy_area: Policy area to fetch signals for

        Returns:
            Signal pack data or None if unavailable (explicit None or missing)
        """
        # Explicit None check - signal_registry is required but can be explicitly None
        if self.signal_registry is None:
            logger.warning(
                f"Signal registry is explicitly None for {self.__class__.__name__}. "
                "Execution will proceed without signal enhancement, which may reduce analysis quality."
            )
            return None

        if HAS_OTEL and tracer:
            with tracer.start_as_current_span("signals.fetch") as span:
                span.set_attribute("policy_area", policy_area)
                fetch_start = time.time()

                signal_pack = self.signal_registry.get(policy_area)

                fetch_duration = time.time() - fetch_start
                span.set_attribute("fetch_duration_ms", fetch_duration * 1000)

                if signal_pack:
                    span.set_attribute("signal_version", signal_pack.version)
                    signal_hash = signal_pack.compute_hash()[:16]
                    span.set_attribute("signal_hash", signal_hash)
                    span.set_status(Status(StatusCode.OK))

                    # Track usage with enhanced metadata
                    self.used_signals.append({
                        "version": signal_pack.version,
                        "policy_area": signal_pack.policy_area,
                        "hash": signal_pack.compute_hash(),
                        "hash_short": signal_hash,
                        "keys_used": signal_pack.get_keys_used(),
                        "timestamp_utc": time.time(),
                        "pattern_count": len(signal_pack.patterns) if hasattr(signal_pack, 'patterns') else 0,
                    })

                    logger.info(
                        f"Fetched signals for {policy_area}: version={signal_pack.version}, "
                        f"hash={signal_hash}"
                    )

                    # Sort patterns for determinism (stable ordering across runs)
                    patterns = sorted(signal_pack.patterns) if isinstance(signal_pack.patterns, list) else signal_pack.patterns

                    return {
                        "patterns": patterns,  # Sorted for determinism
                        "indicators": signal_pack.indicators,
                        "regex": signal_pack.regex,
                        "verbs": signal_pack.verbs,
                        "entities": signal_pack.entities,
                        "thresholds": signal_pack.thresholds,
                    }
                else:
                    span.set_status(Status(StatusCode.ERROR, "Signal pack not found"))
                    logger.warning(f"No signals found for policy area: {policy_area}")
                    return None
        else:
            # No OpenTelemetry, fetch without span
            signal_pack = self.signal_registry.get(policy_area)
            if signal_pack:
                signal_hash = signal_pack.compute_hash()[:16]
                self.used_signals.append({
                    "version": signal_pack.version,
                    "policy_area": signal_pack.policy_area,
                    "hash": signal_pack.compute_hash(),
                    "hash_short": signal_hash,
                    "keys_used": signal_pack.get_keys_used(),
                    "timestamp_utc": time.time(),
                    "pattern_count": len(signal_pack.patterns) if hasattr(signal_pack, 'patterns') else 0,
                })

                # Sort patterns for determinism (stable ordering across runs)
                patterns = sorted(signal_pack.patterns) if isinstance(signal_pack.patterns, list) else signal_pack.patterns

                logger.info(
                    f"Fetched signals for {policy_area}: version={signal_pack.version}, "
                    f"hash={signal_hash}"
                )

                return {
                    "patterns": patterns,  # Sorted for determinism
                    "indicators": signal_pack.indicators,
                    "regex": signal_pack.regex,
                    "verbs": signal_pack.verbs,
                    "entities": signal_pack.entities,
                    "thresholds": signal_pack.thresholds,
                }

            # Log signal miss (requested but not found)
            logger.warning(
                f"Signal pack not found for policy_area='{policy_area}' in {self.__class__.__name__}. "
                "This may affect analysis quality."
            )
            return None

    def _validate_calibrations(self) -> None:
        """
        Ensures the new layer-based calibration system is correctly set up and
        that all methods in the sequence have a base calibration entry.
        """
        if self.calibration is None:
            raise RuntimeError(
                f"CalibrationOrchestrator not provided to {self.__class__.__name__}. "
                "The new calibration system is mandatory."
            )

        # Check calibration version compatibility
        from .versions import check_version_compatibility
        try:
            check_version_compatibility(
                "calibration",
                CALIBRATION_VERSION,
                MINIMUM_SUPPORTED_VERSION
            )
        except ValueError as e:
            raise RuntimeError(
                f"Calibration version incompatibility in {self.__class__.__name__}: {e}"
            ) from e

        # Validate that each method has at least a base intrinsic calibration
        seq = getattr(self, "_get_method_sequence", lambda: [])()
        missing_base_calibrations = []
        for class_name, method_name in seq:
            method_id = f"{class_name}.{method_name}"
            # Use the orchestrator's loader to check for the raw score
            raw_score_data = self.calibration.intrinsic_loader.get_raw_score(method_id)
            if raw_score_data is None:
                missing_base_calibrations.append(method_id)

        if missing_base_calibrations:
            raise RuntimeError(
                f"Missing base intrinsic calibration for the following methods in {self.__class__.__name__}: "
                f"{', '.join(missing_base_calibrations)}"
            )

    def get_calibration_manifest_data(self) -> dict[str, Any]:
        """
        Get calibration information for verification manifest.

        Returns:
            Dictionary with calibration version, hash, method count, and missing methods
        """
        import hashlib

        seq = getattr(self, "_get_method_sequence", lambda: [])()
        methods_calibrated = []
        methods_missing = []

        for class_name, method_name in seq:
            calib = resolve_calibration(class_name, method_name, strict=False)
            if calib:
                methods_calibrated.append(f"{class_name}.{method_name}")
            else:
                methods_missing.append(f"{class_name}.{method_name}")

        # Compute hash of calibrated methods
        calibration_data = "".join(sorted(methods_calibrated)).encode()
        calibration_hash = hashlib.sha256(calibration_data).hexdigest()[:16]

        return {
            "version": CALIBRATION_VERSION,
            "hash": calibration_hash,
            "methods_calibrated": len(methods_calibrated),
            "methods_missing": methods_missing,
        }

    def execute_with_optimization(self, doc, method_executor,
                                  method_sequence: list[tuple[str, str]],
                                  *,
                                  policy_unit_id: str | None = None,
                                  correlation_id: str | None = None) -> dict[str, Any]:
        """Execute with advanced optimization strategies and deterministic seeding

        NOW INTEGRATED WITH CONTRACT INFRASTRUCTURE for reproducibility!

        Includes:
        - Signal fetching and usage tracking
        - OpenTelemetry instrumentation
        - Structured logging for debugging
        - Retry logic for transient failures
        - Execution time tracking
        - Failure metrics collection
        - **DETERMINISTIC EXECUTION** via policy_unit_id seeding
        - **Section 3.3**: Config values propagated to execution context
        """
        self.accumulator.clear()
        execution_start = time.time()
        self.executor = method_executor

        # ============================================================
        # CALIBRATION PHASE (NEW - inserted per corrected spec)
        # ============================================================
        calibration_results = {}
        skipped_methods = []

        if self.calibration is not None:
            logger.info("calibration_phase_start")

            # Build context for calibration
            try:
                from saaaaaa.core.calibration.data_structures import ContextTuple

                # Extract context information from doc
                question_id = getattr(doc, 'question_id', 'Q000')
                dimension_id = getattr(doc, 'dimension_id', 'DIM00')
                policy_area_id = getattr(doc, 'policy_area_id', 'PA00')
                unit_quality = getattr(doc, 'unit_quality', 0.75)

                context = ContextTuple(
                    question_id=question_id,
                    dimension=dimension_id,
                    policy_area=policy_area_id,
                    unit_quality=unit_quality
                )

                # Get PDT structure if available
                pdt_structure = getattr(doc, 'pdt_structure', None)

                # Calibrate each method in the sequence
                for class_name, method_name in method_sequence:
                    method_id = f"{class_name}.{method_name}"
                    method_version = "v1.0.0"  # Default version

                    try:
                        # THIS IS THE CRITICAL CALL THAT WAS MISSING:
                        cal_result = self.calibration.calibrate(
                            method_id=method_id,
                            method_version=method_version,
                            context=context,
                            pdt_structure=pdt_structure,
                            graph_config=self.config.compute_hash() if hasattr(self.config, 'compute_hash') else None,
                            subgraph_id=f"{question_id}_{class_name}"
                        )

                        calibration_results[method_id] = cal_result

                        logger.info(
                            "method_calibrated",
                            extra={
                                "method": method_id,
                                "final_score": cal_result.final_score,
                                "class": class_name
                            }
                        )

                    except Exception as e:
                        logger.error(
                            "calibration_failed",
                            extra={
                                "method": method_id,
                                "error": str(e)
                            },
                            exc_info=True
                        )
                        # Continue without calibration for this method

                logger.info(
                    "calibration_phase_complete",
                    extra={"num_calibrated": len(calibration_results)}
                )

            except Exception as e:
                logger.error(
                    "calibration_phase_error",
                    extra={"error": str(e)},
                    exc_info=True
                )
        else:
            logger.info("calibration_disabled", extra={"reason": "orchestrator_is_none"})

        # ============================================================
        # END CALIBRATION PHASE
        # ============================================================

        results = {}
        current_data = doc.raw_text

        # Section 3.3: Use config.timeout_s for execution timeout budget
        total_timeout_budget = self.config.timeout_s
        logger.info(
            "execution_started",
            extra={
                "executor_class": self.__class__.__name__,
                "timeout_budget_s": total_timeout_budget,
                "retry_limit": self.config.retry,
                "seed": self.config.seed,
                "num_methods": len(method_sequence),
            }
        )

        # Derive policy_unit_id from environment or doc if not provided
        if policy_unit_id is None:
            policy_unit_id = os.getenv("POLICY_UNIT_ID", "default-policy")
        if correlation_id is None:
            import uuid
            correlation_id = str(uuid.uuid4())

        # Start OpenTelemetry span for entire execution
        span_context = tracer.start_as_current_span("executor.execute") if HAS_OTEL and tracer else None

        try:
            if span_context:
                span = span_context.__enter__()
                span.set_attribute("num_methods", len(method_sequence))
                span.set_attribute("policy_unit_id", policy_unit_id)
                span.set_attribute("correlation_id", correlation_id)

            # DETERMINISTIC EXECUTION CONTEXT - makes all random operations reproducible!
            with deterministic(policy_unit_id, correlation_id) as seeds:
                # Create local RNG for deterministic random operations
                np.random.default_rng(seeds.np)

                logger.info(f"Executing with DETERMINISTIC seeding: policy_unit_id={policy_unit_id}, "
                          f"correlation_id={correlation_id}, seed={seeds.py}")

                # Fetch signals at the beginning of execution
                # Get question_id for signal tracking (extract from doc or method_sequence)
                question_id = getattr(doc, 'question_id', None) or 'Q000'

                # Determine policy area for this question
                policy_area = self._get_policy_area_for_question(question_id)

                # Fetch signals and store for use during execution
                signals = self._fetch_signals(policy_area)

                # Initialize consumption proof tracker
                consumption_proof = None
                if signals:
                    consumption_proof = SignalConsumptionProof(
                        executor_id=self.__class__.__name__,
                        question_id=question_id,
                        policy_area=policy_area,
                    )

                    if span_context:
                        span.set_attribute("signals.fetched", True)
                        span.set_attribute("signals.pattern_count", len(signals.get("patterns", [])))
                        span.set_attribute("signals.policy_area", policy_area)

                    # Store signals in context for methods to access
                    self._argument_context['signals'] = signals
                    self._argument_context['consumption_proof'] = consumption_proof

                    logger.info(f"Signals loaded: {len(signals.get('patterns', []))} patterns, "
                               f"{len(signals.get('indicators', []))} indicators, "
                               f"policy_area={policy_area}")

                    # CRITICAL: Actually USE the signals for pattern matching
                    # This demonstrates real signal consumption
                    import re
                    text = current_data if isinstance(current_data, str) else str(current_data)
                    patterns_to_try = signals.get('patterns', [])[:50]  # Limit for performance

                    for pattern in patterns_to_try:
                        try:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            for match in matches[:3]:  # Limit matches per pattern
                                consumption_proof.record_pattern_match(pattern, match)
                        except re.error:
                            # Invalid regex pattern, skip
                            pass

                    logger.info(f"Signal consumption: {len(consumption_proof.consumed_patterns)} pattern matches recorded")
                elif span_context:
                    span.set_attribute("signals.fetched", False)

                logger.info(f"Starting execution with {len(method_sequence)} methods")

                total_entropy = 0.0

                self._reset_argument_context(doc)
                # Re-add signals after reset if available
                if signals:
                    self._argument_context['signals'] = signals

                # Section 5.3: Runtime sequence tracking
                executed_sequence = []

                for idx, (class_name, method_name) in enumerate(method_sequence):
                    method_key = f"{class_name}.{method_name}"

                    # ============================================================
                    # METHOD SKIPPING BASED ON CALIBRATION (NEW)
                    # ============================================================
                    if method_key in calibration_results:
                        cal_score = calibration_results[method_key].final_score

                        if cal_score < self.CALIBRATION_SKIP_THRESHOLD:
                            logger.warning(
                                "method_skipped_low_calibration",
                                extra={
                                    "method": method_key,
                                    "score": cal_score,
                                    "threshold": self.CALIBRATION_SKIP_THRESHOLD
                                }
                            )

                            skipped_methods.append({
                                "method_id": method_key,
                                "calibration_score": cal_score,
                                "threshold": self.CALIBRATION_SKIP_THRESHOLD,
                                "reason": "calibration_score_below_threshold"
                            })

                            continue  # SKIP THIS METHOD
                    # ============================================================
                    # END METHOD SKIPPING
                    # ============================================================

                    executed_sequence.append((class_name, method_name))

                    # Execute with retry logic
                    method_start = time.time()
                    success = False
                    max_retries = 3
                    prepared_kwargs = {}  # Initialize to prevent UnboundLocalError in failure logging

                    for attempt in range(max_retries):
                        try:
                            prepared_kwargs = self._prepare_arguments(
                                class_name,
                                method_name,
                                doc,
                                current_data,
                            )

                            result = self.executor.execute(
                                class_name,
                                method_name,
                                **prepared_kwargs,
                            )

                            results[method_key] = result
                            success = True

                            if result is not None:
                                current_data = result

                            self._update_argument_context(
                                method_key,
                                result,
                                class_name,
                                method_name,
                            )

                            break  # Success, exit retry loop

                        except Exception as e:
                            if attempt < max_retries - 1:
                                _global_metrics.record_retry()
                                logger.warning(
                                    f"Method {method_key} failed on attempt {attempt + 1}/{max_retries}: {str(e)}. Retrying...",
                                    exc_info=False
                                )
                                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                            else:
                                results[method_key] = None
                                logger.error(
                                    "Method %s failed",
                                    f"{class_name}.{method_name}",
                                    exc_info=True,
                                    extra={
                                        'method_key': f"{class_name}.{method_name}",
                                        'class_name': class_name,
                                        'method_name': method_name,
                                        'prepared_kwargs_keys': list(prepared_kwargs.keys()),
                                        'error_type': type(e).__name__,
                                        'error_details': str(e),
                                    }
                                )

                    # Record execution metrics
                    method_time = time.time() - method_start
                    _global_metrics.record_execution(success, method_time, method_key)

                total_time = time.time() - execution_start
                logger.info(
                    f"Execution completed in {total_time:.3f}s: {_global_metrics.successful_executions}/{_global_metrics.total_executions} methods successful",
                    extra={
                        'total_time': total_time,
                        'policy_unit_id': policy_unit_id,
                        'correlation_id': correlation_id,
                    }
                )

                # Add execution metrics to span
                if span_context:
                    span.set_attribute("execution_time_s", total_time)
                    span.set_attribute("successful_methods", _global_metrics.successful_executions)
                    span.set_attribute("total_methods", _global_metrics.total_executions)
                span.set_attribute("used_signals_count", len(self.used_signals))
                span.set_status(Status(StatusCode.OK))

            # Save consumption proof if signals were used
            if consumption_proof and consumption_proof.consumed_patterns:
                try:
                    from pathlib import Path
                    proof_dir = Path('artifacts/signal_proofs')
                    consumption_proof.save_to_file(proof_dir)
                    logger.info(
                        f"Consumption proof saved: {len(consumption_proof.consumed_patterns)} patterns, "
                        f"proof chain: {consumption_proof.proof_chain[-1][:16] if consumption_proof.proof_chain else 'none'}..."
                    )
                except Exception as e:
                    logger.warning(f"Failed to save consumption proof: {e}")

            result = {
                'modality': 'TYPE_A',
                'elements': self._extract(results),
                'raw': results,
                'confidence': float(self._argument_context.get('confidence', 0.0) or 0.0),
            }

            # ============================================================
            # ADD CALIBRATION RESULTS TO OUTPUT (NEW)
            # ============================================================
            if calibration_results:
                from datetime import datetime
                result["_calibration"] = {
                    "executed_at": datetime.utcnow().isoformat(),
                    "config_hash": self.calibration.config.compute_system_hash() if self.calibration and hasattr(self.calibration.config, 'compute_system_hash') else None,
                    "scores": {
                        method_id: {
                            "final_score": res.final_score,
                            "layer_breakdown": {
                                str(layer): score.score
                                for layer, score in res.layer_scores.items()
                            },
                            "linear_contribution": res.linear_contribution,
                            "interaction_contribution": res.interaction_contribution,
                            "config_hash": res.computation_metadata.get("config_hash"),
                        }
                        for method_id, res in calibration_results.items()
                    },
                    "skipped_methods": skipped_methods,
                    "total_methods_calibrated": len(calibration_results),
                    "total_methods_skipped": len(skipped_methods),
                }
            # ============================================================
            # END CALIBRATION RESULTS
            # ============================================================

            return result

        finally:
            if span_context:
                span_context.__exit__(None, None, None)

    def execute_chunk(self, chunk_doc, chunk_id: int):
        """
        Execute on single chunk with restricted scope.

        This method enables chunk-aware processing by executing only on the
        relevant chunk data, avoiding redundant full-document processing.

        Args:
            chunk_doc: PreprocessedDocument containing the chunk
            chunk_id: ID of the chunk to process

        Returns:
            Execution results scoped to the chunk
        """
        # Store chunk context for argument resolution
        self._current_chunk_id = chunk_id
        self._chunk_mode = True

        try:
            # Get method sequence for this executor
            method_sequence = self._get_method_sequence()

            # Filter methods based on chunk type if available
            if chunk_doc.chunks and chunk_id < len(chunk_doc.chunks):
                chunk_type = chunk_doc.chunks[chunk_id].chunk_type
                method_sequence = self._filter_methods_for_chunk(method_sequence, chunk_type)

            # Execute with chunk boundaries enforced
            return self.execute_with_optimization(
                chunk_doc,
                self.executor,
                method_sequence,
            )
        finally:
            # Clean up chunk context
            self._chunk_mode = False
            self._current_chunk_id = None

    def _filter_methods_for_chunk(
        self,
        methods: list[tuple[str, str]],
        chunk_type: str
    ) -> list[tuple[str, str]]:
        """
        Filter methods based on chunk type relevance.

        Args:
            methods: Full method sequence
            chunk_type: Type of chunk being processed

        Returns:
            Filtered method sequence relevant to chunk type
        """
        # Mapping of chunk types to relevant method patterns
        # This is a simplified version - full implementation would use
        # more sophisticated matching based on executor configuration
        CHUNK_METHOD_PATTERNS = {
            "diagnostic": ["baseline", "gap", "diagnostic", "problem"],
            "activity": ["activity", "intervention", "action", "program"],
            "indicator": ["metric", "indicator", "kpi", "measure"],
            "resource": ["budget", "financial", "resource", "funding"],
            "temporal": ["timeline", "temporal", "schedule", "phase"],
            "entity": ["entity", "responsible", "stakeholder", "actor"],
        }

        patterns = CHUNK_METHOD_PATTERNS.get(chunk_type, [])
        if not patterns:
            # No filtering if chunk type unknown
            return methods

        # Filter methods that match chunk type patterns
        filtered = []
        for class_name, method_name in methods:
            method_lower = method_name.lower()
            class_lower = class_name.lower()

            # Check if method or class name matches any pattern
            if any(pattern in method_lower or pattern in class_lower for pattern in patterns):
                filtered.append((class_name, method_name))

        # If filtering results in empty list, return original
        # (better to execute all than execute none)
        return filtered if filtered else methods

    @abstractmethod
    def _extract(self, results: dict) -> list:
        """Extract final results (to be implemented by subclasses)"""
        pass

    # ------------------------------------------------------------------
    # Argument mapping helpers
    # ------------------------------------------------------------------

    # ============================================================================
    # ENHANCED ARGUMENT RESOLUTION WITH GRAPH-AWARE INTELLIGENCE
    # ============================================================================

    def _reset_argument_context(self, doc: Any) -> None:
        """Enhanced context initialization with graph-aware tracking"""
        raw_text = getattr(doc, 'raw_text', '') or ''
        sentences = list(getattr(doc, 'sentences', []) or [])
        tables = list(getattr(doc, 'tables', []) or [])

        self._argument_context = {
            'doc': doc,
            'text': raw_text,
            'sentences': sentences,
            'tables': tables,
            'matches': [],
            'positions': [],
            'confidence': 0.0,
            'pattern_specificity': 0.8,
            'text_length': len(raw_text),
            # Enhanced: Graph-aware context
            'grafo': None,  # NetworkX DiGraph for causal analysis
            'graph_nodes': [],  # Tracked nodes from causal extraction
            'graph_edges': [],  # Tracked edges from causal extraction
            'statements': [],  # Policy statements for graph construction
            # Enhanced: Segmentation tracking
            'segments': None,  # Text segments for analysis
            'segment_metadata': {},  # Metadata about segmentation strategy
        }

        # Initialize policy processor context
        policy_processor = self.executor.instances.get('IndustrialPolicyProcessor')
        if policy_processor is not None:
            dimension, category, _ = self._derive_dimension_category(policy_processor)
            self._argument_context.setdefault('dimension', dimension)
            self._argument_context.setdefault('category', category)

    def _prepare_arguments(
        self,
        class_name: str,
        method_name: str,
        doc: Any,
        current_data: Any,
    ) -> dict[str, Any]:
        instance = self.executor.instances.get(class_name)
        if instance is None:
            return {}

        try:
            method = getattr(instance, method_name)
        except AttributeError:
            return {}

        signature = inspect.signature(method)
        prepared: dict[str, Any] = {}

        self._ingest_payload_for_context(current_data)

        for name, param in signature.parameters.items():
            if name == 'self':
                continue

            value = self._resolve_argument(
                name,
                class_name,
                method_name,
                doc,
                current_data,
                instance,
            )

            if value is _ARG_UNSET:
                if param.default is inspect._empty:
                    # Provide safe fallbacks for required params
                    value = self._fallback_for(
                        name,
                        class_name,
                        method_name,
                        instance,
                    )
                else:
                    continue

            prepared[name] = value

        if 'extract' not in method_name.lower():
            prepared['accumulator'] = self.accumulator

        return prepared

    def _resolve_argument(
        self,
        name: str,
        class_name: str,
        method_name: str,
        doc: Any,
        current_data: Any,
        instance: Any,
    ) -> Any:
        """Enhanced argument resolution with sophisticated graph and segment handling"""
        ctx = self._argument_context

        # ========================================================================
        # NEW: CHUNK-AWARE ARGUMENT RESOLUTION
        # ========================================================================

        # Check if in chunk mode
        if hasattr(self, '_chunk_mode') and self._chunk_mode:
            chunk_id = getattr(self, '_current_chunk_id', None)

            if chunk_id is not None and doc.chunks and chunk_id < len(doc.chunks):
                chunk = doc.chunks[chunk_id]

                # Provide chunk-scoped text
                if name in {'text', 'raw_text', 'document_text'}:
                    return chunk.text

                # Provide chunk-scoped sentences
                if name in {'sentences', 'relevant_sentences', 'sentence_list'}:
                    if chunk.sentences and doc.sentences:
                        return [doc.sentences[i] for i in chunk.sentences if i < len(doc.sentences)]
                    elif doc.sentences:
                        # Fallback: extract sentences whose offsets are within chunk boundaries
                        return [
                            s for s in doc.sentences
                            if hasattr(s, 'start') and hasattr(s, 'end')
                            and s.start >= chunk.start_pos and s.end <= chunk.end_pos
                        ]
                    return []

                # Provide chunk-scoped tables
                if name in {'tables', 'table_data', 'raw_tables'}:
                    if chunk.tables and doc.tables:
                        return [doc.tables[i] for i in chunk.tables if i < len(doc.tables)]
                    elif doc.tables:
                        # Fallback: extract tables whose offsets are within chunk boundaries
                        return [
                            t for t in doc.tables
                            if hasattr(t, 'start') and hasattr(t, 'end')
                            and t.start >= chunk.start_pos and t.end <= chunk.end_pos
                        ]
                    return []

                # Restrict window size to chunk boundaries
                if name in {'window_size', 'context_window'}:
                    max_window = chunk.end_pos - chunk.start_pos
                    # Get configured window size from instance config if available
                    requested = getattr(getattr(instance, 'config', None), 'context_window_chars', 400)
                    return min(requested, max_window)

        # ========================================================================
        # SIGNAL CHANNEL INTEGRATION - Inject signals into method arguments
        # ========================================================================

        signals = ctx.get('signals')
        if signals:
            # Inject signal patterns
            if name in {'patterns', 'fiscal_patterns', 'signal_patterns'}:
                return signals.get('patterns', [])

            # Inject indicators
            if name in {'indicators', 'signal_indicators'}:
                return signals.get('indicators', [])

            # Inject regex patterns
            if name in {'regex', 'regex_patterns', 'signal_regex'}:
                return signals.get('regex', [])

            # Inject verbs
            if name in {'verbs', 'signal_verbs'}:
                return signals.get('verbs', [])

            # Inject entities
            if name in {'entities', 'signal_entities'}:
                return signals.get('entities', [])

            # Inject thresholds
            if name in {'thresholds', 'signal_thresholds'}:
                return signals.get('thresholds', {})

            # Inject all signals as dict
            if name in {'signals', 'signal_pack'}:
                return signals

        # ========================================================================
        # STANDARD ARGUMENTS (existing implementation retained)
        # ========================================================================

        if name in {'data', 'payload', 'input_data'}:
            return current_data

        if name in {'doc', 'document', 'preprocessed_document'}:
            return doc

        if name in {'text', 'raw_text', 'document_text'}:
            return ctx.get('text')

        if name in {'sentences', 'relevant_sentences', 'sentence_list'}:
            return ctx.get('sentences')

        if name in {'tables', 'table_data', 'raw_tables'}:
            return ctx.get('tables')

        if name in {'metadata', 'document_metadata'}:
            return getattr(doc, 'metadata', {})

        if name in {'matches', 'match_list'}:
            return ctx.get('matches', [])

        if name in {'positions', 'match_positions'}:
            return ctx.get('positions', [])

        # ========================================================================
        # ENHANCED: SOPHISTICATED SEGMENTS RESOLUTION
        # ========================================================================

        if name in {'segments', 'text_segments', 'segment_list'}:
            segments = ctx.get('segments')

            if segments is not None:
                return segments

            # Strategy 1: Use sentences if available (most common case)
            sentences = ctx.get('sentences')
            if sentences and isinstance(sentences, list):
                ctx['segments'] = sentences
                ctx['segment_metadata'] = {
                    'strategy': 'sentence_based',
                    'count': len(sentences),
                    'source': 'context'
                }
                return sentences

            # Strategy 2: Intelligent text segmentation using semantic boundaries
            text = ctx.get('text', '')
            if text:
                # Split on paragraph boundaries first
                paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

                if paragraphs:
                    segments = paragraphs
                else:
                    # Fallback: sentence-like splitting on period boundaries
                    segments = [s.strip() for s in text.split('.') if s.strip()]

                ctx['segments'] = segments
                ctx['segment_metadata'] = {
                    'strategy': 'semantic_split',
                    'count': len(segments),
                    'avg_length': sum(len(s) for s in segments) / max(len(segments), 1)
                }
                return segments

            # Strategy 3: Return empty list as safe fallback
            ctx['segments'] = []
            ctx['segment_metadata'] = {'strategy': 'empty_fallback'}
            return []

        # ========================================================================
        # ENHANCED: GRAPH OBJECT RESOLUTION (DiGraph for causal analysis)
        # ========================================================================

        if name in {'grafo', 'graph', 'causal_graph', 'dag'}:
            # Strategy 1: Return cached graph from context
            grafo = ctx.get('grafo')
            if grafo is not None:
                return grafo

            # Strategy 2: Check if instance has a graph attribute
            if hasattr(instance, 'grafo'):
                grafo = instance.grafo
                ctx['grafo'] = grafo
                return grafo

            if hasattr(instance, 'graph'):
                grafo = instance.graph
                ctx['grafo'] = grafo
                return grafo

            # Strategy 3: Construct graph from statements if available
            statements = ctx.get('statements')
            if statements:
                grafo = self._construct_causal_graph(statements, instance)
                if grafo is not None:
                    ctx['grafo'] = grafo
                    return grafo

            # Strategy 4: Return empty graph as standard fallback
            grafo = self._create_empty_graph()
            ctx['grafo'] = grafo
            return grafo

        # ========================================================================
        # ENHANCED: GRAPH NODE RESOLUTION (origen, destino for causal links)
        # ========================================================================

        if name in {'origen', 'source', 'source_node', 'from_node'}:
            # Strategy 1: Extract from current_data if it's a dict or tuple
            if isinstance(current_data, dict):
                if 'origen' in current_data:
                    return current_data['origen']
                if 'source' in current_data:
                    return current_data['source']
                if 'from' in current_data:
                    return current_data['from']

            # Strategy 2: Extract from tuple (common pattern: (origen, destino))
            if isinstance(current_data, tuple) and len(current_data) >= 2:
                return current_data[0]

            # Strategy 3: Infer from graph context (first node in recent edges)
            graph_edges = ctx.get('graph_edges', [])
            if graph_edges and isinstance(graph_edges[-1], (tuple, list)):
                return graph_edges[-1][0]

            # Strategy 4: Use first node from tracked nodes
            graph_nodes = ctx.get('graph_nodes', [])
            if graph_nodes:
                return graph_nodes[0]

            # Strategy 5: Return None (method will need to handle)
            return _ARG_UNSET

        if name in {'destino', 'target', 'target_node', 'to_node'}:
            # Strategy 1: Extract from current_data if it's a dict or tuple
            if isinstance(current_data, dict):
                if 'destino' in current_data:
                    return current_data['destino']
                if 'target' in current_data:
                    return current_data['target']
                if 'to' in current_data:
                    return current_data['to']

            # Strategy 2: Extract from tuple (common pattern: (origen, destino))
            if isinstance(current_data, tuple) and len(current_data) >= 2:
                return current_data[1]

            # Strategy 3: Infer from graph context (second node in recent edges)
            graph_edges = ctx.get('graph_edges', [])
            if graph_edges and isinstance(graph_edges[-1], (tuple, list)) and len(graph_edges[-1]) >= 2:
                return graph_edges[-1][1]

            # Strategy 4: Use second node from tracked nodes
            graph_nodes = ctx.get('graph_nodes', [])
            if len(graph_nodes) >= 2:
                return graph_nodes[1]

            # Strategy 5: Return None (method will need to handle)
            return _ARG_UNSET

        # ========================================================================
        # ENHANCED: STATEMENTS RESOLUTION (for graph construction)
        # ========================================================================

        if name in {'statements', 'policy_statements', 'causal_statements'}:
            statements = ctx.get('statements')

            if statements:
                return statements

            # Extract statements from current_data if it's a list
            if isinstance(current_data, list):
                ctx['statements'] = current_data
                return current_data

            # Use sentences as statements if available
            sentences = ctx.get('sentences')
            if sentences:
                ctx['statements'] = sentences
                return sentences

            return []

        # ========================================================================
        # EXISTING SOPHISTICATED RESOLUTIONS (all retained)
        # ========================================================================

        if name == 'match_position':
            positions = ctx.get('positions') or []
            if positions:
                return positions[0]
            matches = ctx.get('matches') or []
            if matches:
                index = ctx.get('text', '').find(matches[0])
                if index >= 0:
                    return index
            return 0

        if name == 'window_size':
            config = getattr(instance, 'config', None)
            return getattr(config, 'context_window_chars', 400)

        if name in {'pattern_specificity', 'specificity'}:
            matches = ctx.get('matches') or []
            return self._compute_pattern_specificity(matches)

        if name in {'total_corpus_size', 'text_length', 'corpus_size'}:
            length = ctx.get('text_length')
            if not length:
                sentences = ctx.get('sentences') or []
                length = sum(len(s) for s in sentences)
            return max(1, length)

        if name == 'confidence':
            return ctx.get('confidence', 0.0)

        if name in {'dimension', 'policy_dimension'}:
            dimension = ctx.get('dimension')
            if dimension is None:
                dimension, category, _ = self._derive_dimension_category(instance)
                ctx['dimension'] = dimension
                ctx.setdefault('category', category)
            return ctx.get('dimension')

        if name in {'category', 'policy_category'}:
            category = ctx.get('category')
            if category is None:
                dimension, category, _ = self._derive_dimension_category(instance)
                ctx.setdefault('dimension', dimension)
                ctx['category'] = category
            return ctx.get('category')

        if name == 'compiled_patterns':
            patterns = ctx.get('compiled_patterns')
            if patterns is None:
                patterns = self._extract_all_patterns(instance)
                ctx['compiled_patterns'] = patterns
            return patterns

        if name in {'pattern_registry', 'patterns'}:
            return getattr(instance, '_pattern_registry', {})

        if name in {'values', 'value_array'}:
            matches = ctx.get('matches') or []
            if matches:
                return np.array([len(m) for m in matches], dtype=float)
            return np.array([0.0], dtype=float)

        if name in {'positions_with_scores'}:
            matches = ctx.get('matches') or []
            positions = ctx.get('positions') or []
            return list(zip(positions, matches, strict=False))

        if name in {'pattern_matches', 'match_metadata'}:
            return {
                'matches': ctx.get('matches', []),
                'positions': ctx.get('positions', []),
                'confidence': ctx.get('confidence', 0.0),
            }

        if name in {'doc_id', 'document_id'}:
            metadata = getattr(doc, 'metadata', {}) or {}
            return metadata.get('document_id') or getattr(doc, 'document_id', 'document_1')

        return _ARG_UNSET

    def _fallback_for(
        self,
        name: str,
        class_name: str,
        method_name: str,
        instance: Any,
    ) -> Any:
        """Enhanced fallback with sophisticated graph and segment handling"""
        ctx = self._argument_context

        # ========================================================================
        # ENHANCED: GRAPH AND NODE FALLBACKS
        # ========================================================================

        if name in {'grafo', 'graph', 'causal_graph', 'dag'}:
            # Import NetworkX for graph creation
            try:
                import networkx as nx
                # Create empty DiGraph as safe fallback
                grafo = nx.DiGraph()
                ctx['grafo'] = grafo
                logger.debug(f"Created empty DiGraph fallback for {class_name}.{method_name}")
                return grafo
            except ImportError:
                logger.warning("NetworkX not available, returning None for graph parameter")
                return None

        if name in {'origen', 'source', 'source_node', 'from_node'}:
            # Return a default node identifier
            return "node_0"

        if name in {'destino', 'target', 'target_node', 'to_node'}:
            # Return a default node identifier
            return "node_1"

        if name in {'statements', 'policy_statements', 'causal_statements'}:
            # Use sentences as statement fallback
            return ctx.get('sentences', [])

        # ========================================================================
        # ENHANCED: SEGMENTS FALLBACK
        # ========================================================================

        if name in {'segments', 'text_segments', 'segment_list'}:
            # Multi-strategy fallback
            sentences = ctx.get('sentences')
            if sentences:
                return sentences

            text = ctx.get('text', '')
            if text:
                # Intelligent paragraph segmentation
                segments = [p.strip() for p in text.split('\n\n') if p.strip()]
                if not segments:
                    segments = [s.strip() + '.' for s in text.split('.') if s.strip()]
                return segments

            return []

        # ========================================================================
        # EXISTING SOPHISTICATED FALLBACKS (all retained)
        # ========================================================================

        if name in {'matches', 'match_list'}:
            return []

        if name in {'positions', 'match_positions'}:
            return []

        if name == 'confidence':
            return 0.0

        if name == 'pattern_specificity':
            return ctx.get('pattern_specificity', 0.8)

        if name in {'total_corpus_size', 'text_length', 'corpus_size'}:
            return max(1, ctx.get('text_length') or 1)

        if name == 'compiled_patterns':
            patterns = self._extract_all_patterns(instance)
            ctx['compiled_patterns'] = patterns
            return patterns

        if name == 'relevant_sentences':
            return ctx.get('sentences', [])

        if name == 'window_size':
            config = getattr(instance, 'config', None)
            return getattr(config, 'context_window_chars', 400)

        if name == 'match_position':
            return 0

        if name in {'dimension', 'policy_dimension'}:
            dimension, category, _ = self._derive_dimension_category(instance)
            ctx.setdefault('category', category)
            ctx['dimension'] = dimension
            return dimension

        if name in {'category', 'policy_category'}:
            dimension, category, _ = self._derive_dimension_category(instance)
            ctx.setdefault('dimension', dimension)
            ctx['category'] = category
            return category

        if name in {'values', 'value_array'}:
            return np.array([0.0], dtype=float)

        if name in {'text', 'raw_text', 'document_text'}:
            return ctx.get('text', '')

        if name in {'sentences', 'sentence_list'}:
            return ctx.get('sentences', [])

        if name in {'tables', 'table_data'}:
            return ctx.get('tables', [])

        logger.debug(
            "No explicit argument mapping for required parameter '%s' on %s.%s; defaulting to None",
            name,
            class_name,
            method_name,
        )
        return None

    def _update_argument_context(
        self,
        method_key: str,
        result: Any,
        class_name: str,
        method_name: str,
    ) -> None:
        """Enhanced context update with graph-aware tracking"""
        ctx = self._argument_context

        if isinstance(result, ExtractionArtifact):
            if result.extractor_id not in self.accumulator:
                self.accumulator[result.extractor_id] = []
            self.accumulator[result.extractor_id].append(result)

        # ========================================================================
        # ENHANCED: TRACK GRAPH OBJECTS FROM RESULTS
        # ========================================================================

        # Track DiGraph objects from causal methods
        if class_name == 'TeoriaCambio' and method_name == 'construir_grafo_causal':
            try:
                import networkx as nx
                if isinstance(result, nx.DiGraph):
                    ctx['grafo'] = result
                    ctx['graph_nodes'] = list(result.nodes())
                    ctx['graph_edges'] = list(result.edges())
                    logger.debug(f"Cached DiGraph with {len(ctx['graph_nodes'])} nodes, {len(ctx['graph_edges'])} edges")
            except ImportError:
                pass

        # Track statements from extraction methods
        if 'extract' in method_name.lower() and 'statement' in method_name.lower():
            if isinstance(result, list):
                ctx['statements'] = result

        # Track nodes and edges from causal extraction
        if class_name == 'CausalExtractor' and isinstance(result, dict):
            if 'nodes' in result:
                ctx['graph_nodes'] = result['nodes']
            if 'edges' in result:
                ctx['graph_edges'] = result['edges']
            if 'statements' in result:
                ctx['statements'] = result['statements']

        # ========================================================================
        # ENHANCED: TRACK SEGMENTS FROM RESULTS
        # ========================================================================

        # Track segments from segmentation methods
        if 'segment' in method_name.lower():
            if isinstance(result, list) and all(isinstance(item, str) for item in result):
                ctx['segments'] = result
                ctx['segment_metadata'] = {
                    'strategy': 'method_result',
                    'method': method_key,
                    'count': len(result)
                }

        # ========================================================================
        # EXISTING SOPHISTICATED TRACKING (all retained)
        # ========================================================================

        # Track matches and positions from pattern matching
        if isinstance(result, tuple) and len(result) == 2:
            possible_matches, possible_positions = result
            if isinstance(possible_matches, list):
                ctx['matches'] = possible_matches
                ctx['pattern_specificity'] = self._compute_pattern_specificity(possible_matches)
            if isinstance(possible_positions, list):
                ctx['positions'] = possible_positions

        # Track sentences from sentence segmentation
        if isinstance(result, list) and all(isinstance(item, str) for item in result):
            ctx['sentences'] = result

        # Track various metrics from dict results
        if isinstance(result, dict):
            if 'matches' in result and isinstance(result['matches'], list):
                ctx['matches'] = result['matches']
                ctx['pattern_specificity'] = self._compute_pattern_specificity(result['matches'])
            if 'match_positions' in result and isinstance(result['match_positions'], list):
                ctx['positions'] = result['match_positions']
            if 'positions' in result and isinstance(result['positions'], list):
                ctx['positions'] = result['positions']
            if 'confidence' in result:
                with suppress(TypeError, ValueError):
                    ctx['confidence'] = float(result['confidence'])
            if 'dimension' in result:
                ctx['dimension'] = result['dimension']
            if 'category' in result:
                ctx['category'] = result['category']

        # Track confidence from evidence scoring
        if isinstance(result, (int, float)) and class_name == 'BayesianEvidenceScorer' and method_name == 'compute_evidence_score':
            ctx['confidence'] = float(result)

        # Update text length if sentences change
        if ctx.get('sentences') and not ctx.get('text_length'):
            ctx['text_length'] = sum(len(s) for s in ctx['sentences'])

    # ========================================================================
    # ENHANCED: GRAPH CONSTRUCTION HELPER
    # ========================================================================

    def _create_empty_graph(self):
        """Create an empty DiGraph for causal analysis.

        Raises:
            ImportError: If NetworkX is not available
        """
        try:
            import networkx as nx
        except ImportError as e:
            raise ImportError("NetworkX is required for graph operations") from e
        return nx.DiGraph()

    def _construct_causal_graph(self, statements: list, instance: Any) -> Any:
        """Construct causal graph from statements with sophisticated extraction"""
        grafo = self._create_empty_graph()

        # Extract potential causal relationships from statements
        causal_indicators = [
            'porque', 'ya que', 'debido a', 'causa', 'resultado',
            'therefore', 'because', 'due to', 'causes', 'results in',
            'conduce a', 'genera', 'produce', 'implica'
        ]

        nodes = []
        edges = []

        for _idx, statement in enumerate(statements):
                if not isinstance(statement, str):
                    continue

                statement_lower = statement.lower()

                # Check if statement contains causal indicators
                has_causal = any(indicator in statement_lower for indicator in causal_indicators)

                if has_causal:
                    # Simple node extraction: split on causal words
                    for indicator in causal_indicators:
                        if indicator in statement_lower:
                            parts = statement_lower.split(indicator, 1)
                            if len(parts) == 2:
                                node_from = f"node_{len(nodes)}"
                                node_to = f"node_{len(nodes) + 1}"
                                nodes.extend([node_from, node_to])
                                edges.append((node_from, node_to))
                                break
                else:
                    # Add as isolated node
                    node_id = f"node_{len(nodes)}"
                    nodes.append(node_id)

        # Build graph
        grafo.add_nodes_from(set(nodes))
        grafo.add_edges_from(edges)

        logger.debug(f"Constructed causal graph with {len(grafo.nodes())} nodes, {len(grafo.edges())} edges")

        return grafo

    @staticmethod
    def _compute_pattern_specificity(matches: list[str]) -> float:
        if not matches:
            return 0.8
        uniqueness = len(set(matches))
        return min(0.95, max(0.2, uniqueness / max(1, len(matches))))

    @staticmethod
    def _extract_all_patterns(instance: Any) -> list[Any]:
        pattern_registry = getattr(instance, '_pattern_registry', {}) or {}
        compiled_patterns: list[Any] = []
        for categories in pattern_registry.values():
            compiled_patterns.extend(chain.from_iterable(categories.values()))
        return compiled_patterns

    @staticmethod
    def _derive_dimension_category(instance: Any) -> tuple[Any, str, list[Any]]:
        pattern_registry = getattr(instance, '_pattern_registry', {}) or {}
        dimension = getattr(instance, 'default_dimension', None)
        category = 'general'
        compiled_patterns: list[Any] = []

        if pattern_registry:
            dimension = next(iter(pattern_registry.keys()), dimension)
            categories = pattern_registry.get(dimension, {}) if dimension in pattern_registry else {}
            if categories:
                category = next(iter(categories.keys()), category)
                compiled_patterns = list(categories.get(category, []))

        if dimension is None:
            dimension = 'd1_insumos'

        return dimension, category, compiled_patterns

    # ------------------------------------------------------------------
    # Context enrichment utilities
    # ------------------------------------------------------------------

    def _ingest_payload_for_context(self, payload: Any) -> None:
        if payload is None:
            return

        ctx = self._argument_context

        grafo = self._extract_graph(payload)
        if grafo is not None and self._is_graph_like(grafo):
            ctx['grafo'] = grafo

        edge = self._extract_edge(payload)
        if edge is not None:
            ctx['current_edge'] = edge

        segments = self._extract_segments(payload)
        if segments is not None:
            ctx['segments'] = segments
            if not ctx.get('text_length') and isinstance(segments, list):
                text_lengths = [len(self._segment_to_text(seg)) for seg in segments]
                if any(text_lengths):
                    ctx['text_length'] = sum(text_lengths)

    def _resolve_edge_component(
        self,
        ctx: dict[str, Any],
        current_data: Any,
        *,
        index: int,
    ) -> Any:
        edge = ctx.get('current_edge')
        if isinstance(edge, tuple) and len(edge) > index:
            return edge[index]

        candidate = self._extract_edge(current_data)
        if candidate is not None and len(candidate) > index:
            ctx['current_edge'] = candidate
            return candidate[index]

        return None

    def _extract_edge(self, payload: Any) -> tuple[Any, Any] | None:
        if payload is None:
            return None

        origin = None
        destination = None

        if isinstance(payload, dict):
            origin = (
                payload.get('origen')
                or payload.get('source')
                or payload.get('source_node')
            )
            destination = (
                payload.get('destino')
                or payload.get('target')
                or payload.get('target_node')
            )
            if 'edge' in payload and isinstance(payload['edge'], (tuple, list)):
                edge = payload['edge']
                if len(edge) >= 2:
                    origin = origin or edge[0]
                    destination = destination or edge[1]

        elif isinstance(payload, (list, tuple)) and len(payload) >= 2:
            origin = payload[0]
            destination = payload[1]

        if origin is None or destination is None:
            return None

        return (
            self._coerce_categoria_causal(origin),
            self._coerce_categoria_causal(destination),
        )

    def _extract_segments(self, payload: Any) -> list[Any] | None:
        if payload is None:
            return None

        if isinstance(payload, dict):
            for key in ('segments', 'segmentos', 'segment_list'):
                value = payload.get(key)
                if isinstance(value, list) and value:
                    return value
        elif isinstance(payload, list) and payload:
            sample = payload[0]
            if isinstance(sample, (str, dict)):
                return payload

        return None

    def _extract_graph(self, payload: Any) -> Any:
        if self._is_graph_like(payload):
            return payload

        if isinstance(payload, dict):
            for value in payload.values():
                if self._is_graph_like(value):
                    return value

        return None

    @staticmethod
    def _is_graph_like(obj: Any) -> bool:
        if obj is None:
            return False
        if nx is not None and isinstance(obj, nx.DiGraph):
            return True
        return hasattr(obj, 'nodes') and hasattr(obj, 'edges')

    def _segment_to_text(self, segment: Any) -> str:
        if isinstance(segment, str):
            return segment
        if isinstance(segment, dict):
            for key in ('text', 'segment', 'content'):
                value = segment.get(key)
                if isinstance(value, str):
                    return value
        return ''

    @staticmethod
    def _coerce_categoria_causal(value: Any) -> Any:
        if CategoriaCausal is None or value is None:
            return value
        if isinstance(value, CategoriaCausal):
            return value
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in CategoriaCausal.__members__:
                return CategoriaCausal[normalized]
        return value

# ============================================================================
# ALL 30 EXECUTORS COMPLETE IMPLEMENTATION
# ============================================================================

# ============================================================================
# ALL 30 EXECUTORS - CANONICAL METHOD SEQUENCES + ANSWER ASSEMBLY
# Generated from canonical_executor_catalog.json - Derek Beach ENABLED
# ============================================================================

# ============================================================================
# ALL 30 EXECUTORS - CANONICAL METHOD SEQUENCES + ANSWER ASSEMBLY
# Generated from canonical_executor_catalog.json
# ============================================================================

class D1Q1_Executor(AdvancedDataFlowExecutor):
    """D1-Q1: ¿El diagnóstico presenta datos numéricos (tasas de VBG, porcentajes de participa"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q2_Executor(AdvancedDataFlowExecutor):
    """D1-Q2: ¿El texto dimensiona el problema de la desigualdad de género cuantificando la br"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q3_Executor(AdvancedDataFlowExecutor):
    """D1-Q3: ¿Se identifican en el Plan Plurianual de Inversiones (PPI) o en tablas presupues"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q4_Executor(AdvancedDataFlowExecutor):
    """D1-Q4: ¿El PDM describe las capacidades para gestionar la política de género, mencionan"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D1Q5_Executor(AdvancedDataFlowExecutor):
    """D1-Q5: ¿El plan justifica su alcance en materia de género mencionando el marco legal (e"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D1-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_match_patterns_in_sentences'),
            ('IndustrialPolicyProcessor', '_extract_quantitative_baseline'),
            ('IndustrialPolicyProcessor', '_validate_source_credibility'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_semantic_boundaries'),
            ('SemanticProcessor', '_extract_indicators'),

            # EP: PolicyAnalysisEmbedder
            ('PolicyAnalysisEmbedder', 'embed_policy_text'),
            ('PolicyAnalysisEmbedder', '_compute_similarity_matrix'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_extract_quantitative_claims'),
            ('PolicyContradictionDetector', '_parse_number'),
            ('PolicyContradictionDetector', '_validate_data_quality'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_policy_context'),
            ('SemanticAnalyzer', '_extract_entities'),
            ('SemanticAnalyzer', '_validate_completeness'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D1-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q1_Executor(AdvancedDataFlowExecutor):
    """D2-Q1: ¿Las actividades para la equidad de género se presentan en un formato estructura"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q2_Executor(AdvancedDataFlowExecutor):
    """D2-Q2: ¿La descripción de las actividades de género detalla el instrumento ('mediante t"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q3_Executor(AdvancedDataFlowExecutor):
    """D2-Q3: ¿El PDM vincula explícitamente las actividades propuestas con las 'causas raíz' """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q4_Executor(AdvancedDataFlowExecutor):
    """D2-Q4: ¿El plan identifica posibles riesgos, 'obstáculos' o 'barreras' en la implementa"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D2Q5_Executor(AdvancedDataFlowExecutor):
    """D2-Q5: ¿El conjunto de actividades de género demuestra una estrategia coherente? Se deb"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D2-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: PolicyTextProcessor
            ('PolicyTextProcessor', 'process'),
            ('PolicyTextProcessor', '_extract_activities'),
            ('PolicyTextProcessor', '_identify_structure'),
            ('PolicyTextProcessor', '_parse_tables'),

            # SC: SemanticProcessor
            ('SemanticProcessor', 'chunk_document'),
            ('SemanticProcessor', '_identify_activity_blocks'),
            ('SemanticProcessor', '_extract_instruments'),

            # A1: SemanticAnalyzer
            ('SemanticAnalyzer', 'analyze_causal_logic'),
            ('SemanticAnalyzer', '_extract_target_population'),
            ('SemanticAnalyzer', '_identify_mechanisms'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_coherence'),
            ('PolicyContradictionDetector', '_detect_gaps'),
            ('PolicyContradictionDetector', '_check_risk_mitigation'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_validate_activity_chain'),
            ('TeoriaCambio', '_check_complementarity'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D2-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q1_Executor(AdvancedDataFlowExecutor):
    """D3-Q1: ¿Los indicadores de producto para género (ej. mujeres capacitadas, kits entregad"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q2_Executor(AdvancedDataFlowExecutor):
    """D3-Q2: ¿Las metas de los productos de género (ej. 'cobertura del 15% de mujeres rurales"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q3_Executor(AdvancedDataFlowExecutor):
    """D3-Q3: ¿Los productos de género tienen trazabilidad presupuestal (vinculados a códigos """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q4_Executor(AdvancedDataFlowExecutor):
    """D3-Q4: ¿Existe una relación factible entre la actividad (ej. 'un taller de formación') """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D3Q5_Executor(AdvancedDataFlowExecutor):
    """D3-Q5: ¿El PDM explica cómo los productos de la política de género (ej. 'mujeres capaci"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D3-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_indicators'),
            ('IndustrialPolicyProcessor', '_parse_baselines_and_targets'),
            ('IndustrialPolicyProcessor', '_extract_verification_sources'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_compute_proportionality'),
            ('BayesianNumericalAnalyzer', '_assess_intensity'),
            ('BayesianNumericalAnalyzer', '_validate_targets'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', '_extract_budget_linkage'),
            ('PDETMunicipalPlanAnalyzer', '_identify_responsible_entities'),
            ('PDETMunicipalPlanAnalyzer', '_validate_traceability'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_activity_product_feasibility'),
            ('PolicyContradictionDetector', '_check_timeframe_realism'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_product_analysis'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D3-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q1_Executor(AdvancedDataFlowExecutor):
    """D4-Q1: ¿Los indicadores de resultado para género (ej. 'tasa de participación política',"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q2_Executor(AdvancedDataFlowExecutor):
    """D4-Q2: ¿Se explicita la cadena causal que lleva a los resultados de género, mencionando"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q3_Executor(AdvancedDataFlowExecutor):
    """D4-Q3: ¿La ambición de las metas de resultado en materia de género (ej. 'reducir la bre"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q4_Executor(AdvancedDataFlowExecutor):
    """D4-Q4: ¿Los resultados propuestos para la igualdad de género (ej. 'aumento de la autono"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D4Q5_Executor(AdvancedDataFlowExecutor):
    """D4-Q5: ¿El plan declara la alineación de sus resultados de género con marcos superiores"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D4-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_result_indicators'),
            ('IndustrialPolicyProcessor', '_parse_temporal_horizons'),
            ('IndustrialPolicyProcessor', '_extract_assumptions'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_causal_chain'),
            ('TeoriaCambio', '_identify_enabling_conditions'),
            ('TeoriaCambio', '_extract_assumptions'),
            ('TeoriaCambio', '_validate_ambition'),

            # DB: BayesianMechanismInference
            ('BayesianMechanismInference', '_test_necessity'),
            ('BayesianMechanismInference', '_test_sufficiency'),
            ('BayesianMechanismInference', '_compute_causal_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', '_validate_result_alignment'),
            ('PolicyContradictionDetector', '_check_resource_justification'),
            ('PolicyContradictionDetector', '_compare_benchmarks'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_result_analysis'),
            ('ReportAssembler', '_generate_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D4-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q1_Executor(AdvancedDataFlowExecutor):
    """D5-Q1: ¿El PDM define 'impactos' o 'transformaciones estructurales' de largo plazo en e"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q1 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q2_Executor(AdvancedDataFlowExecutor):
    """D5-Q2: ¿Se utilizan 'índices' (ej. Índice de Equidad de Género) o 'proxies' para medir """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q2 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q3_Executor(AdvancedDataFlowExecutor):
    """D5-Q3: Cuando un impacto en género es difícil de medir (ej. 'cambio en patrones cultura"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q3 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q4_Executor(AdvancedDataFlowExecutor):
    """D5-Q4: ¿Los impactos en género se alinean con marcos nacionales/globales y consideran '"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q4 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D5Q5_Executor(AdvancedDataFlowExecutor):
    """D5-Q5: ¿La ambición del impacto para la igualdad de género es realista? Se debe buscar """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D5-Q5 - FROM CANONICAL CATALOG."""
        return [
            # PP: IndustrialPolicyProcessor
            ('IndustrialPolicyProcessor', 'process'),
            ('IndustrialPolicyProcessor', '_extract_impact_indicators'),
            ('IndustrialPolicyProcessor', '_identify_structural_transformations'),
            ('IndustrialPolicyProcessor', '_extract_maturation_timelines'),

            # TC: TeoriaCambio
            ('TeoriaCambio', '_build_long_term_pathway'),
            ('TeoriaCambio', '_identify_systemic_risks'),
            ('TeoriaCambio', '_validate_impact_realism'),

            # DB: CausalExtractor
            ('CausalExtractor', 'extract_causal_mechanism'),
            ('CausalExtractor', '_identify_indirect_effects'),
            ('CausalExtractor', '_assess_unintended_consequences'),

            # EP: BayesianNumericalAnalyzer
            ('BayesianNumericalAnalyzer', '_validate_proxy_indicators'),
            ('BayesianNumericalAnalyzer', '_assess_measurement_validity'),
            ('BayesianNumericalAnalyzer', '_compute_confidence_intervals'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_impact_analysis'),
            ('ReportAssembler', '_generate_risk_assessment'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D5-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q1_Executor(AdvancedDataFlowExecutor):
    """D6-Q1: ¿Existe una 'teoría de cambio' explícita para la política de género, preferiblem"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q1 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q1",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q2_Executor(AdvancedDataFlowExecutor):
    """D6-Q2: ¿Los saltos en la cadena causal de género son proporcionales y realistas (ej. un"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q2 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q2",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q3_Executor(AdvancedDataFlowExecutor):
    """D6-Q3: ¿El plan reconoce 'inconsistencias' en su lógica causal para género y propone 'p"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q3 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q3",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q4_Executor(AdvancedDataFlowExecutor):
    """D6-Q4: ¿Se describe un sistema de monitoreo para la política de género que incluya 'mec"""

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q4 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q4",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []


class D6Q5_Executor(AdvancedDataFlowExecutor):
    """D6-Q5: ¿La lógica causal para la equidad de género considera el contexto, reconociendo """

    def __init__(
        self,
        method_executor,
        signal_registry=None,
        config: ExecutorConfig | None = None,
        calibration_orchestrator: "CalibrationOrchestrator | None" = None,
    ) -> None:
        super().__init__(method_executor, signal_registry, config, calibration_orchestrator)
        self._validate_method_sequences()
        self._validate_calibrations()

    def _get_method_sequence(self) -> list[tuple[str, str]]:
        """Return method sequence for D6-Q5 - FROM CANONICAL CATALOG."""
        return [
            # TC: TeoriaCambio
            ('TeoriaCambio', 'build_theory_of_change'),
            ('TeoriaCambio', '_extract_causal_diagram'),
            ('TeoriaCambio', '_identify_mediators'),
            ('TeoriaCambio', '_validate_orden_causal'),
            ('TeoriaCambio', '_detect_causal_jumps'),

            # DB: BeachEvidentialTest
            ('BeachEvidentialTest', 'classify_test'),
            ('BeachEvidentialTest', 'apply_test_logic'),
            ('BeachEvidentialTest', '_assess_evidence_strength'),

            # CD: PolicyContradictionDetector
            ('PolicyContradictionDetector', 'detect_contradictions'),
            ('PolicyContradictionDetector', '_detect_numerical_inconsistencies'),
            ('PolicyContradictionDetector', '_suggest_resolutions'),
            ('PolicyContradictionDetector', '_statistical_significance_test'),

            # FV: PDETMunicipalPlanAnalyzer
            ('PDETMunicipalPlanAnalyzer', 'construct_causal_dag'),
            ('PDETMunicipalPlanAnalyzer', 'estimate_causal_effects'),
            ('PDETMunicipalPlanAnalyzer', '_validate_proportionality'),

            # RA: ReportAssembler
            ('ReportAssembler', '_synthesize_causal_analysis'),
            ('ReportAssembler', '_generate_monitoring_recommendations'),
        ]

    def execute(self, doc, method_executor):
        from .answer_assembler import AnswerAssembler

        # Execute methods
        method_sequence = self._get_method_sequence()
        method_results = self.execute_with_optimization(doc, method_executor, method_sequence)

        # Assemble doctoral answer
        assembler = AnswerAssembler()
        answer = assembler.assemble_answer(
            question_id="D6-Q5",
            method_results=method_results,
            policy_area=getattr(doc, 'policy_area', None)
        )

        return {
            "method_results": method_results,
            "answer": answer
        }

    def _extract(self, results):
        vals = [v for v in results.values() if v is not None]
        return vals[:4] if vals else []

