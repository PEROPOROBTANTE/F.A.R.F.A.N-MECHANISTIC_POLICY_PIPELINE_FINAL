"""
Method validation system using calibration scores.

This module implements automatic validation that uses calibration scores
to make PASS/FAIL decisions about method execution.

Design:
- Integrates CalibrationOrchestrator for score computation
- Loads thresholds from MethodParameterLoader
- Makes validation decisions based on score vs threshold
- Provides detailed failure analysis
- Generates comprehensive validation reports
"""
import logging
from datetime import datetime
from typing import Dict, Optional, List, Any
from dataclasses import dataclass, field
from enum import Enum

from .orchestrator import CalibrationOrchestrator
from .parameter_loader import ParameterLoader
from .data_structures import CalibrationResult, ContextTuple, LayerID
from .pdt_structure import PDTStructure
from .intrinsic_loader import IntrinsicCalibrationLoader

logger = logging.getLogger(__name__)


class ValidationDecision(str, Enum):
    """Validation decision outcomes."""
    PASS = "PASS"
    FAIL = "FAIL"
    CONDITIONAL_PASS = "CONDITIONAL_PASS"
    SKIPPED = "SKIPPED"


class FailureReason(str, Enum):
    """Reasons for validation failure."""
    SCORE_BELOW_THRESHOLD = "score_below_threshold"
    BASE_LAYER_LOW = "base_layer_low_quality"
    CHAIN_LAYER_FAIL = "chain_layer_missing_inputs"
    CONGRUENCE_FAIL = "congruence_layer_inconsistent"
    UNIT_LAYER_FAIL = "unit_layer_pdt_quality_low"
    CONTEXTUAL_FAIL = "contextual_layer_incompatible"
    META_LAYER_FAIL = "meta_layer_governance_fail"
    METHOD_EXCLUDED = "method_excluded_from_calibration"
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of a single method validation."""
    method_id: str
    decision: ValidationDecision
    calibration_score: float
    threshold: float
    timestamp: str
    calibration_result: Optional[CalibrationResult] = None
    failure_reason: Optional[FailureReason] = None
    failure_details: Optional[str] = None
    layer_scores: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "method_id": self.method_id,
            "decision": self.decision.value,
            "calibration_score": self.calibration_score,
            "threshold": self.threshold,
            "timestamp": self.timestamp,
            "failure_reason": self.failure_reason.value if self.failure_reason else None,
            "failure_details": self.failure_details,
            "layer_scores": self.layer_scores,
            "recommendations": self.recommendations
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report for multiple methods."""
    plan_id: str
    timestamp: str
    total_methods: int
    passed: int
    failed: int
    conditional_pass: int
    skipped: int
    method_results: List[ValidationResult] = field(default_factory=list)
    overall_decision: ValidationDecision = ValidationDecision.CONDITIONAL_PASS
    summary: str = ""

    def pass_rate(self) -> float:
        """Calculate pass rate (0.0 - 1.0)."""
        if self.total_methods == 0:
            return 0.0
        return self.passed / self.total_methods

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "plan_id": self.plan_id,
            "timestamp": self.timestamp,
            "total_methods": self.total_methods,
            "passed": self.passed,
            "failed": self.failed,
            "conditional_pass": self.conditional_pass,
            "skipped": self.skipped,
            "pass_rate": self.pass_rate(),
            "overall_decision": self.overall_decision.value,
            "summary": self.summary,
            "method_results": [r.to_dict() for r in self.method_results]
        }


class CalibrationValidator:
    """
    Validates methods using calibration scores.

    This is the main entry point for automatic validation based on calibration.

    Usage:
        validator = CalibrationValidator(
            orchestrator=calibration_orchestrator,
            parameter_loader=parameter_loader
        )

        # Validate a single method
        result = validator.validate_method(
            method_id="D1Q1_Executor",
            method_version="1.0.0",
            context=context,
            pdt_structure=pdt
        )

        if result.decision == ValidationDecision.FAIL:
            print(f"Method failed: {result.failure_reason}")

        # Validate all executors for a plan
        report = validator.validate_plan_executors(
            plan_id="plan_bogota_2024",
            context=context,
            pdt_structure=pdt
        )

        print(f"Plan validation: {report.overall_decision}")
        print(f"Pass rate: {report.pass_rate():.1%}")
    """

    def __init__(
        self,
        orchestrator: CalibrationOrchestrator,
        parameter_loader: ParameterLoader,
        intrinsic_loader: Optional[IntrinsicCalibrationLoader] = None
    ):
        """
        Initialize the validator.

        Args:
            orchestrator: Calibration orchestrator for computing scores
            parameter_loader: Loader for method parameters and thresholds
            intrinsic_loader: Optional intrinsic score loader (for exclusion checks)
        """
        self.orchestrator = orchestrator
        self.parameter_loader = parameter_loader
        self.intrinsic_loader = intrinsic_loader or orchestrator.intrinsic_loader

        logger.info("calibration_validator_initialized")

    def validate_method(
        self,
        method_id: str,
        method_version: str,
        context: ContextTuple,
        pdt_structure: PDTStructure,
        graph_config: str = "default",
        subgraph_id: str = "default",
        override_threshold: Optional[float] = None
    ) -> ValidationResult:
        """
        Validate a single method using calibration.

        Args:
            method_id: Method identifier
            method_version: Method version
            context: Execution context
            pdt_structure: PDT structure for unit layer
            graph_config: Computational graph hash
            subgraph_id: Subgraph identifier
            override_threshold: Optional threshold override (for testing)

        Returns:
            ValidationResult with decision and details
        """
        timestamp = datetime.utcnow().isoformat()

        canonical_method_id = self._resolve_canonical_method_id(method_id)

        # Check if method is excluded from calibration
        if self.intrinsic_loader and self.intrinsic_loader.is_excluded(canonical_method_id):
            logger.info(
                "method_excluded_from_calibration",
                extra={
                    "method_id": method_id,
                    "canonical_method_id": canonical_method_id,
                }
            )
            return ValidationResult(
                method_id=method_id,
                decision=ValidationDecision.SKIPPED,
                calibration_score=1.0,  # Neutral, doesn't penalize
                threshold=0.0,
                timestamp=timestamp,
                failure_reason=FailureReason.METHOD_EXCLUDED,
                failure_details="Method is explicitly excluded from calibration system"
            )

        # Get validation threshold
        if override_threshold is not None:
            threshold = override_threshold
        else:
            threshold = self._get_threshold_for_method(
                method_id,
                canonical_method_id=canonical_method_id,
            )

        logger.info(
            "validating_method",
            extra={
                "method_id": method_id,
                "canonical_method_id": canonical_method_id,
                "threshold": threshold,
                "context": context.to_dict() if hasattr(context, 'to_dict') else str(context)
            }
        )

        # Perform calibration
        try:
            calibration_result = self.orchestrator.calibrate(
                method_id=canonical_method_id,
                method_version=method_version,
                context=context,
                pdt_structure=pdt_structure,
                graph_config=graph_config,
                subgraph_id=subgraph_id
            )

            final_score = calibration_result.final_score

            # Extract layer scores
            layer_scores = {
                layer_score.layer.value: layer_score.score
                for layer_score in calibration_result.layer_scores.values()
            }

            # Make decision
            if final_score >= threshold:
                decision = ValidationDecision.PASS
                failure_reason = None
                failure_details = None
                recommendations = []
            else:
                decision = ValidationDecision.FAIL
                failure_reason, failure_details = self._analyze_failure(
                    calibration_result, threshold
                )
                recommendations = self._generate_recommendations(
                    calibration_result, failure_reason
                )

            logger.info(
                "validation_complete",
                extra={
                    "method_id": method_id,
                    "canonical_method_id": canonical_method_id,
                    "decision": decision.value,
                    "score": final_score,
                    "threshold": threshold
                }
            )

            return ValidationResult(
                method_id=method_id,
                decision=decision,
                calibration_score=final_score,
                threshold=threshold,
                timestamp=timestamp,
                calibration_result=calibration_result,
                failure_reason=failure_reason,
                failure_details=failure_details,
                layer_scores=layer_scores,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(
                "validation_error",
                extra={
                    "method_id": method_id,
                    "canonical_method_id": canonical_method_id,
                    "error": str(e),
                },
                exc_info=True
            )

            return ValidationResult(
                method_id=method_id,
                decision=ValidationDecision.FAIL,
                calibration_score=0.0,
                threshold=threshold,
                timestamp=timestamp,
                failure_reason=FailureReason.UNKNOWN,
                failure_details=f"Calibration error: {str(e)}",
                recommendations=["Fix calibration system errors before retrying"]
            )

    def validate_plan_executors(
        self,
        plan_id: str,
        context: ContextTuple,
        pdt_structure: PDTStructure,
        executor_names: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Validate all executors for a plan.

        Args:
            plan_id: Plan identifier
            context: Execution context
            pdt_structure: PDT structure
            executor_names: Optional list of executor names (defaults to all 30)

        Returns:
            ValidationReport with overall results
        """
        timestamp = datetime.utcnow().isoformat()

        # Default: all 30 executors
        if executor_names is None:
            executor_names = [
                f"D{d}Q{q}_Executor"
                for d in range(1, 7)
                for q in range(1, 6)
            ]

        logger.info(
            "validating_plan_executors",
            extra={
                "plan_id": plan_id,
                "executor_count": len(executor_names)
            }
        )

        # Validate each executor
        results = []
        for executor_name in executor_names:
            result = self.validate_method(
                method_id=executor_name,
                method_version="1.0.0",  # TODO: Get from actual executor
                context=context,
                pdt_structure=pdt_structure,
                subgraph_id=f"{plan_id}_{executor_name}"
            )
            results.append(result)

        # Compute statistics
        passed = sum(1 for r in results if r.decision == ValidationDecision.PASS)
        failed = sum(1 for r in results if r.decision == ValidationDecision.FAIL)
        conditional = sum(1 for r in results if r.decision == ValidationDecision.CONDITIONAL_PASS)
        skipped = sum(1 for r in results if r.decision == ValidationDecision.SKIPPED)

        # Determine overall decision
        total_evaluated = len(executor_names) - skipped
        if total_evaluated == 0:
            overall_decision = ValidationDecision.SKIPPED
            summary = "No executors were evaluated"
        elif failed == 0:
            overall_decision = ValidationDecision.PASS
            summary = f"All {passed} executors passed validation"
        elif passed >= total_evaluated * 0.8:  # 80% threshold
            overall_decision = ValidationDecision.CONDITIONAL_PASS
            summary = f"{passed}/{total_evaluated} executors passed ({passed/total_evaluated:.1%})"
        else:
            overall_decision = ValidationDecision.FAIL
            summary = f"Only {passed}/{total_evaluated} executors passed ({passed/total_evaluated:.1%})"

        report = ValidationReport(
            plan_id=plan_id,
            timestamp=timestamp,
            total_methods=len(executor_names),
            passed=passed,
            failed=failed,
            conditional_pass=conditional,
            skipped=skipped,
            method_results=results,
            overall_decision=overall_decision,
            summary=summary
        )

        logger.info(
            "plan_validation_complete",
            extra={
                "plan_id": plan_id,
                "overall_decision": overall_decision.value,
                "pass_rate": report.pass_rate(),
                "passed": passed,
                "failed": failed
            }
        )

        return report

    def _get_threshold_for_method(
        self,
        method_id: str,
        *,
        canonical_method_id: Optional[str] = None,
    ) -> float:
        """
        Determine the appropriate threshold for a method.

        Args:
            method_id: Method identifier

        Returns:
            Threshold value in [0.0, 1.0]
        """
        # Check if it's an executor
        if "_Executor" in method_id or method_id.startswith("D") and "Q" in method_id:
            threshold = self.parameter_loader.get_executor_threshold(method_id)
            logger.debug(
                "using_executor_threshold",
                extra={"method_id": method_id, "threshold": threshold}
            )
            return threshold

        # Otherwise, get threshold by role
        canonical = canonical_method_id or method_id
        role = self.intrinsic_loader.get_layer(canonical) if self.intrinsic_loader else None

        if role:
            threshold = self.parameter_loader.get_validation_threshold_for_role(role)
            logger.debug(
                "using_role_threshold",
                extra={
                    "method_id": method_id,
                    "canonical_method_id": canonical,
                    "role": role,
                    "threshold": threshold,
                }
            )
            return threshold

        # Default: conservative threshold
        default_threshold = 0.70
        logger.debug(
            "using_default_threshold",
            extra={"method_id": method_id, "threshold": default_threshold}
        )
        return default_threshold

    def _resolve_canonical_method_id(self, method_id: str) -> str:
        """
        Resolve display-level identifiers to canonical catalogue identifiers.

        Args:
            method_id: Input identifier (e.g., "D1Q1_Executor")

        Returns:
            Canonical identifier suitable for calibration lookups.
        """
        # Already canonical (src.* namespace)
        if method_id.startswith("src."):
            return method_id

        # If intrinsic loader already knows this identifier, keep it
        if self.intrinsic_loader:
            try:
                if self.intrinsic_loader.get_method_data(method_id):
                    return method_id
            except Exception:
                # Fall back to heuristic resolutions
                pass

        if method_id.endswith("_Executor"):
            canonical = f"src.saaaaaa.core.orchestrator.executors.{method_id}.execute"
            if self.intrinsic_loader:
                try:
                    data = self.intrinsic_loader.get_method_data(canonical)
                    if data:
                        return canonical
                except Exception:
                    # Even if lookup fails, return canonical form for downstream systems
                    pass
            return canonical

        return method_id

    def _analyze_failure(
        self,
        calibration_result: CalibrationResult,
        threshold: float
    ) -> tuple[FailureReason, str]:
        """
        Analyze why a method failed validation.

        Args:
            calibration_result: Calibration result
            threshold: Threshold that was not met

        Returns:
            Tuple of (FailureReason, detailed_explanation)
        """
        # Find the lowest-scoring layer
        layer_scores = calibration_result.layer_scores
        if not layer_scores:
            return (
                FailureReason.UNKNOWN,
                f"Score {calibration_result.final_score:.3f} < {threshold:.3f}, but no layer breakdown available"
            )

        lowest_layer = min(layer_scores.values(), key=lambda ls: ls.score)

        # Determine failure reason based on lowest layer
        if lowest_layer.layer == LayerID.BASE:
            return (
                FailureReason.BASE_LAYER_LOW,
                f"Base layer (intrinsic quality) is low: {lowest_layer.score:.3f}. "
                f"Code quality issues detected. {lowest_layer.rationale}"
            )
        elif lowest_layer.layer == LayerID.CHAIN:
            return (
                FailureReason.CHAIN_LAYER_FAIL,
                f"Chain layer (data flow) failed: {lowest_layer.score:.3f}. "
                f"Missing or incompatible inputs. {lowest_layer.rationale}"
            )
        elif lowest_layer.layer == LayerID.CONGRUENCE:
            return (
                FailureReason.CONGRUENCE_FAIL,
                f"Congruence layer (method compatibility) failed: {lowest_layer.score:.3f}. "
                f"Inconsistent method ensemble. {lowest_layer.rationale}"
            )
        elif lowest_layer.layer == LayerID.UNIT:
            return (
                FailureReason.UNIT_LAYER_FAIL,
                f"Unit layer (PDT quality) is low: {lowest_layer.score:.3f}. "
                f"PDT structure issues detected. {lowest_layer.rationale}"
            )
        elif lowest_layer.layer in {LayerID.QUESTION, LayerID.DIMENSION, LayerID.POLICY}:
            return (
                FailureReason.CONTEXTUAL_FAIL,
                f"Contextual layer ({lowest_layer.layer.value}) incompatible: {lowest_layer.score:.3f}. "
                f"{lowest_layer.rationale}"
            )
        elif lowest_layer.layer == LayerID.META:
            return (
                FailureReason.META_LAYER_FAIL,
                f"Meta layer (governance) failed: {lowest_layer.score:.3f}. "
                f"Governance/transparency issues. {lowest_layer.rationale}"
            )
        else:
            return (
                FailureReason.SCORE_BELOW_THRESHOLD,
                f"Overall score {calibration_result.final_score:.3f} < {threshold:.3f}. "
                f"Lowest layer: {lowest_layer.layer.value} = {lowest_layer.score:.3f}"
            )

    def _generate_recommendations(
        self,
        calibration_result: CalibrationResult,
        failure_reason: FailureReason
    ) -> List[str]:
        """
        Generate actionable recommendations based on failure reason.

        Args:
            calibration_result: Calibration result
            failure_reason: Why validation failed

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if failure_reason == FailureReason.BASE_LAYER_LOW:
            recommendations.extend([
                "Improve code quality: add tests, documentation, type hints",
                "Review theoretical foundation of the method",
                "Consider refactoring for better maintainability"
            ])
        elif failure_reason == FailureReason.CHAIN_LAYER_FAIL:
            recommendations.extend([
                "Verify all required inputs are available in execution graph",
                "Check method_signatures.json for correct input specification",
                "Ensure upstream methods are executing correctly"
            ])
        elif failure_reason == FailureReason.CONGRUENCE_FAIL:
            recommendations.extend([
                "Review method ensemble for semantic compatibility",
                "Check method_registry.json for correct semantic tags",
                "Consider using different fusion rules"
            ])
        elif failure_reason == FailureReason.UNIT_LAYER_FAIL:
            recommendations.extend([
                "Improve PDT structure quality",
                "Ensure all mandatory sections are present",
                "Validate indicator and PPI quality"
            ])
        elif failure_reason == FailureReason.CONTEXTUAL_FAIL:
            recommendations.extend([
                "Verify method is appropriate for this question/dimension/policy",
                "Check compatibility registry for correct mappings",
                "Consider using a different method for this context"
            ])
        elif failure_reason == FailureReason.META_LAYER_FAIL:
            recommendations.extend([
                "Improve traceability: export formulas, add logging",
                "Validate governance compliance",
                "Optimize execution time if performance is an issue"
            ])
        else:
            recommendations.append(
                "Review all layer scores to identify specific improvement areas"
            )

        return recommendations
