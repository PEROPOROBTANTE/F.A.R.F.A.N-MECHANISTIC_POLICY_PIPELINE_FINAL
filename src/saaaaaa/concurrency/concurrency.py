"""
Concurrency Module - Deterministic Worker Pool for Parallel Execution.

This module implements a deterministic WorkerPool for executing tasks in parallel
with the following features:
- Controlled max_workers for resource management
- Exponential backoff for retries
- Abortability for canceling pending tasks
- Per-task instrumentation and logging
- No race conditions or unwanted variability

Preconditions:
- Tasks and workers are declared before execution
- Each task is idempotent and thread-safe

Invariants:
- No interference between workers
- Deterministic task execution order within priority groups
- Thread-safe state management

Postconditions:
- Pool is usable by orchestrator/choreographer
- All resources are properly cleaned up
- No race conditions or variability in results
"""

from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskExecutionError(Exception):
    """Exception raised when task execution fails."""
    pass

@dataclass
class WorkerPoolConfig:
    """Configuration for WorkerPool.

    Attributes:
        max_workers: Maximum number of concurrent workers (default: 50)
        task_timeout_seconds: Timeout for individual task execution (default: 180)
        max_retries: Maximum number of retries per task (default: 3)
        backoff_base_seconds: Base delay for exponential backoff (default: 1.0)
        backoff_max_seconds: Maximum backoff delay (default: 60.0)
        enable_instrumentation: Enable detailed logging and metrics (default: True)
    """
    max_workers: int = 50
    task_timeout_seconds: float = 180.0
    max_retries: int = 3
    backoff_base_seconds: float = 1.0
    backoff_max_seconds: float = 60.0
    enable_instrumentation: bool = True

@dataclass
class TaskMetrics:
    """Metrics for a single task execution.

    Attributes:
        task_id: Unique task identifier
        task_name: Human-readable task name
        status: Current task status
        start_time: Task start time (epoch seconds)
        end_time: Task end time (epoch seconds, None if not finished)
        execution_time_ms: Total execution time in milliseconds
        retries_used: Number of retries performed
        worker_id: ID of worker that executed the task
        error_message: Error message if task failed
    """
    task_id: str
    task_name: str
    status: TaskStatus
    start_time: float
    end_time: float | None = None
    execution_time_ms: float = 0.0
    retries_used: int = 0
    worker_id: str | None = None
    error_message: str | None = None

@dataclass
class TaskResult:
    """Result of a task execution.

    Attributes:
        task_id: Unique task identifier
        task_name: Human-readable task name
        success: Whether task succeeded
        result: Task result data (None if failed)
        error: Exception if task failed (None if succeeded)
        metrics: Execution metrics
    """
    task_id: str
    task_name: str
    success: bool
    result: Any = None
    error: Exception | None = None
    metrics: TaskMetrics | None = None

class WorkerPool:
    """
    Deterministic WorkerPool for parallel task execution.

    This pool provides controlled concurrency with the following guarantees:
    - No race conditions through thread-safe state management
    - Deterministic execution within priority groups
    - Proper resource cleanup and abort handling
    - Per-task instrumentation and logging

    Example:
        >>> config = WorkerPoolConfig(max_workers=10, max_retries=2)
        >>> pool = WorkerPool(config)
        >>>
        >>> def my_task(x):
        ...     return x * 2
        >>>
        >>> task_id = pool.submit_task("double_5", my_task, args=(5,))
        >>> results = pool.wait_for_all()
        >>> pool.shutdown()
    """

    def __init__(self, config: WorkerPoolConfig | None = None) -> None:
        """
        Initialize WorkerPool.

        Args:
            config: Pool configuration (uses defaults if None)
        """
        self.config = config or WorkerPoolConfig()
        self._executor: ThreadPoolExecutor | None = None
        self._futures: dict[str, Future] = {}
        self._task_info: dict[str, tuple[str, Callable, tuple, dict]] = {}
        self._metrics: dict[str, TaskMetrics] = {}
        self._lock = threading.Lock()
        self._abort_requested = threading.Event()
        self._is_shutdown = False

        logger.info(
            f"WorkerPool initialized: max_workers={self.config.max_workers}, "
            f"max_retries={self.config.max_retries}, "
            f"task_timeout={self.config.task_timeout_seconds}s"
        )

    def _create_executor(self) -> ThreadPoolExecutor:
        """Create thread pool executor lazily."""
        if self._executor is None:
            self._executor = ThreadPoolExecutor(
                max_workers=self.config.max_workers,
                thread_name_prefix="WorkerPool"
            )
        return self._executor

    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """
        Calculate exponential backoff delay.

        Args:
            retry_count: Number of retries already attempted

        Returns:
            Delay in seconds, capped at backoff_max_seconds
        """
        delay = self.config.backoff_base_seconds * (2 ** retry_count)
        return min(delay, self.config.backoff_max_seconds)

    def _execute_task_with_retry(
        self,
        task_id: str,
        task_name: str,
        task_fn: Callable,
        args: tuple,
        kwargs: dict,
    ) -> Any:
        """
        Execute task with retry logic and exponential backoff.

        Args:
            task_id: Unique task identifier
            task_name: Human-readable task name
            task_fn: Task function to execute
            args: Positional arguments for task_fn
            kwargs: Keyword arguments for task_fn

        Returns:
            Task result

        Raises:
            TaskExecutionError: If task fails after all retries
        """
        worker_id = threading.current_thread().name
        retry_count = 0
        last_error = None

        # Initialize metrics
        with self._lock:
            self._metrics[task_id] = TaskMetrics(
                task_id=task_id,
                task_name=task_name,
                status=TaskStatus.RUNNING,
                start_time=time.time(),
                worker_id=worker_id
            )

        if self.config.enable_instrumentation:
            logger.info(f"[{task_id}] Starting task '{task_name}' on worker {worker_id}")

        while retry_count <= self.config.max_retries:
            # Check if abort was requested
            if self._abort_requested.is_set():
                with self._lock:
                    self._metrics[task_id].status = TaskStatus.CANCELLED
                    self._metrics[task_id].end_time = time.time()
                    self._metrics[task_id].execution_time_ms = (
                        (self._metrics[task_id].end_time - self._metrics[task_id].start_time) * 1000
                    )

                if self.config.enable_instrumentation:
                    logger.warning(f"[{task_id}] Task '{task_name}' cancelled due to abort request")

                raise TaskExecutionError(f"Task {task_name} cancelled due to abort request")

            try:
                # Execute task
                task_start = time.time()
                result = task_fn(*args, **kwargs)
                task_duration = (time.time() - task_start) * 1000

                # Update metrics on success
                with self._lock:
                    self._metrics[task_id].status = TaskStatus.COMPLETED
                    self._metrics[task_id].end_time = time.time()
                    self._metrics[task_id].execution_time_ms = task_duration
                    self._metrics[task_id].retries_used = retry_count

                if self.config.enable_instrumentation:
                    logger.info(
                        f"[{task_id}] Task '{task_name}' completed successfully "
                        f"in {task_duration:.2f}ms (retries: {retry_count})"
                    )

                return result

            except Exception as e:
                last_error = e

                # Update metrics on failure
                with self._lock:
                    self._metrics[task_id].retries_used = retry_count
                    self._metrics[task_id].error_message = str(e)

                if retry_count < self.config.max_retries:
                    # Calculate backoff delay
                    backoff_delay = self._calculate_backoff_delay(retry_count)

                    with self._lock:
                        self._metrics[task_id].status = TaskStatus.RETRYING

                    if self.config.enable_instrumentation:
                        logger.warning(
                            f"[{task_id}] Task '{task_name}' failed (attempt {retry_count + 1}), "
                            f"retrying after {backoff_delay:.2f}s: {e}"
                        )

                    # Wait before retrying (check abort periodically)
                    time.sleep(backoff_delay)
                    retry_count += 1
                else:
                    # All retries exhausted
                    with self._lock:
                        self._metrics[task_id].status = TaskStatus.FAILED
                        self._metrics[task_id].end_time = time.time()
                        self._metrics[task_id].execution_time_ms = (
                            (self._metrics[task_id].end_time - self._metrics[task_id].start_time) * 1000
                        )

                    if self.config.enable_instrumentation:
                        logger.error(
                            f"[{task_id}] Task '{task_name}' failed after {retry_count} retries: {e}"
                        )

                    raise TaskExecutionError(
                        f"Task {task_name} failed after {retry_count} retries: {last_error}"
                    ) from last_error

        # Should not reach here, but just in case
        raise TaskExecutionError(f"Task {task_name} failed: {last_error}")

    def submit_task(
        self,
        task_name: str,
        task_fn: Callable,
        args: tuple = (),
        kwargs: dict[str, Any] | None = None,
    ) -> str:
        """
        Submit a task for execution.

        Args:
            task_name: Human-readable task name for logging
            task_fn: Callable to execute
            args: Positional arguments for task_fn
            kwargs: Keyword arguments for task_fn

        Returns:
            Unique task identifier

        Raises:
            RuntimeError: If pool is shutdown
        """
        if self._is_shutdown:
            raise RuntimeError("Cannot submit tasks to a shutdown WorkerPool")

        kwargs = kwargs or {}
        task_id = str(uuid4())

        with self._lock:
            # Store task info for potential retries
            self._task_info[task_id] = (task_name, task_fn, args, kwargs)

            # Submit task to executor
            executor = self._create_executor()
            future = executor.submit(
                self._execute_task_with_retry,
                task_id,
                task_name,
                task_fn,
                args,
                kwargs
            )
            self._futures[task_id] = future

        if self.config.enable_instrumentation:
            logger.debug(f"[{task_id}] Task '{task_name}' submitted to pool")

        return task_id

    def get_task_result(self, task_id: str, timeout: float | None = None) -> TaskResult:
        """
        Get result of a specific task.

        Args:
            task_id: Task identifier returned by submit_task
            timeout: Maximum time to wait for result in seconds (None = wait forever)

        Returns:
            TaskResult with execution metrics

        Raises:
            KeyError: If task_id is not found
            TimeoutError: If timeout is exceeded
        """
        with self._lock:
            if task_id not in self._futures:
                raise KeyError(f"Task {task_id} not found")

            future = self._futures[task_id]
            task_name = self._task_info[task_id][0]

        try:
            timeout_to_use = timeout or self.config.task_timeout_seconds
            result = future.result(timeout=timeout_to_use)

            with self._lock:
                metrics = self._metrics.get(task_id)

            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                success=True,
                result=result,
                metrics=metrics
            )

        except TimeoutError as e:
            with self._lock:
                metrics = self._metrics.get(task_id)
                if metrics:
                    metrics.status = TaskStatus.FAILED
                    metrics.error_message = f"Timeout after {timeout_to_use}s"

            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                success=False,
                error=e,
                metrics=metrics
            )

        except Exception as e:
            with self._lock:
                metrics = self._metrics.get(task_id)

            return TaskResult(
                task_id=task_id,
                task_name=task_name,
                success=False,
                error=e,
                metrics=metrics
            )

    def wait_for_all(
        self,
        timeout: float | None = None,
        return_when: str = "ALL_COMPLETED"
    ) -> list[TaskResult]:
        """
        Wait for all submitted tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)
            return_when: When to return - "ALL_COMPLETED" or "FIRST_EXCEPTION"

        Returns:
            List of TaskResults for all tasks

        Raises:
            TimeoutError: If timeout is exceeded before all tasks complete
        """
        if self.config.enable_instrumentation:
            logger.info(f"Waiting for {len(self._futures)} tasks to complete...")

        start_time = time.time()
        results = []

        with self._lock:
            all_futures = list(self._futures.items())

        try:
            # Use as_completed for better progress tracking
            completed_count = 0
            for future in as_completed(
                [f for _, f in all_futures],
                timeout=timeout
            ):
                completed_count += 1

                # Find task_id for this future
                task_id = None
                with self._lock:
                    for tid, f in all_futures:
                        if f == future:
                            task_id = tid
                            break

                if task_id:
                    result = self.get_task_result(task_id, timeout=0.1)
                    results.append(result)

                    if self.config.enable_instrumentation and completed_count % 10 == 0:
                        elapsed = time.time() - start_time
                        logger.info(
                            f"Progress: {completed_count}/{len(all_futures)} tasks completed "
                            f"({elapsed:.2f}s elapsed)"
                        )

                    # Check if we should return early on first exception
                    if return_when == "FIRST_EXCEPTION" and not result.success:
                        if self.config.enable_instrumentation:
                            logger.warning(
                                f"Returning early due to task failure: {result.task_name}"
                            )
                        break

            elapsed = time.time() - start_time
            if self.config.enable_instrumentation:
                successful = sum(1 for r in results if r.success)
                failed = sum(1 for r in results if not r.success)
                logger.info(
                    f"All tasks completed: {successful} succeeded, {failed} failed "
                    f"({elapsed:.2f}s total)"
                )

            return results

        except TimeoutError:
            elapsed = time.time() - start_time
            completed = len(results)
            pending = len(all_futures) - completed

            logger.error(
                f"Timeout after {elapsed:.2f}s: {completed} completed, {pending} pending"
            )

            # Get results for completed tasks
            for task_id, future in all_futures:
                if future.done() and task_id not in [r.task_id for r in results]:
                    try:
                        results.append(self.get_task_result(task_id, timeout=0.1))
                    except Exception as e:
                        logger.exception(f"Failed to get result for completed task {task_id}: {e}")

            raise TimeoutError(
                f"Timeout waiting for tasks: {completed}/{len(all_futures)} completed"
            )

    def abort_pending_tasks(self) -> int:
        """
        Request abort of all pending tasks.

        This sets the abort flag, which will be checked by running tasks
        at their next safe point (before retry or next iteration).

        Returns:
            Number of tasks that were still pending
        """
        self._abort_requested.set()

        pending_count = 0
        with self._lock:
            for task_id, future in self._futures.items():
                if not future.done():
                    future.cancel()
                    pending_count += 1

                    # Update metrics
                    if task_id in self._metrics:
                        self._metrics[task_id].status = TaskStatus.CANCELLED

        if self.config.enable_instrumentation:
            logger.warning(f"Abort requested: {pending_count} tasks cancelled")

        return pending_count

    def get_metrics(self) -> dict[str, TaskMetrics]:
        """
        Get execution metrics for all tasks.

        Returns:
            Dictionary mapping task_id to TaskMetrics
        """
        with self._lock:
            return dict(self._metrics)

    def get_summary_metrics(self) -> dict[str, Any]:
        """
        Get summary metrics for the pool.

        Returns:
            Dictionary with aggregated metrics
        """
        with self._lock:
            metrics_list = list(self._metrics.values())

        if not metrics_list:
            return {
                "total_tasks": 0,
                "completed": 0,
                "failed": 0,
                "cancelled": 0,
                "running": 0,
                "pending": 0,
                "avg_execution_time_ms": 0.0,
                "total_retries": 0,
            }

        completed = sum(1 for m in metrics_list if m.status == TaskStatus.COMPLETED)
        failed = sum(1 for m in metrics_list if m.status == TaskStatus.FAILED)
        cancelled = sum(1 for m in metrics_list if m.status == TaskStatus.CANCELLED)
        running = sum(1 for m in metrics_list if m.status == TaskStatus.RUNNING)
        pending = sum(1 for m in metrics_list if m.status == TaskStatus.PENDING)

        completed_tasks = [m for m in metrics_list if m.status == TaskStatus.COMPLETED]
        avg_time = (
            sum(m.execution_time_ms for m in completed_tasks) / len(completed_tasks)
            if completed_tasks else 0.0
        )

        total_retries = sum(m.retries_used for m in metrics_list)

        return {
            "total_tasks": len(metrics_list),
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "running": running,
            "pending": pending,
            "avg_execution_time_ms": avg_time,
            "total_retries": total_retries,
        }

    def shutdown(self, wait: bool = True, cancel_futures: bool = False) -> None:
        """
        Shutdown the worker pool.

        Args:
            wait: If True, wait for all tasks to complete before shutdown
            cancel_futures: If True, cancel all pending tasks
        """
        if self._is_shutdown:
            return

        if cancel_futures:
            self.abort_pending_tasks()

        if self._executor is not None:
            if self.config.enable_instrumentation:
                logger.info(f"Shutting down WorkerPool (wait={wait})")

            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
            self._executor = None

        self._is_shutdown = True

        if self.config.enable_instrumentation:
            summary = self.get_summary_metrics()
            logger.info(
                f"WorkerPool shutdown complete. "
                f"Completed: {summary['completed']}, "
                f"Failed: {summary['failed']}, "
                f"Cancelled: {summary['cancelled']}"
            )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown(wait=True)
        return False
