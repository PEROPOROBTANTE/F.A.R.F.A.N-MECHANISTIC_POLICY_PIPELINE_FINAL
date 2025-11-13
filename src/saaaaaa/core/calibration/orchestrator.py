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
from .unit_layer import UnitLayerEvaluator
from .pdt_structure import PDTStructure
from .compatibility import CompatibilityRegistry, ContextualLayerEvaluator
from .congruence_layer import CongruenceLayerEvaluator
from .chain_layer import ChainLayerEvaluator
from .meta_layer import MetaLayerEvaluator
from .choquet_aggregator import ChoquetAggregator

logger = logging.getLogger(__name__)


class CalibrationOrchestrator:
    """
    Top-level orchestrator for method calibration.
    
    Usage:
        orchestrator = CalibrationOrchestrator(
            config=DEFAULT_CALIBRATION_CONFIG,
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
        compatibility_path: Path | str = None,
        method_registry_path: Path | str = None,
        method_signatures_path: Path | str = None
    ):
        self.config = config or DEFAULT_CALIBRATION_CONFIG

        # Initialize layer evaluators
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

        logger.info(
            "calibration_orchestrator_initialized",
            extra={
                "config_hash": self.config.compute_system_hash(),
                "anti_universality_enabled": self.config.enable_anti_universality_check
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
        
        # Layer 1: Base (@b) - ASSUMED COMPLETE
        # This comes from intrinsic calibration (already done)
        # TODO: This should come from actual base layer evaluation, not hardcoded
        base_score = 0.9  # Placeholder until base layer integration complete
        layer_scores[LayerID.BASE] = LayerScore(
            layer=LayerID.BASE,
            score=base_score,
            rationale=f"Base layer (intrinsic quality) - STUB using {base_score}",
            metadata={"stub": True, "warning": "Hardcoded value pending integration"}
        )
        
        # Layer 2: Unit (@u)
        unit_score = self.unit_evaluator.evaluate(pdt_structure)
        layer_scores[LayerID.UNIT] = unit_score
        
        # Layers 3-5: Contextual (@q, @d, @p)
        if self.contextual_evaluator:
            contextual_scores = self.contextual_evaluator.evaluate_all_contextual(
                method_id=method_id,
                question_id=context.question_id,
                dimension=context.dimension,
                policy_area=context.policy_area
            )
            
            layer_scores[LayerID.QUESTION] = LayerScore(
                layer=LayerID.QUESTION,
                score=contextual_scores['q'],
                rationale=f"Question compatibility for {context.question_id}"
            )
            
            layer_scores[LayerID.DIMENSION] = LayerScore(
                layer=LayerID.DIMENSION,
                score=contextual_scores['d'],
                rationale=f"Dimension compatibility for {context.dimension}"
            )
            
            layer_scores[LayerID.POLICY] = LayerScore(
                layer=LayerID.POLICY,
                score=contextual_scores['p'],
                rationale=f"Policy compatibility for {context.policy_area}"
            )
        else:
            # No compatibility data - use penalties
            for layer, name in [(LayerID.QUESTION, "question"), 
                               (LayerID.DIMENSION, "dimension"), 
                               (LayerID.POLICY, "policy")]:
                layer_scores[layer] = LayerScore(
                    layer=layer,
                    score=0.1,
                    rationale=f"No compatibility data - penalty applied"
                )
        
        # Layer 6: Congruence (@C)
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
        
        # Layer 7: Chain (@chain)
        chain_score = self.chain_evaluator.evaluate(
            method_id=method_id,
            provided_inputs=[]  # TODO: Get from actual graph execution
        )
        layer_scores[LayerID.CHAIN] = LayerScore(
            layer=LayerID.CHAIN,
            score=chain_score,
            rationale="Chain integrity"
        )
        
        # Layer 8: Meta (@m)
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
