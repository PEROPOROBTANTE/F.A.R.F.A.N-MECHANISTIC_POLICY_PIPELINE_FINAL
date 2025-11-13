# Executor Monitoring and Instrumentation Guide

## Overview

The executors module now includes comprehensive monitoring, logging, and instrumentation capabilities to help with production debugging, performance tracking, and system optimization.

## Features

### 1. Structured Logging

All executors now use Python's `logging` module instead of `warnings.warn()` for better control and integration with logging infrastructure.

#### Log Levels Used

- **DEBUG**: Detailed information about internal state (quantum convergence, meta-learner decisions)
- **INFO**: High-level execution flow (question starts/ends, batch execution progress)
- **WARNING**: Non-fatal issues (information bottlenecks detected)
- **ERROR**: Method failures with full context and retry information

#### Configuring Logging

```python
import logging

# Set up logging for executors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# For more detailed debugging
logger = logging.getLogger('saaaaaa.core.orchestrator.executors')
logger.setLevel(logging.DEBUG)
```

#### Log Examples

```
2024-11-02 10:15:23 - saaaaaa.core.orchestrator.executors - INFO - Starting execution with 15 methods using strategy 2
2024-11-02 10:15:23 - saaaaaa.core.orchestrator.executors - DEBUG - Meta-learner selected strategy 2 (performance: 0.847)
2024-11-02 10:15:23 - saaaaaa.core.orchestrator.executors - DEBUG - Quantum optimization converged in 0.0234s, path length: 15
2024-11-02 10:15:24 - saaaaaa.core.orchestrator.executors - WARNING - Information bottlenecks detected at stages: [7, 12]
2024-11-02 10:15:25 - saaaaaa.core.orchestrator.executors - INFO - Execution completed in 1.823s: 14/15 methods successful
```

### 2. Retry Logic

Methods that fail are automatically retried up to 3 times with exponential backoff.

#### Configuration

The retry behavior is built into the `execute_with_optimization` method:

- **Max retries**: 3 attempts
- **Backoff**: 0.1s * (attempt_number)
  - 1st retry: 0.1s delay
  - 2nd retry: 0.2s delay
  - 3rd retry: 0.3s delay

#### Error Handling

On final failure after all retries, errors are logged with full context:

```python
# Logged error includes:
# - method name
# - class name
# - attempt number
# - error type
# - full stack trace (when exc_info=True)
```

### 3. Execution Metrics

Comprehensive metrics are collected automatically during execution.

#### Accessing Metrics

```python
from saaaaaa.core.orchestrator.executors import get_execution_metrics

# Get global metrics instance
metrics = get_execution_metrics()

# Get summary
summary = metrics.get_summary()
print(summary)
```

#### Metrics Collected

##### Execution Statistics
- `total_executions`: Total number of method executions attempted
- `successful_executions`: Number of successful executions
- `failed_executions`: Number of failed executions
- `success_rate`: Ratio of successful to total executions
- `total_execution_time`: Cumulative execution time
- `avg_execution_time`: Average time per execution
- `retry_attempts`: Total number of retry attempts

##### Quantum Optimizer Metrics
- `quantum_optimizations`: Number of quantum optimization invocations
- `avg_quantum_convergence_time`: Average time for quantum path optimization

##### Meta-Learner Metrics
- `meta_learner_strategies`: Dictionary of strategy selections (strategy_id -> count)

##### Information Flow Metrics
- `information_bottlenecks_detected`: Number of bottlenecks found
- `method_execution_times`: Per-method execution time history

#### Metrics in Results

Execution results now include metrics summary in metadata:

```python
result = executor.execute(doc, method_executor)

# Access metrics from result
metrics_summary = result['meta']['metrics_summary']
print(f"Success rate: {metrics_summary['success_rate']:.2%}")
print(f"Total time: {metrics_summary['total_execution_time']:.2f}s")
```

### 4. Performance Tracking

#### Per-Method Execution Times

Track execution times for each method:

```python
from saaaaaa.core.orchestrator.executors import get_execution_metrics

metrics = get_execution_metrics()

# Get execution times for specific method
method_times = metrics.method_execution_times.get('PolicyProcessor.process', [])
if method_times:
    print(f"Average: {sum(method_times) / len(method_times):.3f}s")
    print(f"Min: {min(method_times):.3f}s")
    print(f"Max: {max(method_times):.3f}s")
```

#### Quantum Optimizer Convergence

Monitor quantum optimization performance:

```python
metrics = get_execution_metrics()

convergence_times = metrics.quantum_convergence_times
if convergence_times:
    print(f"Average convergence: {sum(convergence_times) / len(convergence_times):.4f}s")
    print(f"Fastest: {min(convergence_times):.4f}s")
    print(f"Slowest: {max(convergence_times):.4f}s")
```

#### Meta-Learner Strategy Performance

Analyze which strategies are selected most often:

```python
metrics = get_execution_metrics()

strategy_selections = metrics.meta_learner_strategy_selections
total_selections = sum(strategy_selections.values())

for strategy_id, count in sorted(strategy_selections.items(), key=lambda x: x[1], reverse=True):
    percentage = (count / total_selections) * 100
    print(f"Strategy {strategy_id}: {count} selections ({percentage:.1f}%)")
```

## Advanced Paradigms Reference

### When Each Paradigm Activates

1. **Quantum Optimization**: Activated when `num_methods >= 3` for path selection
2. **Neuromorphic Computing**: Activated on every data flow for adaptive processing
3. **Causal Inference**: Activated when optimizing execution order for 2+ questions
4. **Meta-Learning**: Activated on every execution to select optimal strategy
5. **Information Theory**: Activated to detect bottlenecks and optimize entropy
6. **Attention Mechanism**: Activated to prioritize method execution
7. **Topological Analysis**: Activated for complex data manifold understanding
8. **Category Theory**: Activated for composable execution pipelines
9. **Probabilistic Programming**: Activated for uncertainty quantification per method

### Expected Execution Times

| Operation | Time Range | Notes |
|-----------|------------|-------|
| Single Question Executor | 50-200ms | Varies by question complexity |
| Batch Execution (5 questions) | 300-1000ms | Includes optimization overhead |
| Batch Execution (30 questions) | 2-5 seconds | Full orchestrator workload |
| Quantum Optimization | +10-50ms | Per invocation |
| Causal Structure Learning | +100-500ms | For 30 variables |

### Memory Requirements

| Component | Memory Usage |
|-----------|--------------|
| Base Memory per Executor | ~10MB |
| Quantum State (30 methods) | ~5MB |
| Causal Graph (30 variables) | ~50MB |
| Neuromorphic Controller | ~20MB |
| Information Flow Optimizer | ~15MB |
| **Total for Full Orchestrator** | **~200-300MB** |
| **Large Documents (10MB+)** | **+50-100MB working memory** |

## Production Deployment

### Recommended Configuration

```python
import logging
import logging.handlers

# Set up rotating file handler
handler = logging.handlers.RotatingFileHandler(
    'executor_logs.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
handler.setLevel(logging.INFO)

# Set up formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)

# Configure executor logger
logger = logging.getLogger('saaaaaa.core.orchestrator.executors')
logger.addHandler(handler)
logger.setLevel(logging.INFO)
```

### Monitoring Dashboard

Periodically export metrics for monitoring:

```python
from saaaaaa.core.orchestrator.executors import get_execution_metrics
import json
import time

def export_metrics_to_file():
    """Export metrics to JSON for monitoring dashboard"""
    metrics = get_execution_metrics()
    summary = metrics.get_summary()
    
    with open('executor_metrics.json', 'w') as f:
        json.dump({
            'timestamp': time.time(),
            'metrics': summary
        }, f, indent=2)

# Call periodically (e.g., every 60 seconds)
export_metrics_to_file()
```

### Performance Alerts

Set up alerts for performance issues:

```python
from saaaaaa.core.orchestrator.executors import get_execution_metrics

def check_performance_alerts():
    """Check metrics and alert on issues"""
    metrics = get_execution_metrics()
    summary = metrics.get_summary()
    
    # Alert on low success rate
    if summary['success_rate'] < 0.95:
        alert(f"Low success rate: {summary['success_rate']:.2%}")
    
    # Alert on high retry rate
    retry_rate = summary['retry_attempts'] / max(summary['total_executions'], 1)
    if retry_rate > 0.1:
        alert(f"High retry rate: {retry_rate:.2%}")
    
    # Alert on slow execution
    if summary['avg_execution_time'] > 2.0:
        alert(f"Slow execution: {summary['avg_execution_time']:.2f}s average")
    
    # Alert on information bottlenecks
    if summary['information_bottlenecks_detected'] > 0:
        alert(f"Information bottlenecks detected: {summary['information_bottlenecks_detected']}")
```

## Testing

See `tests/test_executor_monitoring.py` for comprehensive test examples covering:

- Metrics collection
- Logging functionality
- Retry logic
- Instrumentation accuracy
- Performance tracking

## Troubleshooting

### High Retry Rates

If you see many retries:

1. Check logs for common error patterns
2. Review method dependencies - may need to be executed in different order
3. Verify input data quality
4. Check resource availability (memory, CPU)

### Slow Execution

If execution times are high:

1. Check for information bottlenecks in logs
2. Review quantum optimizer convergence times
3. Analyze per-method execution times to find slow methods
4. Consider reducing document size or complexity

### Information Bottlenecks

If bottlenecks are frequently detected:

1. Review method sequence ordering
2. Check data quality at bottleneck stages
3. Consider alternative execution strategies
4. Verify method implementations are returning rich data

## API Reference

### `get_execution_metrics() -> ExecutionMetrics`

Returns the global ExecutionMetrics instance.

### `ExecutionMetrics` Class

#### Methods
- `record_execution(success: bool, execution_time: float, method_key: str = None)`
- `record_quantum_optimization(convergence_time: float)`
- `record_meta_learner_selection(strategy_idx: int)`
- `record_information_bottleneck()`
- `record_retry()`
- `get_summary() -> Dict[str, Any]`

### Logger Name

`saaaaaa.core.orchestrator.executors`

Use this logger name for configuration and filtering.
