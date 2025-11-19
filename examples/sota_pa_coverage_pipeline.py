#!/usr/bin/env python3
"""SOTA PA Coverage Pipeline - Production-grade integration example.

This example demonstrates the complete SOTA/Frontier PA coverage pipeline with:

1. Soft-alias pattern (prevents duplicate fingerprints)
2. Quality metrics monitoring (PA coverage observability)
3. Intelligent fallback fusion (PA07-PA10 coverage gap resolution)
4. Hard calibration gates (prevents silent degradation)
5. Cache invalidation (data integrity)

Usage:
    python examples/sota_pa_coverage_pipeline.py

Expected Output:
    - Quality metrics report showing PA01-PA06 vs PA07-PA10 gap
    - Calibration gate validation results
    - Intelligent fallback fusion applied to low-coverage PAs
    - Cache warming and integrity validation
    - Final quality report with all gates passed
"""

import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

from saaaaaa.core.orchestrator.signal_loader import build_all_signal_packs
from saaaaaa.core.orchestrator.signal_aliasing import (
    upgrade_legacy_fingerprints,
    validate_fingerprint_uniqueness,
)
from saaaaaa.core.orchestrator.signal_quality_metrics import (
    compute_signal_quality_metrics,
    analyze_coverage_gaps,
    generate_quality_report,
)
from saaaaaa.core.orchestrator.signal_fallback_fusion import (
    apply_intelligent_fallback_fusion,
    generate_fusion_audit_report,
    FusionStrategy,
)
from saaaaaa.core.orchestrator.signal_calibration_gate import (
    run_calibration_gates,
    generate_gate_report,
    CalibrationGateConfig,
)
from saaaaaa.core.orchestrator.signal_cache_invalidation import (
    create_global_cache,
    validate_cache_integrity,
)


def run_sota_pipeline():
    """Run complete SOTA PA coverage pipeline."""

    print("=" * 80)
    print("SOTA PA COVERAGE PIPELINE - PRODUCTION INTEGRATION")
    print("=" * 80)
    print()

    # Step 1: Load signal packs
    print("Step 1: Loading signal packs for PA01-PA10...")
    signal_packs = build_all_signal_packs()
    print(f"✓ Loaded {len(signal_packs)} signal packs")
    print()

    # Step 2: Upgrade legacy fingerprints (soft-alias pattern)
    print("Step 2: Upgrading legacy fingerprints (soft-alias pattern)...")
    signal_packs = upgrade_legacy_fingerprints(signal_packs)

    # Validate fingerprint uniqueness
    fingerprint_validation = validate_fingerprint_uniqueness(signal_packs)
    if fingerprint_validation["is_valid"]:
        print(f"✓ All {fingerprint_validation['total_fingerprints']} fingerprints are unique")
    else:
        print(f"✗ Fingerprint collisions detected: {fingerprint_validation['duplicates']}")
        print("  Remediation: Check soft-alias implementation")
    print()

    # Step 3: Compute quality metrics
    print("Step 3: Computing quality metrics for PA coverage...")
    metrics_by_pa = {
        pa: compute_signal_quality_metrics(pack, pa)
        for pa, pack in signal_packs.items()
    }
    print(f"✓ Computed metrics for {len(metrics_by_pa)} policy areas")

    # Show coverage tiers
    print("\nCoverage Tiers:")
    for pa, metrics in sorted(metrics_by_pa.items()):
        tier_symbol = {
            "EXCELLENT": "★★★★",
            "GOOD": "★★★",
            "ADEQUATE": "★★",
            "SPARSE": "★",
        }.get(metrics.coverage_tier, "?")
        print(f"  {pa}: {tier_symbol} {metrics.coverage_tier:12s} ({metrics.pattern_count:3d} patterns)")
    print()

    # Step 4: Analyze coverage gaps
    print("Step 4: Analyzing coverage gaps (PA01-PA06 vs PA07-PA10)...")
    gap_analysis = analyze_coverage_gaps(metrics_by_pa)
    print(f"  Gap Severity: {gap_analysis.gap_severity}")
    print(f"  Coverage Delta: {gap_analysis.coverage_delta:.1f} patterns")
    print(f"  Requires Fallback Fusion: {gap_analysis.requires_fallback_fusion}")

    if gap_analysis.recommendations:
        print("\n  Recommendations:")
        for rec in gap_analysis.recommendations:
            print(f"    • {rec}")
    print()

    # Step 5: Run calibration gates (BEFORE fusion)
    print("Step 5: Running calibration gates (pre-fusion)...")
    gate_config = CalibrationGateConfig(
        min_patterns_per_pa=10,  # Relaxed for PA07-PA10
        min_confidence_threshold=0.70,
        max_threshold_drift=0.15,
    )
    pre_fusion_result = run_calibration_gates(signal_packs, metrics_by_pa, gate_config)

    print(f"  Gates Passed: {'✓ YES' if pre_fusion_result.passed else '✗ NO'}")
    print(f"  Errors: {pre_fusion_result.summary['errors']}")
    print(f"  Warnings: {pre_fusion_result.summary['warnings']}")

    if not pre_fusion_result.passed:
        print("\n⚠️  Pre-fusion gates failed (expected for PA07-PA10 coverage gap)")
        print("   Proceeding with intelligent fallback fusion...")
    print()

    # Step 6: Apply intelligent fallback fusion
    if gap_analysis.requires_fallback_fusion:
        print("Step 6: Applying intelligent fallback fusion...")
        fusion_strategy = FusionStrategy(
            min_source_patterns=20,
            max_fusion_ratio=0.50,
            similarity_threshold=0.30,
        )

        fused_signal_packs = apply_intelligent_fallback_fusion(
            signal_packs,
            metrics_by_pa,
            fusion_strategy,
        )

        # Generate fusion audit report
        fusion_report = generate_fusion_audit_report(fused_signal_packs)
        print(f"✓ Fusion applied to {len(fusion_report['fusion_enabled_pas'])} policy areas")
        print(f"  Total fused patterns: {fusion_report['total_fused_patterns']}")
        print(f"  Avg fusion ratio: {fusion_report['avg_fusion_ratio']:.2%}")

        # Update signal packs to fused version
        signal_packs = fused_signal_packs

        # Recompute metrics after fusion
        metrics_by_pa = {
            pa: compute_signal_quality_metrics(pack, pa)
            for pa, pack in signal_packs.items()
        }
        print()
    else:
        print("Step 6: Skipping fusion (coverage gap negligible)")
        print()

    # Step 7: Run calibration gates (AFTER fusion)
    print("Step 7: Running calibration gates (post-fusion)...")
    post_fusion_result = run_calibration_gates(signal_packs, metrics_by_pa, gate_config)

    print(f"  Gates Passed: {'✓ YES' if post_fusion_result.passed else '✗ NO'}")
    print(f"  Errors: {post_fusion_result.summary['errors']}")
    print(f"  Warnings: {post_fusion_result.summary['warnings']}")

    if post_fusion_result.passed:
        print("\n✓ All calibration gates passed!")
    else:
        print("\n✗ Calibration gates failed - see detailed report below")
        print("\nDetailed Gate Report:")
        print(generate_gate_report(post_fusion_result))
    print()

    # Step 8: Warm cache with validated signal packs
    print("Step 8: Warming cache with validated signal packs...")
    cache = create_global_cache()
    warmed_count = cache.warm_cache(signal_packs)
    print(f"✓ Warmed cache with {warmed_count} entries")

    # Validate cache integrity
    cache_validation = validate_cache_integrity(cache, signal_packs)
    if cache_validation["is_valid"]:
        print(f"✓ Cache integrity validated")
    else:
        print(f"✗ Cache integrity violation detected")
        print(f"  Stale entries: {len(cache_validation['stale_entries'])}")
        print(f"  Mismatched entries: {len(cache_validation['mismatched_entries'])}")

    cache_stats = cache.get_stats()
    print(f"  Cache size: {cache_stats['size']}/{cache_stats['max_size']}")
    print()

    # Step 9: Generate final quality report
    print("Step 9: Generating final quality report...")
    quality_report = generate_quality_report(metrics_by_pa)

    print("\n" + "=" * 80)
    print("FINAL QUALITY REPORT")
    print("=" * 80)
    print()

    # Summary
    summary = quality_report["summary"]
    print(f"Total Policy Areas: {summary['total_policy_areas']}")
    print(f"Total Patterns: {summary['total_patterns']}")
    print(f"Total Indicators: {summary['total_indicators']}")
    print(f"Total Entities: {summary['total_entities']}")
    print(f"Avg Patterns/PA: {summary['avg_patterns_per_pa']:.1f}")
    print(f"High Quality PAs: {len(summary['high_quality_pas'])}/{summary['total_policy_areas']} ({summary['high_quality_percentage']:.1f}%)")
    print()

    # Coverage tier distribution
    print("Coverage Tier Distribution:")
    for tier, count in sorted(summary["coverage_tier_distribution"].items()):
        print(f"  {tier:12s}: {count:2d} PAs")
    print()

    # Coverage gap analysis
    gap = quality_report["coverage_gap_analysis"]
    print(f"Coverage Gap Severity: {gap['gap_severity']}")
    print(f"Coverage Delta: {gap['coverage_delta']:.1f} patterns")
    print(f"Requires Fallback Fusion: {gap['requires_fallback_fusion']}")
    print()

    # Quality gates
    gates = quality_report["quality_gates"]
    print("Quality Gates:")
    for gate_name, passed in gates.items():
        if gate_name == "all_gates_passed":
            continue
        status = "✓" if passed else "✗"
        print(f"  {status} {gate_name.replace('_', ' ').title()}")
    print()

    if gates["all_gates_passed"]:
        print("=" * 80)
        print("✓ SOTA PA COVERAGE PIPELINE COMPLETE - ALL GATES PASSED")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("✗ SOTA PA COVERAGE PIPELINE COMPLETE - SOME GATES FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_sota_pipeline()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Pipeline failed with exception")
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
