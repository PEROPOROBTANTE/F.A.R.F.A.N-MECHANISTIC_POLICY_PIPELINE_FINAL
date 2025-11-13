"""Compatibility package for concurrency utilities.

IMPORTANT: This is a COMPATIBILITY LAYER for backward compatibility only.
The real concurrency implementation is in src/saaaaaa/concurrency/.

New code should import directly from saaaaaa.concurrency, not from this
compatibility layer.
"""
from __future__ import annotations

from pathlib import Path

# Add src to path for development environments
_SRC_PATH = Path(__file__).resolve().parent.parent / "src"
if _SRC_PATH.exists():  # pragma: no cover - executed at import time
    src_str = str(_SRC_PATH)
from saaaaaa.concurrency.concurrency import (  # noqa: F401, E402
    TaskExecutionError,
    TaskMetrics,
    TaskResult,
    TaskStatus,
    WorkerPool,
    WorkerPoolConfig,
)

__all__ = [
    "TaskExecutionError",
    "TaskMetrics",
    "TaskResult",
    "TaskStatus",
    "WorkerPool",
    "WorkerPoolConfig",
]
