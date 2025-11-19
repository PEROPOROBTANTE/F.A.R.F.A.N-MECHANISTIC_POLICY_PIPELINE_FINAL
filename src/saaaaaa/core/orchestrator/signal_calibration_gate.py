"""Signal Calibration Gate Module - Hard quality gates for SOTA requirements.

This module implements hard calibration gates to prevent silent degradation
in signal quality, coverage, and threshold calibration.

Key Features:
- Hard quality thresholds (fail-fast on violations)
- Calibration drift detection (threshold consistency)
- Coverage completeness checks (all PA01-PA10 present)
- Fingerprint uniqueness validation
- Temporal freshness gates (TTL bounds)

SOTA Requirements:
- Prevents silent degradation from misconfigured signals
- Enforces minimum quality bar for production
- Provides actionable error messages for violations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .signals import SignalPack
    from .signal_quality_metrics import SignalQualityMetrics

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class GateSeverity(str, Enum):
    """Gate violation severity levels."""
    ERROR = "ERROR"  # Blocks deployment
    WARNING = "WARNING"  # Logged but doesn't block
    INFO = "INFO"  # Informational only


@dataclass
class GateViolation:
    """Container for gate violation details.

    Attributes:
        gate_name: Name of violated gate
        severity: Violation severity
        policy_area_id: Affected policy area (if applicable)
        message: Human-readable error message
        actual_value: Actual measured value
        expected_value: Expected/threshold value
        remediation: Suggested fix
    """
    gate_name: str
    severity: GateSeverity
    policy_area_id: str | None
    message: str
    actual_value: Any
    expected_value: Any
    remediation: str


@dataclass
class CalibrationGateResult:
    """Result of calibration gate validation.

    Attributes:
        passed: Whether all gates passed
        violations: List of gate violations
        summary: Summary statistics
    """
    passed: bool
    violations: list[GateViolation] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """Check if any ERROR-level violations exist."""
        return any(v.severity == GateSeverity.ERROR for v in self.violations)

    @property
    def has_warnings(self) -> bool:
        """Check if any WARNING-level violations exist."""
        return any(v.severity == GateSeverity.WARNING for v in self.violations)

    def get_violations_by_severity(
        self,
        severity: GateSeverity
    ) -> list[GateViolation]:
        """Get violations filtered by severity."""
        return [v for v in self.violations if v.severity == severity]


@dataclass
class CalibrationGateConfig:
    """Configuration for calibration gates.

    Attributes:
        min_patterns_per_pa: Minimum patterns required per PA
        min_indicators_per_pa: Minimum indicators required per PA
        min_entities_per_pa: Minimum entities required per PA
        min_confidence_threshold: Minimum allowed confidence threshold
        max_confidence_threshold: Maximum allowed confidence threshold
        min_evidence_threshold: Minimum allowed evidence threshold
        max_threshold_drift: Maximum allowed drift between PA thresholds
        min_ttl_hours: Minimum TTL in hours
        max_ttl_hours: Maximum TTL in hours
        require_all_pas: Whether all PA01-PA10 must be present
        require_unique_fingerprints: Whether fingerprints must be unique
    """
    min_patterns_per_pa: int = 10
    min_indicators_per_pa: int = 2
    min_entities_per_pa: int = 2
    min_confidence_threshold: float = 0.70
    max_confidence_threshold: float = 0.95
    min_evidence_threshold: float = 0.65
    max_threshold_drift: float = 0.15
    min_ttl_hours: float = 1.0
    max_ttl_hours: float = 48.0
    require_all_pas: bool = True
    require_unique_fingerprints: bool = True


def validate_pattern_coverage_gate(
    metrics_by_pa: dict[str, SignalQualityMetrics],
    config: CalibrationGateConfig,
) -> list[GateViolation]:
    """
    Validate pattern coverage gate.

    Checks:
    - Each PA has minimum pattern count
    - Each PA has minimum indicator count
    - Each PA has minimum entity count

    Args:
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics
        config: Calibration gate configuration

    Returns:
        List of gate violations
    """
    violations = []

    for pa, metrics in metrics_by_pa.items():
        # Pattern count
        if metrics.pattern_count < config.min_patterns_per_pa:
            violations.append(GateViolation(
                gate_name="pattern_coverage",
                severity=GateSeverity.ERROR,
                policy_area_id=pa,
                message=f"Insufficient patterns in {pa}",
                actual_value=metrics.pattern_count,
                expected_value=config.min_patterns_per_pa,
                remediation="Extract more patterns from questionnaire or enable fusion",
            ))

        # Indicator count
        if metrics.indicator_count < config.min_indicators_per_pa:
            violations.append(GateViolation(
                gate_name="indicator_coverage",
                severity=GateSeverity.WARNING,
                policy_area_id=pa,
                message=f"Insufficient indicators in {pa}",
                actual_value=metrics.indicator_count,
                expected_value=config.min_indicators_per_pa,
                remediation="Review INDICADOR patterns in questionnaire",
            ))

        # Entity count
        if metrics.entity_count < config.min_entities_per_pa:
            violations.append(GateViolation(
                gate_name="entity_coverage",
                severity=GateSeverity.WARNING,
                policy_area_id=pa,
                message=f"Insufficient entities in {pa}",
                actual_value=metrics.entity_count,
                expected_value=config.min_entities_per_pa,
                remediation="Review FUENTE_OFICIAL patterns in questionnaire",
            ))

    return violations


def validate_threshold_calibration_gate(
    metrics_by_pa: dict[str, SignalQualityMetrics],
    config: CalibrationGateConfig,
) -> list[GateViolation]:
    """
    Validate threshold calibration gate.

    Checks:
    - Confidence thresholds within bounds
    - Evidence thresholds within bounds
    - Threshold drift across PAs is acceptable

    Args:
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics
        config: Calibration gate configuration

    Returns:
        List of gate violations
    """
    violations = []

    confidence_thresholds = []
    evidence_thresholds = []

    for pa, metrics in metrics_by_pa.items():
        # Confidence threshold bounds
        if metrics.threshold_min_confidence < config.min_confidence_threshold:
            violations.append(GateViolation(
                gate_name="confidence_threshold_too_low",
                severity=GateSeverity.ERROR,
                policy_area_id=pa,
                message=f"Confidence threshold too low in {pa}",
                actual_value=metrics.threshold_min_confidence,
                expected_value=config.min_confidence_threshold,
                remediation="Increase min_confidence threshold in signal pack",
            ))

        if metrics.threshold_min_confidence > config.max_confidence_threshold:
            violations.append(GateViolation(
                gate_name="confidence_threshold_too_high",
                severity=GateSeverity.WARNING,
                policy_area_id=pa,
                message=f"Confidence threshold too high in {pa}",
                actual_value=metrics.threshold_min_confidence,
                expected_value=config.max_confidence_threshold,
                remediation="Decrease min_confidence threshold to improve recall",
            ))

        # Evidence threshold bounds
        if metrics.threshold_min_evidence < config.min_evidence_threshold:
            violations.append(GateViolation(
                gate_name="evidence_threshold_too_low",
                severity=GateSeverity.ERROR,
                policy_area_id=pa,
                message=f"Evidence threshold too low in {pa}",
                actual_value=metrics.threshold_min_evidence,
                expected_value=config.min_evidence_threshold,
                remediation="Increase min_evidence threshold in signal pack",
            ))

        confidence_thresholds.append(metrics.threshold_min_confidence)
        evidence_thresholds.append(metrics.threshold_min_evidence)

    # Threshold drift check
    if confidence_thresholds:
        max_confidence = max(confidence_thresholds)
        min_confidence = min(confidence_thresholds)
        confidence_drift = max_confidence - min_confidence

        if confidence_drift > config.max_threshold_drift:
            violations.append(GateViolation(
                gate_name="threshold_drift_excessive",
                severity=GateSeverity.WARNING,
                policy_area_id=None,
                message="Excessive threshold drift across policy areas",
                actual_value=confidence_drift,
                expected_value=config.max_threshold_drift,
                remediation="Recalibrate thresholds for consistency",
            ))

    return violations


def validate_completeness_gate(
    signal_packs: dict[str, SignalPack],
    config: CalibrationGateConfig,
) -> list[GateViolation]:
    """
    Validate completeness gate.

    Checks:
    - All PA01-PA10 are present
    - No missing policy areas

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack
        config: Calibration gate configuration

    Returns:
        List of gate violations
    """
    violations = []

    if config.require_all_pas:
        expected_pas = {f"PA{i:02d}" for i in range(1, 11)}
        actual_pas = set(signal_packs.keys())
        missing_pas = expected_pas - actual_pas

        if missing_pas:
            violations.append(GateViolation(
                gate_name="completeness_missing_pas",
                severity=GateSeverity.ERROR,
                policy_area_id=None,
                message="Missing policy areas",
                actual_value=sorted(actual_pas),
                expected_value=sorted(expected_pas),
                remediation=f"Add missing policy areas: {sorted(missing_pas)}",
            ))

    return violations


def validate_fingerprint_uniqueness_gate(
    signal_packs: dict[str, SignalPack],
    config: CalibrationGateConfig,
) -> list[GateViolation]:
    """
    Validate fingerprint uniqueness gate.

    Checks:
    - All fingerprints are unique
    - No duplicate fingerprints

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack
        config: Calibration gate configuration

    Returns:
        List of gate violations
    """
    violations = []

    if config.require_unique_fingerprints:
        # Import here to avoid circular dependency
        from .signal_aliasing import validate_fingerprint_uniqueness

        result = validate_fingerprint_uniqueness(signal_packs)

        if not result["is_valid"]:
            for fingerprint, pas in result["collisions"].items():
                violations.append(GateViolation(
                    gate_name="fingerprint_collision",
                    severity=GateSeverity.ERROR,
                    policy_area_id=None,
                    message=f"Duplicate fingerprint across policy areas",
                    actual_value=pas,
                    expected_value="unique fingerprints",
                    remediation=f"Use soft-alias pattern to resolve collision: {pas}",
                ))

    return violations


def validate_temporal_freshness_gate(
    metrics_by_pa: dict[str, SignalQualityMetrics],
    config: CalibrationGateConfig,
) -> list[GateViolation]:
    """
    Validate temporal freshness gate.

    Checks:
    - TTL within bounds
    - Temporal bounds set (valid_from/valid_to)

    Args:
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics
        config: Calibration gate configuration

    Returns:
        List of gate violations
    """
    violations = []

    for pa, metrics in metrics_by_pa.items():
        # TTL bounds
        if metrics.ttl_hours < config.min_ttl_hours:
            violations.append(GateViolation(
                gate_name="ttl_too_short",
                severity=GateSeverity.WARNING,
                policy_area_id=pa,
                message=f"TTL too short in {pa}",
                actual_value=metrics.ttl_hours,
                expected_value=config.min_ttl_hours,
                remediation="Increase TTL to reduce cache churn",
            ))

        if metrics.ttl_hours > config.max_ttl_hours:
            violations.append(GateViolation(
                gate_name="ttl_too_long",
                severity=GateSeverity.WARNING,
                policy_area_id=pa,
                message=f"TTL too long in {pa}",
                actual_value=metrics.ttl_hours,
                expected_value=config.max_ttl_hours,
                remediation="Decrease TTL to ensure freshness",
            ))

        # Temporal bounds
        if not metrics.has_temporal_bounds:
            violations.append(GateViolation(
                gate_name="missing_temporal_bounds",
                severity=GateSeverity.INFO,
                policy_area_id=pa,
                message=f"Missing temporal bounds in {pa}",
                actual_value=None,
                expected_value="valid_from/valid_to",
                remediation="Set valid_from/valid_to for temporal tracking",
            ))

    return violations


def run_calibration_gates(
    signal_packs: dict[str, SignalPack],
    metrics_by_pa: dict[str, SignalQualityMetrics],
    config: CalibrationGateConfig | None = None,
) -> CalibrationGateResult:
    """
    Run all calibration gates and return comprehensive result.

    This is the main entry point for calibration gate validation.

    Args:
        signal_packs: Dict mapping policy_area_id to SignalPack
        metrics_by_pa: Dict mapping policy_area_id to SignalQualityMetrics
        config: Calibration gate configuration (uses default if None)

    Returns:
        CalibrationGateResult with validation results

    Example:
        >>> packs = build_all_signal_packs()
        >>> metrics = {pa: compute_signal_quality_metrics(pack, pa) for pa, pack in packs.items()}
        >>> result = run_calibration_gates(packs, metrics)
        >>> if not result.passed:
        >>>     for violation in result.get_violations_by_severity(GateSeverity.ERROR):
        >>>         print(f"ERROR: {violation.message}")
        >>>     raise ValueError("Calibration gates failed")
    """
    if config is None:
        config = CalibrationGateConfig()

    all_violations: list[GateViolation] = []

    # Run all gates
    all_violations.extend(validate_pattern_coverage_gate(metrics_by_pa, config))
    all_violations.extend(validate_threshold_calibration_gate(metrics_by_pa, config))
    all_violations.extend(validate_completeness_gate(signal_packs, config))
    all_violations.extend(validate_fingerprint_uniqueness_gate(signal_packs, config))
    all_violations.extend(validate_temporal_freshness_gate(metrics_by_pa, config))

    # Classify violations by severity
    errors = [v for v in all_violations if v.severity == GateSeverity.ERROR]
    warnings = [v for v in all_violations if v.severity == GateSeverity.WARNING]
    infos = [v for v in all_violations if v.severity == GateSeverity.INFO]

    # Gates pass only if no errors
    passed = len(errors) == 0

    summary = {
        "total_violations": len(all_violations),
        "errors": len(errors),
        "warnings": len(warnings),
        "infos": len(infos),
        "gates_passed": passed,
        "gates_run": 5,  # Number of gate functions
    }

    result = CalibrationGateResult(
        passed=passed,
        violations=all_violations,
        summary=summary,
    )

    if passed:
        logger.info(
            "calibration_gates_passed",
            total_violations=len(all_violations),
            warnings=len(warnings),
            infos=len(infos),
        )
    else:
        logger.error(
            "calibration_gates_failed",
            total_violations=len(all_violations),
            errors=len(errors),
            warnings=len(warnings),
        )

    return result


def generate_gate_report(result: CalibrationGateResult) -> str:
    """
    Generate human-readable report for calibration gate results.

    Args:
        result: CalibrationGateResult to report

    Returns:
        Formatted report string

    Example:
        >>> result = run_calibration_gates(packs, metrics)
        >>> print(generate_gate_report(result))
    """
    lines = []
    lines.append("=" * 80)
    lines.append("CALIBRATION GATE REPORT")
    lines.append("=" * 80)
    lines.append("")

    # Summary
    lines.append(f"Gates Passed: {'✓ YES' if result.passed else '✗ NO'}")
    lines.append(f"Total Violations: {result.summary['total_violations']}")
    lines.append(f"  - Errors: {result.summary['errors']}")
    lines.append(f"  - Warnings: {result.summary['warnings']}")
    lines.append(f"  - Infos: {result.summary['infos']}")
    lines.append("")

    # Errors
    errors = result.get_violations_by_severity(GateSeverity.ERROR)
    if errors:
        lines.append("ERRORS:")
        for v in errors:
            pa_str = f"[{v.policy_area_id}] " if v.policy_area_id else ""
            lines.append(f"  ✗ {pa_str}{v.message}")
            lines.append(f"    Actual: {v.actual_value}, Expected: {v.expected_value}")
            lines.append(f"    Remediation: {v.remediation}")
            lines.append("")

    # Warnings
    warnings = result.get_violations_by_severity(GateSeverity.WARNING)
    if warnings:
        lines.append("WARNINGS:")
        for v in warnings:
            pa_str = f"[{v.policy_area_id}] " if v.policy_area_id else ""
            lines.append(f"  ⚠ {pa_str}{v.message}")
            lines.append(f"    Actual: {v.actual_value}, Expected: {v.expected_value}")
            lines.append(f"    Remediation: {v.remediation}")
            lines.append("")

    lines.append("=" * 80)

    return "\n".join(lines)
