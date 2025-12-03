# Batch Executor Usage Guide

## Overview

The `BatchExecutor` provides scalable batch processing infrastructure for executor scalability with:

- **Configurable batch sizes** per executor type based on object complexity
- **Streaming result aggregation** to avoid memory accumulation
- **Async executor flow** integration for parallel batch processing
- **Batch-level error handling** with partial success recovery

## Basic Usage

### 1. Configuration

```python
from farfan_pipeline.core.orchestrator.batch_executor import (
    BatchExecutor,
    BatchExecutorConfig,
)

# Configure batch executor
config = BatchExecutorConfig(
    default_batch_size=10,
    max_batch_size=100,
    min_batch_size=2,
    enable_streaming=True,
    error_threshold=0.5,  # 50% failure threshold
    max_retries=2,
    enable_instrumentation=True,
)

# Initialize executor
executor = BatchExecutor(
    config=config,
    method_executor=method_executor,
    signal_registry=signal_registry,
    questionnaire_provider=questionnaire_provider,
)
```

### 2. Streaming Batch Execution

Process entities in batches with streaming results:

```python
# Process 100 entities in chunks of 10
entities = list(range(100))

async for batch_result in executor.execute_batches(
    items=entities,
    executor_class=D1Q1_Executor,
    document=preprocessed_document,
    question_context=question_context,
    base_slot="D1-Q1",  # Auto-determines batch size based on complexity
):
    # Process results as they complete
    for item, result in batch_result.get_successful_results():
        aggregate(result)
    
    # Handle failures
    for failed_item in batch_result.get_failed_items():
        log_failure(failed_item)
```

### 3. Parallel Batch Execution

Execute multiple batches concurrently:

```python
# Process batches in parallel with max 4 concurrent batches
batch_results = await executor.execute_batches_parallel(
    items=entities,
    executor_class=D3Q2_Executor,
    document=preprocessed_document,
    question_context=question_context,
    base_slot="D3-Q2",  # Very complex executor -> batch size of 5
    max_concurrent_batches=4,
)

# Aggregate all results
aggregated = await executor.aggregate_batch_results(batch_results)
print(f"Success rate: {aggregated.success_rate():.2%}")
print(f"Total time: {aggregated.execution_time_ms:.2f}ms")
```

### 4. Streaming Aggregation

Aggregate results without accumulating all in memory:

```python
def accumulate_scores(accumulator, result):
    """Incremental aggregation function."""
    if accumulator is None:
        accumulator = {"total": 0, "count": 0}
    
    accumulator["total"] += result.get("score", 0)
    accumulator["count"] += 1
    return accumulator

# Stream and aggregate
batch_stream = executor.execute_batches(
    items=entities,
    executor_class=D1Q1_Executor,
    document=preprocessed_document,
    question_context=question_context,
    batch_size=20,
)

final_result = await executor.stream_aggregate_batches(
    batch_stream=batch_stream,
    aggregation_fn=accumulate_scores,
)

average_score = final_result["total"] / final_result["count"]
```

## Complexity-Based Batch Sizing

The executor automatically determines optimal batch sizes based on executor complexity:

| Complexity | Batch Size | Example Executors |
|------------|-----------|------------------|
| SIMPLE | 50 | Simple text extraction |
| MODERATE | 20 | D1-Q1, D1-Q2, D2-Q1 |
| COMPLEX | 10 | D2-Q3, D3-Q1, D4-Q2 |
| VERY_COMPLEX | 5 | D2-Q2, D3-Q2, D3-Q3, D3-Q4, D3-Q5, D4-Q1, D5-Q2 |

Complexity is automatically inferred from the `base_slot`:

```python
# Automatically uses batch size of 5 for very complex executor
batch_size = executor.get_batch_size_for_executor("D3-Q2")
assert batch_size == 5
```

## Error Handling

The executor provides three levels of error handling:

### 1. Item-Level Failures

Individual items can fail without affecting the batch:

```python
batch_result = await execute_batch(...)

# Check batch status
if batch_result.status == BatchStatus.PARTIAL_SUCCESS:
    # Process successful results
    for item, result in batch_result.get_successful_results():
        process(result)
    
    # Handle failures
    for error in batch_result.errors:
        logger.error(f"Item {error['item_index']} failed: {error['error_message']}")
```

### 2. Batch-Level Failures

Batches are marked as failed when error threshold is exceeded:

```python
# Configure 60% error threshold
config = BatchExecutorConfig(error_threshold=0.6)

# Batch with 50% failures -> PARTIAL_SUCCESS
# Batch with 70% failures -> FAILED
```

### 3. Automatic Retries

Failed batches are automatically retried with exponential backoff:

```python
config = BatchExecutorConfig(
    max_retries=2,  # Retry up to 2 times
    backoff_base_seconds=1.0,  # 1s, 2s, 4s backoff
)

# Batch automatically retried on failure
batch_result = await executor._execute_batch_with_retry(...)
print(f"Retries used: {batch_result.metrics['retries_used']}")
```

## Performance Monitoring

The executor provides detailed metrics for monitoring:

```python
# Per-batch metrics
batch_result = await execute_batch(...)
print(f"Batch execution time: {batch_result.metrics['execution_time_ms']:.2f}ms")
print(f"Success rate: {batch_result.metrics['successful_items']}/{batch_result.metrics['batch_size']}")

# Aggregated metrics
aggregated = await executor.aggregate_batch_results(batch_results)
print(f"Total batches: {aggregated.total_batches}")
print(f"Total items: {aggregated.total_items}")
print(f"Success rate: {aggregated.success_rate():.2%}")
print(f"Total time: {aggregated.execution_time_ms:.2f}ms")

# Per-batch performance analysis
for metrics in aggregated.batch_metrics:
    print(f"Batch {metrics['batch_index']}: {metrics['execution_time_ms']:.2f}ms")
```

## Integration with Orchestrator

The batch executor integrates seamlessly with the existing orchestrator:

```python
from farfan_pipeline.core.orchestrator.core import Orchestrator

class Orchestrator:
    def __init__(self, ...):
        # Initialize batch executor alongside existing components
        self.batch_executor = BatchExecutor(
            config=BatchExecutorConfig(),
            method_executor=self.executor,
            signal_registry=self.executor.signal_registry,
            questionnaire_provider=self.questionnaire_provider,
        )
    
    async def _execute_micro_questions_async(self, document, config):
        micro_questions = config.get("micro_questions", [])
        
        # Group questions by base_slot for batch processing
        questions_by_executor = {}
        for q in micro_questions:
            base_slot = q.get("base_slot")
            if base_slot not in questions_by_executor:
                questions_by_executor[base_slot] = []
            questions_by_executor[base_slot].append(q)
        
        # Process each executor's questions in batches
        all_results = []
        for base_slot, questions in questions_by_executor.items():
            executor_class = self.executors[base_slot]
            
            batch_results = await self.batch_executor.execute_batches_parallel(
                items=questions,
                executor_class=executor_class,
                document=document,
                question_context=questions[0],  # Use first for context
                base_slot=base_slot,
                max_concurrent_batches=4,
            )
            
            # Aggregate results
            aggregated = await self.batch_executor.aggregate_batch_results(batch_results)
            all_results.extend(aggregated.results)
        
        return all_results
```

## Best Practices

1. **Use streaming for large datasets**: Avoid accumulating all results in memory
2. **Tune batch sizes**: Adjust based on executor complexity and available resources
3. **Monitor metrics**: Track performance to identify bottlenecks
4. **Handle partial failures**: Process successful results even when some items fail
5. **Configure error thresholds**: Set appropriate thresholds based on acceptable failure rates
6. **Use parallel execution carefully**: Balance concurrency with resource limits

## Example: Processing 100 Entities

```python
async def process_entities_example():
    # Configure executor
    config = BatchExecutorConfig(
        default_batch_size=10,
        max_batch_size=50,
        error_threshold=0.3,  # Allow up to 30% failures per batch
        max_retries=2,
        enable_instrumentation=True,
    )
    
    executor = BatchExecutor(config=config, method_executor=method_executor)
    
    # Process 100 entities in chunks of 10
    entities = list(range(100))
    all_results = []
    
    async for batch_result in executor.execute_batches(
        items=entities,
        executor_class=D1Q1_Executor,
        document=document,
        question_context=context,
        base_slot="D1-Q1",
    ):
        # Log progress
        logger.info(
            f"Batch {batch_result.batch_index}: "
            f"{batch_result.metrics['successful_items']}/{batch_result.metrics['batch_size']} successful "
            f"({batch_result.metrics['execution_time_ms']:.2f}ms)"
        )
        
        # Collect successful results
        for item, result in batch_result.get_successful_results():
            all_results.append(result)
        
        # Log failures
        if batch_result.errors:
            logger.warning(f"Batch {batch_result.batch_index} had {len(batch_result.errors)} failures")
    
    # Final summary
    logger.info(f"Processed {len(all_results)}/{len(entities)} entities successfully")
    return all_results
```

## API Reference

See `batch_executor.py` for full API documentation including:

- `BatchExecutor`: Main executor class
- `BatchExecutorConfig`: Configuration dataclass
- `BatchResult`: Single batch result
- `AggregatedBatchResults`: Aggregated results from multiple batches
- `BatchStatus`: Enum for batch execution status
- `ExecutorComplexity`: Enum for executor complexity classification
