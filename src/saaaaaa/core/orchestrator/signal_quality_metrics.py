"""Signal Quality Metrics Module - Observability for PA coverage analysis.

This module implements quality metrics monitoring for policy area coverage,
specifically designed to detect and measure PA07-PA10 coverage gaps.

Key Features:
- Pattern density metrics (patterns per policy area)
- Threshold calibration tracking (min_confidence, min_evidence)
- Entity coverage analysis (institutional completeness)
- Temporal freshness monitoring (TTL, valid_from/valid_to)
- Coverage gap detection (PA07-PA10 vs PA01-PA06 comparison)

SOTA Requirements:
- Observability for PA coverage gaps
- Quality gates for calibration drift
- Metrics for intelligent fallback fusion
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .signals import SignalPack

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class SignalQualityMetrics:
    """Quality metrics for a single SignalPack.

    Attributes:
        policy_area_id: Policy area identifier (PA01-PA10)
        pattern_count: Total number of patterns
        indicator_count: Total number of indicators
        entity_count: Total number of entities
        regex_count: Total number of regex patterns
        threshold_min_confidence: Minimum confidence threshold
        threshold_min_evidence: Minimum evidence threshold
        ttl_hours: Time-to-live in hours
        has_temporal_bounds: Whether valid_from/valid_to are set
        pattern_density: Patterns per 100 tokens (estimated)
        entity_coverage_ratio: Entities / patterns ratio
        fingerprint: Source fingerprint
        metadata: Additional metadata
    """
    policy_area_id: str
    pattern_count: int
    indicator_count: int
    entity_count: int
    regex_count: int
    threshold_min_confidence: float
    threshold_min_evidence: float
    ttl_hours: float
    has_temporal_bounds: bool
    pattern_density: float
    entity_coverage_ratio: float
    fingerprint: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_quality(self) -> bool:
        """Check if signal pack meets high-quality thresholds.

        High-quality criteria:
        - At least 15 patterns
        - At least 3 indicators
        - At least 3 entities
        - Min confidence >= 0.75
        - Min evidence >= 0.70
        - Entity coverage ratio >= 0.15
        """
        return (
            self.pattern_count >= 15
            and self.indicator_count >= 3
            and self.entity_count >= 3
            and self.threshold_min_confidence >= 0.75
            and self.threshold_min_evidence >= 0.70
            and self.entity_coverage_ratio >= 0.15
        )

    @property
    def coverage_tier(self) -> str:
        """Classify coverage tier based on pattern count.

        Tiers:
        - EXCELLENT: >= 30 patterns
        - GOOD: >= 20 patterns
        - ADEQUATE: >= 15 patterns
        - SPARSE: < 15 patterns
        """
        if self.pattern_count >= 30:
            return "EXCELLENT"
        elif self.pattern_count >= 20:
            return "GOOD"
        elif self.pattern_count >= 15:
            return "ADEQUATE"
        else:
            return "SPARSE"


@dataclass
class CoverageGapAnalysis:
    """Coverage gap analysis comparing PA groups.

    Attributes:
        high_coverage_pas: List of PA IDs with high coverage (typically PA01-PA06)
        low_coverage_pas: List of PA IDs with low coverage (typically PA07-PA10)
        coverage_delta: Average pattern count difference
        threshold_delta: Average confidence threshold difference
        gap_severity: Classification of gap severity
        recommendations: List of recommended actions
    """
    high_coverage_pas: list[str]
    low_coverage_pas: list[str]
    coverage_delta: float
    threshold_delta: float
    gap_severity: str
    recommendations: list[str] = field(default_factory=list)

    @property
    def requires_fallback_fusion(self) -> bool:
        """Check if coverage gap requires intelligent fallback fusion."""
        return self.gap_severity in ("CRITICAL", "SEVERE")


def compute_signal_quality_metrics(
    signal_pack: SignalPack,
    policy_area_id: str,
) -> SignalQualityMetrics:
    """
    Compute quality metrics for a SignalPack.

    Args:
        signal_pack: SignalPack object to analyze
        policy_area_id: Policy area identifier (PA01-PA10)

    Returns:
        SignalQualityMetrics object

    Example:
        >>> pack = build_signal_pack_from_monolith("PA07")
        >>> metrics = compute_signal_quality_metrics(pack, "PA07")
        >>> print(f"Coverage tier: {metrics.coverage_tier}")
        >>> print(f"High quality: {metrics.is_high_quality}")
    """
    pattern_count = len(signal_pack.patterns)
    indicator_count = len(signal_pack.indicators)
    entity_count = len(signal_pack.entities)
    regex_count = len(signal_pack.regex)

    # Extract thresholds
    threshold_min_confidence = signal_pack.thresholds.get("min_confidence", 0.85)
    threshold_min_evidence = signal_pack.thresholds.get("min_evidence", 0.70)

    # Convert TTL to hours
    ttl_hours = signal_pack.ttl_s / 3600.0 if signal_pack.ttl_s else 24.0

    # Check temporal bounds
    has_temporal_bounds = bool(
        signal_pack.metadata.get("valid_from") or
        hasattr(signal_pack, 'valid_from') and signal_pack.valid_from  # type: ignore
    )

    # Estimate pattern density (patterns per 100 tokens)
    # Assuming average pattern length of 3 tokens
    estimated_tokens = pattern_count * 3
    pattern_density = (pattern_count / max(estimated_tokens, 1)) * 100

    # Entity coverage ratio
    entity_coverage_ratio = entity_count / max(pattern_count, 1)

    metrics = SignalQualityMetrics(
        policy_area_id=policy_area_id,
        pattern_count=pattern_count,
        indicator_count=indicator_count,
        entity_count=entity_count,
        regex_count=regex_count,
        threshold_min_confidence=threshold_min_confidence,
        threshold_min_evidence=threshold_min_evidence,
        ttl_hours=ttl_hours,
        has_temporal_bounds=has_temporal_bounds,
        pattern_density=pattern_density,
        entity_coverage_ratio=entity_coverage_ratio,
        fingerprint=signal_pack.source_fingerprint,
        metadata={
            "version": signal_pack.version,
            "original_metadata": signal_pack.metadata,
        },
    )

    logger.debug(
        "signal_quality_metrics_computed",
        policy_area_id=policy_area_id,
        coverage_tier=metrics.coverage_tier,
        is_high_quality=metrics.is_high_quality,
        pattern_count=pattern_count,
    )

    return metrics


def analyze_coverage_gaps(
    metrics_by_pa: dict[str, SignalQualityMetrics]
) -> CoverageGapAnalysis:
    """
    Analyze coverage gaps between PA groups (PA01-PA06 vs PA07-PA10).

    This implements the coverage gap detection algorithm for SOTA requirements.

    Args:
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics

    Returns:
        CoverageGapAnalysis object

    Example:
        >>> packs = build_all_signal_packs()
        >>> metrics = {pa: compute_signal_quality_metrics(pack, pa) for pa, pack in packs.items()}
        >>> gap_analysis = analyze_coverage_gaps(metrics)
        >>> print(f"Gap severity: {gap_analysis.gap_severity}")
        >>> print(f"Requires fallback: {gap_analysis.requires_fallback_fusion}")
    """
    # Split into high-coverage and low-coverage groups
    pa01_pa06 = [f"PA{i:02d}" for i in range(1, 7)]
    pa07_pa10 = [f"PA{i:02d}" for i in range(7, 11)]

    high_coverage_metrics = [
        metrics_by_pa[pa] for pa in pa01_pa06 if pa in metrics_by_pa
    ]
    low_coverage_metrics = [
        metrics_by_pa[pa] for pa in pa07_pa10 if pa in metrics_by_pa
    ]

    if not high_coverage_metrics or not low_coverage_metrics:
        return CoverageGapAnalysis(
            high_coverage_pas=[],
            low_coverage_pas=[],
            coverage_delta=0.0,
            threshold_delta=0.0,
            gap_severity="UNKNOWN",
            recommendations=["Insufficient data for gap analysis"],
        )

    # Compute average pattern counts
    high_avg_patterns = sum(m.pattern_count for m in high_coverage_metrics) / len(high_coverage_metrics)
    low_avg_patterns = sum(m.pattern_count for m in low_coverage_metrics) / len(low_coverage_metrics)
    coverage_delta = high_avg_patterns - low_avg_patterns

    # Compute average confidence thresholds
    high_avg_confidence = sum(m.threshold_min_confidence for m in high_coverage_metrics) / len(high_coverage_metrics)
    low_avg_confidence = sum(m.threshold_min_confidence for m in low_coverage_metrics) / len(low_coverage_metrics)
    threshold_delta = high_avg_confidence - low_avg_confidence

    # Classify gap severity
    if coverage_delta >= 50:
        gap_severity = "CRITICAL"
    elif coverage_delta >= 30:
        gap_severity = "SEVERE"
    elif coverage_delta >= 15:
        gap_severity = "MODERATE"
    elif coverage_delta >= 5:
        gap_severity = "MINOR"
    else:
        gap_severity = "NEGLIGIBLE"

    # Generate recommendations
    recommendations = []
    if gap_severity in ("CRITICAL", "SEVERE"):
        recommendations.append("Enable intelligent fallback fusion for PA07-PA10")
        recommendations.append("Review pattern extraction for low-coverage PAs")
        recommendations.append("Consider cross-PA pattern sharing for common terms")

    if threshold_delta > 0.05:
        recommendations.append("Recalibrate confidence thresholds for consistency")

    # Identify specific low-coverage PAs
    sparse_pas = [
        m.policy_area_id for m in low_coverage_metrics
        if m.coverage_tier == "SPARSE"
    ]
    if sparse_pas:
        recommendations.append(f"Boost pattern extraction for: {', '.join(sparse_pas)}")

    analysis = CoverageGapAnalysis(
        high_coverage_pas=[m.policy_area_id for m in high_coverage_metrics],
        low_coverage_pas=[m.policy_area_id for m in low_coverage_metrics],
        coverage_delta=coverage_delta,
        threshold_delta=threshold_delta,
        gap_severity=gap_severity,
        recommendations=recommendations,
    )

    logger.info(
        "coverage_gap_analysis_completed",
        gap_severity=gap_severity,
        coverage_delta=coverage_delta,
        requires_fallback=analysis.requires_fallback_fusion,
    )

    return analysis


def generate_quality_report(
    metrics_by_pa: dict[str, SignalQualityMetrics]
) -> dict[str, Any]:
    """
    Generate comprehensive quality report for all policy areas.

    Args:
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics

    Returns:
        Quality report dict with:
        - summary: Overall statistics
        - by_policy_area: Per-PA metrics
        - coverage_gap_analysis: Gap analysis results
        - quality_gates: Pass/fail status for quality gates

    Example:
        >>> packs = build_all_signal_packs()
        >>> metrics = {pa: compute_signal_quality_metrics(pack, pa) for pa, pack in packs.items()}
        >>> report = generate_quality_report(metrics)
        >>> print(json.dumps(report["summary"], indent=2))
    """
    # Overall statistics
    total_patterns = sum(m.pattern_count for m in metrics_by_pa.values())
    total_indicators = sum(m.indicator_count for m in metrics_by_pa.values())
    total_entities = sum(m.entity_count for m in metrics_by_pa.values())

    avg_confidence = sum(m.threshold_min_confidence for m in metrics_by_pa.values()) / len(metrics_by_pa)
    avg_evidence = sum(m.threshold_min_evidence for m in metrics_by_pa.values()) / len(metrics_by_pa)

    high_quality_pas = [
        pa for pa, m in metrics_by_pa.items() if m.is_high_quality
    ]

    # Coverage tier distribution
    tier_distribution = {}
    for m in metrics_by_pa.values():
        tier = m.coverage_tier
        tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

    # Coverage gap analysis
    gap_analysis = analyze_coverage_gaps(metrics_by_pa)

    # Quality gates
    quality_gates = {
        "all_pas_have_patterns": all(m.pattern_count > 0 for m in metrics_by_pa.values()),
        "all_pas_high_quality": len(high_quality_pas) == len(metrics_by_pa),
        "no_critical_gaps": gap_analysis.gap_severity not in ("CRITICAL",),
        "thresholds_calibrated": abs(gap_analysis.threshold_delta) < 0.10,
    }

    quality_gates["all_gates_passed"] = all(quality_gates.values())

    report = {
        "summary": {
            "total_policy_areas": len(metrics_by_pa),
            "total_patterns": total_patterns,
            "total_indicators": total_indicators,
            "total_entities": total_entities,
            "avg_patterns_per_pa": total_patterns / len(metrics_by_pa),
            "avg_confidence_threshold": round(avg_confidence, 3),
            "avg_evidence_threshold": round(avg_evidence, 3),
            "high_quality_pas": high_quality_pas,
            "high_quality_percentage": round(len(high_quality_pas) / len(metrics_by_pa) * 100, 1),
            "coverage_tier_distribution": tier_distribution,
        },
        "by_policy_area": {
            pa: {
                "pattern_count": m.pattern_count,
                "indicator_count": m.indicator_count,
                "entity_count": m.entity_count,
                "coverage_tier": m.coverage_tier,
                "is_high_quality": m.is_high_quality,
                "threshold_min_confidence": m.threshold_min_confidence,
                "threshold_min_evidence": m.threshold_min_evidence,
                "entity_coverage_ratio": round(m.entity_coverage_ratio, 3),
            }
            for pa, m in metrics_by_pa.items()
        },
        "coverage_gap_analysis": {
            "high_coverage_pas": gap_analysis.high_coverage_pas,
            "low_coverage_pas": gap_analysis.low_coverage_pas,
            "coverage_delta": round(gap_analysis.coverage_delta, 2),
            "threshold_delta": round(gap_analysis.threshold_delta, 3),
            "gap_severity": gap_analysis.gap_severity,
            "requires_fallback_fusion": gap_analysis.requires_fallback_fusion,
            "recommendations": gap_analysis.recommendations,
        },
        "quality_gates": quality_gates,
    }

    logger.info(
        "quality_report_generated",
        total_pas=len(metrics_by_pa),
        all_gates_passed=quality_gates["all_gates_passed"],
        gap_severity=gap_analysis.gap_severity,
    )

    return report
