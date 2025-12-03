# Executor Performance Profiling Framework

## Overview

The executor performance profiling framework provides comprehensive tracking and analysis of executor performance, including timing, memory usage, serialization overhead, and method-level granularity. It supports baseline comparison for regression detection and generates actionable reports identifying bottleneck executors.

## Features

- **Per-Executor Metrics**: Execution time, memory footprint, peak memory, serialization overhead
- **Method-Level Tracking**: Call counts, timing, and memory delta for individual methods
- **Baseline Management**: Save and load baseline metrics for comparison
- **Regression Detection**: Automatic detection of performance degradation with configurable thresholds
- **Bottleneck Analysis**: Identify top executors requiring optimization
- **Multiple Report Formats**: JSON, Markdown, and HTML exports
- **Automatic Integration**: Context manager for seamless profiling

## Architecture

### Core Components

```
ExecutorProfiler
├── ProfilerContext (context manager)
├── ExecutorMetrics (per-execution data)
│   └── MethodCallMetrics[] (method-level data)
├── Baseline Management
│   ├── save_baseline()
│   └── load_baseline()
├── Analysis
│   ├── detect_regressions()
│   └── identify_bottlenecks()
└── Reporting
    ├── generate_report()
    └── export_report()
```

### Data Models

**MethodCallMetrics**
- `class_name`: Method's class
- `method_name`: Method name
- `execution_time_ms`: Execution time in milliseconds
- `memory_delta_mb`: Memory change in MB
- `call_count`: Number of calls
- `success`: Whether call succeeded
- `error`: Error message if failed

**ExecutorMetrics**
- `executor_id`: Unique executor identifier
- `execution_time_ms`: Total execution time
- `memory_footprint_mb`: Memory usage delta
- `memory_peak_mb`: Peak memory during execution
- `serialization_time_ms`: Result serialization overhead
- `serialization_size_bytes`: Serialized result size
- `method_calls`: List of MethodCallMetrics
- `success`: Whether execution succeeded
- `error`: Error message if failed

**PerformanceRegression**
- `executor_id`: Executor with regression
- `metric_name`: Metric that regressed
- `baseline_value`: Baseline metric value
- `current_value`: Current metric value
- `delta_percent`: Percentage change
- `severity`: "warning" or "critical"
- `recommendation`: Optimization suggestion

**PerformanceReport**
- `total_executors`: Number of profiled executors
- `total_execution_time_ms`: Aggregate execution time
- `total_memory_mb`: Aggregate memory usage
- `regressions`: List of detected regressions
- `bottlenecks`: Top bottleneck executors
- `executor_rankings`: Rankings by different metrics
- `summary`: Aggregated statistics

## Usage

### Basic Profiling

```python
from farfan_pipeline.core.orchestrator.executor_profiler import ExecutorProfiler

# Create profiler
profiler = ExecutorProfiler(memory_tracking=True)

# Profile an executor
with profiler.profile_executor("D1-Q1") as ctx:
    # Execute your code
    result = executor.execute(context)
    
    # Optionally add method-level tracking
    ctx.add_method_call("TextMiner", "extract", 45.2, 2.1)
    ctx.add_method_call("Analyzer", "analyze", 120.5, 5.3)
    
    # Set result for serialization measurement
    ctx.set_result(result)

# Generate report
report = profiler.generate_report()
print(f"Execution time: {report.total_execution_time_ms}ms")
```

### With Baseline Management

```python
from pathlib import Path

profiler = ExecutorProfiler(
    baseline_path=Path("baselines/executor_baseline.json"),
    auto_save_baseline=True,  # Automatically update baseline
    memory_tracking=True,
)

# Profile executors...
# Baseline is automatically updated after each run

# Or manually save baseline
profiler.save_baseline()

# Load baseline for comparison
profiler.load_baseline(Path("baselines/executor_baseline.json"))
```

### Regression Detection

```python
# Detect regressions with custom thresholds
regressions = profiler.detect_regressions(
    thresholds={
        "execution_time_ms": 20.0,      # 20% increase triggers warning
        "memory_footprint_mb": 30.0,     # 30% increase triggers warning
        "serialization_time_ms": 50.0,   # 50% increase triggers warning
    }
)

for regression in regressions:
    print(f"{regression.severity.upper()}: {regression.executor_id}")
    print(f"  {regression.metric_name}: {regression.delta_percent:+.1f}%")
    print(f"  {regression.recommendation}")
```

### Bottleneck Identification

```python
# Identify top bottlenecks
bottlenecks = profiler.identify_bottlenecks(top_n=10)

for bottleneck in bottlenecks:
    print(f"Executor: {bottleneck['executor_id']}")
    print(f"  Score: {bottleneck['bottleneck_score']:.1f}")
    print(f"  Avg Execution Time: {bottleneck['avg_execution_time_ms']:.1f}ms")
    print(f"  Avg Memory: {bottleneck['avg_memory_mb']:.1f}MB")
    print(f"  Slowest Method: {bottleneck['slowest_method']}")
    print(f"  Recommendation: {bottleneck['recommendation']}")
```

### Report Generation and Export

```python
# Generate comprehensive report
report = profiler.generate_report(
    include_regressions=True,
    include_bottlenecks=True,
)

# Export in different formats
profiler.export_report(report, "reports/perf_report.json", format="json")
profiler.export_report(report, "reports/perf_report.md", format="markdown")
profiler.export_report(report, "reports/perf_report.html", format="html")
```

### Integration with BaseExecutor

The profiler integrates seamlessly with `BaseExecutor`:

```python
from farfan_pipeline.core.orchestrator.executors import BaseExecutor
from farfan_pipeline.core.orchestrator.executor_profiler import ExecutorProfiler

class MyExecutor(BaseExecutor):
    def execute(self, context):
        # Your execution logic
        result = self._execute_method("TextMiner", "extract", context)
        # Method calls are automatically profiled if profiler is attached
        return result

# Attach profiler to executor
profiler = ExecutorProfiler()
executor = MyExecutor("D1-Q1", config, method_executor, profiler=profiler)

# Execute with automatic profiling
result = executor.execute_with_profiling(context)

# Generate report
report = profiler.generate_report()
```

## Performance Metrics

### Execution Time
- **Total execution time**: Wall-clock time for executor
- **Method-level timing**: Per-method execution breakdown
- **Serialization overhead**: Time spent serializing results

### Memory Usage
- **Memory footprint**: Delta between start and end
- **Peak memory**: Maximum memory during execution
- **Method-level deltas**: Memory impact per method

### Serialization
- **Serialization time**: Overhead of pickling results
- **Serialization size**: Byte size of serialized output

### Method Statistics
- **Call count**: Number of method invocations
- **Average time**: Mean execution time per method
- **Slowest method**: Method with highest execution time
- **Memory-intensive method**: Method with largest memory delta

## Regression Detection

### Severity Levels

- **Warning**: Metric exceeds threshold (e.g., 20% increase)
- **Critical**: Metric exceeds 2x threshold (e.g., 40% increase)

### Threshold Configuration

```python
thresholds = {
    "execution_time_ms": 20.0,      # Execution time threshold (%)
    "memory_footprint_mb": 30.0,     # Memory threshold (%)
    "serialization_time_ms": 50.0,   # Serialization threshold (%)
}
```

### Recommendations

The profiler generates contextual recommendations:

- **Execution time regressions**: Review method sequence, add caching, optimize slow methods
- **Memory regressions**: Check for leaks, optimize data structures, implement streaming
- **Serialization regressions**: Reduce payload size, use efficient formats

## Bottleneck Analysis

### Bottleneck Score

Composite score combining multiple metrics:
```
score = execution_time * 0.5 + memory * 0.3 + serialization * 0.2
```

### Rankings

Executors are ranked by:
- **Slowest**: Highest average execution time
- **Memory-intensive**: Highest average memory usage
- **Serialization-heavy**: Highest serialization overhead

## Report Formats

### JSON
Structured data for programmatic analysis:
```json
{
  "timestamp": "2024-01-15T10:30:00",
  "total_executors": 30,
  "total_execution_time_ms": 15000.0,
  "regressions": [...],
  "bottlenecks": [...],
  "summary": {...}
}
```

### Markdown
Human-readable tables and statistics:
```markdown
# Executor Performance Report

## Summary
- **Total Executors:** 30
- **Total Execution Time:** 15000.00ms

## Performance Regressions
| Executor | Metric | Delta | Severity |
|----------|--------|-------|----------|
| D3-Q1    | execution_time_ms | +45.2% | critical |
```

### HTML
Interactive report with styling:
- Color-coded severity indicators
- Sortable tables
- Detailed breakdowns

## Best Practices

### 1. Establish Baseline Early
```python
# Profile initial implementation
profiler = ExecutorProfiler(baseline_path="baseline.json")
# ... run profiling
profiler.save_baseline()
```

### 2. Regular Regression Checks
```python
# In CI/CD pipeline
profiler.load_baseline("baseline.json")
# ... run profiling
regressions = profiler.detect_regressions()
if any(r.severity == "critical" for r in regressions):
    raise RuntimeError("Critical performance regression detected")
```

### 3. Profile Representative Workloads
```python
# Use realistic document sizes and complexity
context = load_representative_test_case()
with profiler.profile_executor("D1-Q1") as ctx:
    result = executor.execute(context)
    ctx.set_result(result)
```

### 4. Monitor Trends Over Time
```python
# Track metrics across multiple runs
for run_id in range(10):
    with profiler.profile_executor(f"D1-Q1"):
        # ... execute
        pass

# Analyze average performance
report = profiler.generate_report()
print(f"Avg execution: {report.summary['avg_execution_time_ms']}ms")
```

### 5. Focus on High-Impact Bottlenecks
```python
bottlenecks = profiler.identify_bottlenecks(top_n=5)
# Optimize top 5 bottlenecks first for maximum impact
```

## Example: Complete Profiling Workflow

```python
from pathlib import Path
from farfan_pipeline.core.orchestrator.executor_profiler import ExecutorProfiler

def profile_executor_suite(executors, baseline_path="baseline.json"):
    """Profile a suite of executors and generate reports."""
    
    # Initialize profiler with baseline
    profiler = ExecutorProfiler(
        baseline_path=Path(baseline_path),
        auto_save_baseline=True,
        memory_tracking=True,
    )
    
    # Profile all executors
    for executor_id, executor in executors.items():
        print(f"Profiling {executor_id}...")
        
        with profiler.profile_executor(executor_id) as ctx:
            result = executor.execute(test_context)
            ctx.set_result(result)
    
    # Detect regressions
    regressions = profiler.detect_regressions(
        thresholds={
            "execution_time_ms": 20.0,
            "memory_footprint_mb": 30.0,
        }
    )
    
    if regressions:
        print(f"\n⚠️  {len(regressions)} regression(s) detected:")
        for reg in regressions:
            print(f"  {reg.executor_id}: {reg.metric_name} "
                  f"{reg.delta_percent:+.1f}% ({reg.severity})")
    
    # Identify bottlenecks
    bottlenecks = profiler.identify_bottlenecks(top_n=10)
    print(f"\n🔍 Top {len(bottlenecks)} bottlenecks:")
    for i, b in enumerate(bottlenecks[:5], 1):
        print(f"  {i}. {b['executor_id']}: "
              f"{b['avg_execution_time_ms']:.1f}ms, "
              f"{b['avg_memory_mb']:.1f}MB")
    
    # Generate and export reports
    report = profiler.generate_report()
    
    output_dir = Path("profiling_output")
    output_dir.mkdir(exist_ok=True)
    
    profiler.export_report(report, output_dir / "report.json", "json")
    profiler.export_report(report, output_dir / "report.md", "markdown")
    profiler.export_report(report, output_dir / "report.html", "html")
    
    print(f"\n✓ Reports exported to {output_dir}")
    
    return report, regressions, bottlenecks
```

## Troubleshooting

### Memory Tracking Not Working
If memory tracking is unavailable:
```python
# Install psutil
pip install psutil

# Or disable memory tracking
profiler = ExecutorProfiler(memory_tracking=False)
```

### Serialization Measurement Fails
Some objects cannot be pickled:
```python
# Profiler handles this gracefully, logging a warning
# Serialization metrics will be 0.0 for unpicklable results
```

### High Profiling Overhead
To reduce overhead:
```python
# Disable memory tracking
profiler = ExecutorProfiler(memory_tracking=False)

# Profile selectively, not every execution
if should_profile:
    with profiler.profile_executor(executor_id):
        # ...
else:
    # Direct execution without profiling
    result = executor.execute(context)
```

## API Reference

See inline documentation in `src/farfan_pipeline/core/orchestrator/executor_profiler.py` for complete API details.

### Key Classes
- `ExecutorProfiler`: Main profiling orchestrator
- `ProfilerContext`: Context manager for automatic profiling
- `ExecutorMetrics`: Per-execution metrics container
- `MethodCallMetrics`: Per-method call metrics
- `PerformanceRegression`: Detected regression descriptor
- `PerformanceReport`: Comprehensive performance report

### Key Methods
- `profile_executor(executor_id)`: Create profiling context
- `detect_regressions(thresholds)`: Detect performance regressions
- `identify_bottlenecks(top_n)`: Identify top bottlenecks
- `generate_report()`: Generate comprehensive report
- `export_report(report, path, format)`: Export report to file
- `save_baseline(path)`: Save metrics as baseline
- `load_baseline(path)`: Load baseline for comparison
