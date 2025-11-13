"""Test thread safety of ExecutionMetrics in executors.py."""
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest


def test_metrics_record_execution_thread_safe():
    """Test that record_execution is thread-safe under concurrent updates."""
    from saaaaaa.core.orchestrator.executors import ExecutionMetrics
    
    metrics = ExecutionMetrics()
    
    def record_multiple():
        """Record multiple executions."""
        for _ in range(100):
            metrics.record_execution(success=True, execution_time=0.1, method_key="test_method")
    
    # Run 100 threads, each recording 100 executions
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(record_multiple) for _ in range(100)]
        for future in futures:
            future.result()
    
    # Should have exactly 10,000 total executions
    assert metrics.total_executions == 10000
    assert metrics.successful_executions == 10000
    assert metrics.failed_executions == 0


def test_metrics_record_quantum_optimization_thread_safe():
    """Test that record_quantum_optimization is thread-safe."""
    from saaaaaa.core.orchestrator.executors import ExecutionMetrics
    
    metrics = ExecutionMetrics()
    
    def record_multiple():
        for _ in range(100):
            metrics.record_quantum_optimization(convergence_time=0.05)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(record_multiple) for _ in range(50)]
        for future in futures:
            future.result()
    
    # Should have exactly 5,000 quantum optimizations
    assert metrics.quantum_optimizations == 5000
    assert len(metrics.quantum_convergence_times) == 5000


def test_metrics_record_meta_learner_selection_thread_safe():
    """Test that record_meta_learner_selection is thread-safe."""
    from saaaaaa.core.orchestrator.executors import ExecutionMetrics
    
    metrics = ExecutionMetrics()
    
    def record_multiple():
        for i in range(100):
            metrics.record_meta_learner_selection(strategy_idx=i % 5)
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(record_multiple) for _ in range(50)]
        for future in futures:
            future.result()
    
    # Each strategy (0-4) should have 1000 selections
    for i in range(5):
        assert metrics.meta_learner_strategy_selections[i] == 1000


def test_metrics_concurrent_mixed_operations():
    """Test that mixed operations are thread-safe."""
    from saaaaaa.core.orchestrator.executors import ExecutionMetrics
    
    metrics = ExecutionMetrics()
    
    def record_executions():
        for _ in range(100):
            metrics.record_execution(success=True, execution_time=0.1)
    
    def record_optimizations():
        for _ in range(100):
            metrics.record_quantum_optimization(convergence_time=0.05)
    
    def record_retries():
        for _ in range(100):
            metrics.record_retry()
    
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = []
        for _ in range(10):
            futures.append(executor.submit(record_executions))
            futures.append(executor.submit(record_optimizations))
            futures.append(executor.submit(record_retries))
        
        for future in futures:
            future.result()
    
    assert metrics.total_executions == 1000
    assert metrics.quantum_optimizations == 1000
    assert metrics.retry_attempts == 1000
