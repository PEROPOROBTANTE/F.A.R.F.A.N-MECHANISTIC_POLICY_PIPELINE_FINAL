#!/usr/bin/env python
"""Report ExtendedArgRouter metrics for monitoring and CI.

This script can be imported and called after test runs to report routing metrics.
It helps monitor:
- Silent parameter drops prevented
- Special route hit rates
- Validation error rates

Usage:
    python scripts/report_routing_metrics.py <metrics_json_file>
    
Or programmatically:
    from scripts.report_routing_metrics import report_metrics
    report_metrics(executor.get_routing_metrics())
"""

import json
import sys
from pathlib import Path
from typing import Any


def format_metrics_report(metrics: dict[str, Any]) -> str:
    """Format metrics into a human-readable report.
    
    Args:
        metrics: Routing metrics dict from ExtendedArgRouter.get_metrics()
        
    Returns:
        Formatted report string
    """
    if not metrics:
        return "No routing metrics available (router may not support metrics)"
    
    report_lines = [
        "=" * 70,
        "EXTENDED ARG ROUTER METRICS",
        "=" * 70,
        "",
        f"Total Routes:              {metrics.get('total_routes', 0):,}",
        f"Special Routes Hit:        {metrics.get('special_routes_hit', 0):,}",
        f"Default Routes Hit:        {metrics.get('default_routes_hit', 0):,}",
        f"Special Routes Defined:    {metrics.get('special_routes_coverage', 0)}",
        "",
        "--- Performance ---",
        f"Special Route Hit Rate:    {metrics.get('special_route_hit_rate', 0):.2%}",
        "",
        "--- Validation ---",
        f"Validation Errors:         {metrics.get('validation_errors', 0):,}",
        f"Silent Drops Prevented:    {metrics.get('silent_drops_prevented', 0):,}",
        f"Error Rate:                {metrics.get('error_rate', 0):.2%}",
        "",
    ]
    
    return "\n".join(report_lines)


def report_metrics(metrics: dict[str, Any], fail_on_silent_drops: bool = False) -> int:
    """Report routing metrics and optionally fail if silent drops increased.
    
    Args:
        metrics: Routing metrics dict
        fail_on_silent_drops: If True, exit with error code if silent drops > 0
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print(format_metrics_report(metrics))
    
    silent_drops = metrics.get('silent_drops_prevented', 0)
    
    if fail_on_silent_drops and silent_drops > 0:
        print("=" * 70)
        print("❌ FAILURE: Silent parameter drops detected!")
        print(f"   {silent_drops} contract violations prevented by ExtendedArgRouter")
        print("   These indicate calling code is passing unexpected parameters.")
        print("   Fix the calling code to match method signatures.")
        print("=" * 70)
        return 1
    
    if silent_drops > 0:
        print("⚠️  WARNING: Silent parameter drops were prevented")
        print(f"   {silent_drops} potential contract violations detected")
        print("   Consider fixing calling code to match method signatures")
        print()
    
    print("✅ Routing metrics reported successfully")
    return 0


def main() -> int:
    """CLI entry point for metrics reporting."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/report_routing_metrics.py <metrics.json>")
        print("   or: python scripts/report_routing_metrics.py <metrics.json> --fail-on-silent-drops")
        return 1
    
    metrics_file = Path(sys.argv[1])
    fail_on_silent_drops = '--fail-on-silent-drops' in sys.argv
    
    if not metrics_file.exists():
        print(f"Error: Metrics file not found: {metrics_file}")
        return 1
    
    try:
        with open(metrics_file) as f:
            metrics = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in metrics file: {e}")
        return 1
    
    return report_metrics(metrics, fail_on_silent_drops=fail_on_silent_drops)


if __name__ == '__main__':
    sys.exit(main())
