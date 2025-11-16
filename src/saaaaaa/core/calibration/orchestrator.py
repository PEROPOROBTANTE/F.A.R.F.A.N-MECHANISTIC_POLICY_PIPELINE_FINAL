"""
Calibration orchestrator - integrates all layers.

This is the TOP-LEVEL entry point for calibration.
"""
import logging
import json
from pathlib import Path
from datetime import datetime

from .data_structures import (
    LayerID, LayerScore, ContextTuple, CalibrationSubject, CalibrationResult
)
from .config import CalibrationSystemConfig, DEFAULT_CALIBRATION_CONFIG
from .base_layer import BaseLayerEvaluator
from .unit_layer import UnitLayerEvaluator
from .pdt_structure import PDTStructure
from .compatibility import CompatibilityRegistry, ContextualLayerEvaluator
from .congruence_layer import CongruenceLayerEvaluator
from .chain_layer import ChainLayerEvaluator
from .meta_layer import MetaLayerEvaluator
from .choquet_aggregator import ChoquetAggregator
from .intrinsic_loader import IntrinsicScoreLoader
from .layer_requirements import LayerRequirementsResolver

logger = logging.getLogger(__name__)


class CalibrationOrchestrator:
    """
    Top-level orchestrator for method calibration.

    Usage:
        orchestrator = CalibrationOrchestrator(
            config=DEFAULT_CALIBRATION_CONFIG,
            intrinsic_calibration_path="config/intrinsic_calibration.json",
            compatibility_path="data/method_compatibility.json"
        )

        result = orchestrator.calibrate(
            method_id="pattern_extractor_v2",
            method_version="v2.1.0",
            context=ContextTuple(...),
            pdt_structure=PDTStructure(...)
        )
    """

    def __init__(
        self,
        config: CalibrationSystemConfig = None,
        intrinsic_calibration_path: Path | str = None,
        compatibility_path: Path | str = None,
        method_registry_path: Path | str = None,
        method_signatures_path: Path | str = None,
        intrinsic_calibration_path: Path | str = None
    ):
        self.config = config or DEFAULT_CALIBRATION_CONFIG

        # Initialize BASE layer evaluator
        if intrinsic_calibration_path:
            self.base_evaluator = BaseLayerEvaluator(intrinsic_calibration_path)
        else:
            # Try default path
            default_intrinsic = Path("config/intrinsic_calibration.json")
            if default_intrinsic.exists():
                self.base_evaluator = BaseLayerEvaluator(default_intrinsic)
            else:
                logger.warning(
                    "No intrinsic_calibration.json found, BASE layer will use penalty scores"
                )
                # Create a minimal evaluator that always returns penalty
                self.base_evaluator = None

        # Initialize UNIT layer evaluator
        self.unit_evaluator = UnitLayerEvaluator(self.config.unit_layer)

        # Load compatibility registry
        if compatibility_path:
            self.compat_registry = CompatibilityRegistry(compatibility_path)
            self.contextual_evaluator = ContextualLayerEvaluator(self.compat_registry)

            # Validate anti-universality if enabled
            if self.config.enable_anti_universality_check:
                self.compat_registry.validate_anti_universality(
                    threshold=self.config.max_avg_compatibility
                )
        else:
            self.compat_registry = None
            self.contextual_evaluator = None

        # FIXED: Load method registry and signatures for congruence/chain layers
        # Load method registry for congruence layer
        if method_registry_path:
            registry_path = Path(method_registry_path)
            with open(registry_path) as f:
                registry_data = json.load(f)
            self.congruence_evaluator = CongruenceLayerEvaluator(
                method_registry=registry_data["methods"]
            )
        else:
            # Fallback: try default path or use empty registry
            default_registry = Path("data/method_registry.json")
            if default_registry.exists():
                with open(default_registry) as f:
                    registry_data = json.load(f)
                self.congruence_evaluator = CongruenceLayerEvaluator(
                    method_registry=registry_data["methods"]
                )
            else:
                logger.warning("No method_registry.json found, using empty registry")
                self.congruence_evaluator = CongruenceLayerEvaluator(method_registry={})

        # Load method signatures for chain layer
        if method_signatures_path:
            signatures_path = Path(method_signatures_path)
            with open(signatures_path) as f:
                signatures_data = json.load(f)
            self.chain_evaluator = ChainLayerEvaluator(
                method_signatures=signatures_data["methods"]
            )
        else:
            # Fallback: try default path or use empty signatures
            default_signatures = Path("data/method_signatures.json")
            if default_signatures.exists():
                with open(default_signatures) as f:
                    signatures_data = json.load(f)
                self.chain_evaluator = ChainLayerEvaluator(
                    method_signatures=signatures_data["methods"]
                )
            else:
                logger.warning("No method_signatures.json found, using empty signatures")
                self.chain_evaluator = ChainLayerEvaluator(method_signatures={})

        self.meta_evaluator = MetaLayerEvaluator(self.config.meta_layer)

        # Choquet aggregator
        self.aggregator = ChoquetAggregator(self.config.choquet)

        # Log intrinsic calibration statistics
        intrinsic_stats = self.intrinsic_loader.get_statistics()
        logger.info(
            "calibration_orchestrator_initialized",
            extra={
                "config_hash": self.config.compute_system_hash(),
                "anti_universality_enabled": self.config.enable_anti_universality_check,
                "base_evaluator_loaded": self.base_evaluator is not None,
            }
        )
    
    def calibrate(
        self,
        method_id: str,
        method_version: str,
        context: ContextTuple,
        pdt_structure: PDTStructure,
        graph_config: str = "default",
        subgraph_id: str = "default"
    ) -> CalibrationResult:
        """
        Perform complete calibration for a method in a context.
        
        This executes all 7 layers + Choquet aggregation.
        
        Args:
            method_id: Method identifier (e.g., "pattern_extractor_v2")
            method_version: Method version (e.g., "v2.1.0")
            context: Context tuple (Q, D, P, U)
            pdt_structure: Parsed PDT structure
            graph_config: Hash of computational graph
            subgraph_id: Identifier for interplay subgraph
        
        Returns:
            CalibrationResult with final score and full breakdown
        """
        start_time = datetime.utcnow()
        
        # Create calibration subject
        subject = CalibrationSubject(
            method_id=method_id,
            method_version=method_version,
            graph_config=graph_config,
            subgraph_id=subgraph_id,
            context=context
        )
        
        logger.info(
            "calibration_start",
            extra={
                "method": method_id,
                "question": context.question_id,
                "dimension": context.dimension,
                "policy": context.policy_area
            }
        )
        
        # Collect layer scores
        layer_scores = {}

        # Layer 1: Base (@b) - Intrinsic Quality
        # Loads from intrinsic_calibration.json (populated by rigorous_calibration_triage.py)
        if self.base_evaluator:
            layer_scores[LayerID.BASE] = self.base_evaluator.evaluate(method_id)
        else:
            # Fallback if no calibration data available
            logger.warning(
                "base_evaluator_not_available",
                extra={"method": method_id, "using_penalty": True}
            )
            layer_scores[LayerID.BASE] = LayerScore(
                layer=LayerID.BASE,
                score=BaseLayerEvaluator.UNCALIBRATED_PENALTY,
                rationale="BASE layer: intrinsic calibration not available (penalty applied)",
                metadata={"penalty": True, "reason": "no_calibration_file"}
            )
        
        # Layer 2: Unit (@u)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.UNIT):
            unit_score = self.unit_evaluator.evaluate(pdt_structure)
            layer_scores[LayerID.UNIT] = unit_score
        else:
            logger.debug(
                "layer_skipped",
                extra={"method": method_id, "layer": "u", "reason": "not_required_for_role"}
            )
        
        # Layers 3-5: Contextual (@q, @d, @p)
        # Check which contextual layers are required
        needs_q = not self.layer_resolver.should_skip_layer(method_id, LayerID.QUESTION)
        needs_d = not self.layer_resolver.should_skip_layer(method_id, LayerID.DIMENSION)
        needs_p = not self.layer_resolver.should_skip_layer(method_id, LayerID.POLICY)

        if needs_q or needs_d or needs_p:
            if self.contextual_evaluator:
                # Only evaluate the required contextual layers
                if needs_q:
                    q_score = self.contextual_evaluator.evaluate_question(
                        method_id=method_id,
                        question_id=context.question_id
                    )
                    layer_scores[LayerID.QUESTION] = LayerScore(
                        layer=LayerID.QUESTION,
                        score=q_score,
                        rationale=f"Question compatibility for {context.question_id}"
                    )
                else:
                    logger.debug("layer_skipped", extra={"method": method_id, "layer": "q"})

                if needs_d:
                    d_score = self.contextual_evaluator.evaluate_dimension(
                        method_id=method_id,
                        dimension=context.dimension
                    )
                    layer_scores[LayerID.DIMENSION] = LayerScore(
                        layer=LayerID.DIMENSION,
                        score=d_score,
                        rationale=f"Dimension compatibility for {context.dimension}"
                    )
                else:
                    logger.debug("layer_skipped", extra={"method": method_id, "layer": "d"})

                if needs_p:
                    p_score = self.contextual_evaluator.evaluate_policy(
                        method_id=method_id,
                        policy_area=context.policy_area
                    )
                    layer_scores[LayerID.POLICY] = LayerScore(
                        layer=LayerID.POLICY,
                        score=p_score,
                        rationale=f"Policy compatibility for {context.policy_area}"
                    )
                else:
                    logger.debug("layer_skipped", extra={"method": method_id, "layer": "p"})
            else:
                # No compatibility data - use penalties for required layers only
                for layer, name in [(LayerID.QUESTION, "question"),
                                   (LayerID.DIMENSION, "dimension"),
                                   (LayerID.POLICY, "policy")]:
                    if not self.layer_resolver.should_skip_layer(method_id, layer):
                        layer_scores[layer] = LayerScore(
                            layer=layer,
                            score=0.1,
                            rationale=f"No compatibility data - penalty applied"
                        )
        else:
            logger.debug(
                "contextual_layers_skipped",
                extra={"method": method_id, "layers": ["q", "d", "p"]}
            )
        
        # Layer 6: Congruence (@C)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.CONGRUENCE):
            congruence_score = self.congruence_evaluator.evaluate(
                method_ids=[method_id],
                subgraph_id=subgraph_id,
                fusion_rule="weighted_average",
                available_inputs=[]  # TODO: Get from actual graph execution
            )
            layer_scores[LayerID.CONGRUENCE] = LayerScore(
                layer=LayerID.CONGRUENCE,
                score=congruence_score,
                rationale="Congruence evaluation"
            )
        else:
            logger.debug(
                "layer_skipped",
                extra={"method": method_id, "layer": "C", "reason": "not_required_for_role"}
            )
        
        # Layer 7: Chain (@chain)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.CHAIN):
            chain_score = self.chain_evaluator.evaluate(
                method_id=method_id,
                provided_inputs=[]  # TODO: Get from actual graph execution
            )
            layer_scores[LayerID.CHAIN] = LayerScore(
                layer=LayerID.CHAIN,
                score=chain_score,
                rationale="Chain integrity"
            )
        else:
            logger.debug(
                "layer_skipped",
                extra={"method": method_id, "layer": "chain", "reason": "not_required_for_role"}
            )
        
        # Layer 8: Meta (@m)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.META):
            # FIXED: Pass all required arguments to meta layer
            meta_score = self.meta_evaluator.evaluate(
                method_id=method_id,
                method_version=method_version,
                config_hash=self.config.compute_system_hash(),
                formula_exported=False,  # TODO: Get from actual method execution
                full_trace=False,  # TODO: Get from actual method execution
                logs_conform=False,  # TODO: Validate against log schema
                signature_valid=False,  # TODO: Verify cryptographic signature
                execution_time_s=None  # TODO: Measure actual execution time
            )
            layer_scores[LayerID.META] = LayerScore(
                layer=LayerID.META,
                score=meta_score,
                rationale="Meta/governance evaluation"
            )
        else:
            logger.debug(
                "layer_skipped",
                extra={"method": method_id, "layer": "m", "reason": "not_required_for_role"}
            )
        
        # Choquet aggregation
        end_time = datetime.utcnow()
        metadata = {
            "calibration_start": start_time.isoformat(),
            "calibration_end": end_time.isoformat(),
            "duration_ms": (end_time - start_time).total_seconds() * 1000,
            "config_hash": self.config.compute_system_hash(),
        }
        
        result = self.aggregator.aggregate(
            subject=subject,
            layer_scores=layer_scores,
            metadata=metadata
        )
        
        logger.info(
            "calibration_complete",
            extra={
                "method": method_id,
                "final_score": result.final_score,
                "duration_ms": metadata["duration_ms"]
            }
        )
        
        return result
