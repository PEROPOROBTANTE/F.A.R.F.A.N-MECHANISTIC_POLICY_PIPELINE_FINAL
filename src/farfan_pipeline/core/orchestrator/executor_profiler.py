"""Executor performance profiling framework with regression detection.

This module provides comprehensive profiling for executor performance including:
- Per-executor timing, memory, and serialization metrics
- Method call tracking with granular statistics
- Baseline comparison for regression detection
- Performance report generation identifying bottlenecks
- Integration with BaseExecutor for automatic capture

Architecture:
- ExecutorMetrics: Per-executor performance data
- MethodCallMetrics: Per-method call statistics
- ExecutorProfiler: Main profiler with baseline management
- ProfilerContext: Context manager for automatic profiling
- PerformanceReport: Structured report with bottleneck analysis

Usage:
    profiler = ExecutorProfiler()
    with profiler.profile_executor("D1-Q1"):
        result = executor.execute(context)
    report = profiler.generate_report()
"""

from __future__ import annotations

import gc
import json
import logging
import pickle
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

HIGH_EXECUTION_TIME_THRESHOLD_MS = 1000
HIGH_MEMORY_THRESHOLD_MB = 100
HIGH_SERIALIZATION_THRESHOLD_MS = 100


@dataclass
class MethodCallMetrics:
    """Metrics for a single method call within an executor."""

    class_name: str
    method_name: str
    execution_time_ms: float
    memory_delta_mb: float
    call_count: int = 1
    success: bool = True
    error: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ExecutorMetrics:
    """Comprehensive metrics for a single executor execution."""

    executor_id: str
    execution_time_ms: float
    memory_footprint_mb: float
    memory_peak_mb: float
    serialization_time_ms: float
    serialization_size_bytes: int
    method_calls: list[MethodCallMetrics] = field(default_factory=list)
    call_count: int = 1
    success: bool = True
    error: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_method_calls(self) -> int:
        """Total number of method calls during execution."""
        return sum(m.call_count for m in self.method_calls)

    @property
    def average_method_time_ms(self) -> float:
        """Average method execution time."""
        if not self.method_calls:
            return 0.0
        return sum(m.execution_time_ms for m in self.method_calls) / len(
            self.method_calls
        )

    @property
    def slowest_method(self) -> MethodCallMetrics | None:
        """Identify the slowest method call."""
        if not self.method_calls:
            return None
        return max(self.method_calls, key=lambda m: m.execution_time_ms)

    @property
    def memory_intensive_method(self) -> MethodCallMetrics | None:
        """Identify the most memory-intensive method call."""
        if not self.method_calls:
            return None
        return max(self.method_calls, key=lambda m: abs(m.memory_delta_mb))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["method_calls"] = [m.to_dict() for m in self.method_calls]
        data["total_method_calls"] = self.total_method_calls
        data["average_method_time_ms"] = self.average_method_time_ms
        slowest = self.slowest_method
        data["slowest_method"] = (
            f"{slowest.class_name}.{slowest.method_name}" if slowest else None
        )
        memory_intensive = self.memory_intensive_method
        data["memory_intensive_method"] = (
            f"{memory_intensive.class_name}.{memory_intensive.method_name}"
            if memory_intensive
            else None
        )
        return data


@dataclass
class PerformanceRegression:
    """Detected performance regression for an executor."""

    executor_id: str
    metric_name: str
    baseline_value: float
    current_value: float
    delta_percent: float
    severity: str
    threshold_exceeded: bool
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PerformanceReport:
    """Comprehensive performance report with bottleneck analysis."""

    timestamp: str
    total_executors: int
    total_execution_time_ms: float
    total_memory_mb: float
    regressions: list[PerformanceRegression] = field(default_factory=list)
    bottlenecks: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    executor_rankings: dict[str, list[str]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["regressions"] = [r.to_dict() for r in self.regressions]
        return data


class ExecutorProfiler:
    """Performance profiler with baseline management and regression detection.

    Tracks per-executor metrics including timing, memory, serialization overhead,
    and method call counts. Supports baseline comparison for regression detection
    and generates comprehensive performance reports.
    """

    def __init__(
        self,
        baseline_path: Path | str | None = None,
        auto_save_baseline: bool = False,
        memory_tracking: bool = True,
    ) -> None:
        """Initialize the profiler.

        Args:
            baseline_path: Path to baseline metrics file (JSON)
            auto_save_baseline: Automatically update baseline after each run
            memory_tracking: Enable memory tracking (adds overhead)
        """
        self.baseline_path = Path(baseline_path) if baseline_path else None
        self.auto_save_baseline = auto_save_baseline
        self.memory_tracking = memory_tracking

        self.metrics: dict[str, list[ExecutorMetrics]] = defaultdict(list)
        self.baseline_metrics: dict[str, ExecutorMetrics] = {}
        self.regressions: list[PerformanceRegression] = []

        self._psutil = None
        self._psutil_process = None
        if memory_tracking:
            try:
                import psutil

                self._psutil = psutil
                self._psutil_process = psutil.Process()
            except ImportError:
                logger.warning(
                    "psutil not available, memory tracking disabled. "
                    "Install with: pip install psutil"
                )
                self.memory_tracking = False

        if self.baseline_path and self.baseline_path.exists():
            self.load_baseline(self.baseline_path)

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        if not self.memory_tracking or not self._psutil_process:
            return 0.0
        try:
            return self._psutil_process.memory_info().rss / (1024 * 1024)
        except Exception as exc:
            logger.warning(f"Failed to get memory usage: {exc}")
            return 0.0

    def profile_executor(self, executor_id: str) -> ProfilerContext:
        """Create a profiling context for an executor.

        Args:
            executor_id: Unique executor identifier (e.g., "D1-Q1")

        Returns:
            ProfilerContext for use in with statement

        Example:
            with profiler.profile_executor("D1-Q1") as ctx:
                result = executor.execute(context)
                ctx.add_method_call("TextMiner", "extract", 45.2, 2.1)
        """
        return ProfilerContext(self, executor_id)

    def record_executor_metrics(
        self, executor_id: str, metrics: ExecutorMetrics
    ) -> None:
        """Record metrics for an executor execution.

        Args:
            executor_id: Unique executor identifier
            metrics: Collected metrics for the execution
        """
        self.metrics[executor_id].append(metrics)

        if self.baseline_path and self.auto_save_baseline:
            self._update_baseline(executor_id, metrics)

    def _update_baseline(self, executor_id: str, metrics: ExecutorMetrics) -> None:
        """Update baseline with new metrics (running average).

        Args:
            executor_id: Executor identifier
            metrics: New metrics to incorporate
        """
        if executor_id not in self.baseline_metrics:
            self.baseline_metrics[executor_id] = metrics
        else:
            baseline = self.baseline_metrics[executor_id]
            baseline.execution_time_ms = (
                baseline.execution_time_ms * 0.8 + metrics.execution_time_ms * 0.2
            )
            baseline.memory_footprint_mb = (
                baseline.memory_footprint_mb * 0.8 + metrics.memory_footprint_mb * 0.2
            )
            baseline.serialization_time_ms = (
                baseline.serialization_time_ms * 0.8
                + metrics.serialization_time_ms * 0.2
            )
            baseline.call_count += 1

    def detect_regressions(
        self,
        thresholds: dict[str, float] | None = None,
    ) -> list[PerformanceRegression]:
        """Detect performance regressions against baseline.

        Args:
            thresholds: Regression thresholds for each metric
                       (default: {"execution_time_ms": 20.0, "memory_footprint_mb": 30.0})

        Returns:
            List of detected regressions
        """
        if thresholds is None:
            thresholds = {
                "execution_time_ms": 20.0,
                "memory_footprint_mb": 30.0,
                "serialization_time_ms": 50.0,
            }

        regressions: list[PerformanceRegression] = []

        for executor_id, metric_list in self.metrics.items():
            if not metric_list:
                continue

            if executor_id not in self.baseline_metrics:
                continue

            baseline = self.baseline_metrics[executor_id]
            current = metric_list[-1]

            for metric_name, threshold in thresholds.items():
                baseline_val = getattr(baseline, metric_name, 0.0)
                current_val = getattr(current, metric_name, 0.0)

                if baseline_val == 0:
                    continue

                delta_percent = ((current_val - baseline_val) / baseline_val) * 100

                if delta_percent > threshold:
                    severity = (
                        "critical" if delta_percent > threshold * 2 else "warning"
                    )
                    recommendation = self._generate_recommendation(
                        executor_id, metric_name, delta_percent
                    )

                    regression = PerformanceRegression(
                        executor_id=executor_id,
                        metric_name=metric_name,
                        baseline_value=baseline_val,
                        current_value=current_val,
                        delta_percent=delta_percent,
                        severity=severity,
                        threshold_exceeded=True,
                        recommendation=recommendation,
                    )
                    regressions.append(regression)

        self.regressions = regressions
        return regressions

    def _generate_recommendation(
        self, executor_id: str, metric_name: str, delta_percent: float
    ) -> str:
        """Generate optimization recommendation for a regression.

        Args:
            executor_id: Executor with regression
            metric_name: Metric that regressed
            delta_percent: Percentage increase

        Returns:
            Recommendation string
        """
        recommendations = {
            "execution_time_ms": (
                f"Executor {executor_id} execution time increased by {delta_percent:.1f}%. "
                "Review method call sequence, consider caching, or optimize slow methods."
            ),
            "memory_footprint_mb": (
                f"Executor {executor_id} memory usage increased by {delta_percent:.1f}%. "
                "Check for memory leaks, optimize data structures, or implement streaming."
            ),
            "serialization_time_ms": (
                f"Executor {executor_id} serialization overhead increased by {delta_percent:.1f}%. "
                "Reduce result payload size or use more efficient serialization format."
            ),
        }
        return recommendations.get(
            metric_name,
            f"Performance degradation detected in {metric_name} ({delta_percent:.1f}%)",
        )

    def identify_bottlenecks(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Identify top bottleneck executors requiring optimization.

        Args:
            top_n: Number of top bottlenecks to return

        Returns:
            List of bottleneck descriptors with metrics and recommendations
        """
        bottlenecks: list[dict[str, Any]] = []

        for executor_id, metric_list in self.metrics.items():
            if not metric_list:
                continue

            avg_metrics = self._compute_average_metrics(metric_list)

            bottleneck_score = (
                avg_metrics["execution_time_ms"] * 0.5
                + avg_metrics["memory_footprint_mb"] * 0.3
                + avg_metrics["serialization_time_ms"] * 0.2
            )

            bottleneck = {
                "executor_id": executor_id,
                "bottleneck_score": bottleneck_score,
                "avg_execution_time_ms": avg_metrics["execution_time_ms"],
                "avg_memory_mb": avg_metrics["memory_footprint_mb"],
                "avg_serialization_ms": avg_metrics["serialization_time_ms"],
                "total_method_calls": avg_metrics["total_method_calls"],
                "slowest_method": avg_metrics["slowest_method"],
                "memory_intensive_method": avg_metrics["memory_intensive_method"],
                "recommendation": self._generate_bottleneck_recommendation(
                    executor_id, avg_metrics
                ),
            }
            bottlenecks.append(bottleneck)

        bottlenecks.sort(key=lambda x: x["bottleneck_score"], reverse=True)
        return bottlenecks[:top_n]

    def _compute_average_metrics(
        self, metric_list: list[ExecutorMetrics]
    ) -> dict[str, Any]:
        """Compute average metrics from a list of executor metrics.

        Args:
            metric_list: List of metrics to average

        Returns:
            Dictionary of averaged metrics
        """
        if not metric_list:
            return {}

        return {
            "execution_time_ms": sum(m.execution_time_ms for m in metric_list)
            / len(metric_list),
            "memory_footprint_mb": sum(m.memory_footprint_mb for m in metric_list)
            / len(metric_list),
            "serialization_time_ms": sum(m.serialization_time_ms for m in metric_list)
            / len(metric_list),
            "total_method_calls": sum(m.total_method_calls for m in metric_list)
            / len(metric_list),
            "slowest_method": (
                metric_list[-1].slowest_method.class_name
                + "."
                + metric_list[-1].slowest_method.method_name
                if metric_list[-1].slowest_method
                else None
            ),
            "memory_intensive_method": (
                metric_list[-1].memory_intensive_method.class_name
                + "."
                + metric_list[-1].memory_intensive_method.method_name
                if metric_list[-1].memory_intensive_method
                else None
            ),
        }

    def _generate_bottleneck_recommendation(
        self, _executor_id: str, avg_metrics: dict[str, Any]
    ) -> str:
        """Generate optimization recommendation for a bottleneck.

        Args:
            _executor_id: Executor identifier (unused, kept for API consistency)
            avg_metrics: Average metrics

        Returns:
            Recommendation string
        """
        recommendations = []

        if avg_metrics["execution_time_ms"] > HIGH_EXECUTION_TIME_THRESHOLD_MS:
            recommendations.append(
                f"High execution time ({avg_metrics['execution_time_ms']:.1f}ms): "
                f"optimize {avg_metrics['slowest_method'] or 'slow methods'}"
            )

        if avg_metrics["memory_footprint_mb"] > HIGH_MEMORY_THRESHOLD_MB:
            recommendations.append(
                f"High memory usage ({avg_metrics['memory_footprint_mb']:.1f}MB): "
                f"review {avg_metrics['memory_intensive_method'] or 'data structures'}"
            )

        if avg_metrics["serialization_time_ms"] > HIGH_SERIALIZATION_THRESHOLD_MS:
            recommendations.append(
                f"High serialization overhead ({avg_metrics['serialization_time_ms']:.1f}ms): "
                "reduce payload size"
            )

        if not recommendations:
            return "Performance acceptable, monitor for regressions"

        return "; ".join(recommendations)

    def generate_report(
        self, include_regressions: bool = True, include_bottlenecks: bool = True
    ) -> PerformanceReport:
        """Generate comprehensive performance report.

        Args:
            include_regressions: Include regression detection
            include_bottlenecks: Include bottleneck analysis

        Returns:
            PerformanceReport with analysis and recommendations
        """
        regressions = []
        if include_regressions:
            regressions = self.detect_regressions()

        bottlenecks = []
        if include_bottlenecks:
            bottlenecks = self.identify_bottlenecks()

        total_execution_time = sum(
            m.execution_time_ms for metrics in self.metrics.values() for m in metrics
        )
        total_memory = sum(
            m.memory_footprint_mb for metrics in self.metrics.values() for m in metrics
        )

        executor_rankings = {
            "slowest": self._rank_executors_by("execution_time_ms"),
            "memory_intensive": self._rank_executors_by("memory_footprint_mb"),
            "serialization_heavy": self._rank_executors_by("serialization_time_ms"),
        }

        summary = {
            "total_executors_profiled": len(self.metrics),
            "total_executions": sum(len(m) for m in self.metrics.values()),
            "regressions_detected": len(regressions),
            "critical_regressions": sum(
                1 for r in regressions if r.severity == "critical"
            ),
            "bottlenecks_identified": len(bottlenecks),
            "avg_execution_time_ms": total_execution_time
            / max(1, sum(len(m) for m in self.metrics.values())),
            "avg_memory_mb": total_memory
            / max(1, sum(len(m) for m in self.metrics.values())),
        }

        return PerformanceReport(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_executors=len(self.metrics),
            total_execution_time_ms=total_execution_time,
            total_memory_mb=total_memory,
            regressions=regressions,
            bottlenecks=bottlenecks,
            summary=summary,
            executor_rankings=executor_rankings,
        )

    def _rank_executors_by(self, metric_name: str, top_n: int = 10) -> list[str]:
        """Rank executors by a specific metric.

        Args:
            metric_name: Metric to rank by
            top_n: Number of top executors to return

        Returns:
            List of executor IDs ranked by metric
        """
        rankings = []
        for executor_id, metric_list in self.metrics.items():
            if not metric_list:
                continue
            avg_value = sum(getattr(m, metric_name, 0.0) for m in metric_list) / len(
                metric_list
            )
            rankings.append((executor_id, avg_value))

        rankings.sort(key=lambda x: x[1], reverse=True)
        return [executor_id for executor_id, _ in rankings[:top_n]]

    def save_baseline(self, path: Path | str | None = None) -> None:
        """Save current metrics as baseline.

        Args:
            path: Path to save baseline (uses self.baseline_path if None)
        """
        path = Path(path) if path else self.baseline_path
        if not path:
            raise ValueError("No baseline path specified")

        path.parent.mkdir(parents=True, exist_ok=True)

        baseline_data = {
            executor_id: metrics.to_dict()
            for executor_id, metrics in self.baseline_metrics.items()
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(baseline_data, f, indent=2)

        logger.info(f"Baseline saved to {path}")

    def load_baseline(self, path: Path | str) -> None:
        """Load baseline metrics from file.

        Args:
            path: Path to baseline file
        """
        path = Path(path)
        if not path.exists():
            logger.warning(f"Baseline file not found: {path}")
            return

        with open(path, encoding="utf-8") as f:
            baseline_data = json.load(f)

        for executor_id, data in baseline_data.items():
            method_calls = [
                MethodCallMetrics(**m) for m in data.pop("method_calls", [])
            ]
            data.pop("total_method_calls", None)
            data.pop("average_method_time_ms", None)
            data.pop("slowest_method", None)
            data.pop("memory_intensive_method", None)
            metrics = ExecutorMetrics(**data, method_calls=method_calls)
            self.baseline_metrics[executor_id] = metrics

        logger.info(
            f"Baseline loaded from {path}: {len(self.baseline_metrics)} executors"
        )

    def export_report(
        self, report: PerformanceReport, path: Path | str, format: str = "json"
    ) -> None:
        """Export performance report to file.

        Args:
            report: Performance report to export
            path: Output path
            format: Output format ("json", "markdown", or "html")
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(report.to_dict(), f, indent=2)

        elif format == "markdown":
            self._export_markdown(report, path)

        elif format == "html":
            self._export_html(report, path)

        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Report exported to {path}")

    def _export_markdown(self, report: PerformanceReport, path: Path) -> None:
        """Export report as Markdown."""
        lines = [
            "# Executor Performance Report",
            f"**Generated:** {report.timestamp}",
            "",
            "## Summary",
            f"- **Total Executors:** {report.total_executors}",
            f"- **Total Execution Time:** {report.total_execution_time_ms:.2f}ms",
            f"- **Total Memory:** {report.total_memory_mb:.2f}MB",
            f"- **Regressions Detected:** {report.summary.get('regressions_detected', 0)}",
            f"- **Bottlenecks Identified:** {report.summary.get('bottlenecks_identified', 0)}",
            "",
        ]

        if report.regressions:
            lines.extend(
                [
                    "## Performance Regressions",
                    "",
                    "| Executor | Metric | Baseline | Current | Delta | Severity |",
                    "|----------|--------|----------|---------|-------|----------|",
                ]
            )
            for reg in report.regressions:
                lines.append(
                    f"| {reg.executor_id} | {reg.metric_name} | "
                    f"{reg.baseline_value:.2f} | {reg.current_value:.2f} | "
                    f"{reg.delta_percent:+.1f}% | {reg.severity} |"
                )
            lines.append("")

        if report.bottlenecks:
            lines.extend(
                [
                    "## Top Bottlenecks",
                    "",
                    "| Rank | Executor | Score | Exec Time | Memory | Recommendation |",
                    "|------|----------|-------|-----------|--------|----------------|",
                ]
            )
            for i, bottleneck in enumerate(report.bottlenecks[:10], 1):
                lines.append(
                    f"| {i} | {bottleneck['executor_id']} | "
                    f"{bottleneck['bottleneck_score']:.1f} | "
                    f"{bottleneck['avg_execution_time_ms']:.1f}ms | "
                    f"{bottleneck['avg_memory_mb']:.1f}MB | "
                    f"{bottleneck['recommendation'][:50]}... |"
                )
            lines.append("")

        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _export_html(self, report: PerformanceReport, path: Path) -> None:
        """Export report as HTML."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Executor Performance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .critical {{ color: red; font-weight: bold; }}
        .warning {{ color: orange; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Executor Performance Report</h1>
    <p><strong>Generated:</strong> {report.timestamp}</p>

    <h2>Summary</h2>
    <ul>
        <li><strong>Total Executors:</strong> {report.total_executors}</li>
        <li><strong>Total Execution Time:</strong> {report.total_execution_time_ms:.2f}ms</li>
        <li><strong>Total Memory:</strong> {report.total_memory_mb:.2f}MB</li>
        <li><strong>Regressions Detected:</strong> {report.summary.get('regressions_detected', 0)}</li>
        <li><strong>Bottlenecks Identified:</strong> {report.summary.get('bottlenecks_identified', 0)}</li>
    </ul>
"""

        if report.regressions:
            html += """
    <h2>Performance Regressions</h2>
    <table>
        <tr>
            <th>Executor</th>
            <th>Metric</th>
            <th>Baseline</th>
            <th>Current</th>
            <th>Delta</th>
            <th>Severity</th>
        </tr>
"""
            for reg in report.regressions:
                severity_class = reg.severity
                html += f"""
        <tr>
            <td>{reg.executor_id}</td>
            <td>{reg.metric_name}</td>
            <td>{reg.baseline_value:.2f}</td>
            <td>{reg.current_value:.2f}</td>
            <td>{reg.delta_percent:+.1f}%</td>
            <td class="{severity_class}">{reg.severity}</td>
        </tr>
"""
            html += "    </table>\n"

        if report.bottlenecks:
            html += """
    <h2>Top Bottlenecks</h2>
    <table>
        <tr>
            <th>Rank</th>
            <th>Executor</th>
            <th>Score</th>
            <th>Exec Time</th>
            <th>Memory</th>
            <th>Recommendation</th>
        </tr>
"""
            for i, bottleneck in enumerate(report.bottlenecks[:10], 1):
                html += f"""
        <tr>
            <td>{i}</td>
            <td>{bottleneck['executor_id']}</td>
            <td>{bottleneck['bottleneck_score']:.1f}</td>
            <td>{bottleneck['avg_execution_time_ms']:.1f}ms</td>
            <td>{bottleneck['avg_memory_mb']:.1f}MB</td>
            <td>{bottleneck['recommendation']}</td>
        </tr>
"""
            html += "    </table>\n"

        html += """
</body>
</html>
"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    def clear_metrics(self) -> None:
        """Clear all collected metrics (but not baseline)."""
        self.metrics.clear()
        self.regressions.clear()


class ProfilerContext:
    """Context manager for automatic executor profiling.

    Automatically captures timing, memory, and serialization metrics
    when used with a 'with' statement.
    """

    def __init__(self, profiler: ExecutorProfiler, executor_id: str) -> None:
        """Initialize profiler context.

        Args:
            profiler: Parent profiler instance
            executor_id: Executor being profiled
        """
        self.profiler = profiler
        self.executor_id = executor_id
        self.start_time: float = 0.0
        self.start_memory: float = 0.0
        self.method_calls: list[MethodCallMetrics] = []
        self.result: Any = None
        self.error: str | None = None

    def __enter__(self) -> ProfilerContext:
        """Enter profiling context."""
        self.start_time = time.perf_counter()
        self.start_memory = self.profiler._get_memory_usage_mb()
        gc.collect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit profiling context and record metrics."""
        execution_time = (time.perf_counter() - self.start_time) * 1000
        end_memory = self.profiler._get_memory_usage_mb()
        memory_footprint = end_memory - self.start_memory
        memory_peak = max(end_memory, self.start_memory)

        serialization_time, serialization_size = self._measure_serialization()

        metrics = ExecutorMetrics(
            executor_id=self.executor_id,
            execution_time_ms=execution_time,
            memory_footprint_mb=memory_footprint,
            memory_peak_mb=memory_peak,
            serialization_time_ms=serialization_time,
            serialization_size_bytes=serialization_size,
            method_calls=self.method_calls,
            success=exc_type is None,
            error=str(exc_val) if exc_val else None,
        )

        self.profiler.record_executor_metrics(self.executor_id, metrics)

    def _measure_serialization(self) -> tuple[float, int]:
        """Measure serialization overhead for the result.

        Returns:
            Tuple of (serialization_time_ms, serialization_size_bytes)
        """
        if self.result is None:
            return 0.0, 0

        try:
            start = time.perf_counter()
            serialized = pickle.dumps(self.result, protocol=pickle.HIGHEST_PROTOCOL)
            serialization_time = (time.perf_counter() - start) * 1000
            serialization_size = len(serialized)
            return serialization_time, serialization_size
        except Exception as exc:
            logger.warning(f"Failed to measure serialization: {exc}")
            return 0.0, 0

    def add_method_call(
        self,
        class_name: str,
        method_name: str,
        execution_time_ms: float,
        memory_delta_mb: float = 0.0,
        success: bool = True,
        error: str | None = None,
    ) -> None:
        """Add a method call to the profiling context.

        Args:
            class_name: Class of the method
            method_name: Name of the method
            execution_time_ms: Execution time in milliseconds
            memory_delta_mb: Memory delta in MB
            success: Whether the call succeeded
            error: Error message if failed
        """
        metrics = MethodCallMetrics(
            class_name=class_name,
            method_name=method_name,
            execution_time_ms=execution_time_ms,
            memory_delta_mb=memory_delta_mb,
            success=success,
            error=error,
        )
        self.method_calls.append(metrics)

    def set_result(self, result: object) -> None:
        """Set the result for serialization measurement.

        Args:
            result: Execution result (can be any serializable object)
        """
        self.result = result


__all__ = [
    "ExecutorProfiler",
    "ProfilerContext",
    "ExecutorMetrics",
    "MethodCallMetrics",
    "PerformanceRegression",
    "PerformanceReport",
]
