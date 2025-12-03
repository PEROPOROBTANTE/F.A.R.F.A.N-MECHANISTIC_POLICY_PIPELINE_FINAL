"""Adaptive Resource Management System.

Provides dynamic resource allocation, degradation strategies, circuit breakers,
and priority-based resource allocation for policy analysis executors.

This module integrates with ResourceLimits to provide:
- Real-time resource monitoring and adaptive allocation
- Graceful degradation strategies when resources are constrained
- Circuit breakers for memory-intensive executors
- Priority-based resource allocation (critical executors first)
- Comprehensive observability with alerts
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.core import ResourceLimits

logger = logging.getLogger(__name__)


class ResourcePressureLevel(Enum):
    """Resource pressure severity levels."""
    
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class ExecutorPriority(Enum):
    """Priority levels for executor resource allocation."""
    
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ExecutorMetrics:
    """Metrics for individual executor performance and resource usage."""
    
    executor_id: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0
    avg_duration_ms: float = 0.0
    last_execution_time: datetime | None = None
    memory_samples: list[float] = field(default_factory=list)
    duration_samples: list[float] = field(default_factory=list)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    
    failure_threshold: int = 5
    timeout_seconds: float = 60.0
    half_open_timeout: float = 30.0
    memory_threshold_mb: float = 2048.0
    success_threshold: int = 3


@dataclass
class CircuitBreaker:
    """Circuit breaker for memory-intensive executors."""
    
    executor_id: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: datetime | None = None
    last_state_change: datetime | None = None
    config: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    
    def can_execute(self) -> bool:
        """Check if executor can be executed based on circuit state."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            if self.last_state_change:
                elapsed = (datetime.utcnow() - self.last_state_change).total_seconds()
                if elapsed >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(
                        f"Circuit breaker for {self.executor_id} moved to HALF_OPEN"
                    )
                    return True
            return False
        
        return True
    
    def record_success(self) -> None:
        """Record successful execution."""
        self.failure_count = 0
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.last_state_change = datetime.utcnow()
                logger.info(
                    f"Circuit breaker for {self.executor_id} closed after "
                    f"{self.success_count} successes"
                )
    
    def record_failure(self, memory_mb: float | None = None) -> None:
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        exceeded_memory = (
            memory_mb is not None and memory_mb > self.config.memory_threshold_mb
        )
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()
            logger.warning(
                f"Circuit breaker for {self.executor_id} opened from HALF_OPEN "
                f"(memory: {memory_mb}MB)"
            )
        elif (
            self.failure_count >= self.config.failure_threshold or exceeded_memory
        ):
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.utcnow()
            logger.warning(
                f"Circuit breaker for {self.executor_id} opened "
                f"(failures: {self.failure_count}, memory: {memory_mb}MB)"
            )


@dataclass
class DegradationStrategy:
    """Defines degradation behavior for resource-constrained scenarios."""
    
    name: str
    pressure_threshold: ResourcePressureLevel
    enabled: bool = True
    entity_limit_factor: float = 1.0
    disable_expensive_computations: bool = False
    use_simplified_methods: bool = False
    skip_optional_analysis: bool = False
    reduce_embedding_dims: bool = False
    applied_count: int = 0
    
    def should_apply(self, pressure: ResourcePressureLevel) -> bool:
        """Check if strategy should be applied at current pressure level."""
        if not self.enabled:
            return False
        
        pressure_values = {
            ResourcePressureLevel.NORMAL: 0,
            ResourcePressureLevel.ELEVATED: 1,
            ResourcePressureLevel.HIGH: 2,
            ResourcePressureLevel.CRITICAL: 3,
            ResourcePressureLevel.EMERGENCY: 4,
        }
        
        return pressure_values[pressure] >= pressure_values[self.pressure_threshold]


@dataclass
class ResourceAllocationPolicy:
    """Defines resource allocation priority for executors."""
    
    executor_id: str
    priority: ExecutorPriority
    min_memory_mb: float
    max_memory_mb: float
    min_workers: int
    max_workers: int
    is_memory_intensive: bool = False
    is_cpu_intensive: bool = False


@dataclass
class ResourcePressureEvent:
    """Event capturing resource pressure state changes."""
    
    timestamp: datetime
    pressure_level: ResourcePressureLevel
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    worker_count: int
    active_executors: int
    degradation_applied: list[str]
    circuit_breakers_open: list[str]
    message: str


class AdaptiveResourceManager:
    """Manages dynamic resource allocation and degradation strategies."""
    
    CRITICAL_EXECUTORS = {
        "D3-Q3": ExecutorPriority.CRITICAL,
        "D4-Q2": ExecutorPriority.CRITICAL,
        "D3-Q2": ExecutorPriority.HIGH,
        "D4-Q1": ExecutorPriority.HIGH,
        "D2-Q3": ExecutorPriority.HIGH,
    }
    
    DEFAULT_POLICIES = {
        "D3-Q3": ResourceAllocationPolicy(
            executor_id="D3-Q3",
            priority=ExecutorPriority.CRITICAL,
            min_memory_mb=256.0,
            max_memory_mb=1024.0,
            min_workers=2,
            max_workers=8,
            is_memory_intensive=True,
        ),
        "D4-Q2": ResourceAllocationPolicy(
            executor_id="D4-Q2",
            priority=ExecutorPriority.CRITICAL,
            min_memory_mb=256.0,
            max_memory_mb=1024.0,
            min_workers=2,
            max_workers=8,
            is_memory_intensive=True,
        ),
        "D3-Q2": ResourceAllocationPolicy(
            executor_id="D3-Q2",
            priority=ExecutorPriority.HIGH,
            min_memory_mb=128.0,
            max_memory_mb=512.0,
            min_workers=1,
            max_workers=6,
        ),
        "D4-Q1": ResourceAllocationPolicy(
            executor_id="D4-Q1",
            priority=ExecutorPriority.HIGH,
            min_memory_mb=128.0,
            max_memory_mb=512.0,
            min_workers=1,
            max_workers=6,
        ),
    }
    
    def __init__(
        self,
        resource_limits: ResourceLimits,
        enable_circuit_breakers: bool = True,
        enable_degradation: bool = True,
        alert_callback: Callable[[ResourcePressureEvent], None] | None = None,
    ) -> None:
        self.resource_limits = resource_limits
        self.enable_circuit_breakers = enable_circuit_breakers
        self.enable_degradation = enable_degradation
        self.alert_callback = alert_callback
        
        self.executor_metrics: dict[str, ExecutorMetrics] = {}
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.allocation_policies: dict[str, ResourceAllocationPolicy] = (
            self.DEFAULT_POLICIES.copy()
        )
        
        self.degradation_strategies = self._init_degradation_strategies()
        self.pressure_history: deque[ResourcePressureEvent] = deque(maxlen=100)
        self.current_pressure = ResourcePressureLevel.NORMAL
        
        self._lock = asyncio.Lock()
        self._active_executors: set[str] = set()
        
        logger.info("Adaptive Resource Manager initialized")
    
    def _init_degradation_strategies(self) -> list[DegradationStrategy]:
        """Initialize degradation strategies for different pressure levels."""
        return [
            DegradationStrategy(
                name="reduce_entity_limits",
                pressure_threshold=ResourcePressureLevel.ELEVATED,
                entity_limit_factor=0.8,
            ),
            DegradationStrategy(
                name="skip_optional_analysis",
                pressure_threshold=ResourcePressureLevel.HIGH,
                skip_optional_analysis=True,
            ),
            DegradationStrategy(
                name="disable_expensive_computations",
                pressure_threshold=ResourcePressureLevel.HIGH,
                disable_expensive_computations=True,
            ),
            DegradationStrategy(
                name="use_simplified_methods",
                pressure_threshold=ResourcePressureLevel.CRITICAL,
                use_simplified_methods=True,
                entity_limit_factor=0.5,
            ),
            DegradationStrategy(
                name="reduce_embedding_dimensions",
                pressure_threshold=ResourcePressureLevel.CRITICAL,
                reduce_embedding_dims=True,
            ),
            DegradationStrategy(
                name="emergency_mode",
                pressure_threshold=ResourcePressureLevel.EMERGENCY,
                entity_limit_factor=0.3,
                disable_expensive_computations=True,
                use_simplified_methods=True,
                skip_optional_analysis=True,
                reduce_embedding_dims=True,
            ),
        ]
    
    def get_or_create_circuit_breaker(
        self, executor_id: str
    ) -> CircuitBreaker:
        """Get or create circuit breaker for executor."""
        if executor_id not in self.circuit_breakers:
            config = CircuitBreakerConfig()
            
            if executor_id in self.allocation_policies:
                policy = self.allocation_policies[executor_id]
                if policy.is_memory_intensive:
                    config.memory_threshold_mb = policy.max_memory_mb * 1.5
            
            self.circuit_breakers[executor_id] = CircuitBreaker(
                executor_id=executor_id, config=config
            )
        
        return self.circuit_breakers[executor_id]
    
    def can_execute(self, executor_id: str) -> tuple[bool, str]:
        """Check if executor can be executed based on circuit breaker state."""
        if not self.enable_circuit_breakers:
            return True, "Circuit breakers disabled"
        
        breaker = self.get_or_create_circuit_breaker(executor_id)
        
        if not breaker.can_execute():
            return False, f"Circuit breaker is {breaker.state.value}"
        
        return True, "OK"
    
    async def assess_resource_pressure(self) -> ResourcePressureLevel:
        """Assess current resource pressure level."""
        usage = self.resource_limits.get_resource_usage()
        
        cpu_percent = usage.get("cpu_percent", 0.0)
        memory_percent = usage.get("memory_percent", 0.0)
        rss_mb = usage.get("rss_mb", 0.0)
        
        max_memory_mb = self.resource_limits.max_memory_mb or 4096.0
        max_cpu = self.resource_limits.max_cpu_percent
        
        memory_ratio = rss_mb / max_memory_mb
        cpu_ratio = cpu_percent / max_cpu if max_cpu else 0.0
        
        if memory_ratio >= 0.95 or cpu_ratio >= 0.95:
            pressure = ResourcePressureLevel.EMERGENCY
        elif memory_ratio >= 0.85 or cpu_ratio >= 0.85:
            pressure = ResourcePressureLevel.CRITICAL
        elif memory_ratio >= 0.75 or cpu_ratio >= 0.75:
            pressure = ResourcePressureLevel.HIGH
        elif memory_ratio >= 0.65 or cpu_ratio >= 0.65:
            pressure = ResourcePressureLevel.ELEVATED
        else:
            pressure = ResourcePressureLevel.NORMAL
        
        if pressure != self.current_pressure:
            await self._handle_pressure_change(pressure, usage)
        
        self.current_pressure = pressure
        return pressure
    
    async def _handle_pressure_change(
        self, new_pressure: ResourcePressureLevel, usage: dict[str, Any]
    ) -> None:
        """Handle resource pressure level changes."""
        degradation_applied = []
        
        for strategy in self.degradation_strategies:
            if strategy.should_apply(new_pressure):
                degradation_applied.append(strategy.name)
                strategy.applied_count += 1
        
        circuit_breakers_open = [
            executor_id
            for executor_id, breaker in self.circuit_breakers.items()
            if breaker.state == CircuitState.OPEN
        ]
        
        event = ResourcePressureEvent(
            timestamp=datetime.utcnow(),
            pressure_level=new_pressure,
            cpu_percent=usage.get("cpu_percent", 0.0),
            memory_mb=usage.get("rss_mb", 0.0),
            memory_percent=usage.get("memory_percent", 0.0),
            worker_count=int(usage.get("worker_budget", 0)),
            active_executors=len(self._active_executors),
            degradation_applied=degradation_applied,
            circuit_breakers_open=circuit_breakers_open,
            message=f"Resource pressure changed: {self.current_pressure.value} -> {new_pressure.value}",
        )
        
        self.pressure_history.append(event)
        
        logger.warning(
            f"Resource pressure: {new_pressure.value}",
            extra={
                "cpu_percent": event.cpu_percent,
                "memory_mb": event.memory_mb,
                "memory_percent": event.memory_percent,
                "degradation_applied": degradation_applied,
                "circuit_breakers_open": circuit_breakers_open,
            },
        )
        
        if self.alert_callback:
            try:
                self.alert_callback(event)
            except Exception as exc:
                logger.error(f"Alert callback failed: {exc}")
    
    def get_degradation_config(
        self, executor_id: str
    ) -> dict[str, Any]:
        """Get degradation configuration for executor at current pressure."""
        config: dict[str, Any] = {
            "entity_limit_factor": 1.0,
            "disable_expensive_computations": False,
            "use_simplified_methods": False,
            "skip_optional_analysis": False,
            "reduce_embedding_dims": False,
            "applied_strategies": [],
        }
        
        if not self.enable_degradation:
            return config
        
        for strategy in self.degradation_strategies:
            if strategy.should_apply(self.current_pressure):
                config["entity_limit_factor"] = min(
                    config["entity_limit_factor"], strategy.entity_limit_factor
                )
                config["disable_expensive_computations"] = (
                    config["disable_expensive_computations"]
                    or strategy.disable_expensive_computations
                )
                config["use_simplified_methods"] = (
                    config["use_simplified_methods"] or strategy.use_simplified_methods
                )
                config["skip_optional_analysis"] = (
                    config["skip_optional_analysis"] or strategy.skip_optional_analysis
                )
                config["reduce_embedding_dims"] = (
                    config["reduce_embedding_dims"] or strategy.reduce_embedding_dims
                )
                config["applied_strategies"].append(strategy.name)
        
        return config
    
    async def allocate_resources(
        self, executor_id: str
    ) -> dict[str, Any]:
        """Allocate resources for executor based on priority and availability."""
        await self.assess_resource_pressure()
        
        policy = self.allocation_policies.get(
            executor_id,
            ResourceAllocationPolicy(
                executor_id=executor_id,
                priority=ExecutorPriority.NORMAL,
                min_memory_mb=64.0,
                max_memory_mb=256.0,
                min_workers=1,
                max_workers=4,
            ),
        )
        
        degradation = self.get_degradation_config(executor_id)
        
        max_memory = policy.max_memory_mb * degradation["entity_limit_factor"]
        max_workers = min(
            policy.max_workers,
            max(policy.min_workers, self.resource_limits.max_workers),
        )
        
        if self.current_pressure in [
            ResourcePressureLevel.CRITICAL,
            ResourcePressureLevel.EMERGENCY,
        ]:
            if policy.priority == ExecutorPriority.CRITICAL:
                max_workers = policy.max_workers
            elif policy.priority == ExecutorPriority.HIGH:
                max_workers = max(policy.min_workers, policy.max_workers - 2)
            else:
                max_workers = policy.min_workers
        
        return {
            "max_memory_mb": max_memory,
            "max_workers": max_workers,
            "priority": policy.priority.value,
            "degradation": degradation,
        }
    
    async def start_executor_execution(
        self, executor_id: str
    ) -> dict[str, Any]:
        """Start tracking executor execution."""
        async with self._lock:
            self._active_executors.add(executor_id)
        
        allocation = await self.allocate_resources(executor_id)
        
        if executor_id not in self.executor_metrics:
            self.executor_metrics[executor_id] = ExecutorMetrics(
                executor_id=executor_id
            )
        
        return allocation
    
    async def end_executor_execution(
        self,
        executor_id: str,
        success: bool,
        duration_ms: float,
        memory_mb: float | None = None,
    ) -> None:
        """End tracking executor execution and update metrics."""
        async with self._lock:
            self._active_executors.discard(executor_id)
        
        metrics = self.executor_metrics.get(executor_id)
        if not metrics:
            return
        
        metrics.total_executions += 1
        metrics.last_execution_time = datetime.utcnow()
        
        if success:
            metrics.successful_executions += 1
            if self.enable_circuit_breakers:
                breaker = self.get_or_create_circuit_breaker(executor_id)
                breaker.record_success()
        else:
            metrics.failed_executions += 1
            if self.enable_circuit_breakers:
                breaker = self.get_or_create_circuit_breaker(executor_id)
                breaker.record_failure(memory_mb)
        
        if memory_mb is not None:
            metrics.memory_samples.append(memory_mb)
            if len(metrics.memory_samples) > 100:
                metrics.memory_samples.pop(0)
            
            metrics.avg_memory_mb = sum(metrics.memory_samples) / len(
                metrics.memory_samples
            )
            metrics.peak_memory_mb = max(
                metrics.peak_memory_mb, memory_mb
            )
        
        metrics.duration_samples.append(duration_ms)
        if len(metrics.duration_samples) > 100:
            metrics.duration_samples.pop(0)
        
        metrics.avg_duration_ms = sum(metrics.duration_samples) / len(
            metrics.duration_samples
        )
    
    def get_executor_metrics(self, executor_id: str) -> dict[str, Any]:
        """Get metrics for specific executor."""
        metrics = self.executor_metrics.get(executor_id)
        if not metrics:
            return {}
        
        success_rate = 0.0
        if metrics.total_executions > 0:
            success_rate = (
                metrics.successful_executions / metrics.total_executions
            ) * 100
        
        breaker = self.circuit_breakers.get(executor_id)
        
        return {
            "executor_id": executor_id,
            "total_executions": metrics.total_executions,
            "successful_executions": metrics.successful_executions,
            "failed_executions": metrics.failed_executions,
            "success_rate_percent": success_rate,
            "avg_memory_mb": metrics.avg_memory_mb,
            "peak_memory_mb": metrics.peak_memory_mb,
            "avg_duration_ms": metrics.avg_duration_ms,
            "last_execution": (
                metrics.last_execution_time.isoformat()
                if metrics.last_execution_time
                else None
            ),
            "circuit_breaker_state": breaker.state.value if breaker else "closed",
        }
    
    def get_resource_status(self) -> dict[str, Any]:
        """Get comprehensive resource management status."""
        usage = self.resource_limits.get_resource_usage()
        
        executor_stats = {
            executor_id: self.get_executor_metrics(executor_id)
            for executor_id in self.executor_metrics
        }
        
        active_strategies = [
            {
                "name": strategy.name,
                "threshold": strategy.pressure_threshold.value,
                "applied_count": strategy.applied_count,
                "config": {
                    "entity_limit_factor": strategy.entity_limit_factor,
                    "disable_expensive_computations": strategy.disable_expensive_computations,
                    "use_simplified_methods": strategy.use_simplified_methods,
                    "skip_optional_analysis": strategy.skip_optional_analysis,
                    "reduce_embedding_dims": strategy.reduce_embedding_dims,
                },
            }
            for strategy in self.degradation_strategies
            if strategy.should_apply(self.current_pressure)
        ]
        
        circuit_breaker_summary = {
            executor_id: {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "last_failure": (
                    breaker.last_failure_time.isoformat()
                    if breaker.last_failure_time
                    else None
                ),
            }
            for executor_id, breaker in self.circuit_breakers.items()
        }
        
        recent_pressure = list(self.pressure_history)[-10:]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_pressure": self.current_pressure.value,
            "resource_usage": usage,
            "active_executors": list(self._active_executors),
            "executor_metrics": executor_stats,
            "active_degradation_strategies": active_strategies,
            "circuit_breakers": circuit_breaker_summary,
            "recent_pressure_events": [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "level": event.pressure_level.value,
                    "cpu_percent": event.cpu_percent,
                    "memory_mb": event.memory_mb,
                    "message": event.message,
                }
                for event in recent_pressure
            ],
        }
    
    def register_allocation_policy(
        self, policy: ResourceAllocationPolicy
    ) -> None:
        """Register custom resource allocation policy for executor."""
        self.allocation_policies[policy.executor_id] = policy
        logger.info(
            f"Registered allocation policy for {policy.executor_id}: "
            f"priority={policy.priority.value}"
        )
    
    def reset_circuit_breaker(self, executor_id: str) -> bool:
        """Manually reset circuit breaker for executor."""
        breaker = self.circuit_breakers.get(executor_id)
        if not breaker:
            return False
        
        breaker.state = CircuitState.CLOSED
        breaker.failure_count = 0
        breaker.success_count = 0
        breaker.last_state_change = datetime.utcnow()
        
        logger.info(f"Circuit breaker reset for {executor_id}")
        return True
