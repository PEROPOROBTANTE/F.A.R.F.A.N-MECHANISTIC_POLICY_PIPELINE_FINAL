"""
Calibration orchestrator - integrates all layers.

This is the TOP-LEVEL entry point for calibration.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base_layer import BaseLayerEvaluator
from .chain_layer import ChainLayerEvaluator
from .choquet_aggregator import ChoquetAggregator
from .compatibility import CompatibilityRegistry, ContextualLayerEvaluator
from .config import DEFAULT_CALIBRATION_CONFIG, CalibrationSystemConfig
from .congruence_layer import CongruenceLayerEvaluator
from .data_structures import (
    CalibrationResult,
    CalibrationSubject,
    ContextTuple,
    LayerID,
    LayerScore,
)
from .intrinsic_loader import IntrinsicScoreLoader
from .layer_requirements import LayerRequirementsResolver
from .meta_layer import MetaLayerEvaluator
from .pdt_structure import PDTStructure
from .unit_layer import UnitLayerEvaluator

logger = logging.getLogger(__name__)

# Repository root (5 levels up from this file)
_REPO_ROOT = Path(__file__).resolve().parents[4]


def _load_default_paths():
    """Load default paths from config/calibration_paths.json."""
    paths_file = _REPO_ROOT / "config" / "calibration_paths.json"
    if not paths_file.exists():
        return {}
    try:
        with open(paths_file, 'r') as f:
            return json.load(f).get('defaults', {})
    except Exception as e:
        logger.error(f"Failed to load calibration_paths.json: {e}")
        return {}


class CalibrationOrchestrator:
    """
    Top-level orchestrator for method calibration.

    This class coordinates all 8 calibration layers (@b, @u, @q, @d, @p, @C, @chain, @m)
    and performs Choquet aggregation to produce final calibration scores.

    The orchestrator:
    1. Loads configuration and initializes all layer evaluators
    2. Uses LayerRequirementsResolver to determine which layers to evaluate
    3. Executes only required layers based on method role
    4. Aggregates scores using Choquet integral for non-linear fusion

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
        config: Optional[CalibrationSystemConfig] = None,
        intrinsic_calibration_path: Optional[Path | str] = None,
        compatibility_path: Optional[Path | str] = None,
        method_registry_path: Optional[Path | str] = None,
        method_signatures_path: Optional[Path | str] = None,
        parameter_loader: Optional[object] = None  # For base layer thresholds
    ) -> None:
        """
        Initialize the calibration orchestrator.

        Args:
            config: Calibration system configuration
            intrinsic_calibration_path: Path to intrinsic_calibration.json
            compatibility_path: Path to method_compatibility.json
            method_registry_path: Path to method_registry.json for congruence layer
            method_signatures_path: Path to method_signatures.json for chain layer
            parameter_loader: Optional loader for configurable thresholds
        """
        self.config = config or DEFAULT_CALIBRATION_CONFIG

        # Load default paths from config
        default_paths = _load_default_paths()

        # Initialize IntrinsicScoreLoader (singleton pattern, lazy-loaded)
        if intrinsic_calibration_path:
            intrinsic_path = Path(intrinsic_calibration_path)
        else:
            # Use path from calibration_paths.json
            path_str = default_paths.get('intrinsic_calibration_path', 'config/intrinsic_calibration.json')
            intrinsic_path = _REPO_ROOT / path_str

        if not intrinsic_path.exists():
            raise FileNotFoundError(
                f"Intrinsic calibration file not found: {intrinsic_path}\n"
                f"Configure path in config/calibration_paths.json"
            )

        self.intrinsic_loader = IntrinsicScoreLoader(str(intrinsic_path))

        # Initialize LayerRequirementsResolver
        self.layer_resolver = LayerRequirementsResolver(self.intrinsic_loader)

        # Initialize BASE layer evaluator with optional parameter loader (same path as intrinsic loader)
        self.base_evaluator = BaseLayerEvaluator(
            str(intrinsic_path),
            parameter_loader=parameter_loader
        )

        # Initialize UNIT layer evaluator
        self.unit_evaluator = UnitLayerEvaluator(self.config.unit_layer)

        # Load compatibility registry
        if compatibility_path:
            compat_path = Path(compatibility_path)
        else:
            path_str = default_paths.get('compatibility_path', 'config/canonical_method_catalog.json')
            compat_path = _REPO_ROOT / path_str

        if compat_path.exists():
            try:
                self.compat_registry = CompatibilityRegistry(str(compat_path))
                self.contextual_evaluator = ContextualLayerEvaluator(self.compat_registry)
                if self.config.enable_anti_universality_check:
                    self.compat_registry.validate_anti_universality(
                        threshold=self.config.max_avg_compatibility
                    )
            except (ValueError, KeyError) as e:
                logger.warning(f"Compatibility file format issue: {e}. Skipping.")
                self.compat_registry = None
                self.contextual_evaluator = None
        else:
            logger.warning(f"Compatibility file not found: {compat_path}")
            self.compat_registry = None
            self.contextual_evaluator = None

        # Load method registry for congruence layer
        if method_registry_path:
            registry_path = Path(method_registry_path)
        else:
            path_str = default_paths.get('method_registry_path', 'config/canonical_method_catalog.json')
            registry_path = _REPO_ROOT / path_str

        if registry_path.exists():
            with open(registry_path, encoding='utf-8') as f:
                registry_data = json.load(f)
            # Handle both formats: direct "methods" key or "layers" structure
            if "methods" in registry_data:
                self.congruence_evaluator = CongruenceLayerEvaluator(
                    method_registry=registry_data["methods"]
                )
            elif "layers" in registry_data:
                # Flatten layers
                all_methods = {}
                for layer in registry_data.get("layers", {}).values():
                    if isinstance(layer, list):
                        for method in layer:
                            mid = method.get("canonical_name") or method.get("method_name")
                            if mid:
                                all_methods[mid] = method
                self.congruence_evaluator = CongruenceLayerEvaluator(method_registry=all_methods)
            else:
                logger.warning("Unrecognized registry format")
                self.congruence_evaluator = CongruenceLayerEvaluator(method_registry={})
        else:
            logger.warning(f"Method registry not found: {registry_path}")
            self.congruence_evaluator = CongruenceLayerEvaluator(method_registry={})

        # Load method signatures for chain layer
        if method_signatures_path:
            signatures_path = Path(method_signatures_path)
        else:
            path_str = default_paths.get('method_signatures_path', 'config/canonical_method_catalog.json')
            signatures_path = _REPO_ROOT / path_str

        if signatures_path.exists():
            with open(signatures_path, encoding='utf-8') as f:
                signatures_data = json.load(f)
            # Handle both formats
            if "methods" in signatures_data:
                self.chain_evaluator = ChainLayerEvaluator(
                    method_signatures=signatures_data["methods"]
                )
            elif "layers" in signatures_data:
                # Flatten layers
                all_methods = {}
                for layer in signatures_data.get("layers", {}).values():
                    if isinstance(layer, list):
                        for method in layer:
                            mid = method.get("canonical_name") or method.get("method_name")
                            if mid:
                                all_methods[mid] = method
                self.chain_evaluator = ChainLayerEvaluator(method_signatures=all_methods)
            else:
                logger.warning("Unrecognized signatures format")
                self.chain_evaluator = ChainLayerEvaluator(method_signatures={})
        else:
            logger.warning(f"Method signatures not found: {signatures_path}")
            self.chain_evaluator = ChainLayerEvaluator(method_signatures={})

        self.meta_evaluator = MetaLayerEvaluator(self.config.meta_layer)

        # Choquet aggregator
        self.aggregator = ChoquetAggregator(self.config.choquet)

        # Log intrinsic calibration statistics
        stats = self.intrinsic_loader.get_statistics()
        logger.info(
            "calibration_orchestrator_initialized",
            extra={
                "config_hash": self.config.compute_system_hash(),
                "anti_universality_enabled": self.config.enable_anti_universality_check,
                "base_evaluator_loaded": self.base_evaluator is not None,
                "total_calibrated_methods": stats.get("total", stats.get("total_methods", 0)),
                "methods_by_layer": stats.get("by_layer", {})
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

        This executes required layers based on method role and performs Choquet aggregation.

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

        # Log which layers will be evaluated
        required_layers = self.layer_resolver.get_required_layers(method_id)
        layer_summary = self.layer_resolver.get_layer_summary(method_id)
        
        logger.info(
            "calibration_start",
            extra={
                "method": method_id,
                "question": context.question_id,
                "dimension": context.dimension,
                "policy": context.policy_area,
                "layer_config": layer_summary,
                "required_layers": [l.value for l in required_layers]
            }
        )

        # Collect layer scores
        layer_scores: dict[LayerID, LayerScore] = {}

        # Layer 1: Base (@b) - Intrinsic Quality
        # ALWAYS REQUIRED - loads from intrinsic_calibration.json
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
                # No compatibility data - use penalties for required layers only
                if needs_q:
                    layer_scores[LayerID.QUESTION] = LayerScore(
                        layer=LayerID.QUESTION,
                        score=0.1,
                        rationale="No compatibility data - penalty applied",
                        metadata={"penalty": True}
                    )
                if needs_d:
                    layer_scores[LayerID.DIMENSION] = LayerScore(
                        layer=LayerID.DIMENSION,
                        score=0.1,
                        rationale="No compatibility data - penalty applied",
                        metadata={"penalty": True}
                    )
                if needs_p:
                    layer_scores[LayerID.POLICY] = LayerScore(
                        layer=LayerID.POLICY,
                        score=0.1,
                        rationale="No compatibility data - penalty applied",
                        metadata={"penalty": True}
                    )

        # Layer 6: Congruence (@C)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.CONGRUENCE):
            congruence_score = self.congruence_evaluator.evaluate(
                method_ids=[method_id],
                subgraph_id=subgraph_id,
                fusion_rule="weighted_average"
            )
            layer_scores[LayerID.CONGRUENCE] = LayerScore(
                layer=LayerID.CONGRUENCE,
                score=congruence_score,
                rationale=f"Congruence evaluation for subgraph {subgraph_id}"
            )

        # Layer 7: Chain (@chain)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.CHAIN):
            chain_score = self.chain_evaluator.evaluate(
                method_id=method_id,
                provided_inputs=[]  # TODO: Get actual provided inputs from execution context
            )
            layer_scores[LayerID.CHAIN] = LayerScore(
                layer=LayerID.CHAIN,
                score=chain_score,
                rationale="Chain integrity verification"
            )

        # Layer 8: Meta (@m)
        if not self.layer_resolver.should_skip_layer(method_id, LayerID.META):
            # TODO: These parameters should come from actual method execution
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
            "layers_evaluated": len(layer_scores),
            "layers_skipped": len(required_layers) - len(layer_scores),
            "method_role": self.intrinsic_loader.get_layer(method_id) or "unknown"
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
                "duration_ms": metadata["duration_ms"],
                "layers_evaluated": metadata["layers_evaluated"],
                "choquet_integral": result.choquet_value if hasattr(result, 'choquet_value') else None
            }
        )

        return result

    def get_layer_requirements(self, method_id: str) -> dict[str, bool]:
        """
        Get a dictionary showing which layers are required for a method.

        Args:
            method_id: Method identifier

        Returns:
            Dictionary mapping layer IDs to boolean (required/not required)
        """
        required = self.layer_resolver.get_required_layers(method_id)
        return {
            "b": LayerID.BASE in required,
            "u": LayerID.UNIT in required,
            "q": LayerID.QUESTION in required,
            "d": LayerID.DIMENSION in required,
            "p": LayerID.POLICY in required,
            "C": LayerID.CONGRUENCE in required,
            "chain": LayerID.CHAIN in required,
            "m": LayerID.META in required
        }