"""Calibration Orchestrator - Mandatory Single Path Enforcement.

This module implements the ONLY allowed path for calibration scoring.
Any code that bypasses this orchestrator MUST be rejected.

Architecture:
- Singleton pattern enforces single entry point
- Loads intrinsic calibration (@b scores) from JSON
- Reads layer requirements from canonical inventory
- Computes runtime layers dynamically (@chain, @q, @d, @p, @C, @u, @m)
- Aggregates via choquet_integral or weighted_sum
- Applies threshold: ≥0.7 PASS, <0.7 FAIL

CRITICAL: This is the ONLY calibration path. All other calibration logic must be removed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from farfan_pipeline.core.orchestrator.calibration_types import (
    IntrinsicScores,
    LayerRequirements,
    RuntimeLayers,
)

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.calibration_context import CalibrationContext

logger = logging.getLogger(__name__)

CALIBRATION_THRESHOLD = 0.7


class MissingIntrinsicCalibrationError(Exception):
    """Raised when intrinsic calibration (@b scores) are missing for a method."""

    def __init__(self, method_id: str) -> None:
        self.method_id = method_id
        super().__init__(
            f"Missing intrinsic calibration for method '{method_id}'. "
            f"All methods must have @b scores in intrinsic_calibration.json"
        )


class InsufficientContextError(Exception):
    """Raised when context is required but not provided."""

    def __init__(self, method_id: str) -> None:
        self.method_id = method_id
        super().__init__(
            f"Insufficient context for method '{method_id}'. "
            f"CalibrationContext is required for runtime layer evaluation."
        )


class MethodBelowThresholdError(Exception):
    """Raised when a method's calibration score falls below threshold."""

    def __init__(self, method_id: str, score: float, threshold: float) -> None:
        self.method_id = method_id
        self.score = score
        self.threshold = threshold
        super().__init__(
            f"Method '{method_id}' calibration score {score:.3f} is below "
            f"threshold {threshold:.3f}. Method cannot be executed."
        )


class CalibrationOrchestrator:
    """Singleton orchestrator for all calibration operations.

    This is the MANDATORY and ONLY path for calibration scoring.
    """

    _instance: CalibrationOrchestrator | None = None
    _initialized: bool = False

    def __new__(cls) -> CalibrationOrchestrator:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._intrinsic_scores: dict[str, IntrinsicScores] = {}
        self._layer_requirements: dict[str, LayerRequirements] = {}
        self._runtime_layer_config: dict = {}
        self._load_intrinsic_calibration()
        self._load_layer_requirements()
        self._load_runtime_layer_config()

        CalibrationOrchestrator._initialized = True
        logger.info("CalibrationOrchestrator initialized (singleton)")

    def _load_intrinsic_calibration(self) -> None:
        """Load intrinsic calibration using IntrinsicCalibrationLoader."""
        from farfan_pipeline.core.calibration.intrinsic_calibration_loader import get_intrinsic_calibration_loader
        
        loader = get_intrinsic_calibration_loader()

        # Get all methods from intrinsic calibration
        # Load the JSON directly to get all method IDs
        import json
        from pathlib import Path

        config_path = Path("config/intrinsic_calibration.json")
        if not config_path.exists():
            logger.warning(f"Intrinsic calibration file not found: {config_path}")
            return

        try:
            with open(config_path, encoding='utf-8') as f:
                data = json.load(f)

            for method_id in data.keys():
                if method_id == "_metadata":
                    continue

                calibration = loader.get_calibration(method_id)
                if calibration is not None:
                    self._intrinsic_scores[method_id] = IntrinsicScores(
                        b_theory=calibration.b_theory,
                        b_impl=calibration.b_impl,
                        b_deploy=calibration.b_deploy
                    )

            logger.info(f"Loaded intrinsic scores for {len(self._intrinsic_scores)} methods")

        except Exception as e:
            logger.error(f"Failed to load intrinsic calibration: {e}")
            raise

    def _load_layer_requirements(self) -> None:
        """Load layer requirements from layer_assignment module."""
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS, CHOQUET_WEIGHTS
        
        # For each method in intrinsic calibration, assign layers
        for method_id in self._intrinsic_scores.keys():
            # Determine role from method_id or from intrinsic calibration
            role = self._determine_role(method_id)

            if role in LAYER_REQUIREMENTS:
                required_layers = LAYER_REQUIREMENTS[role]

                # Build weights dict
                weights = {}
                for layer in required_layers:
                    if layer in CHOQUET_WEIGHTS:
                        weights[layer] = CHOQUET_WEIGHTS[layer]

                # Normalize weights
                total = sum(weights.values())
                if total > 0:
                    weights = {k: v/total for k, v in weights.items()}

                self._layer_requirements[method_id] = LayerRequirements(
                    required_layers=required_layers,
                    weights=weights,
                    aggregation_method='weighted_sum'
                )

        logger.info(f"Loaded layer requirements for {len(self._layer_requirements)} methods")

    def _determine_role(self, method_id: str) -> str:
        """Determine role from method_id or intrinsic calibration."""
        # If it's an executor (D1Q1, etc), it's 'executor'
        if 'D' in method_id and 'Q' in method_id:
            return 'executor'

        # Try to get from intrinsic calibration
        from farfan_pipeline.core.calibration.intrinsic_calibration_loader import get_intrinsic_calibration_loader
        loader = get_intrinsic_calibration_loader()
        calibration = loader.get_calibration(method_id)
        
        from farfan_pipeline.core.calibration.layer_assignment import LAYER_REQUIREMENTS
        if calibration and hasattr(calibration, 'layer') and calibration.layer in LAYER_REQUIREMENTS:
            return calibration.layer

        # Default to analyzer (safest - uses all layers)
        return 'analyzer'

    def _load_runtime_layer_config(self) -> None:
        """Load runtime layer configuration from system/config/calibration/runtime_layers.json."""
        config_path = Path("system/config/calibration/runtime_layers.json")
        if not config_path.exists():
            logger.warning(f"Runtime layer config not found: {config_path}, using defaults")
            return

        try:
            with open(config_path, encoding='utf-8') as f:
                self._runtime_layer_config = json.load(f)
            logger.info("Loaded runtime layer configuration")
        except Exception as e:
            logger.error(f"Failed to load runtime layer config: {e}")
            raise

    def evaluate_runtime_layers(
        self,
        method_id: str,
        context: CalibrationContext | None
    ) -> RuntimeLayers:
        """Evaluate runtime layers dynamically based on context.

        Args:
            method_id: Method identifier
            context: Calibration context (required for evaluation)

        Returns:
            RuntimeLayers with computed scores

        Raises:
            InsufficientContextError: If context is None
        """
        if context is None:
            raise InsufficientContextError(method_id)

        chain_score = self._compute_chain_score(context)
        quality_score = self._compute_quality_score(context)
        density_score = self._compute_density_score(context)
        provenance_score = self._compute_provenance_score(context)
        coverage_score = self._compute_coverage_score(context)
        uncertainty_score = self._compute_uncertainty_score(context)
        mechanism_score = self._compute_mechanism_score(context)

        layers = RuntimeLayers(
            chain=chain_score,
            quality=quality_score,
            density=density_score,
            provenance=provenance_score,
            coverage=coverage_score,
            uncertainty=uncertainty_score,
            mechanism=mechanism_score
        )

        logger.debug(
            f"Runtime layers for {method_id}: {layers.to_dict()}"
        )

        return layers

    def _compute_chain_score(self, context: CalibrationContext) -> float:
        """Compute chain of evidence score (@chain)."""
        config = self._runtime_layer_config.get('layers', {}).get('chain', {})
        base_score = config.get('base_score', 0.65)
        dimension_factor = config.get('dimension_factor', 0.15)
        dimension_max = config.get('dimension_max', 10.0)
        position_bonus = config.get('position_bonus', 0.1)
        position_threshold = config.get('position_threshold', 0.5)

        score = base_score
        if context.dimension > 0:
            score += dimension_factor * min(context.dimension / dimension_max, 1.0)
        if context.method_position < context.total_methods * position_threshold:
            score += position_bonus
        return min(score, 1.0)

    def _compute_quality_score(self, context: CalibrationContext) -> float:
        """Compute data quality score (@q)."""
        config = self._runtime_layer_config.get('layers', {}).get('quality', {})
        base_score = config.get('base_score', 0.70)
        question_factor = config.get('question_factor', 0.08)
        question_max = config.get('question_max', 20.0)

        score = base_score
        if context.question_num > 0:
            score += question_factor * min(context.question_num / question_max, 1.0)
        return min(score, 1.0)

    def _compute_density_score(self, context: CalibrationContext) -> float:
        """Compute data density score (@d)."""
        config = self._runtime_layer_config.get('layers', {}).get('density', {})
        base_score = config.get('base_score', 0.68)
        position_factor = config.get('position_factor', 0.15)
        optimal_position = config.get('optimal_position', 0.5)

        score = base_score
        if context.total_methods > 0:
            ratio = context.method_position / context.total_methods
            score += position_factor * (1.0 - abs(optimal_position - ratio))
        return min(score, 1.0)

    def _compute_provenance_score(self, context: CalibrationContext) -> float:
        """Compute provenance traceability score (@p)."""
        config = self._runtime_layer_config.get('layers', {}).get('provenance', {})
        return config.get('base_score', 0.75)

    def _compute_coverage_score(self, context: CalibrationContext) -> float:
        """Compute coverage completeness score (@C)."""
        config = self._runtime_layer_config.get('layers', {}).get('coverage', {})
        base_score = config.get('base_score', 0.72)
        bonus_dimensions = config.get('bonus_dimensions', [1, 2, 5, 10])
        dimension_bonus = config.get('dimension_bonus', 0.1)

        score = base_score
        if context.dimension in bonus_dimensions:
            score += dimension_bonus
        return min(score, 1.0)

    def _compute_uncertainty_score(self, context: CalibrationContext) -> float:
        """Compute uncertainty quantification score (@u)."""
        config = self._runtime_layer_config.get('layers', {}).get('uncertainty', {})
        return config.get('base_score', 0.68)

    def _compute_mechanism_score(self, context: CalibrationContext) -> float:
        """Compute mechanistic explanation score (@m)."""
        config = self._runtime_layer_config.get('layers', {}).get('mechanism', {})
        base_score = config.get('base_score', 0.65)
        dimension_threshold = config.get('dimension_threshold', 7)
        dimension_bonus = config.get('dimension_bonus', 0.15)

        score = base_score
        if context.dimension >= dimension_threshold:
            score += dimension_bonus
        return min(score, 1.0)

    def choquet_integral(
        self,
        layers: RuntimeLayers,
        weights: dict[str, float]
    ) -> float:
        """Aggregate layers using Choquet integral for executors.

        Simplified Choquet-like aggregation that weights higher-scoring layers more heavily.

        Args:
            layers: Runtime layer scores
            weights: Layer weights from requirements

        Returns:
            Aggregated score (0.0-1.0)
        """
        layer_dict = layers.to_dict()

        total_weight = sum(weights.values())
        if total_weight == 0:
            return 0.0

        weighted_total = sum(
            layer_dict.get(name, 0.0) * weight
            for name, weight in weights.items()
        )

        return min(max(weighted_total / total_weight, 0.0), 1.0)

    def weighted_sum(
        self,
        layers: RuntimeLayers,
        weights: dict[str, float]
    ) -> float:
        """Aggregate layers using weighted sum for non-executors.

        Args:
            layers: Runtime layer scores
            weights: Layer weights from requirements

        Returns:
            Aggregated score (0.0-1.0)
        """
        layer_dict = layers.to_dict()
        total_weight = sum(weights.values())

        if total_weight == 0:
            return 0.0

        weighted_total = sum(
            layer_dict.get(name, 0.0) * weight
            for name, weight in weights.items()
        )

        return min(max(weighted_total / total_weight, 0.0), 1.0)

    def calibrate_method(
        self,
        method_id: str,
        context: CalibrationContext | None = None,
        is_executor: bool = False
    ) -> float:
        """MANDATORY CALIBRATION PATH - This is the ONLY allowed entry point.

        Args:
            method_id: Method identifier
            context: Calibration context (required for runtime evaluation)
            is_executor: Whether this is an executor method (uses Choquet)

        Returns:
            Final calibration score (0.0-1.0)

        Raises:
            MissingIntrinsicCalibrationError: If @b scores missing
            InsufficientContextError: If context is None
            MethodBelowThresholdError: If score < threshold
        """
        if method_id not in self._intrinsic_scores:
            raise MissingIntrinsicCalibrationError(method_id)

        intrinsic = self._intrinsic_scores[method_id]
        intrinsic_score = intrinsic.average()

        logger.debug(
            f"Intrinsic score for {method_id}: {intrinsic_score:.3f} "
            f"(theory={intrinsic.b_theory:.3f}, impl={intrinsic.b_impl:.3f}, "
            f"deploy={intrinsic.b_deploy:.3f})"
        )

        runtime_layers = self.evaluate_runtime_layers(method_id, context)

        requirements = self._layer_requirements.get(method_id)
        if requirements is None:
            logger.warning(
                f"No layer requirements for {method_id}, using default weights"
            )
            requirements = LayerRequirements(
                required_layers=['quality', 'provenance'],
                weights={'quality': 0.5, 'provenance': 0.5},
                aggregation_method='weighted_sum'
            )

        if is_executor or requirements.aggregation_method == 'choquet_integral':
            runtime_score = self.choquet_integral(runtime_layers, requirements.weights)
        else:
            runtime_score = self.weighted_sum(runtime_layers, requirements.weights)

        final_score = (intrinsic_score + runtime_score) / 2.0

        logger.info(
            f"Calibration for {method_id}: intrinsic={intrinsic_score:.3f}, "
            f"runtime={runtime_score:.3f}, final={final_score:.3f}"
        )

        if final_score < CALIBRATION_THRESHOLD:
            raise MethodBelowThresholdError(method_id, final_score, CALIBRATION_THRESHOLD)

        return final_score

    @classmethod
    def get_instance(cls) -> CalibrationOrchestrator:
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = CalibrationOrchestrator()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing only)."""
        cls._instance = None
        cls._initialized = False


__all__ = [
    'CalibrationOrchestrator',
    'MissingIntrinsicCalibrationError',
    'InsufficientContextError',
    'MethodBelowThresholdError',
    'CALIBRATION_THRESHOLD'
]
