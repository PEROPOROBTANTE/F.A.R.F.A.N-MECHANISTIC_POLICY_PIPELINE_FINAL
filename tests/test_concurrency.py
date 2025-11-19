#!/usr/bin/env python3
"""
Tests for concurrency module.

Tests verify:
- Deterministic execution
- No race conditions
- Proper max_workers control
- Backoff and retry behavior
- Abortability
- Instrumentation and logging
"""

import time
import unittest
from concurrent.futures import ThreadPoolExecutor

from saaaaaa.concurrency import (
    TaskExecutionError,
    TaskStatus,
    WorkerPool,
    WorkerPoolConfig,
)

class TestWorkerPoolBasics(unittest.TestCase):
    """Test basic WorkerPool functionality."""

    def test_pool_initialization(self):
        """Test that pool initializes with correct config."""
        config = WorkerPoolConfig(
            max_workers=10,
            max_retries=2,
            task_timeout_seconds=60.0
        )
        pool = WorkerPool(config)

        self.assertEqual(pool.config.max_workers, 10)
        self.assertEqual(pool.config.max_retries, 2)
        self.assertEqual(pool.config.task_timeout_seconds, 60.0)

        pool.shutdown()

    def test_simple_task_submission(self):
        """Test submitting and executing a simple task."""
        pool = WorkerPool()

        def simple_task(x):
            return x * 2

        task_id = pool.submit_task("double_5", simple_task, args=(5,))
        result = pool.get_task_result(task_id)

        self.assertTrue(result.success)
        self.assertEqual(result.result, 10)
        self.assertIsNotNone(result.metrics)
        self.assertEqual(result.metrics.status, TaskStatus.COMPLETED)

        pool.shutdown()

    def test_multiple_tasks(self):
        """Test executing multiple tasks in parallel."""
        config = WorkerPoolConfig(max_workers=5)
        pool = WorkerPool(config)

        def square(x):
            time.sleep(0.01)  # Simulate work
            return x * x

        # Submit 10 tasks
        task_ids = []
        for i in range(10):
            task_id = pool.submit_task(f"square_{i}", square, args=(i,))
            task_ids.append(task_id)

        # Wait for all tasks
        results = pool.wait_for_all()

        self.assertEqual(len(results), 10)
        self.assertTrue(all(r.success for r in results))

        # Verify results (order may vary due to parallelism)
        result_values = sorted([r.result for r in results])
        expected = [i * i for i in range(10)]
        self.assertEqual(result_values, expected)

        pool.shutdown()

    def test_context_manager(self):
        """Test WorkerPool as context manager."""
        def dummy_task():
            return 42

        with WorkerPool() as pool:
            task_id = pool.submit_task("dummy", dummy_task)
            result = pool.get_task_result(task_id)
            self.assertTrue(result.success)
            self.assertEqual(result.result, 42)

        # Pool should be shutdown after context exit
        self.assertTrue(pool._is_shutdown)

class TestWorkerPoolRetry(unittest.TestCase):
    """Test retry and backoff behavior."""

    def test_successful_task_no_retry(self):
        """Test that successful tasks don't retry."""
        config = WorkerPoolConfig(max_retries=3)
        pool = WorkerPool(config)

        def always_succeed():
            return "success"

        task_id = pool.submit_task("no_retry", always_succeed)
        result = pool.get_task_result(task_id)

        self.assertTrue(result.success)
        self.assertEqual(result.result, "success")
        self.assertEqual(result.metrics.retries_used, 0)

        pool.shutdown()

    def test_task_retry_on_failure(self):
        """Test that failing tasks are retried."""
        config = WorkerPoolConfig(max_retries=2, backoff_base_seconds=0.01)
        pool = WorkerPool(config)

        # Counter to track attempts
        attempts = {"count": 0}

        def fail_twice_then_succeed():
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise ValueError(f"Attempt {attempts['count']} failed")
            return "success"

        task_id = pool.submit_task("retry_task", fail_twice_then_succeed)
        result = pool.get_task_result(task_id, timeout=5.0)

        self.assertTrue(result.success)
        self.assertEqual(result.result, "success")
        self.assertEqual(result.metrics.retries_used, 2)
        self.assertEqual(attempts["count"], 3)  # Initial + 2 retries

        pool.shutdown()

    def test_task_fails_after_max_retries(self):
        """Test that tasks fail after exhausting retries."""
        config = WorkerPoolConfig(max_retries=2, backoff_base_seconds=0.01)
        pool = WorkerPool(config)

        def always_fail():
            raise ValueError("Always fails")

        task_id = pool.submit_task("fail_task", always_fail)
        result = pool.get_task_result(task_id, timeout=5.0)

        self.assertFalse(result.success)
        self.assertIsInstance(result.error, TaskExecutionError)
        self.assertEqual(result.metrics.status, TaskStatus.FAILED)
        self.assertEqual(result.metrics.retries_used, 2)

        pool.shutdown()

    def test_exponential_backoff(self):
        """Test that backoff increases exponentially."""
        config = WorkerPoolConfig(
            max_retries=3,
            backoff_base_seconds=0.1,
            backoff_max_seconds=1.0
        )
        pool = WorkerPool(config)

        # Test backoff calculation
        self.assertEqual(pool._calculate_backoff_delay(0), 0.1)
        self.assertEqual(pool._calculate_backoff_delay(1), 0.2)
        self.assertEqual(pool._calculate_backoff_delay(2), 0.4)
        self.assertEqual(pool._calculate_backoff_delay(3), 0.8)

        # Should be capped at max
        self.assertEqual(pool._calculate_backoff_delay(10), 1.0)

        pool.shutdown()

class TestWorkerPoolAbort(unittest.TestCase):
    """Test abort and cancellation functionality."""

    def test_abort_pending_tasks(self):
        """Test aborting pending tasks."""
        config = WorkerPoolConfig(max_workers=2)
        pool = WorkerPool(config)

        def slow_task():
            time.sleep(1.0)
            return "done"

        # Submit many tasks to queue them up
        task_ids = []
        for i in range(10):
            task_id = pool.submit_task(f"slow_{i}", slow_task)
            task_ids.append(task_id)

        # Give some time for a few to start
        time.sleep(0.1)

        # Abort pending tasks
        cancelled_count = pool.abort_pending_tasks()

        # Should have cancelled some tasks
        self.assertGreater(cancelled_count, 0)

        pool.shutdown(wait=False, cancel_futures=True)

class TestWorkerPoolMetrics(unittest.TestCase):
    """Test metrics and instrumentation."""

    def test_task_metrics_collection(self):
        """Test that metrics are collected for each task."""
        pool = WorkerPool()

        def task_with_delay(delay):
            time.sleep(delay)
            return "done"

        task_id = pool.submit_task("delayed", task_with_delay, args=(0.05,))
        result = pool.get_task_result(task_id)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.metrics)
        self.assertEqual(result.metrics.task_id, task_id)
        self.assertEqual(result.metrics.task_name, "delayed")
        self.assertEqual(result.metrics.status, TaskStatus.COMPLETED)
        self.assertGreater(result.metrics.execution_time_ms, 0)
        self.assertIsNotNone(result.metrics.worker_id)

        pool.shutdown()

    def test_summary_metrics(self):
        """Test summary metrics aggregation."""
        config = WorkerPoolConfig(max_workers=5, max_retries=1)
        pool = WorkerPool(config)

        def success_task():
            return "ok"

        def fail_task():
            raise ValueError("fail")

        # Submit mix of successful and failing tasks
        for i in range(5):
            pool.submit_task(f"success_{i}", success_task)
        for i in range(3):
            pool.submit_task(f"fail_{i}", fail_task)

        # Wait for all
        results = pool.wait_for_all(timeout=10.0)

        # Assert results: 5 successes, 3 failures
        success_count = 0
        fail_count = 0
        for result in results:
            if isinstance(result, Exception):
                fail_count += 1
                self.assertIsInstance(result, TaskExecutionError)
            else:
                success_count += 1
                self.assertEqual(result, "ok")

        self.assertEqual(success_count, 5)
        self.assertEqual(fail_count, 3)

        # Validate results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        self.assertEqual(len(successful), 5)
        self.assertEqual(len(failed), 3)

        # Get summary
        summary = pool.get_summary_metrics()

        self.assertEqual(summary["total_tasks"], 8)
        self.assertEqual(summary["completed"], 5)
        self.assertEqual(summary["failed"], 3)
        self.assertGreater(summary["avg_execution_time_ms"], 0)
        # Failing tasks should have retried once each
        self.assertEqual(summary["total_retries"], 3)

        pool.shutdown()

class TestWorkerPoolThreadSafety(unittest.TestCase):
    """Test thread safety and no race conditions."""

    def test_concurrent_submissions(self):
        """Test submitting tasks from multiple threads."""
        pool = WorkerPool()

        task_ids = []
        lock = ThreadPoolExecutor(max_workers=5)

        def submit_tasks(start, end):
            for i in range(start, end):
                task_id = pool.submit_task(
                    f"task_{i}",
                    lambda x, val=i: val * 2,
                    args=(i,)
                )
                task_ids.append(task_id)

        # Submit from multiple threads
        futures = []
        for i in range(5):
            future = lock.submit(submit_tasks, i * 10, (i + 1) * 10)
            futures.append(future)

        # Wait for submissions
        for future in futures:
            future.result()

        lock.shutdown()

        # All 50 tasks should be submitted
        self.assertEqual(len(task_ids), 50)

        # Wait for all tasks
        results = pool.wait_for_all(timeout=10.0)
        self.assertEqual(len(results), 50)
        self.assertTrue(all(r.success for r in results))

        pool.shutdown()

    def test_no_race_conditions_in_metrics(self):
        """Test that metrics are updated atomically without races."""
        config = WorkerPoolConfig(max_workers=10)
        pool = WorkerPool(config)

        def increment_shared(shared_dict, key):
            # Simulate work
            time.sleep(0.001)
            return key

        shared = {}

        # Submit many tasks
        for i in range(100):
            pool.submit_task(f"task_{i}", increment_shared, args=(shared, i))

        # Wait for all
        results = pool.wait_for_all(timeout=20.0)

        # Verify all tasks completed
        self.assertEqual(len(results), 100)

        # Check metrics consistency
        metrics = pool.get_metrics()
        self.assertEqual(len(metrics), 100)

        # All should be completed or failed (no partial states)
        for metric in metrics.values():
            self.assertIn(
                metric.status,
                [TaskStatus.COMPLETED, TaskStatus.FAILED]
            )

        pool.shutdown()

class TestWorkerPoolDeterminism(unittest.TestCase):
    """Test deterministic behavior."""

    def test_consistent_results(self):
        """Test that same tasks produce consistent results."""
        def deterministic_task(x):
            # Pure function - always produces same output for same input
            return x * x + 2 * x + 1

        # Run twice with same inputs
        results1 = []
        results2 = []

        for run in range(2):
            pool = WorkerPool()

            for i in range(20):
                pool.submit_task(f"task_{i}", deterministic_task, args=(i,))

            results = pool.wait_for_all()
            if run == 0:
                results1 = sorted([r.result for r in results if r.success])
            else:
                results2 = sorted([r.result for r in results if r.success])

            pool.shutdown()

        # Results should be identical
        self.assertEqual(results1, results2)

    def test_task_execution_order_within_constraints(self):
        """Test that tasks respect max_workers constraint."""
        config = WorkerPoolConfig(max_workers=2)
        pool = WorkerPool(config)

        execution_log = []

        def logged_task(task_num):
            execution_log.append(("start", task_num, time.time()))
            time.sleep(0.1)
            execution_log.append(("end", task_num, time.time()))
            return task_num

        # Submit 6 tasks
        for i in range(6):
            pool.submit_task(f"task_{i}", logged_task, args=(i,))

        pool.wait_for_all(timeout=10.0)

        # Check that at most 2 tasks were running simultaneously
        running = []
        max_concurrent = 0

        for event, task_num, _timestamp in execution_log:
            if event == "start":
                running.append(task_num)
                max_concurrent = max(max_concurrent, len(running))
            elif event == "end":
                running.remove(task_num)

        # Should not exceed max_workers
        self.assertLessEqual(max_concurrent, 2)

        pool.shutdown()

def run_tests():
    """Run all tests."""
    unittest.main(verbosity=2)

if __name__ == "__main__":
    run_tests()
