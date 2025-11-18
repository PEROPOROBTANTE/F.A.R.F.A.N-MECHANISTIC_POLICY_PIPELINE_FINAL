"""
Base Layer (@b) - Intrinsic Quality Evaluator.

This layer evaluates the inherent quality of methods based on:
- b_theory: Theoretical foundation quality
- b_impl: Implementation quality
- b_deploy: Deployment maturity

Scores are loaded from intrinsic_calibration.json, which is populated
by rigorous_calibration_triage.py using intrinsic_calibration_rubric.json.
"""
import json
import logging
from pathlib import Path
from typing import Any

from .data_structures import LayerID, LayerScore

logger = logging.getLogger(__name__)


class BaseLayerEvaluator:
    """
    Evaluates Base Layer (@b) - Intrinsic method quality.

    This layer reads pre-computed calibration scores from the
    intrinsic calibration registry.

    Usage:
        evaluator = BaseLayerEvaluator("config/intrinsic_calibration.json")
        score = evaluator.evaluate("pattern_extractor_v2")
    """

    # Aggregation weights for base layer components
    # These define how b_theory, b_impl, b_deploy combine into final @b score
    THEORY_WEIGHT = 0.4   # Theoretical foundation importance
    IMPL_WEIGHT = 0.4     # Implementation quality importance
    DEPLOY_WEIGHT = 0.2   # Deployment maturity importance

    # Penalty score for methods without calibration data
    UNCALIBRATED_PENALTY = 0.1

    def __init__(self, intrinsic_calibration_path: Path | str) -> None:
        """
        Initialize evaluator with intrinsic calibration data.

        Args:
            intrinsic_calibration_path: Path to intrinsic_calibration.json

        Raises:
            FileNotFoundError: If calibration file doesn't exist
            ValueError: If calibration file has invalid structure
        """
        self.calibration_path = Path(intrinsic_calibration_path)
        self.calibrations: dict[str, dict[str, Any]] = {}
        self._load()

        # Verify aggregation weights sum to 1.0
        total_weight = self.THEORY_WEIGHT + self.IMPL_WEIGHT + self.DEPLOY_WEIGHT
        if abs(total_weight - 1.0) > 1e-6:
            raise ValueError(
                f"Base layer component weights must sum to 1.0, got {total_weight}"
            )

    def _load(self) -> None:
        """Load intrinsic calibration scores from JSON."""
        if not self.calibration_path.exists():
            raise FileNotFoundError(
                f"Intrinsic calibration file not found: {self.calibration_path}\n"
                f"Run scripts/rigorous_calibration_triage.py to generate it."
            )

        with open(self.calibration_path, encoding='utf-8') as f:
            data = json.load(f)

        # Validate structure
        if "methods" not in data:
            raise ValueError(
                "Intrinsic calibration file must have 'methods' key at top level"
            )

        # Load each method's calibration
        methods = data["methods"]

        for method_id, cal_data in methods.items():
            # Skip metadata entries (start with _)
            if method_id.startswith("_"):
                continue

            calibration_status = cal_data.get("calibration_status", "unknown")

            # Only load methods with computed calibration
            if calibration_status == "computed":
                self.calibrations[method_id] = {
                    "b_theory": cal_data.get("b_theory", 0.0),
                    "b_impl": cal_data.get("b_impl", 0.0),
                    "b_deploy": cal_data.get("b_deploy", 0.0),
                    "evidence": cal_data.get("evidence", {}),
                    "layer": cal_data.get("layer", "unknown"),
                    "last_updated": cal_data.get("last_updated", "unknown"),
                }

                logger.debug(
                    "intrinsic_calibration_loaded",
                    extra={
                        "method": method_id,
                        "b_theory": self.calibrations[method_id]["b_theory"],
                        "b_impl": self.calibrations[method_id]["b_impl"],
                        "b_deploy": self.calibrations[method_id]["b_deploy"],
                    }
                )
            elif calibration_status == "excluded":
                # Methods explicitly excluded from calibration
                logger.debug(
                    "method_excluded_from_calibration",
                    extra={
                        "method": method_id,
                        "reason": cal_data.get("reason", "unknown"),
                    }
                )

        logger.info(
            "base_layer_calibrations_loaded",
            extra={
                "total_methods": len(self.calibrations),
                "calibration_file": str(self.calibration_path),
            }
        )

    def evaluate(self, method_id: str) -> LayerScore:
        """
        Evaluate BASE layer (@b) for a method.

        This retrieves pre-computed intrinsic calibration scores and
        aggregates them using configured weights.

        Args:
            method_id: Canonical method identifier (e.g., "pattern_extractor_v2")

        Returns:
            LayerScore with @b score and component breakdown

        Formula:
            @b = w_theory · b_theory + w_impl · b_impl + w_deploy · b_deploy
            where w_theory=0.4, w_impl=0.4, w_deploy=0.2
        """
        # Check if method has calibration data
        if method_id not in self.calibrations:
            logger.warning(
                "method_not_calibrated",
                extra={
                    "method": method_id,
                    "penalty_score": self.UNCALIBRATED_PENALTY,
                }
            )
            return LayerScore(
                layer=LayerID.BASE,
                score=self.UNCALIBRATED_PENALTY,
                rationale=f"Method '{method_id}' not found in intrinsic calibration registry. "
                          f"Using penalty score {self.UNCALIBRATED_PENALTY}. "
                          f"Run rigorous_calibration_triage.py to calibrate.",
                metadata={
                    "calibration_status": "not_found",
                    "penalty": True,
                }
            )

        # Get calibration components
        cal = self.calibrations[method_id]
        b_theory = cal["b_theory"]
        b_impl = cal["b_impl"]
        b_deploy = cal["b_deploy"]

        # Aggregate components using weights
        base_score = (
            self.THEORY_WEIGHT * b_theory +
            self.IMPL_WEIGHT * b_impl +
            self.DEPLOY_WEIGHT * b_deploy
        )

        # Determine quality level
        if base_score >= 0.8:
            quality = "excellent"
        elif base_score >= 0.6:
            quality = "good"
        elif base_score >= 0.4:
            quality = "acceptable"
        else:
            quality = "needs_improvement"

        logger.info(
            "base_layer_evaluated",
            extra={
                "method": method_id,
                "base_score": base_score,
                "quality": quality,
                "b_theory": b_theory,
                "b_impl": b_impl,
                "b_deploy": b_deploy,
            }
        )

        # Create LayerScore with full breakdown
        return LayerScore(
            layer=LayerID.BASE,
            score=base_score,
            components={
                "b_theory": b_theory,
                "b_impl": b_impl,
                "b_deploy": b_deploy,
                "theory_weight": self.THEORY_WEIGHT,
                "impl_weight": self.IMPL_WEIGHT,
                "deploy_weight": self.DEPLOY_WEIGHT,
            },
            rationale=f"Intrinsic quality: {quality} "
                     f"(theory={b_theory:.2f}, impl={b_impl:.2f}, deploy={b_deploy:.2f})",
            metadata={
                "calibration_status": "loaded",
                "layer": cal["layer"],
                "last_updated": cal["last_updated"],
                "formula": f"{self.THEORY_WEIGHT}*theory + {self.IMPL_WEIGHT}*impl + {self.DEPLOY_WEIGHT}*deploy",
                "quality_level": quality,
            }
        )

    def get_calibration_info(self, method_id: str) -> dict[str, Any] | None:
        """
        Get full calibration info for a method (including evidence).

        This is useful for debugging or detailed auditing.

        Args:
            method_id: Method identifier

        Returns:
            Calibration dictionary or None if not found
        """
        return self.calibrations.get(method_id)

    def get_coverage_stats(self) -> dict[str, Any]:
        """
        Get statistics about calibration coverage.

        Returns:
            Dict with coverage information:
                - total_calibrated: Number of methods with calibration
                - by_layer: Breakdown by layer
                - avg_scores: Average scores per component
        """
        total = len(self.calibrations)

        # Count by layer
        by_layer = {}
        for cal in self.calibrations.values():
            layer = cal["layer"]
            by_layer[layer] = by_layer.get(layer, 0) + 1

        # Compute average scores
        if total > 0:
            avg_theory = sum(c["b_theory"] for c in self.calibrations.values()) / total
            avg_impl = sum(c["b_impl"] for c in self.calibrations.values()) / total
            avg_deploy = sum(c["b_deploy"] for c in self.calibrations.values()) / total
        else:
            avg_theory = avg_impl = avg_deploy = 0.0

        return {
            "total_calibrated": total,
            "by_layer": by_layer,
            "avg_scores": {
                "b_theory": round(avg_theory, 3),
                "b_impl": round(avg_impl, 3),
                "b_deploy": round(avg_deploy, 3),
            },
            "calibration_file": str(self.calibration_path),
        }
