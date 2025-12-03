"""
Memory Safety Guards for Executor System

Provides systematic memory safety across all executors processing large objects
(entities, DAGs, causal effects, etc.) with:
- Size estimation for Python objects and JSON serialization
- Configurable limits per executor type
- Memory pressure detection using psutil
- Fallback strategies (sampling, truncation) with logging and metrics
"""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ExecutorType(Enum):
    """Executor classification for memory limit configuration."""

    ENTITY = "entity"
    DAG = "dag"
    CAUSAL_EFFECTS = "causal_effects"
    SEMANTIC = "semantic"
    FINANCIAL = "financial"
    GENERIC = "generic"


@dataclass
class MemorySafetyConfig:
    """Configuration for memory safety per executor type."""

    entity_limit_mb: float = 1.0
    dag_limit_mb: float = 5.0
    causal_effects_limit_mb: float = 10.0
    semantic_limit_mb: float = 2.0
    financial_limit_mb: float = 2.0
    generic_limit_mb: float = 5.0

    memory_pressure_threshold_pct: float = 80.0
    enable_pressure_detection: bool = True
    enable_auto_sampling: bool = True
    enable_auto_truncation: bool = True

    max_list_elements: int = 1000
    max_string_length: int = 100_000
    max_dict_keys: int = 500

    def get_limit_bytes(self, executor_type: ExecutorType) -> int:
        """Get memory limit in bytes for executor type."""
        limits = {
            ExecutorType.ENTITY: self.entity_limit_mb,
            ExecutorType.DAG: self.dag_limit_mb,
            ExecutorType.CAUSAL_EFFECTS: self.causal_effects_limit_mb,
            ExecutorType.SEMANTIC: self.semantic_limit_mb,
            ExecutorType.FINANCIAL: self.financial_limit_mb,
            ExecutorType.GENERIC: self.generic_limit_mb,
        }
        return int(limits[executor_type] * 1024 * 1024)


@dataclass
class MemoryMetrics:
    """Memory usage metrics for monitoring."""

    object_size_bytes: int
    json_size_bytes: int
    pressure_pct: float | None
    was_truncated: bool
    was_sampled: bool
    fallback_strategy: str | None
    elements_before: int | None
    elements_after: int | None


class MemoryPressureDetector:
    """Detects system memory pressure to trigger fallback strategies."""

    @staticmethod
    def get_memory_pressure_pct() -> float | None:
        """Get current system memory pressure percentage (0-100).

        Returns None if psutil is not available.
        """
        if not PSUTIL_AVAILABLE:
            return None

        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            logger.warning(f"Failed to read memory pressure: {e}")
            return None

    @staticmethod
    def is_under_pressure(threshold_pct: float = 80.0) -> bool:
        """Check if system is under memory pressure."""
        pressure = MemoryPressureDetector.get_memory_pressure_pct()
        if pressure is None:
            return False
        return pressure >= threshold_pct


class ObjectSizeEstimator:
    """Estimates size of Python objects including deep structures."""

    @staticmethod
    def estimate_object_size(obj: Any) -> int:
        """Estimate size of Python object in bytes using sys.getsizeof.

        For containers, recursively estimates contents up to reasonable depth.
        """
        size = sys.getsizeof(obj)

        if isinstance(obj, dict):
            size += sum(
                ObjectSizeEstimator.estimate_object_size(k)
                + ObjectSizeEstimator.estimate_object_size(v)
                for k, v in obj.items()
            )
        elif isinstance(obj, (list, tuple, set)):
            size += sum(ObjectSizeEstimator.estimate_object_size(item) for item in obj)
        elif hasattr(obj, "__dict__"):
            size += ObjectSizeEstimator.estimate_object_size(obj.__dict__)

        return size

    @staticmethod
    def estimate_json_size(obj: Any) -> int:
        """Estimate serialized JSON size without full serialization.

        Fast approximation:
        - Strings: len(str) * 1.2 (accounting for escaping)
        - Numbers: ~20 bytes
        - Booleans/None: ~10 bytes
        - Containers: sum of contents + overhead
        """
        if obj is None:
            return 4

        if isinstance(obj, bool):
            return 5

        if isinstance(obj, int):
            return len(str(obj)) + 2

        if isinstance(obj, float):
            return 20

        if isinstance(obj, str):
            return int(len(obj) * 1.2) + 2

        if isinstance(obj, (list, tuple)):
            return 2 + sum(ObjectSizeEstimator.estimate_json_size(item) for item in obj)

        if isinstance(obj, dict):
            size = 2
            for k, v in obj.items():
                size += ObjectSizeEstimator.estimate_json_size(k) + 1
                size += ObjectSizeEstimator.estimate_json_size(v) + 1
            return size

        try:
            return len(json.dumps(obj))
        except (TypeError, ValueError):
            return sys.getsizeof(obj)


class FallbackStrategy:
    """Fallback strategies for handling objects exceeding size limits."""

    @staticmethod
    def sample_list(
        items: list[T], max_elements: int, *, preserve_order: bool = True
    ) -> list[T]:
        """Sample list to max_elements using systematic sampling.

        Args:
            items: List to sample
            max_elements: Maximum elements to keep
            preserve_order: Whether to maintain original order

        Returns:
            Sampled list
        """
        if len(items) <= max_elements:
            return items

        if preserve_order:
            step = len(items) / max_elements
            indices = [int(i * step) for i in range(max_elements)]
            return [items[i] for i in indices]

        import random

        return random.sample(items, max_elements)

    @staticmethod
    def truncate_string(s: str, max_length: int) -> str:
        """Truncate string to max_length with ellipsis."""
        if len(s) <= max_length:
            return s
        return s[: max_length - 3] + "..."

    @staticmethod
    def truncate_dict(d: dict[str, Any], max_keys: int) -> dict[str, Any]:
        """Truncate dictionary to max_keys, preserving most important keys."""
        if len(d) <= max_keys:
            return d

        priority_keys = ["id", "name", "type", "label", "value", "score", "confidence"]

        result = {}
        for key in priority_keys:
            if key in d and len(result) < max_keys:
                result[key] = d[key]

        remaining = max_keys - len(result)
        for key in d:
            if key not in result and remaining > 0:
                result[key] = d[key]
                remaining -= 1

        return result

    @staticmethod
    def apply_recursive_truncation(
        obj: Any, config: MemorySafetyConfig, depth: int = 0, max_depth: int = 10
    ) -> tuple[Any, bool]:
        """Recursively apply truncation strategies to object tree.

        Returns:
            (truncated_object, was_modified)
        """
        if depth > max_depth:
            return obj, False

        modified = False

        if isinstance(obj, str):
            if len(obj) > config.max_string_length:
                obj = FallbackStrategy.truncate_string(obj, config.max_string_length)
                modified = True

        elif isinstance(obj, list):
            if len(obj) > config.max_list_elements:
                obj = FallbackStrategy.sample_list(obj, config.max_list_elements)
                modified = True

            new_items = []
            for item in obj:
                new_item, item_modified = FallbackStrategy.apply_recursive_truncation(
                    item, config, depth + 1, max_depth
                )
                new_items.append(new_item)
                modified = modified or item_modified
            obj = new_items

        elif isinstance(obj, dict):
            if len(obj) > config.max_dict_keys:
                obj = FallbackStrategy.truncate_dict(obj, config.max_dict_keys)
                modified = True

            new_dict = {}
            for k, v in obj.items():
                new_v, v_modified = FallbackStrategy.apply_recursive_truncation(
                    v, config, depth + 1, max_depth
                )
                new_dict[k] = new_v
                modified = modified or v_modified
            obj = new_dict

        return obj, modified


class MemorySafetyGuard:
    """Main guard for memory-safe object processing."""

    def __init__(self, config: MemorySafetyConfig | None = None):
        self.config = config or MemorySafetyConfig()
        self.metrics: list[MemoryMetrics] = []

    def check_and_process(
        self, obj: Any, executor_type: ExecutorType, label: str = "object"
    ) -> tuple[Any, MemoryMetrics]:
        """Check object size and apply fallback strategies if needed.

        Args:
            obj: Object to check
            executor_type: Type of executor processing this object
            label: Human-readable label for logging

        Returns:
            (processed_object, metrics)
        """
        obj_size = ObjectSizeEstimator.estimate_object_size(obj)
        json_size = ObjectSizeEstimator.estimate_json_size(obj)
        limit_bytes = self.config.get_limit_bytes(executor_type)

        pressure_pct = None
        if self.config.enable_pressure_detection:
            pressure_pct = MemoryPressureDetector.get_memory_pressure_pct()

        was_truncated = False
        was_sampled = False
        fallback_strategy = None
        elements_before = self._count_elements(obj)

        under_pressure = (
            pressure_pct is not None
            and pressure_pct >= self.config.memory_pressure_threshold_pct
        )

        if obj_size > limit_bytes or json_size > limit_bytes or under_pressure:
            reason = []
            if obj_size > limit_bytes:
                reason.append(
                    f"object size {obj_size / (1024*1024):.2f}MB exceeds {limit_bytes / (1024*1024):.2f}MB"
                )
            if json_size > limit_bytes:
                reason.append(
                    f"JSON size {json_size / (1024*1024):.2f}MB exceeds {limit_bytes / (1024*1024):.2f}MB"
                )
            if under_pressure:
                reason.append(
                    f"memory pressure {pressure_pct:.1f}% >= {self.config.memory_pressure_threshold_pct}%"
                )

            logger.warning(
                f"Memory safety triggered for {label} ({executor_type.value}): {'; '.join(reason)}"
            )

            if self.config.enable_auto_truncation:
                obj, was_truncated = FallbackStrategy.apply_recursive_truncation(
                    obj, self.config
                )
                fallback_strategy = "truncation"

                obj_size = ObjectSizeEstimator.estimate_object_size(obj)
                json_size = ObjectSizeEstimator.estimate_json_size(obj)
                logger.info(
                    f"Applied truncation to {label}: "
                    f"new size {obj_size / (1024*1024):.2f}MB object, "
                    f"{json_size / (1024*1024):.2f}MB JSON"
                )

        elements_after = self._count_elements(obj)

        metrics = MemoryMetrics(
            object_size_bytes=obj_size,
            json_size_bytes=json_size,
            pressure_pct=pressure_pct,
            was_truncated=was_truncated,
            was_sampled=was_sampled,
            fallback_strategy=fallback_strategy,
            elements_before=elements_before,
            elements_after=elements_after,
        )

        self.metrics.append(metrics)
        return obj, metrics

    def _count_elements(self, obj: Any) -> int | None:
        """Count elements in container objects."""
        if isinstance(obj, (list, tuple)):
            return len(obj)
        if isinstance(obj, dict):
            return len(obj)
        return None

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get summary of all memory operations."""
        if not self.metrics:
            return {
                "total_operations": 0,
                "truncations": 0,
                "samplings": 0,
                "avg_object_size_mb": 0.0,
                "avg_json_size_mb": 0.0,
                "max_object_size_mb": 0.0,
                "max_json_size_mb": 0.0,
            }

        return {
            "total_operations": len(self.metrics),
            "truncations": sum(1 for m in self.metrics if m.was_truncated),
            "samplings": sum(1 for m in self.metrics if m.was_sampled),
            "avg_object_size_mb": sum(m.object_size_bytes for m in self.metrics)
            / len(self.metrics)
            / (1024 * 1024),
            "avg_json_size_mb": sum(m.json_size_bytes for m in self.metrics)
            / len(self.metrics)
            / (1024 * 1024),
            "max_object_size_mb": max(m.object_size_bytes for m in self.metrics)
            / (1024 * 1024),
            "max_json_size_mb": max(m.json_size_bytes for m in self.metrics)
            / (1024 * 1024),
            "pressure_samples": [
                m.pressure_pct for m in self.metrics if m.pressure_pct is not None
            ],
        }


def create_default_guard() -> MemorySafetyGuard:
    """Create memory safety guard with default configuration."""
    return MemorySafetyGuard(MemorySafetyConfig())


__all__ = [
    "ExecutorType",
    "MemorySafetyConfig",
    "MemoryMetrics",
    "MemoryPressureDetector",
    "ObjectSizeEstimator",
    "FallbackStrategy",
    "MemorySafetyGuard",
    "create_default_guard",
]
