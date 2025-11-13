# Métricas y Seguimiento Canónico

Canonical Metrics and Monitoring System for SAAAAAA Orchestration.

## Overview

This module provides comprehensive health checks, metrics export, and observability tools for the SAAAAAA orchestration system. It enables real-time monitoring of system components and provides detailed metrics for performance analysis.

## Components

### 1. Health Module (`health.py`)

Provides system-wide health checks with component-level granularity.

#### Features
- Method executor health monitoring
- Questionnaire provider validation
- Resource usage tracking
- Health status classification (healthy, degraded, unhealthy)
- Warning thresholds for proactive monitoring

#### Usage

```python
from metricas_y_seguimiento_canonico import get_system_health

# Get comprehensive health status
health = get_system_health(orchestrator)

# Check overall status
if health['status'] == 'healthy':
    print("System is healthy")
elif health['status'] == 'degraded':
    print("System is degraded - check components")
else:
    print("System is unhealthy - immediate attention required")

# Check individual components
for component, status in health['components'].items():
    print(f"{component}: {status['status']}")
```

#### Health Status Levels

1. **healthy**: All components functioning normally
2. **degraded**: Some components showing warning signs
   - CPU usage > 80%
   - Memory usage > 3500MB (near 4GB limit)
   - Questionnaire provider has no data
3. **unhealthy**: Critical component failures

#### Component Checks

1. **method_executor**
   - Instances loaded count
   - Calibrations loaded count
   - Overall status

2. **questionnaire_provider**
   - Data availability
   - Provider status

3. **resources**
   - CPU percentage
   - Memory usage (MB)
   - Worker budget
   - Threshold monitoring

### 2. Metrics Module (`metrics.py`)

Exports comprehensive system metrics for monitoring and analysis.

#### Features
- Phase metrics collection
- Resource usage history
- Abort status tracking
- Phase status monitoring

#### Usage

```python
from metricas_y_seguimiento_canonico import export_metrics

# Export all metrics
metrics = export_metrics(orchestrator)

# Access phase metrics
print(metrics['phase_metrics'])

# Access resource usage
print(metrics['resource_usage'])

# Check abort status
if metrics['abort_status']['is_aborted']:
    print(f"System aborted: {metrics['abort_status']['reason']}")
    print(f"Timestamp: {metrics['abort_status']['timestamp']}")

# Monitor phase status
for phase_id, status in metrics['phase_status'].items():
    print(f"Phase {phase_id}: {status}")
```

#### Exported Metrics

1. **phase_metrics**
   - Execution times
   - Success/failure rates
   - Performance statistics

2. **resource_usage**
   - Historical usage data
   - CPU trends
   - Memory trends
   - Worker budget consumption

3. **abort_status**
   - Is aborted flag
   - Abort reason
   - Abort timestamp

4. **phase_status**
   - Per-phase status
   - Phase completion tracking

## Integration

### With Orchestrator

```python
from saaaaaa.core.orchestrator.core import Orchestrator
from metricas_y_seguimiento_canonico import get_system_health, export_metrics

# Create orchestrator
orchestrator = Orchestrator(...)

# Check health before processing
health = get_system_health(orchestrator)
if health['status'] != 'healthy':
    print("Warning: System is not fully healthy")

# Process document
result = orchestrator.process_development_plan(pdf_path)

# Export metrics after processing
metrics = export_metrics(orchestrator)
print(f"Phase metrics: {metrics['phase_metrics']}")
```

### With Monitoring Systems

#### Prometheus-style Metrics

```python
from metricas_y_seguimiento_canonico import export_metrics

def prometheus_format(metrics):
    """Convert metrics to Prometheus format."""
    lines = []
    
    # Health status as gauge
    health = get_system_health(orchestrator)
    status_value = {
        'healthy': 1,
        'degraded': 0.5,
        'unhealthy': 0
    }.get(health['status'], 0)
    lines.append(f'saaaaaa_health_status {status_value}')
    
    # Resource metrics
    if 'resources' in health['components']:
        resources = health['components']['resources']
        lines.append(f'saaaaaa_cpu_percent {resources.get("cpu_percent", 0)}')
        lines.append(f'saaaaaa_memory_mb {resources.get("memory_mb", 0)}')
    
    return '\n'.join(lines)
```

#### JSON API

```python
from flask import Flask, jsonify
from metricas_y_seguimiento_canonico import get_system_health, export_metrics

app = Flask(__name__)

@app.route('/health')
def health_endpoint():
    """Health check endpoint."""
    return jsonify(get_system_health(orchestrator))

@app.route('/metrics')
def metrics_endpoint():
    """Metrics export endpoint."""
    return jsonify(export_metrics(orchestrator))
```

## Best Practices

### 1. Regular Health Checks

```python
import time

def monitor_health(orchestrator, interval=60):
    """Monitor health every interval seconds."""
    while True:
        health = get_system_health(orchestrator)
        
        if health['status'] != 'healthy':
            log_alert(health)
        
        time.sleep(interval)
```

### 2. Metrics Collection

```python
def collect_metrics(orchestrator):
    """Collect and store metrics."""
    metrics = export_metrics(orchestrator)
    
    # Store in time-series database
    store_metrics(
        timestamp=metrics['timestamp'],
        data=metrics
    )
```

### 3. Alerting

```python
def check_and_alert(orchestrator):
    """Check health and send alerts if needed."""
    health = get_system_health(orchestrator)
    
    if health['status'] == 'unhealthy':
        send_alert(
            severity='critical',
            message='System health is critical',
            components=health['components']
        )
    elif health['status'] == 'degraded':
        send_alert(
            severity='warning',
            message='System health is degraded',
            components=health['components']
        )
```

## Error Handling

All functions in this module are designed to be resilient:

```python
# Health checks return errors in component status
health = get_system_health(orchestrator)
for component, status in health['components'].items():
    if status['status'] == 'unhealthy':
        print(f"Error in {component}: {status.get('error', 'Unknown error')}")

# Metrics export includes error information
metrics = export_metrics(orchestrator)
if 'error' in metrics['phase_metrics']:
    print(f"Phase metrics error: {metrics['phase_metrics']['error']}")
```

## Dependencies

- `datetime`: Timestamp generation
- `logging`: Structured logging
- `typing`: Type hints

## Testing

Run the test suite to verify monitoring functionality:

```bash
# Test health checks
python -m pytest tests/test_health.py -v

# Test metrics export
python -m pytest tests/test_metrics.py -v
```

## Contributing

When adding new monitoring features:

1. Add component check to `health.py`
2. Add metric export to `metrics.py`
3. Update this README
4. Add tests for new functionality
5. Ensure type hints are complete

## License

Part of the SAAAAAA orchestration system.
