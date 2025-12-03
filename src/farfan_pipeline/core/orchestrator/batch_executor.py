"""Batch processing infrastructure for executor scalability.

This module provides batched entity processing with:
- Configurable batch sizes per executor type based on object complexity
- Streaming result aggregation to avoid memory accumulation
- Async executor flow integration for parallel batch processing
- Batch-level error handling with partial success recovery

Example:
    >>> config = BatchExecutorConfig(default_batch_size=10, max_batch_size=100)
    >>> executor = BatchExecutor(config, method_executor, signal_registry)
    >>> async for batch_result in executor.execute_batches(entities, question_context):
    ...     process_batch_result(batch_result)
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.core import MethodExecutor
    from farfan_pipeline.core.types import PreprocessedDocument

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Status of batch execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutorComplexity(Enum):
    """Complexity classification for executor types."""

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class BatchExecutorConfig:
    """Configuration for batch processing.

    Attributes:
        default_batch_size: Default batch size for unclassified executors
        max_batch_size: Maximum batch size allowed
        min_batch_size: Minimum batch size allowed
        enable_streaming: Enable streaming result aggregation
        error_threshold: Fraction of failures before marking batch as failed (0.0-1.0)
        max_retries: Maximum number of retries for failed batches
        backoff_base_seconds: Base delay for exponential backoff
        enable_instrumentation: Enable detailed logging and metrics
    """

    default_batch_size: int = 10
    max_batch_size: int = 100
    min_batch_size: int = 1
    enable_streaming: bool = True
    error_threshold: float = 0.5
    max_retries: int = 2
    backoff_base_seconds: float = 1.0
    enable_instrumentation: bool = True

    def __post_init__(self) -> None:
        """Validate configuration parameters."""
        if not (
            1 <= self.min_batch_size <= self.default_batch_size <= self.max_batch_size
        ):
            raise ValueError(
                f"Invalid batch size configuration: min={self.min_batch_size}, "
                f"default={self.default_batch_size}, max={self.max_batch_size}"
            )
        if not 0.0 <= self.error_threshold <= 1.0:
            raise ValueError(
                f"error_threshold must be in [0.0, 1.0], got {self.error_threshold}"
            )


EXECUTOR_COMPLEXITY_MAP: dict[str, ExecutorComplexity] = {
    "D1-Q1": ExecutorComplexity.MODERATE,
    "D1-Q2": ExecutorComplexity.MODERATE,
    "D1-Q3": ExecutorComplexity.COMPLEX,
    "D1-Q4": ExecutorComplexity.MODERATE,
    "D1-Q5": ExecutorComplexity.MODERATE,
    "D2-Q1": ExecutorComplexity.MODERATE,
    "D2-Q2": ExecutorComplexity.VERY_COMPLEX,
    "D2-Q3": ExecutorComplexity.COMPLEX,
    "D2-Q4": ExecutorComplexity.COMPLEX,
    "D2-Q5": ExecutorComplexity.MODERATE,
    "D3-Q1": ExecutorComplexity.MODERATE,
    "D3-Q2": ExecutorComplexity.VERY_COMPLEX,
    "D3-Q3": ExecutorComplexity.VERY_COMPLEX,
    "D3-Q4": ExecutorComplexity.VERY_COMPLEX,
    "D3-Q5": ExecutorComplexity.VERY_COMPLEX,
    "D4-Q1": ExecutorComplexity.VERY_COMPLEX,
    "D4-Q2": ExecutorComplexity.COMPLEX,
    "D4-Q3": ExecutorComplexity.COMPLEX,
    "D4-Q4": ExecutorComplexity.MODERATE,
    "D4-Q5": ExecutorComplexity.MODERATE,
    "D5-Q1": ExecutorComplexity.MODERATE,
    "D5-Q2": ExecutorComplexity.VERY_COMPLEX,
    "D5-Q3": ExecutorComplexity.MODERATE,
    "D5-Q4": ExecutorComplexity.COMPLEX,
    "D5-Q5": ExecutorComplexity.COMPLEX,
    "D6-Q1": ExecutorComplexity.COMPLEX,
    "D6-Q2": ExecutorComplexity.MODERATE,
    "D6-Q3": ExecutorComplexity.COMPLEX,
    "D6-Q4": ExecutorComplexity.MODERATE,
    "D6-Q5": ExecutorComplexity.MODERATE,
}

COMPLEXITY_BATCH_SIZE_MAP: dict[ExecutorComplexity, int] = {
    ExecutorComplexity.SIMPLE: 50,
    ExecutorComplexity.MODERATE: 20,
    ExecutorComplexity.COMPLEX: 10,
    ExecutorComplexity.VERY_COMPLEX: 5,
}


class BatchMetrics(TypedDict):
    """Metrics for a single batch execution."""

    batch_id: str
    batch_index: int
    batch_size: int
    status: BatchStatus
    start_time: float
    end_time: float | None
    execution_time_ms: float
    successful_items: int
    failed_items: int
    retries_used: int
    error_messages: list[str]


@dataclass
class BatchResult:
    """Result of a batch execution.

    Attributes:
        batch_id: Unique batch identifier
        batch_index: Index of the batch in the sequence
        items: List of items in this batch
        results: List of results corresponding to items (may contain None for failures)
        status: Batch execution status
        metrics: Execution metrics
        errors: List of errors encountered (empty if successful)
    """

    batch_id: str
    batch_index: int
    items: list[Any]
    results: list[Any]
    status: BatchStatus
    metrics: BatchMetrics
    errors: list[dict[str, Any]] = field(default_factory=list)

    def is_successful(self) -> bool:
        """Check if batch execution was fully successful."""
        return self.status == BatchStatus.COMPLETED and not self.errors

    def has_partial_success(self) -> bool:
        """Check if batch had partial success."""
        return self.status == BatchStatus.PARTIAL_SUCCESS and any(
            r is not None for r in self.results
        )

    def get_successful_results(self) -> list[tuple[Any, Any]]:
        """Get list of (item, result) pairs for successful executions."""
        return [
            (item, result)
            for item, result in zip(self.items, self.results, strict=False)
            if result is not None
        ]

    def get_failed_items(self) -> list[Any]:
        """Get list of items that failed execution."""
        return [
            item
            for item, result in zip(self.items, self.results, strict=False)
            if result is None
        ]


@dataclass
class AggregatedBatchResults:
    """Aggregated results from multiple batch executions.

    Attributes:
        total_batches: Total number of batches processed
        total_items: Total number of items processed
        successful_items: Number of successfully processed items
        failed_items: Number of failed items
        results: List of all successful results
        errors: List of all errors encountered
        execution_time_ms: Total execution time in milliseconds
        batch_metrics: List of metrics for each batch
    """

    total_batches: int
    total_items: int
    successful_items: int
    failed_items: int
    results: list[Any]
    errors: list[dict[str, Any]]
    execution_time_ms: float
    batch_metrics: list[BatchMetrics]

    def success_rate(self) -> float:
        """Calculate success rate as fraction of successful items."""
        if self.total_items == 0:
            return 0.0
        return self.successful_items / self.total_items


class BatchExecutor:
    """Batch processing executor with streaming aggregation and error recovery.

    This executor provides scalable batch processing for entity collections with:
    - Adaptive batch sizing based on executor complexity
    - Streaming result aggregation to avoid memory accumulation
    - Parallel batch processing via async executor flow
    - Batch-level error handling with partial success recovery
    """

    def __init__(
        self,
        config: BatchExecutorConfig | None = None,
        method_executor: MethodExecutor | None = None,
        signal_registry: Any | None = None,
        questionnaire_provider: Any | None = None,
        calibration_orchestrator: Any | None = None,
    ) -> None:
        """Initialize batch executor.

        Args:
            config: Batch execution configuration
            method_executor: MethodExecutor instance for method routing
            signal_registry: Signal registry for executor instances
            questionnaire_provider: Questionnaire provider
            calibration_orchestrator: Calibration orchestrator
        """
        self.config = config or BatchExecutorConfig()
        self.method_executor = method_executor
        self.signal_registry = signal_registry
        self.questionnaire_provider = questionnaire_provider
        self.calibration_orchestrator = calibration_orchestrator
        self._batch_counter = 0

        if self.config.enable_instrumentation:
            logger.info(
                f"BatchExecutor initialized: default_batch_size={self.config.default_batch_size}, "
                f"max_batch_size={self.config.max_batch_size}, "
                f"error_threshold={self.config.error_threshold}"
            )

    def get_batch_size_for_executor(self, base_slot: str) -> int:
        """Determine batch size for a given executor based on complexity.

        Args:
            base_slot: Executor base slot (e.g., "D1-Q1")

        Returns:
            Recommended batch size for this executor
        """
        complexity = EXECUTOR_COMPLEXITY_MAP.get(base_slot, ExecutorComplexity.MODERATE)
        recommended_size = COMPLEXITY_BATCH_SIZE_MAP.get(
            complexity, self.config.default_batch_size
        )

        batch_size = max(
            self.config.min_batch_size,
            min(recommended_size, self.config.max_batch_size),
        )

        if self.config.enable_instrumentation:
            logger.debug(
                f"Batch size for {base_slot}: {batch_size} "
                f"(complexity={complexity.value}, recommended={recommended_size})"
            )

        return batch_size

    def _create_batches(
        self, items: list[Any], batch_size: int
    ) -> list[tuple[int, list[Any]]]:
        """Split items into batches of specified size.

        Args:
            items: List of items to batch
            batch_size: Size of each batch

        Returns:
            List of (batch_index, batch_items) tuples
        """
        batches = []
        for i in range(0, len(items), batch_size):
            batch_index = i // batch_size
            batch_items = items[i : i + batch_size]
            batches.append((batch_index, batch_items))

        if self.config.enable_instrumentation:
            logger.info(
                f"Created {len(batches)} batches from {len(items)} items "
                f"(batch_size={batch_size})"
            )

        return batches

    async def _execute_single_batch(
        self,
        batch_id: str,
        batch_index: int,
        batch_items: list[Any],
        executor_instance: Any,
        document: PreprocessedDocument,
        question_context: dict[str, Any],
    ) -> BatchResult:
        """Execute a single batch of items.

        Args:
            batch_id: Unique batch identifier
            batch_index: Index of this batch
            batch_items: Items to process in this batch
            executor_instance: Executor instance to use
            document: Document being processed
            question_context: Question context for execution

        Returns:
            BatchResult with execution details
        """
        start_time = time.perf_counter()
        results: list[Any] = []
        errors: list[dict[str, Any]] = []
        successful_items = 0
        failed_items = 0

        if self.config.enable_instrumentation:
            logger.debug(
                f"[{batch_id}] Executing batch {batch_index} with {len(batch_items)} items"
            )

        for item_index, item in enumerate(batch_items):
            try:
                result = await asyncio.to_thread(
                    executor_instance.execute,
                    document,
                    self.method_executor,
                    question_context=question_context,
                )
                results.append(result)
                successful_items += 1
            except Exception as exc:
                results.append(None)
                failed_items += 1
                error_detail = {
                    "batch_id": batch_id,
                    "batch_index": batch_index,
                    "item_index": item_index,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                }
                errors.append(error_detail)

                if self.config.enable_instrumentation:
                    logger.warning(
                        f"[{batch_id}] Item {item_index} failed: {exc}", exc_info=False
                    )

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0

        error_rate = failed_items / len(batch_items) if batch_items else 0.0
        if error_rate >= self.config.error_threshold:
            status = BatchStatus.FAILED
        elif failed_items > 0:
            status = BatchStatus.PARTIAL_SUCCESS
        else:
            status = BatchStatus.COMPLETED

        metrics: BatchMetrics = {
            "batch_id": batch_id,
            "batch_index": batch_index,
            "batch_size": len(batch_items),
            "status": status,
            "start_time": start_time,
            "end_time": end_time,
            "execution_time_ms": execution_time_ms,
            "successful_items": successful_items,
            "failed_items": failed_items,
            "retries_used": 0,
            "error_messages": [e["error_message"] for e in errors],
        }

        if self.config.enable_instrumentation:
            logger.info(
                f"[{batch_id}] Batch {batch_index} completed: "
                f"{successful_items}/{len(batch_items)} successful "
                f"({execution_time_ms:.2f}ms, status={status.value})"
            )

        return BatchResult(
            batch_id=batch_id,
            batch_index=batch_index,
            items=batch_items,
            results=results,
            status=status,
            metrics=metrics,
            errors=errors,
        )

    async def _execute_batch_with_retry(
        self,
        batch_id: str,
        batch_index: int,
        batch_items: list[Any],
        executor_instance: Any,
        document: PreprocessedDocument,
        question_context: dict[str, Any],
    ) -> BatchResult:
        """Execute a batch with retry logic for failed batches.

        Args:
            batch_id: Unique batch identifier
            batch_index: Index of this batch
            batch_items: Items to process in this batch
            executor_instance: Executor instance to use
            document: Document being processed
            question_context: Question context for execution

        Returns:
            BatchResult with execution details
        """
        retry_count = 0
        last_result: BatchResult | None = None

        while retry_count <= self.config.max_retries:
            result = await self._execute_single_batch(
                batch_id,
                batch_index,
                batch_items,
                executor_instance,
                document,
                question_context,
            )

            if result.status in (BatchStatus.COMPLETED, BatchStatus.PARTIAL_SUCCESS):
                result.metrics["retries_used"] = retry_count
                return result

            last_result = result
            retry_count += 1

            if retry_count <= self.config.max_retries:
                backoff_delay = self.config.backoff_base_seconds * (
                    2 ** (retry_count - 1)
                )
                if self.config.enable_instrumentation:
                    logger.warning(
                        f"[{batch_id}] Batch {batch_index} failed (attempt {retry_count}), "
                        f"retrying after {backoff_delay:.2f}s"
                    )
                await asyncio.sleep(backoff_delay)

        if last_result:
            last_result.metrics["retries_used"] = retry_count - 1
            if self.config.enable_instrumentation:
                logger.error(
                    f"[{batch_id}] Batch {batch_index} failed after {retry_count - 1} retries"
                )
            return last_result

        raise RuntimeError(f"Batch {batch_id} execution failed without result")

    async def execute_batches(
        self,
        items: list[Any],
        executor_class: type,
        document: PreprocessedDocument,
        question_context: dict[str, Any],
        base_slot: str | None = None,
        batch_size: int | None = None,
    ) -> AsyncIterator[BatchResult]:
        """Execute items in batches with streaming result generation.

        This method processes items in batches and yields results as they complete,
        enabling streaming aggregation without accumulating all results in memory.

        Args:
            items: List of items to process
            executor_class: Executor class to instantiate
            document: Document being processed
            question_context: Question context for execution
            base_slot: Base slot for complexity-based batch sizing (optional)
            batch_size: Override batch size (optional, uses complexity-based sizing if None)

        Yields:
            BatchResult for each completed batch

        Example:
            >>> batches = executor.execute_batches(entities, D1Q1_Executor, doc, ctx)
            >>> async for batch_result in batches:
            ...     for item, result in batch_result.get_successful_results():
            ...         aggregate(result)
        """
        if not items:
            logger.warning("execute_batches called with empty items list")
            return

        if batch_size is None:
            if base_slot:
                batch_size = self.get_batch_size_for_executor(base_slot)
            else:
                batch_size = self.config.default_batch_size

        batches = self._create_batches(items, batch_size)

        for batch_index, batch_items in batches:
            self._batch_counter += 1
            batch_id = f"batch_{self._batch_counter:06d}"

            executor_instance = executor_class(
                method_executor=self.method_executor,
                signal_registry=self.signal_registry,
                config=self.config,
                questionnaire_provider=self.questionnaire_provider,
                calibration_orchestrator=self.calibration_orchestrator,
            )

            batch_result = await self._execute_batch_with_retry(
                batch_id,
                batch_index,
                batch_items,
                executor_instance,
                document,
                question_context,
            )

            yield batch_result

    async def execute_batches_parallel(
        self,
        items: list[Any],
        executor_class: type,
        document: PreprocessedDocument,
        question_context: dict[str, Any],
        base_slot: str | None = None,
        batch_size: int | None = None,
        max_concurrent_batches: int = 4,
    ) -> list[BatchResult]:
        """Execute batches in parallel with concurrency control.

        Args:
            items: List of items to process
            executor_class: Executor class to instantiate
            document: Document being processed
            question_context: Question context for execution
            base_slot: Base slot for complexity-based batch sizing (optional)
            batch_size: Override batch size (optional)
            max_concurrent_batches: Maximum number of concurrent batch executions

        Returns:
            List of BatchResults for all batches
        """
        if not items:
            return []

        if batch_size is None:
            if base_slot:
                batch_size = self.get_batch_size_for_executor(base_slot)
            else:
                batch_size = self.config.default_batch_size

        batches = self._create_batches(items, batch_size)
        semaphore = asyncio.Semaphore(max_concurrent_batches)
        results: list[BatchResult] = []

        async def process_batch_with_semaphore(
            batch_index: int, batch_items: list[Any]
        ) -> BatchResult:
            async with semaphore:
                self._batch_counter += 1
                batch_id = f"batch_{self._batch_counter:06d}"

                executor_instance = executor_class(
                    method_executor=self.method_executor,
                    signal_registry=self.signal_registry,
                    config=self.config,
                    questionnaire_provider=self.questionnaire_provider,
                    calibration_orchestrator=self.calibration_orchestrator,
                )

                return await self._execute_batch_with_retry(
                    batch_id,
                    batch_index,
                    batch_items,
                    executor_instance,
                    document,
                    question_context,
                )

        tasks = [
            asyncio.create_task(process_batch_with_semaphore(batch_index, batch_items))
            for batch_index, batch_items in batches
        ]

        if self.config.enable_instrumentation:
            logger.info(
                f"Executing {len(tasks)} batches in parallel "
                f"(max_concurrent={max_concurrent_batches})"
            )

        for task in asyncio.as_completed(tasks):
            result = await task
            results.append(result)

        return results

    async def aggregate_batch_results(
        self, batch_results: Iterable[BatchResult]
    ) -> AggregatedBatchResults:
        """Aggregate results from multiple batches.

        Args:
            batch_results: Iterable of BatchResults to aggregate

        Returns:
            AggregatedBatchResults with summary statistics
        """
        start_time = time.perf_counter()

        total_batches = 0
        total_items = 0
        successful_items = 0
        failed_items = 0
        all_results: list[Any] = []
        all_errors: list[dict[str, Any]] = []
        batch_metrics_list: list[BatchMetrics] = []

        for batch_result in batch_results:
            total_batches += 1
            total_items += len(batch_result.items)
            successful_items += batch_result.metrics["successful_items"]
            failed_items += batch_result.metrics["failed_items"]

            for item, result in zip(
                batch_result.items, batch_result.results, strict=False
            ):
                if result is not None:
                    all_results.append(result)

            all_errors.extend(batch_result.errors)
            batch_metrics_list.append(batch_result.metrics)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0

        aggregated = AggregatedBatchResults(
            total_batches=total_batches,
            total_items=total_items,
            successful_items=successful_items,
            failed_items=failed_items,
            results=all_results,
            errors=all_errors,
            execution_time_ms=execution_time_ms,
            batch_metrics=batch_metrics_list,
        )

        if self.config.enable_instrumentation:
            logger.info(
                f"Aggregated {total_batches} batches: {successful_items}/{total_items} successful "
                f"(success_rate={aggregated.success_rate():.2%}, "
                f"aggregation_time={execution_time_ms:.2f}ms)"
            )

        return aggregated

    async def stream_aggregate_batches(
        self,
        batch_stream: AsyncIterator[BatchResult],
        aggregation_fn: Callable[[Any, Any], Any],
    ) -> Any:
        """Stream aggregation of batch results without accumulating in memory.

        Args:
            batch_stream: Async iterator of BatchResults
            aggregation_fn: Function to aggregate results incrementally
                (accumulator, new_result) -> accumulator

        Returns:
            Final aggregated result

        Example:
            >>> def aggregate_fn(acc, result):
            ...     acc['count'] += 1
            ...     acc['total'] += result['score']
            ...     return acc
            >>>
            >>> batches = executor.execute_batches(entities, D1Q1_Executor, doc, ctx)
            >>> final = await executor.stream_aggregate_batches(batches, aggregate_fn)
        """
        accumulator = None

        async for batch_result in batch_stream:
            for result in batch_result.results:
                if result is not None:
                    if accumulator is None:
                        accumulator = result
                    else:
                        accumulator = aggregation_fn(accumulator, result)

        return accumulator
