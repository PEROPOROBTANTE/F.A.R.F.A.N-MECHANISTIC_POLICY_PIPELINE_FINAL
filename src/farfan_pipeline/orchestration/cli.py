#!/usr/bin/env python3
"""
CLI Entry Point for F.A.R.F.A.N Pipeline Orchestrator.

Provides a command-line interface for executing the complete pipeline
with various configuration options.

Usage:
    # Run full pipeline with default configuration
    python -m farfan_pipeline.orchestration.cli

    # Run with custom configuration
    python -m farfan_pipeline.orchestration.cli --config config.json

    # Run specific phase range
    python -m farfan_pipeline.orchestration.cli --start-phase P01 --end-phase P05

    # Run with environment configuration
    FARFAN_STRICT_MODE=false python -m farfan_pipeline.orchestration.cli

Author: F.A.R.F.A.N Core Team
Version: 1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import structlog

from farfan_pipeline.orchestration.orchestrator import (
    UnifiedOrchestrator as PipelineOrchestrator,
    PhaseID,
    PhaseStatus,
    OrchestratorConfig,
    ConfigValidationError,
    get_development_config,
    get_production_config,
    get_testing_config,
    validate_config,
)

logger = structlog.get_logger(__name__)


# =============================================================================
# CLI ARGUMENT PARSER
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="F.A.R.F.A.N Pipeline Orchestrator - Execute the complete policy analysis pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline with default configuration
  %(prog)s

  # Run specific phase range
  %(prog)s --start-phase P01 --end-phase P05

  # Use development preset
  %(prog)s --preset development

  # Load configuration from file
  %(prog)s --config my_config.json

  # Enable verbose logging
  %(prog)s --log-level DEBUG

  # Non-deterministic execution
  %(prog)s --no-deterministic

Phase IDs:
  P00: Bootstrap & Validation
  P01: CPP Ingestion
  P02: Executor Factory & Dispatch
  P03: Layer Scoring
  P04: Dimension Aggregation
  P05: Policy Area Aggregation
  P06: Cluster Aggregation
  P07: Macro Aggregation
  P08: Recommendations Engine
  P09: Report Assembly
  P10: Verification
        """,
    )

    # Configuration sources
    config_group = parser.add_argument_group("Configuration")
    config_group.add_argument(
        "--config",
        type=Path,
        metavar="FILE",
        help="Load configuration from JSON file",
    )
    config_group.add_argument(
        "--preset",
        choices=["development", "production", "testing"],
        help="Use configuration preset",
    )

    # Phase control
    phase_group = parser.add_argument_group("Phase Control")
    phase_group.add_argument(
        "--start-phase",
        type=str,
        metavar="PHASE",
        default="P00",
        choices=["P00", "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10"],
        help="Starting phase (default: P00)",
    )
    phase_group.add_argument(
        "--end-phase",
        type=str,
        metavar="PHASE",
        default="P09",
        choices=["P00", "P01", "P02", "P03", "P04", "P05", "P06", "P07", "P08", "P09", "P10"],
        help="Ending phase (default: P09)",
    )

    # Paths
    path_group = parser.add_argument_group("Paths")
    path_group.add_argument(
        "--questionnaire",
        type=Path,
        metavar="FILE",
        help="Path to questionnaire monolith JSON",
    )
    path_group.add_argument(
        "--executor-config",
        type=Path,
        metavar="FILE",
        help="Path to executor configuration",
    )
    path_group.add_argument(
        "--output-dir",
        type=Path,
        metavar="DIR",
        help="Output directory for reports and artifacts",
    )

    # Execution control
    exec_group = parser.add_argument_group("Execution Control")
    exec_group.add_argument(
        "--strict",
        action="store_true",
        default=None,
        help="Enable strict mode (raise exceptions on critical violations)",
    )
    exec_group.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict mode (warnings instead of errors)",
    )
    exec_group.add_argument(
        "--deterministic",
        action="store_true",
        default=None,
        help="Enable deterministic execution (SIN_CARRETA compliance)",
    )
    exec_group.add_argument(
        "--no-deterministic",
        action="store_true",
        help="Disable deterministic execution",
    )

    # Logging
    log_group = parser.add_argument_group("Logging")
    log_group.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set logging level",
    )
    log_group.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output (ERROR level)",
    )
    log_group.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output (DEBUG level)",
    )

    # Output control
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--json-output",
        type=Path,
        metavar="FILE",
        help="Write execution summary to JSON file",
    )
    output_group.add_argument(
        "--report-format",
        choices=["json", "markdown", "html", "pdf"],
        default="json",
        help="Final report format (default: json)",
    )

    return parser


# =============================================================================
# CONFIGURATION BUILDING
# =============================================================================


def build_config_from_args(args: argparse.Namespace) -> OrchestratorConfig:
    """Build configuration from CLI arguments.

    Args:
        args: Parsed CLI arguments

    Returns:
        OrchestratorConfig instance
    """
    # Start with preset or environment
    if args.preset == "development":
        config = get_development_config()
    elif args.preset == "production":
        config = get_production_config()
    elif args.preset == "testing":
        config = get_testing_config()
    elif args.config:
        # Load from file
        with open(args.config, encoding="utf-8") as f:
            config_data = json.load(f)
        config = OrchestratorConfig.from_dict(config_data)
    else:
        # Use environment or defaults
        config = OrchestratorConfig.from_env()

    # Override with CLI arguments
    if args.questionnaire:
        config.questionnaire_path = args.questionnaire
    if args.executor_config:
        config.executor_config_path = args.executor_config
    if args.output_dir:
        config.output_dir = args.output_dir

    # Execution control
    if args.strict:
        config.strict_mode = True
    elif args.no_strict:
        config.strict_mode = False

    if args.deterministic:
        config.deterministic = True
    elif args.no_deterministic:
        config.deterministic = False

    # Phase control
    config.start_phase = args.start_phase
    config.end_phase = args.end_phase

    # Logging
    if args.quiet:
        config.log_level = "ERROR"
    elif args.verbose:
        config.log_level = "DEBUG"
    elif args.log_level:
        config.log_level = args.log_level

    return config


# =============================================================================
# OUTPUT FORMATTING
# =============================================================================


def format_execution_summary(context: Any) -> dict[str, Any]:
    """Format execution context as summary dictionary.

    Args:
        context: ExecutionContext from pipeline execution

    Returns:
        Summary dictionary
    """
    summary = context.get_execution_summary()

    # Add phase-by-phase breakdown
    phase_breakdown = []
    for phase_id, result in context.phase_results.items():
        phase_breakdown.append({
            "phase_id": phase_id.value,
            "phase_name": result.phase_id.value,
            "status": result.status.value,
            "execution_time_s": round(result.execution_time_s, 3),
            "violations": len(result.violations),
            "critical_violations": sum(
                1 for v in result.violations if v.severity.value == "CRITICAL"
            ),
        })

    summary["phase_breakdown"] = phase_breakdown

    # Add violation summary
    violation_summary = {}
    for violation in context.total_violations:
        severity = violation.severity.value
        if severity not in violation_summary:
            violation_summary[severity] = []
        violation_summary[severity].append({
            "type": violation.type,
            "component": violation.component_path,
            "message": violation.message,
        })

    summary["violations"] = violation_summary

    return summary


def print_execution_summary(context: Any) -> None:
    """Print execution summary to console.

    Args:
        context: ExecutionContext from pipeline execution
    """
    summary = context.get_execution_summary()

    print("\n" + "=" * 70)
    print("F.A.R.F.A.N PIPELINE EXECUTION SUMMARY")
    print("=" * 70)
    print(f"Execution ID:       {summary['execution_id']}")
    print(f"Total Time:         {summary['elapsed_time_s']:.2f}s")
    print(f"Phases Completed:   {summary['phases_completed']}/{summary['total_phases']}")
    print(f"Phases Failed:      {summary['phases_failed']}")
    print(f"Total Violations:   {summary['total_violations']}")
    print(f"Critical Violations: {summary['critical_violations']}")
    print(f"Deterministic:      {'Yes' if summary['deterministic'] else 'No'}")
    print("=" * 70)

    # Phase breakdown
    print("\nPHASE BREAKDOWN:")
    print("-" * 70)
    for phase_id, result in context.phase_results.items():
        status_symbol = "✓" if result.status == PhaseStatus.COMPLETED else "✗"
        print(
            f"{status_symbol} {phase_id.value}: {result.execution_time_s:6.2f}s "
            f"({len(result.violations)} violations)"
        )

    # Violation summary
    if context.total_violations:
        print("\nVIOLATIONS:")
        print("-" * 70)
        critical = [v for v in context.total_violations if v.severity.value == "CRITICAL"]
        high = [v for v in context.total_violations if v.severity.value == "HIGH"]

        if critical:
            print(f"\n🔴 CRITICAL ({len(critical)}):")
            for v in critical[:5]:  # Show first 5
                print(f"  • {v.component_path}: {v.message}")
            if len(critical) > 5:
                print(f"  ... and {len(critical) - 5} more")

        if high:
            print(f"\n🟠 HIGH ({len(high)}):")
            for v in high[:5]:  # Show first 5
                print(f"  • {v.component_path}: {v.message}")
            if len(high) > 5:
                print(f"  ... and {len(high) - 5} more")

    print("\n" + "=" * 70)


# =============================================================================
# MAIN EXECUTION
# =============================================================================


def main(argv: list[str] | None = None) -> int:
    """Main CLI entry point.

    Args:
        argv: Command-line arguments (default: sys.argv)

    Returns:
        Exit code (0 = success, 1 = failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Build configuration
    try:
        config = build_config_from_args(args)
        warnings = validate_config(config)

        # Show warnings
        for warning in warnings:
            logger.warning("config_validation_warning", message=warning)

    except ConfigValidationError as e:
        print(f"❌ Configuration Error: {e}", file=sys.stderr)
        return 1

    # Configure logging using standard logging levels
    import logging
    log_level = getattr(logging, config.log_level, logging.INFO)
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )

    # Display configuration
    if config.log_level in ("DEBUG", "INFO"):
        print("=" * 70)
        print("F.A.R.F.A.N PIPELINE ORCHESTRATOR")
        print("=" * 70)
        print(f"Configuration Preset: {args.preset or 'custom'}")
        print(f"Phase Range:          {config.start_phase} → {config.end_phase}")
        print(f"Strict Mode:          {config.strict_mode}")
        print(f"Deterministic:        {config.deterministic}")
        print(f"Output Directory:     {config.output_dir}")
        print("=" * 70)
        print()

    # Create orchestrator
    orchestrator = PipelineOrchestrator(config=config)

    # Execute pipeline
    try:
        logger.info(
            "pipeline_execution_start",
            start_phase=config.start_phase,
            end_phase=config.end_phase,
        )

        result = orchestrator.execute()

        # Print summary
        print_execution_summary(result)

        # Write JSON output if requested
        if args.json_output:
            summary = format_execution_summary(result)
            with open(args.json_output, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            print(f"\n✓ Execution summary written to: {args.json_output}")

        # Check for failures using result
        if hasattr(result, 'get_execution_summary'):
            summary = result.get_execution_summary()
            if summary.get("phases_failed", 0) > 0:
                print("\n❌ Pipeline execution completed with failures")
                return 1
            elif summary.get("critical_violations", 0) > 0:
                print("\n⚠️  Pipeline execution completed with critical violations")
                return 1

        print("\n✅ Pipeline execution completed successfully")
        return 0

    except Exception as e:
        logger.error("pipeline_execution_failed", error=str(e), error_type=type(e).__name__)
        print(f"\n❌ Pipeline Execution Failed: {e}", file=sys.stderr)

        if config.log_level == "DEBUG":
            import traceback
            traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
