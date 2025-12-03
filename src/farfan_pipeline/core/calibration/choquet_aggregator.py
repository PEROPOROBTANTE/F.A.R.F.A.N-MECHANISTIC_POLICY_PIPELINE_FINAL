"""
Choquet 2-Additive Aggregation.

This implements the final score computation:
    Cal(I) = Σ a_ℓ·x_ℓ + Σ a_ℓk·min(x_ℓ, x_k)

Where:
- First sum: linear terms (weighted sum of layer scores)
- Second sum: interaction terms (synergies via weakest link)
"""
import logging
from typing import Dict

from farfan_pipeline.core.calibration.data_structures import (
    CalibrationResult,
    CalibrationSubject,
    InteractionTerm,
    LayerID,
    LayerScore,
)
from farfan_pipeline.core.calibration.config import ChoquetAggregationConfig

logger = logging.getLogger(__name__)


class ChoquetAggregator:
    """
    Choquet 2-Additive integral aggregator.
    
    This is the FINAL step in the calibration pipeline.
    """
    
    def __init__(self, config: ChoquetAggregationConfig):
        self.config = config
        
        # Pre-build interaction terms for efficiency
        self.interaction_terms = [
            InteractionTerm(
                layer_1=LayerID(l1),
                layer_2=LayerID(l2),
                weight=weight,
                rationale=self.config.interaction_rationales.get((l1, l2), "")
            )
            for (l1, l2), weight in self.config.interaction_weights.items()
        ]
        
        logger.info(
            "choquet_aggregator_initialized",
            extra={
                "num_layers": len(self.config.linear_weights),
                "num_interactions": len(self.interaction_terms),
                "config_hash": self.config.compute_hash()
            }
        )
    
    def aggregate(
        self,
        subject: CalibrationSubject,
        layer_scores: Dict[LayerID, LayerScore],
        metadata: dict = None
    ) -> CalibrationResult:
        """
        Compute final calibration score using Choquet aggregation.
        
        Args:
            subject: The calibration subject I = (M, v, Γ, G, ctx)
            layer_scores: Dict mapping LayerID to LayerScore
            metadata: Additional computation metadata
        
        Returns:
            CalibrationResult with final score and full breakdown
        
        Raises:
            ValueError: If layer scores are incomplete or invalid
        """
        if metadata is None:
            metadata = {}
        
        # Extract numeric scores for computation
        scores = {
            layer_id: layer_score.score
            for layer_id, layer_score in layer_scores.items()
        }
        
        # Verify all expected layers present
        expected_layers = set(LayerID(k) for k in self.config.linear_weights.keys())
        missing_layers = expected_layers - set(scores.keys())
        if missing_layers:
            logger.warning(
                "missing_layers",
                extra={
                    "missing": [l.value for l in missing_layers],
                    "subject": subject.method_id
                }
            )
            # For missing layers, use score = 0.0
            for layer in missing_layers:
                scores[layer] = 0.0
        
        # STEP 1: Compute linear contribution
        # Formula: Σ a_ℓ · x_ℓ
        linear_contribution = 0.0
        linear_breakdown = {}
        
        for layer_key, weight in self.config.linear_weights.items():
            layer_id = LayerID(layer_key)
            score = scores.get(layer_id, 0.0)
            contribution = weight * score
            linear_contribution += contribution
            linear_breakdown[layer_key] = contribution
            
            logger.debug(
                "linear_term",
                extra={
                    "layer": layer_key,
                    "weight": weight,
                    "score": score,
                    "contribution": contribution
                }
            )
        
        logger.info(
            "linear_contribution_computed",
            extra={
                "total": linear_contribution,
                "breakdown": linear_breakdown
            }
        )
        
        # STEP 2: Compute interaction contribution
        # Formula: Σ a_ℓk · min(x_ℓ, x_k)
        interaction_contribution = 0.0
        interaction_breakdown = {}
        
        for term in self.interaction_terms:
            contribution = term.compute(scores)
            interaction_contribution += contribution
            
            key = f"{term.layer_1.value}_{term.layer_2.value}"
            interaction_breakdown[key] = {
                "contribution": contribution,
                "weight": term.weight,
                "score_1": scores.get(term.layer_1, 0.0),
                "score_2": scores.get(term.layer_2, 0.0),
                "min_score": min(
                    scores.get(term.layer_1, 0.0),
                    scores.get(term.layer_2, 0.0)
                ),
                "rationale": term.rationale,
            }
            
            logger.debug(
                "interaction_term",
                extra={
                    "layers": f"{term.layer_1.value}+{term.layer_2.value}",
                    "weight": term.weight,
                    "min_score": interaction_breakdown[key]["min_score"],
                    "contribution": contribution,
                    "rationale": term.rationale
                }
            )
        
        logger.info(
            "interaction_contribution_computed",
            extra={
                "total": interaction_contribution,
                "num_terms": len(interaction_breakdown)
            }
        )
        
        # STEP 3: Compute final score
        # Cal(I) = linear + interaction
        final_score = linear_contribution + interaction_contribution
        
        # Verify final_score is in [0.0, 1.0] (should already be in range due to normalization)
        if not (0.0 <= final_score <= 1.0):
            logger.error(
                "final_score_out_of_bounds",
                extra={
                    "final_score": final_score,
                    "linear_contribution": linear_contribution,
                    "interaction_contribution": interaction_contribution,
                    "method": subject.method_id,
                }
            )
            raise ValueError(
                f"Final score {final_score:.6f} out of bounds [0.0, 1.0]. "
                f"This indicates a bug in weight normalization or layer score validation."
            )
        
        logger.info(
            "final_calibration_computed",
            extra={
                "method": subject.method_id,
                "context": f"{subject.context.question_id}_{subject.context.dimension}_{subject.context.policy_area}",
                "final_score": final_score,
                "linear": linear_contribution,
                "interaction": interaction_contribution
            }
        )
        
        # Build metadata
        full_metadata = {
            **metadata,
            "config_hash": self.config.compute_hash(),
            "linear_breakdown": linear_breakdown,
            "interaction_breakdown": interaction_breakdown,
            "normalization_check": {
                "expected_sum": 1.0,
                "actual_sum": sum(self.config.linear_weights.values()) + 
                             sum(self.config.interaction_weights.values()),
            }
        }
        
        # Create result
        result = CalibrationResult(
            subject=subject,
            layer_scores=layer_scores,
            linear_contribution=linear_contribution,
            interaction_contribution=interaction_contribution,
            final_score=final_score,
            computation_metadata=full_metadata,
        )
        
        return result
