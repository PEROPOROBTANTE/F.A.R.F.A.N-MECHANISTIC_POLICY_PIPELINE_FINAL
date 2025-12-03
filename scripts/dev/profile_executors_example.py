"""Example script demonstrating executor performance profiling.

This script shows how to:
1. Create and configure an ExecutorProfiler
2. Profile executor executions automatically
3. Detect performance regressions
4. Generate and export performance reports
5. Identify bottleneck executors

Usage:
    python scripts/dev/profile_executors_example.py
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from farfan_pipeline.core.orchestrator.executor_profiler import ExecutorProfiler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def simulate_executor_execution(executor_id: str, execution_time_ms: float, memory_mb: float) -> dict:
    """Simulate an executor execution."""
    import time
    
    time.sleep(execution_time_ms / 1000.0)
    
    return {
        "executor_id": executor_id,
        "result": {"evidence": ["item1", "item2"], "confidence": 0.95},
    }


def main():
    """Demonstrate executor profiling capabilities."""
    logger.info("=== Executor Performance Profiling Demo ===\n")
    
    baseline_path = Path("profiling_output/baseline.json")
    baseline_path.parent.mkdir(exist_ok=True)
    
    logger.info("1. Creating profiler with baseline management...")
    profiler = ExecutorProfiler(
        baseline_path=baseline_path,
        auto_save_baseline=True,
        memory_tracking=True,
    )
    
    logger.info("2. Simulating executor executions...\n")
    
    executors = [
        ("D1-Q1", 100.0, 5.0),
        ("D1-Q2", 150.0, 8.0),
        ("D2-Q1", 200.0, 12.0),
        ("D2-Q2", 80.0, 4.0),
        ("D3-Q1", 500.0, 50.0),
    ]
    
    for executor_id, exec_time, memory in executors:
        logger.info(f"Profiling {executor_id}...")
        
        with profiler.profile_executor(executor_id) as ctx:
            ctx.add_method_call("TextMiner", "extract", exec_time * 0.3, memory * 0.2)
            ctx.add_method_call("Analyzer", "analyze", exec_time * 0.5, memory * 0.5)
            ctx.add_method_call("Validator", "validate", exec_time * 0.2, memory * 0.3)
            
            result = simulate_executor_execution(executor_id, exec_time, memory)
            ctx.set_result(result)
        
        logger.info(f"  ✓ Completed in ~{exec_time:.0f}ms\n")
    
    logger.info("3. Generating performance report...\n")
    report = profiler.generate_report(include_regressions=True, include_bottlenecks=True)
    
    logger.info(f"Summary:")
    logger.info(f"  - Total Executors: {report.total_executors}")
    logger.info(f"  - Total Execution Time: {report.total_execution_time_ms:.2f}ms")
    logger.info(f"  - Total Memory: {report.total_memory_mb:.2f}MB")
    logger.info(f"  - Regressions Detected: {len(report.regressions)}")
    logger.info(f"  - Bottlenecks Identified: {len(report.bottlenecks)}\n")
    
    logger.info("4. Top Bottlenecks:")
    for i, bottleneck in enumerate(report.bottlenecks[:3], 1):
        logger.info(f"\n  {i}. {bottleneck['executor_id']}")
        logger.info(f"     - Score: {bottleneck['bottleneck_score']:.1f}")
        logger.info(f"     - Execution Time: {bottleneck['avg_execution_time_ms']:.1f}ms")
        logger.info(f"     - Memory: {bottleneck['avg_memory_mb']:.1f}MB")
        logger.info(f"     - Slowest Method: {bottleneck['slowest_method']}")
        logger.info(f"     - Recommendation: {bottleneck['recommendation']}")
    
    logger.info("\n\n5. Executor Rankings:")
    logger.info(f"   Slowest: {', '.join(report.executor_rankings['slowest'][:3])}")
    logger.info(f"   Memory Intensive: {', '.join(report.executor_rankings['memory_intensive'][:3])}")
    
    logger.info("\n6. Exporting reports...")
    output_dir = Path("profiling_output")
    output_dir.mkdir(exist_ok=True)
    
    profiler.export_report(report, output_dir / "report.json", format="json")
    logger.info(f"  ✓ JSON report: {output_dir / 'report.json'}")
    
    profiler.export_report(report, output_dir / "report.md", format="markdown")
    logger.info(f"  ✓ Markdown report: {output_dir / 'report.md'}")
    
    profiler.export_report(report, output_dir / "report.html", format="html")
    logger.info(f"  ✓ HTML report: {output_dir / 'report.html'}")
    
    logger.info("\n7. Simulating second run with performance regression...")
    
    with profiler.profile_executor("D3-Q1") as ctx:
        ctx.add_method_call("TextMiner", "extract", 200.0, 15.0)
        ctx.add_method_call("Analyzer", "analyze", 600.0, 80.0)
        ctx.add_method_call("Validator", "validate", 100.0, 10.0)
        
        result = simulate_executor_execution("D3-Q1", 900.0, 105.0)
        ctx.set_result(result)
    
    logger.info("   ✓ Simulated slower execution\n")
    
    logger.info("8. Detecting regressions...")
    regressions = profiler.detect_regressions(
        thresholds={
            "execution_time_ms": 20.0,
            "memory_footprint_mb": 30.0,
            "serialization_time_ms": 50.0,
        }
    )
    
    if regressions:
        logger.info(f"   ⚠️  {len(regressions)} regression(s) detected:\n")
        for reg in regressions:
            logger.info(f"   {reg.severity.upper()}: {reg.executor_id}")
            logger.info(f"     - Metric: {reg.metric_name}")
            logger.info(f"     - Baseline: {reg.baseline_value:.2f}")
            logger.info(f"     - Current: {reg.current_value:.2f}")
            logger.info(f"     - Delta: {reg.delta_percent:+.1f}%")
            logger.info(f"     - Recommendation: {reg.recommendation}\n")
    else:
        logger.info("   ✓ No regressions detected\n")
    
    logger.info("9. Saving baseline for future comparisons...")
    profiler.save_baseline(baseline_path)
    logger.info(f"   ✓ Baseline saved to {baseline_path}\n")
    
    logger.info("=== Demo Complete ===")
    logger.info(f"Output directory: {output_dir.absolute()}")
    logger.info("View report.html in a browser for detailed visualization.")


if __name__ == "__main__":
    main()
