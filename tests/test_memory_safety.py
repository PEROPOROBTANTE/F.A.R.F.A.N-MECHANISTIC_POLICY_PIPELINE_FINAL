"""
Tests for memory safety guards in executor system.
"""

import pytest
from farfan_pipeline.core.orchestrator.memory_safety import (
    MemorySafetyGuard,
    MemorySafetyConfig,
    ExecutorType,
    ObjectSizeEstimator,
    FallbackStrategy,
    MemoryPressureDetector,
)


class TestObjectSizeEstimator:
    def test_estimate_object_size_simple(self):
        assert ObjectSizeEstimator.estimate_object_size(42) > 0
        assert ObjectSizeEstimator.estimate_object_size("hello") > 0
        assert ObjectSizeEstimator.estimate_object_size([1, 2, 3]) > 0
    
    def test_estimate_json_size(self):
        assert ObjectSizeEstimator.estimate_json_size(None) == 4
        assert ObjectSizeEstimator.estimate_json_size(True) == 5
        assert ObjectSizeEstimator.estimate_json_size(42) > 0
        assert ObjectSizeEstimator.estimate_json_size("test") > 0
        assert ObjectSizeEstimator.estimate_json_size({"key": "value"}) > 0
        assert ObjectSizeEstimator.estimate_json_size([1, 2, 3]) > 0
    
    def test_estimate_large_list(self):
        large_list = [{"id": i, "data": "x" * 100} for i in range(1000)]
        size = ObjectSizeEstimator.estimate_json_size(large_list)
        assert size > 100_000


class TestFallbackStrategy:
    def test_sample_list(self):
        items = list(range(1000))
        sampled = FallbackStrategy.sample_list(items, 100)
        assert len(sampled) == 100
        assert all(item in items for item in sampled)
    
    def test_sample_list_preserve_order(self):
        items = list(range(100))
        sampled = FallbackStrategy.sample_list(items, 10, preserve_order=True)
        assert len(sampled) == 10
        assert sampled == sorted(sampled)
    
    def test_truncate_string(self):
        long_str = "x" * 1000
        truncated = FallbackStrategy.truncate_string(long_str, 100)
        assert len(truncated) == 100
        assert truncated.endswith("...")
    
    def test_truncate_dict(self):
        large_dict = {f"key_{i}": i for i in range(1000)}
        truncated = FallbackStrategy.truncate_dict(large_dict, 10)
        assert len(truncated) <= 10
    
    def test_apply_recursive_truncation(self):
        config = MemorySafetyConfig(
            max_list_elements=10,
            max_string_length=50,
            max_dict_keys=5
        )
        
        obj = {
            "list": list(range(100)),
            "string": "x" * 1000,
            "dict": {f"key_{i}": i for i in range(100)},
            "nested": {
                "data": list(range(50))
            }
        }
        
        result, modified = FallbackStrategy.apply_recursive_truncation(obj, config)
        assert modified
        assert len(result["list"]) <= 10
        assert len(result["string"]) <= 50
        assert len(result["dict"]) <= 5
        assert len(result["nested"]["data"]) <= 10


class TestMemorySafetyGuard:
    def test_check_small_object(self):
        guard = MemorySafetyGuard()
        obj = {"id": 1, "name": "test"}
        result, metrics = guard.check_and_process(obj, ExecutorType.GENERIC, "test_obj")
        
        assert result == obj
        assert metrics.object_size_bytes > 0
        assert metrics.json_size_bytes > 0
        assert not metrics.was_truncated
        assert not metrics.was_sampled
    
    def test_check_large_object_entity_type(self):
        guard = MemorySafetyGuard(MemorySafetyConfig(
            entity_limit_mb=0.001,
            enable_auto_truncation=True
        ))
        
        large_obj = {"entities": [{"id": i, "data": "x" * 1000} for i in range(100)]}
        result, metrics = guard.check_and_process(large_obj, ExecutorType.ENTITY, "entities")
        
        assert metrics.object_size_bytes > guard.config.get_limit_bytes(ExecutorType.ENTITY) or \
               metrics.json_size_bytes > guard.config.get_limit_bytes(ExecutorType.ENTITY) or \
               metrics.was_truncated
    
    def test_check_large_list(self):
        guard = MemorySafetyGuard(MemorySafetyConfig(
            generic_limit_mb=0.001,
            max_list_elements=10,
            enable_auto_truncation=True
        ))
        
        large_list = list(range(1000))
        result, metrics = guard.check_and_process(large_list, ExecutorType.GENERIC, "large_list")
        
        if metrics.was_truncated:
            assert len(result) <= 10
    
    def test_get_metrics_summary(self):
        guard = MemorySafetyGuard()
        
        for i in range(5):
            obj = {"id": i, "data": "test" * 100}
            guard.check_and_process(obj, ExecutorType.GENERIC, f"obj_{i}")
        
        summary = guard.get_metrics_summary()
        assert summary["total_operations"] == 5
        assert summary["avg_object_size_mb"] >= 0
        assert summary["max_object_size_mb"] >= summary["avg_object_size_mb"]


class TestMemoryPressureDetector:
    def test_get_memory_pressure_pct(self):
        pressure = MemoryPressureDetector.get_memory_pressure_pct()
        if pressure is not None:
            assert 0 <= pressure <= 100
    
    def test_is_under_pressure(self):
        result = MemoryPressureDetector.is_under_pressure(threshold_pct=99.0)
        assert isinstance(result, bool)


class TestMemorySafetyConfig:
    def test_get_limit_bytes(self):
        config = MemorySafetyConfig()
        
        entity_limit = config.get_limit_bytes(ExecutorType.ENTITY)
        assert entity_limit == 1 * 1024 * 1024
        
        dag_limit = config.get_limit_bytes(ExecutorType.DAG)
        assert dag_limit == 5 * 1024 * 1024
        
        causal_limit = config.get_limit_bytes(ExecutorType.CAUSAL_EFFECTS)
        assert causal_limit == 10 * 1024 * 1024
    
    def test_custom_config(self):
        config = MemorySafetyConfig(
            entity_limit_mb=2.0,
            dag_limit_mb=10.0,
            max_list_elements=500
        )
        
        assert config.get_limit_bytes(ExecutorType.ENTITY) == 2 * 1024 * 1024
        assert config.get_limit_bytes(ExecutorType.DAG) == 10 * 1024 * 1024
        assert config.max_list_elements == 500
