"""Tests for executor performance profiling framework."""

import json
import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from farfan_pipeline.core.orchestrator.executor_profiler import (
    ExecutorMetrics,
    ExecutorProfiler,
    MethodCallMetrics,
    PerformanceRegression,
    PerformanceReport,
    ProfilerContext,
)


@pytest.fixture
def profiler():
    """Create a profiler instance for testing."""
    return ExecutorProfiler(memory_tracking=False)


@pytest.fixture
def profiler_with_memory():
    """Create a profiler with memory tracking."""
    profiler = ExecutorProfiler(memory_tracking=True)
    if profiler._psutil_process is None:
        # Mock psutil if not available
        profiler._psutil_process = MagicMock()
        profiler.memory_tracking = True
    profiler._psutil_process.memory_info.return_value.rss = 100 * 1024 * 1024
    return profiler


@pytest.fixture
def sample_metrics():
    """Create sample executor metrics."""
    method_calls = [
        MethodCallMetrics("TextMiner", "extract", 45.2, 2.1),
        MethodCallMetrics("Analyzer", "analyze", 120.5, 5.3),
        MethodCallMetrics("Validator", "validate", 30.1, 1.2),
    ]
    return ExecutorMetrics(
        executor_id="D1-Q1",
        execution_time_ms=200.0,
        memory_footprint_mb=10.5,
        memory_peak_mb=15.2,
        serialization_time_ms=5.0,
        serialization_size_bytes=1024,
        method_calls=method_calls,
    )


def test_method_call_metrics_creation():
    """Test MethodCallMetrics creation and serialization."""
    metrics = MethodCallMetrics("TestClass", "test_method", 100.5, 2.5)
    assert metrics.class_name == "TestClass"
    assert metrics.method_name == "test_method"
    assert metrics.execution_time_ms == 100.5
    assert metrics.memory_delta_mb == 2.5
    assert metrics.success is True

    data = metrics.to_dict()
    assert data["class_name"] == "TestClass"
    assert data["execution_time_ms"] == 100.5


def test_executor_metrics_properties(sample_metrics):
    """Test ExecutorMetrics computed properties."""
    assert sample_metrics.total_method_calls == 3
    assert sample_metrics.average_method_time_ms == pytest.approx(65.27, rel=0.01)

    slowest = sample_metrics.slowest_method
    assert slowest is not None
    assert slowest.class_name == "Analyzer"
    assert slowest.method_name == "analyze"

    memory_intensive = sample_metrics.memory_intensive_method
    assert memory_intensive is not None
    assert memory_intensive.class_name == "Analyzer"


def test_executor_metrics_to_dict(sample_metrics):
    """Test ExecutorMetrics serialization."""
    data = sample_metrics.to_dict()
    assert data["executor_id"] == "D1-Q1"
    assert data["execution_time_ms"] == 200.0
    assert data["total_method_calls"] == 3
    assert data["slowest_method"] == "Analyzer.analyze"
    assert len(data["method_calls"]) == 3


def test_profiler_initialization():
    """Test profiler initialization with various configurations."""
    profiler = ExecutorProfiler()
    # Memory tracking may be False if psutil not installed
    assert profiler.auto_save_baseline is False
    assert len(profiler.metrics) == 0

    profiler2 = ExecutorProfiler(memory_tracking=False, auto_save_baseline=True)
    assert profiler2.memory_tracking is False
    assert profiler2.auto_save_baseline is True


def test_profiler_context_basic(profiler):
    """Test basic profiler context usage."""
    with profiler.profile_executor("TEST-01") as ctx:
        ctx.add_method_call("Class1", "method1", 50.0, 1.0)
        ctx.add_method_call("Class2", "method2", 75.0, 2.5)
        ctx.set_result({"test": "data"})

    assert "TEST-01" in profiler.metrics
    metrics = profiler.metrics["TEST-01"][0]
    assert metrics.executor_id == "TEST-01"
    assert len(metrics.method_calls) == 2
    assert metrics.success is True


def test_profiler_context_with_exception(profiler):
    """Test profiler context with exception."""
    with pytest.raises(ValueError):
        with profiler.profile_executor("TEST-02"):
            raise ValueError("Test error")

    assert "TEST-02" in profiler.metrics
    metrics = profiler.metrics["TEST-02"][0]
    assert metrics.success is False
    assert metrics.error == "Test error"


def test_profiler_context_memory_tracking(profiler_with_memory):
    """Test memory tracking in profiler context."""
    with profiler_with_memory.profile_executor("TEST-03"):
        pass

    metrics = profiler_with_memory.metrics["TEST-03"][0]
    assert metrics.memory_footprint_mb >= 0


def test_profiler_serialization_measurement(profiler):
    """Test serialization overhead measurement."""
    test_data = {"key": "value" * 1000, "list": list(range(100))}

    with profiler.profile_executor("TEST-04") as ctx:
        ctx.set_result(test_data)

    metrics = profiler.metrics["TEST-04"][0]
    assert metrics.serialization_time_ms > 0
    assert metrics.serialization_size_bytes > 0


def test_regression_detection_no_baseline(profiler, sample_metrics):
    """Test regression detection without baseline."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    regressions = profiler.detect_regressions()
    assert len(regressions) == 0


def test_regression_detection_with_baseline(profiler):
    """Test regression detection with baseline."""
    baseline = ExecutorMetrics(
        executor_id="D1-Q1",
        execution_time_ms=100.0,
        memory_footprint_mb=5.0,
        memory_peak_mb=8.0,
        serialization_time_ms=2.0,
        serialization_size_bytes=512,
        method_calls=[],
    )
    profiler.baseline_metrics["D1-Q1"] = baseline

    regressed = ExecutorMetrics(
        executor_id="D1-Q1",
        execution_time_ms=150.0,
        memory_footprint_mb=8.0,
        memory_peak_mb=12.0,
        serialization_time_ms=4.0,
        serialization_size_bytes=1024,
        method_calls=[],
    )
    profiler.record_executor_metrics("D1-Q1", regressed)

    regressions = profiler.detect_regressions(
        thresholds={"execution_time_ms": 20.0, "memory_footprint_mb": 30.0}
    )

    assert len(regressions) >= 1
    exec_regression = next(
        (r for r in regressions if r.metric_name == "execution_time_ms"), None
    )
    assert exec_regression is not None
    assert exec_regression.delta_percent == 50.0
    assert exec_regression.threshold_exceeded is True


def test_regression_severity_classification(profiler):
    """Test regression severity classification."""
    baseline = ExecutorMetrics(
        executor_id="D2-Q1",
        execution_time_ms=100.0,
        memory_footprint_mb=5.0,
        memory_peak_mb=8.0,
        serialization_time_ms=2.0,
        serialization_size_bytes=512,
        method_calls=[],
    )
    profiler.baseline_metrics["D2-Q1"] = baseline

    critical_regression = ExecutorMetrics(
        executor_id="D2-Q1",
        execution_time_ms=300.0,
        memory_footprint_mb=5.0,
        memory_peak_mb=8.0,
        serialization_time_ms=2.0,
        serialization_size_bytes=512,
        method_calls=[],
    )
    profiler.record_executor_metrics("D2-Q1", critical_regression)

    regressions = profiler.detect_regressions(thresholds={"execution_time_ms": 50.0})

    exec_regression = next(
        (r for r in regressions if r.metric_name == "execution_time_ms"), None
    )
    assert exec_regression is not None
    assert exec_regression.severity == "critical"
    assert "200.0%" in exec_regression.recommendation


def test_bottleneck_identification(profiler):
    """Test bottleneck identification."""
    fast_metrics = ExecutorMetrics(
        executor_id="D1-Q1",
        execution_time_ms=50.0,
        memory_footprint_mb=2.0,
        memory_peak_mb=3.0,
        serialization_time_ms=1.0,
        serialization_size_bytes=256,
        method_calls=[],
    )

    slow_metrics = ExecutorMetrics(
        executor_id="D2-Q1",
        execution_time_ms=500.0,
        memory_footprint_mb=50.0,
        memory_peak_mb=75.0,
        serialization_time_ms=20.0,
        serialization_size_bytes=4096,
        method_calls=[MethodCallMetrics("SlowClass", "slow_method", 400.0, 40.0)],
    )

    profiler.record_executor_metrics("D1-Q1", fast_metrics)
    profiler.record_executor_metrics("D2-Q1", slow_metrics)

    bottlenecks = profiler.identify_bottlenecks(top_n=2)

    assert len(bottlenecks) == 2
    assert bottlenecks[0]["executor_id"] == "D2-Q1"
    assert bottlenecks[0]["bottleneck_score"] > bottlenecks[1]["bottleneck_score"]
    assert "SlowClass.slow_method" in bottlenecks[0]["slowest_method"]


def test_performance_report_generation(profiler, sample_metrics):
    """Test comprehensive performance report generation."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)

    another_metrics = ExecutorMetrics(
        executor_id="D1-Q2",
        execution_time_ms=150.0,
        memory_footprint_mb=8.0,
        memory_peak_mb=12.0,
        serialization_time_ms=3.0,
        serialization_size_bytes=768,
        method_calls=[],
    )
    profiler.record_executor_metrics("D1-Q2", another_metrics)

    report = profiler.generate_report()

    assert report.total_executors == 2
    assert report.total_execution_time_ms == 350.0
    assert report.total_memory_mb == 18.5
    assert report.summary["total_executors_profiled"] == 2
    assert report.summary["total_executions"] == 2
    assert "slowest" in report.executor_rankings
    assert "memory_intensive" in report.executor_rankings


def test_executor_rankings(profiler):
    """Test executor ranking by different metrics."""
    for i in range(5):
        metrics = ExecutorMetrics(
            executor_id=f"D{i}-Q1",
            execution_time_ms=100.0 * (i + 1),
            memory_footprint_mb=10.0 * (i + 1),
            memory_peak_mb=15.0 * (i + 1),
            serialization_time_ms=5.0 * (i + 1),
            serialization_size_bytes=1024 * (i + 1),
            method_calls=[],
        )
        profiler.record_executor_metrics(f"D{i}-Q1", metrics)

    slowest = profiler._rank_executors_by("execution_time_ms", top_n=3)
    assert len(slowest) == 3
    assert slowest[0] == "D4-Q1"
    assert slowest[1] == "D3-Q1"
    assert slowest[2] == "D2-Q1"

    memory_intensive = profiler._rank_executors_by("memory_footprint_mb", top_n=3)
    assert memory_intensive[0] == "D4-Q1"


def test_baseline_save_and_load(profiler, sample_metrics):
    """Test baseline save and load functionality."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    profiler.baseline_metrics["D1-Q1"] = sample_metrics

    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        profiler.save_baseline(baseline_path)

        assert baseline_path.exists()

        new_profiler = ExecutorProfiler()
        new_profiler.load_baseline(baseline_path)

        assert "D1-Q1" in new_profiler.baseline_metrics
        loaded = new_profiler.baseline_metrics["D1-Q1"]
        assert loaded.executor_id == "D1-Q1"
        assert loaded.execution_time_ms == 200.0


def test_baseline_auto_update(sample_metrics):
    """Test automatic baseline updating."""
    with tempfile.TemporaryDirectory() as tmpdir:
        baseline_path = Path(tmpdir) / "baseline.json"
        profiler = ExecutorProfiler(
            baseline_path=baseline_path, auto_save_baseline=True
        )

        profiler.record_executor_metrics("D1-Q1", sample_metrics)

        # Auto-update updates baseline_metrics but doesn't save to file automatically
        # Must call save_baseline() explicitly to persist
        assert "D1-Q1" in profiler.baseline_metrics

        # Save and verify
        profiler.save_baseline()
        assert baseline_path.exists()


def test_report_export_json(profiler, sample_metrics):
    """Test JSON report export."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    report = profiler.generate_report()

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.json"
        profiler.export_report(report, report_path, format="json")

        assert report_path.exists()
        with open(report_path) as f:
            data = json.load(f)

        assert data["total_executors"] == 1
        assert "summary" in data


def test_report_export_markdown(profiler, sample_metrics):
    """Test Markdown report export."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)

    baseline = ExecutorMetrics(
        executor_id="D1-Q1",
        execution_time_ms=100.0,
        memory_footprint_mb=5.0,
        memory_peak_mb=8.0,
        serialization_time_ms=2.0,
        serialization_size_bytes=512,
        method_calls=[],
    )
    profiler.baseline_metrics["D1-Q1"] = baseline

    report = profiler.generate_report(
        include_regressions=True, include_bottlenecks=True
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.md"
        profiler.export_report(report, report_path, format="markdown")

        assert report_path.exists()
        content = report_path.read_text()
        assert "# Executor Performance Report" in content
        assert "## Summary" in content


def test_report_export_html(profiler, sample_metrics):
    """Test HTML report export."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    report = profiler.generate_report()

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.html"
        profiler.export_report(report, report_path, format="html")

        assert report_path.exists()
        content = report_path.read_text()
        assert "<html>" in content
        assert "Executor Performance Report" in content
        assert "<table>" in content


def test_report_export_invalid_format(profiler, sample_metrics):
    """Test invalid format raises error."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    report = profiler.generate_report()

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "report.txt"
        with pytest.raises(ValueError, match="Unsupported format"):
            profiler.export_report(report, report_path, format="invalid")


def test_clear_metrics(profiler, sample_metrics):
    """Test clearing metrics while preserving baseline."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    profiler.baseline_metrics["D1-Q1"] = sample_metrics

    assert len(profiler.metrics) == 1
    assert len(profiler.baseline_metrics) == 1

    profiler.clear_metrics()

    assert len(profiler.metrics) == 0
    assert len(profiler.baseline_metrics) == 1


def test_profiler_without_psutil():
    """Test profiler works without psutil installed."""
    # psutil is imported at module level, can't easily patch it
    # Instead, test the behavior when _psutil_process is None
    profiler = ExecutorProfiler(memory_tracking=True)
    profiler._psutil_process = None

    memory = profiler._get_memory_usage_mb()
    assert memory == 0.0


def test_multiple_executions_same_executor(profiler):
    """Test multiple executions of the same executor."""
    for i in range(3):
        metrics = ExecutorMetrics(
            executor_id="D1-Q1",
            execution_time_ms=100.0 + i * 10,
            memory_footprint_mb=5.0 + i,
            memory_peak_mb=8.0 + i,
            serialization_time_ms=2.0,
            serialization_size_bytes=512,
            method_calls=[],
        )
        profiler.record_executor_metrics("D1-Q1", metrics)

    assert len(profiler.metrics["D1-Q1"]) == 3

    report = profiler.generate_report()
    assert report.summary["total_executions"] == 3


def test_performance_regression_to_dict():
    """Test PerformanceRegression serialization."""
    regression = PerformanceRegression(
        executor_id="D1-Q1",
        metric_name="execution_time_ms",
        baseline_value=100.0,
        current_value=150.0,
        delta_percent=50.0,
        severity="warning",
        threshold_exceeded=True,
        recommendation="Optimize slow methods",
    )

    data = regression.to_dict()
    assert data["executor_id"] == "D1-Q1"
    assert data["delta_percent"] == 50.0
    assert data["severity"] == "warning"


def test_performance_report_to_dict(profiler, sample_metrics):
    """Test PerformanceReport serialization."""
    profiler.record_executor_metrics("D1-Q1", sample_metrics)
    report = profiler.generate_report()

    data = report.to_dict()
    assert "timestamp" in data
    assert "total_executors" in data
    assert "summary" in data
    assert "executor_rankings" in data
    assert isinstance(data["regressions"], list)


def test_method_call_metrics_with_error():
    """Test MethodCallMetrics with error."""
    metrics = MethodCallMetrics(
        "ErrorClass",
        "error_method",
        50.0,
        0.0,
        success=False,
        error="Test error",
    )

    assert metrics.success is False
    assert metrics.error == "Test error"


def test_profiler_context_set_result_serialization_error(profiler):
    """Test handling of serialization errors."""

    class UnserializableClass:
        def __reduce__(self):
            raise TypeError("Cannot serialize")

    with profiler.profile_executor("TEST-05") as ctx:
        ctx.set_result(UnserializableClass())

    metrics = profiler.metrics["TEST-05"][0]
    assert metrics.serialization_time_ms == 0.0
    assert metrics.serialization_size_bytes == 0


def test_recommendation_generation(profiler):
    """Test recommendation generation for different metrics."""
    rec_time = profiler._generate_recommendation("D1-Q1", "execution_time_ms", 50.0)
    assert "execution time" in rec_time.lower()
    assert "50.0%" in rec_time

    rec_memory = profiler._generate_recommendation("D1-Q1", "memory_footprint_mb", 75.0)
    assert "memory" in rec_memory.lower()
    assert "75.0%" in rec_memory

    rec_serial = profiler._generate_recommendation(
        "D1-Q1", "serialization_time_ms", 100.0
    )
    assert "serialization" in rec_serial.lower()


def test_bottleneck_recommendation_generation(profiler):
    """Test bottleneck recommendation generation."""
    avg_metrics = {
        "execution_time_ms": 1500.0,
        "memory_footprint_mb": 150.0,
        "serialization_time_ms": 150.0,
        "total_method_calls": 10,
        "slowest_method": "SlowClass.slow_method",
        "memory_intensive_method": "BigClass.big_method",
    }

    rec = profiler._generate_bottleneck_recommendation("D1-Q1", avg_metrics)
    assert "execution time" in rec.lower()
    assert "memory usage" in rec.lower()
    assert "serialization overhead" in rec.lower()


def test_compute_average_metrics_empty(profiler):
    """Test average metrics computation with empty list."""
    avg = profiler._compute_average_metrics([])
    assert avg == {}


def test_baseline_load_nonexistent_file(profiler):
    """Test loading baseline from nonexistent file."""
    profiler.load_baseline(Path("/nonexistent/baseline.json"))
    assert len(profiler.baseline_metrics) == 0


def test_save_baseline_no_path(profiler):
    """Test saving baseline without path raises error."""
    with pytest.raises(ValueError, match="No baseline path"):
        profiler.save_baseline()
