# Concurrency Module

## Overview

The `concurrency` module provides a deterministic `WorkerPool` for parallel task execution with controlled concurrency, retry logic with exponential backoff, and comprehensive instrumentation. It is designed to be used by the orchestrator and choreographer for executing the 300 micro questions in parallel.

## Features

- **Deterministic Execution**: Thread-safe state management ensures no race conditions
- **Controlled Concurrency**: Configure `max_workers` to limit parallel execution
- **Exponential Backoff**: Automatic retry with configurable backoff for failed tasks
- **Abortability**: Cancel pending tasks gracefully when needed
- **Per-Task Instrumentation**: Detailed logging and metrics for each task
- **No Race Conditions**: Thread-safe operations throughout
- **Context Manager Support**: Use with `with` statement for automatic cleanup

## Installation

The module is part of the SAAAAAA project and is available at:

```
/home/runner/work/SAAAAAA/SAAAAAA/concurrency/
```

## Usage

### Basic Example

```python
from concurrency import WorkerPool, WorkerPoolConfig

# Create configuration
config = WorkerPoolConfig(
    max_workers=50,           # Maximum concurrent workers
    max_retries=3,            # Retry failed tasks up to 3 times
    task_timeout_seconds=180, # 3 minutes per task
    backoff_base_seconds=1.0, # Start with 1s backoff
    backoff_max_seconds=60.0, # Cap backoff at 60s
)

# Create pool (or use context manager)
with WorkerPool(config) as pool:
    # Submit tasks
    def my_task(x):
        return x * 2
    
    task_id = pool.submit_task(
        task_name="double_5",
        task_fn=my_task,
        args=(5,)
    )
    
    # Get individual result
    result = pool.get_task_result(task_id)
    print(f"Result: {result.result}")  # Output: Result: 10
```

### Integration with Orchestrator

```python
from concurrency import WorkerPool, WorkerPoolConfig

def process_all_micro_questions(preprocessed_doc):
    """Process all 300 micro questions using WorkerPool."""
    
    # Configure pool
    config = WorkerPoolConfig(max_workers=50, max_retries=3)
    
    with WorkerPool(config) as pool:
        # Submit all 300 questions
        for q_num in range(1, 301):
            pool.submit_task(
                task_name=f"Q{q_num:03d}",
                task_fn=process_micro_question,
                args=(q_num, preprocessed_doc)
            )
        
        # Wait for all tasks to complete
        results = pool.wait_for_all(timeout=1800)  # 30 min timeout
        
        # Process results
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"Success rate: {len(successful)/len(results)*100:.1f}%")
        
        return results
```

### Handling Failures with Retry

```python
from concurrency import WorkerPool, WorkerPoolConfig

config = WorkerPoolConfig(
    max_workers=10,
    max_retries=3,
    backoff_base_seconds=2.0,  # Exponential: 2s, 4s, 8s, ...
    backoff_max_seconds=30.0   # Cap at 30s
)

with WorkerPool(config) as pool:
    def flaky_task():
        # This might fail occasionally
        return call_external_api()
    
    task_id = pool.submit_task("api_call", flaky_task)
    result = pool.get_task_result(task_id)
    
    if result.success:
        print(f"Success after {result.metrics.retries_used} retries")
    else:
        print(f"Failed after {result.metrics.retries_used} retries: {result.error}")
```

### Aborting Pending Tasks

```python
from concurrency import WorkerPool, WorkerPoolConfig

config = WorkerPoolConfig(max_workers=5)

with WorkerPool(config) as pool:
    # Submit many tasks
    for i in range(100):
        pool.submit_task(f"task_{i}", slow_task, args=(i,))
    
    # Something went wrong, abort pending tasks
    cancelled = pool.abort_pending_tasks()
    print(f"Cancelled {cancelled} pending tasks")
```

### Getting Metrics

```python
from concurrency import WorkerPool

with WorkerPool() as pool:
    # Submit and execute tasks...
    results = pool.wait_for_all()
    
    # Get summary metrics
    summary = pool.get_summary_metrics()
    print(f"Completed: {summary['completed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Average time: {summary['avg_execution_time_ms']:.2f}ms")
    print(f"Total retries: {summary['total_retries']}")
    
    # Get detailed per-task metrics
    all_metrics = pool.get_metrics()
    for task_id, metrics in all_metrics.items():
        print(f"{metrics.task_name}: {metrics.status} in {metrics.execution_time_ms:.2f}ms")
```

## Configuration Options

### WorkerPoolConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_workers` | int | 50 | Maximum number of concurrent workers |
| `task_timeout_seconds` | float | 180.0 | Timeout for individual task execution |
| `max_retries` | int | 3 | Maximum number of retries per task |
| `backoff_base_seconds` | float | 1.0 | Base delay for exponential backoff |
| `backoff_max_seconds` | float | 60.0 | Maximum backoff delay |
| `enable_instrumentation` | bool | True | Enable detailed logging and metrics |

## API Reference

### WorkerPool

#### Methods

- **`__init__(config: Optional[WorkerPoolConfig] = None)`**
  - Initialize the worker pool with optional configuration

- **`submit_task(task_name: str, task_fn: Callable, args: tuple = (), kwargs: Optional[Dict] = None) -> str`**
  - Submit a task for execution
  - Returns unique task identifier

- **`get_task_result(task_id: str, timeout: Optional[float] = None) -> TaskResult`**
  - Get result of a specific task
  - Blocks until task completes or timeout

- **`wait_for_all(timeout: Optional[float] = None, return_when: str = "ALL_COMPLETED") -> List[TaskResult]`**
  - Wait for all submitted tasks to complete
  - Returns list of TaskResults

- **`abort_pending_tasks() -> int`**
  - Cancel all pending tasks
  - Returns number of cancelled tasks

- **`get_metrics() -> Dict[str, TaskMetrics]`**
  - Get detailed metrics for all tasks

- **`get_summary_metrics() -> Dict[str, Any]`**
  - Get aggregated metrics summary

- **`shutdown(wait: bool = True, cancel_futures: bool = False)`**
  - Shutdown the worker pool

### TaskResult

Result object returned by task execution:

```python
@dataclass
class TaskResult:
    task_id: str                      # Unique task identifier
    task_name: str                    # Human-readable task name
    success: bool                     # Whether task succeeded
    result: Any                       # Task result (None if failed)
    error: Optional[Exception]        # Exception if failed
    metrics: Optional[TaskMetrics]    # Execution metrics
```

### TaskMetrics

Detailed metrics for task execution:

```python
@dataclass
class TaskMetrics:
    task_id: str                      # Unique task identifier
    task_name: str                    # Human-readable task name
    status: TaskStatus                # Current status
    start_time: float                 # Start time (epoch seconds)
    end_time: Optional[float]         # End time (None if not finished)
    execution_time_ms: float          # Total execution time in ms
    retries_used: int                 # Number of retries performed
    worker_id: Optional[str]          # ID of worker that executed task
    error_message: Optional[str]      # Error message if failed
```

## Invariants and Guarantees

### Preconditions
- Tasks and workers are declared before execution
- Each task function is idempotent and thread-safe
- Task functions should not share mutable state

### Invariants
- No interference between workers (thread-safe state management)
- Deterministic task execution order within priority groups
- All metrics are updated atomically
- No race conditions in result collection

### Postconditions
- Pool is usable by orchestrator/choreographer
- All resources are properly cleaned up on shutdown
- No race conditions or variability in results
- All tasks complete or fail deterministically

## Testing

Run the test suite:

```bash
python -m unittest tests.test_concurrency -v
```

Test coverage includes:
- Basic task submission and execution
- Multiple tasks in parallel
- Retry and backoff behavior
- Abort functionality
- Thread safety and race condition prevention
- Deterministic execution
- Metrics collection

## Integration with Orchestrator

The concurrency module is designed to replace the direct use of `ThreadPoolExecutor` in the orchestrator with a more robust and feature-rich alternative. See `examples/concurrency_integration_demo.py` for a complete integration example.

### Key Benefits

1. **Determinism**: Ensures consistent behavior across runs
2. **Observability**: Detailed metrics and logging for debugging
3. **Resilience**: Automatic retry with exponential backoff
4. **Control**: Fine-grained control over concurrency and timeouts
5. **Safety**: Thread-safe operations prevent race conditions

## Architecture Alignment

This module implements the concurrency requirements specified in:
- Issue: [Concurrency] Implementar módulo de concurrencia/concurrency.py
- Architecture: ARQUITECTURA_ORQUESTADOR_COREOGRAFO.md

The WorkerPool is designed to be used in:
- FASE 2: Execution of 300 micro questions (ASYNC)
- FASE 3: Scoring of 300 micro results (ASYNC)
- FASE 4: Dimension aggregation - 60 dimensions (ASYNC)
- FASE 5: Policy area aggregation - 10 areas (ASYNC)

## License

Part of the SAAAAAA project.
