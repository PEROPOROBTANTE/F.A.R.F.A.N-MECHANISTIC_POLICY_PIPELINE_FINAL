"""
Concurrency module for deterministic parallel execution.

This module provides a deterministic WorkerPool for parallel task execution
with controlled max_workers, backoff, abortability, and per-task instrumentation.
"""

from .concurrency import (
    TaskExecutionError,
    TaskMetrics,
    TaskResult,
    TaskStatus,
    WorkerPool,
    WorkerPoolConfig,
)

__all__ = [
    "WorkerPool",
    "TaskResult",
    "WorkerPoolConfig",
    "TaskExecutionError",
    "TaskStatus",
    "TaskMetrics",
]
