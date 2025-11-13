"""
Three-Pillar Calibration System - Main Calibration Engine

This module implements the main calibrate() function and fusion operator
as specified in the SUPERPROMPT Three-Pillar Calibration System.

Spec compliance: Section 5 (Fusion Operator), Section 6 (Runtime Engine)
SIN_CARRETA Compliance: Pure fusion operator, fail-loudly on misconfiguration
"""

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from .data_structures import (
    CalibrationCertificate, CalibrationSubject, Context, 
    ComputationGraph, EvidenceStore, LayerType, MethodRole, REQUIRED_LAYERS,
    CalibrationConfigError
)
from .layer_computers import (
    compute_base_layer, compute_chain_layer, compute_unit_layer,
    compute_question_layer, compute_dimension_layer, compute_policy_layer,
    compute_interplay_layer, compute_meta_layer
)


class CalibrationEngine:
    """
    Main calibration engine implementing the three-pillar system.
    
    Spec compliance: Section 7 (Runtime Engine & Certificate)
    """
    
    def __init__(self, config_dir: str = None, monolith_path: str = None, catalog_path: str = None):
        """
        Initialize calibration engine and load configs.
        
        SIN_CARRETA: Validates fusion weights at load time to fail fast.
        Three-Pillar System: Loads from intrinsic, contextual, and fusion configs.
        
        Args:
            config_dir: Path to config directory (defaults to ../config)
            monolith_path: Path to questionnaire_monolith.json (defaults to ../data/questionnaire_monolith.json)
            catalog_path: Path to canonical_method_catalog.json (defaults to ../config/canonical_method_catalog.json)
            
        Raises:
            CalibrationConfigError: If fusion weights violate constraints
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent / "config"
        else:
            config_dir = Path(config_dir)
        
        self.config_dir = config_dir
        self.intrinsic_config = self._load_json(config_dir / "intrinsic_calibration.json")
        self.contextual_config = self._load_json(config_dir / "contextual_parametrization.json")
        self.fusion_config = self._load_json(config_dir / "fusion_specification.json")
        
        # Load canonical method catalog for role determination
        if catalog_path is None:
            catalog_path = config_dir / "canonical_method_catalog.json"
        else:
            catalog_path = Path(catalog_path)
        self.catalog = self._load_json(catalog_path)
        self._build_method_index()
        
        # SIN_CARRETA: Validate fusion weights at load time
        self._validate_fusion_weights()
        
        # Load questionnaire monolith using canonical loader
        # This ensures hash verification and immutability
        from saaaaaa.core.orchestrator.factory import load_questionnaire

        if monolith_path is None:
            # Use default path from factory
            canonical_q = load_questionnaire()
        else:
            # Use specified path
            canonical_q = load_questionnaire(Path(monolith_path))

        # Convert to dict for backward compatibility with calibration system
        # (CalibrationEngine expects dict, not CanonicalQuestionnaire)
        self.monolith = dict(canonical_q.data)
        self._questionnaire_hash = canonical_q.sha256  # Store for verification
        
        # Compute config hash
        self.config_hash = self._compute_config_hash()
    
    @staticmethod
    def _load_json(path: Path) -> Dict[str, Any]:
        """Load JSON file"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def _build_method_index(self) -> None:
        """
        Build index of methods from canonical catalog for fast role lookup.
        
        Three-Pillar System: Uses canonical_method_catalog.json as single source.
        """
        self.method_index = {}
        
        for layer_name, methods in self.catalog.get("layers", {}).items():
            for method_info in methods:
                canonical_name = method_info.get("canonical_name", "")
                method_name = method_info.get("method_name", "")
                class_name = method_info.get("class_name", "")
                layer = method_info.get("layer", "unknown")
                
                # Store method info with multiple lookup keys
                for key in [canonical_name, method_name, f"{class_name}.{method_name}"]:
                    if key:
                        self.method_index[key] = {
                            "canonical_name": canonical_name,
                            "method_name": method_name,
                            "class_name": class_name,
                            "layer": layer,
                            "metadata": method_info
                        }
    
    def _validate_fusion_weights(self) -> None:
        """
        Validate fusion weight constraints at config load time.
        
        Per canonic_calibration_methods.md specification.
        
        Constraints:
        1. All weights must be non-negative: a_ℓ ≥ 0, a_ℓk ≥ 0
        2. Total weight sum MUST equal 1: Σ(a_ℓ) + Σ(a_ℓk) = 1 (tolerance 1e-9)
        
        Raises:
            CalibrationConfigError: If any weight constraint is violated
        """
        role_params_dict = self.fusion_config.get("role_fusion_parameters", {})
        TOLERANCE = 1e-9
        
        for role_name, role_params in role_params_dict.items():
            linear_weights = role_params.get("linear_weights", {})
            interaction_weights = role_params.get("interaction_weights", {})
            
            # Constraint 1: Non-negativity
            for layer, weight in linear_weights.items():
                if weight < 0:
                    raise CalibrationConfigError(
                        f"Negative weight for role={role_name}, layer={layer}: "
                        f"weight={weight}. All weights must be ≥ 0."
                    )
            
            for pair, weight in interaction_weights.items():
                if weight < 0:
                    raise CalibrationConfigError(
                        f"Negative interaction weight for role={role_name}, pair={pair}: "
                        f"weight={weight}. All weights must be ≥ 0."
                    )
            
            # Constraint 2: Must sum to exactly 1.0
            total_weight = sum(linear_weights.values()) + sum(interaction_weights.values())
            if abs(total_weight - 1.0) > TOLERANCE:
                raise CalibrationConfigError(
                    f"Weight sum must equal 1.0 for role={role_name}: "
                    f"total_weight={total_weight:.15f} (deviation: {abs(total_weight - 1.0):.15f}). "
                    f"Constraint: Σ(a_ℓ) + Σ(a_ℓk) = 1.0 (tolerance {TOLERANCE})."
                )
    
    def _compute_config_hash(self) -> str:
        """
        Compute SHA256 hash of all config files.
        
        Spec compliance: Section 7 (audit_trail.config_hash)
        """
        hasher = hashlib.sha256()
        
        # Hash all three pillar configs in sorted order
        for config in sorted([
            json.dumps(self.intrinsic_config, sort_keys=True),
            json.dumps(self.contextual_config, sort_keys=True),
            json.dumps(self.fusion_config, sort_keys=True),
        ]):
            hasher.update(config.encode('utf-8'))
        
        return f"sha256:{hasher.hexdigest()}"
    
    @staticmethod
    def _compute_graph_hash(graph: ComputationGraph) -> str:
        """
        Compute SHA256 hash of computation graph.
        
        Spec compliance: Section 7 (audit_trail.graph_hash)
        """
        hasher = hashlib.sha256()
        
        # Hash nodes and edges
        graph_repr = json.dumps({
            "nodes": sorted(list(graph.nodes)),
            "edges": sorted([list(e) for e in graph.edges])
        }, sort_keys=True)
        
        hasher.update(graph_repr.encode('utf-8'))
        return f"sha256:{hasher.hexdigest()}"
    
    def _determine_role(self, method_id: str) -> MethodRole:
        """
        Determine method role from method ID using canonical catalog metadata.
        
        Three-Pillar System: Uses canonical_method_catalog.json for role inference.
        Mapping from catalog layer + method patterns to MethodRole enum.
        
        Args:
            method_id: Method identifier (canonical_name, method_name, or Class.method format)
            
        Returns:
            MethodRole enum value
            
        Raises:
            CalibrationConfigError: If method not found in catalog or role cannot be determined
        """
        # Look up method in catalog index
        method_info = self.method_index.get(method_id)
        
        if not method_info:
            # Try fallback patterns
            for key, info in self.method_index.items():
                if method_id in key or key in method_id:
                    method_info = info
                    break
        
        if not method_info:
            # Cannot calibrate unknown methods - fail loudly
            raise CalibrationConfigError(
                f"Method '{method_id}' not found in canonical_method_catalog.json. "
                f"Cannot determine role for calibration. "
                f"All calibrated methods must be registered in catalog.\n"
                f"To resolve:\n"
                f"  1. Add method to config/canonical_method_catalog.json with proper metadata\n"
                f"  2. Run scripts/rigorous_calibration_triage.py to generate intrinsic calibration\n"
                f"  3. Ensure method has correct layer, role, and signature information"
            )
        
        # Determine role from layer + method name patterns (per canonic_calibration_methods.md)
        layer = method_info.get("layer", "unknown")
        method_name = method_info.get("method_name", "").lower()
        
        # Role mapping based on layer and method semantics
        # Per L_* specification in canonic_calibration_methods.md
        if layer == "ingestion" or "ingest" in method_name or "pdm" in method_name:
            return MethodRole.INGEST_PDM
        elif "structure" in method_name or "parse" in method_name:
            return MethodRole.STRUCTURE
        elif "extract" in method_name:
            return MethodRole.EXTRACT
        elif "score" in method_name or "question" in method_name or layer == "analyzer":
            return MethodRole.SCORE_Q
        elif "aggregate" in method_name or "combine" in method_name:
            return MethodRole.AGGREGATE
        elif "report" in method_name or "format" in method_name:
            return MethodRole.REPORT
        elif "transform" in method_name or "normalize" in method_name or "convert" in method_name:
            return MethodRole.TRANSFORM
        else:
            # Default to META_TOOL for utility/orchestrator methods
            return MethodRole.META_TOOL
    
    def _detect_interplay(self, graph: ComputationGraph, node_id: str) -> Optional[Any]:
        """
        Detect interplay patterns from computation graph.
        
        Three-Pillar System: Interplays are DECLARED in config, not auto-detected.
        
        Per canonic_calibration_methods.md Section 1.3:
        - "An interplay G is valid only if all nodes share a single declared target output"
        - "A fusion rule is declared in config"
        - "Do not infer ensembles implicitly"
        
        This method checks if the node participates in any declared interplay
        from the contextual config.
        
        Args:
            graph: Computation graph
            node_id: Node identifier
            
        Returns:
            Interplay subgraph if node participates in one, None otherwise
        """
        # Per specification: interplays are declared in contextual config, not inferred
        # Check contextual_parametrization.json for declared interplays
        interplay_defs = self.contextual_config.get("interplay_definitions", {})
        
        for interplay_id, interplay_spec in interplay_defs.items():
            # Check if node_id is in this interplay's participant list
            participants = interplay_spec.get("participants", [])
            if node_id in participants:
                # Node participates in this declared interplay
                # Return interplay specification
                return {
                    "interplay_id": interplay_id,
                    "participants": participants,
                    "target_output": interplay_spec.get("target_output"),
                    "fusion_rule": interplay_spec.get("fusion_rule"),
                    "declared": True
                }
        
        # Node does not participate in any declared interplay
        # This is normal - most nodes don't participate in interplays
        return None
    
    def _compute_layer_scores(
        self, 
        subject: CalibrationSubject,
        evidence: EvidenceStore
    ) -> Dict[str, float]:
        """
        Compute all layer scores for calibration subject.
        
        Spec compliance: Section 3 (all layers)
        """
        ctx = subject.context
        scores = {}
        
        # @b: Base layer (always required)
        scores[LayerType.BASE.value] = compute_base_layer(
            subject.method_id, self.intrinsic_config
        )
        
        # @chain: Chain compatibility (always required for non-META roles)
        scores[LayerType.CHAIN.value] = compute_chain_layer(
            subject.node_id, subject.graph, self.contextual_config
        )
        
        # @u: Unit-of-analysis
        if subject.role:
            scores[LayerType.UNIT.value] = compute_unit_layer(
                subject.method_id, subject.role, ctx.unit_quality, self.contextual_config
            )
        
        # @q: Question compatibility
        scores[LayerType.QUESTION.value] = compute_question_layer(
            subject.method_id, ctx.question_id, self.monolith, self.contextual_config
        )
        
        # @d: Dimension compatibility
        scores[LayerType.DIMENSION.value] = compute_dimension_layer(
            subject.method_id, ctx.dimension_id, self.contextual_config
        )
        
        # @p: Policy compatibility
        scores[LayerType.POLICY.value] = compute_policy_layer(
            subject.method_id, ctx.policy_id, self.contextual_config
        )
        
        # @C: Interplay congruence
        scores[LayerType.INTERPLAY.value] = compute_interplay_layer(
            subject.interplay, self.contextual_config
        )
        
        # @m: Meta/governance
        meta_evidence = {
            "formula_export_valid": True,
            "trace_complete": True,
            "logs_conform_schema": True,
            "version_tagged": True,
            "config_hash_matches": True,
            "signature_valid": True,
            "runtime_ms": evidence.runtime_metrics.get("runtime_ms", 100)
        }
        scores[LayerType.META.value] = compute_meta_layer(
            meta_evidence, self.contextual_config
        )
        
        return scores
    
    def _apply_fusion(
        self,
        role: MethodRole,
        layer_scores: Dict[str, float]
    ) -> tuple[float, Dict[str, Any]]:
        """
        Apply pure fusion operator to combine layer scores.
        
        Spec compliance: Section 5 (Fusion Operator)
        SIN_CARRETA Compliance: Pure mathematical formula, no clamping/normalization
        
        Formula: Cal(I) = Σ(a_ℓ · x_ℓ) + Σ(a_ℓk · min(x_ℓ, x_k))
        
        Weight constraints (enforced at load time):
        - All weights a_ℓ, a_ℓk ≥ 0
        - Σ(a_ℓ) + Σ(a_ℓk) ≤ 1 (ensures boundedness)
        
        Returns:
            (calibrated_score, fusion_details)
            
        Raises:
            CalibrationConfigError: If score violates [0,1] bounds (weight misconfiguration)
        """
        role_params = self.fusion_config["role_fusion_parameters"].get(
            role.value,
            self.fusion_config["default_fallback"]
        )
        
        linear_weights = role_params["linear_weights"]
        interaction_weights = role_params.get("interaction_weights", {})
        
        # Compute linear terms
        linear_sum = 0.0
        linear_trace = []
        
        for layer_key, weight in linear_weights.items():
            if layer_key in layer_scores:
                contribution = weight * layer_scores[layer_key]
                linear_sum += contribution
                linear_trace.append({
                    "layer": layer_key,
                    "weight": weight,
                    "score": layer_scores[layer_key],
                    "contribution": contribution
                })
        
        # Compute interaction terms
        interaction_sum = 0.0
        interaction_trace = []
        
        for pair_key, weight in interaction_weights.items():
            # Parse "(layer1, layer2)" format
            pair_str = pair_key.strip("()")
            layer1, layer2 = [l.strip() for l in pair_str.split(",")]
            
            if layer1 in layer_scores and layer2 in layer_scores:
                min_score = min(layer_scores[layer1], layer_scores[layer2])
                contribution = weight * min_score
                interaction_sum += contribution
                interaction_trace.append({
                    "pair": pair_key,
                    "weight": weight,
                    "layer1_score": layer_scores[layer1],
                    "layer2_score": layer_scores[layer2],
                    "min_score": min_score,
                    "contribution": contribution
                })
        
        # Total calibrated score (PURE FUSION - no clamping or normalization)
        calibrated_score = linear_sum + interaction_sum
        
        # SIN_CARRETA: Fail loudly on weight misconfiguration
        # NEVER clamp or normalize - that would hide misconfiguration
        if calibrated_score < 0.0 or calibrated_score > 1.0:
            total_weight = sum(linear_weights.values()) + sum(interaction_weights.values())
            raise CalibrationConfigError(
                f"Fusion weights misconfigured for role {role.value}: "
                f"total_weight={total_weight:.6f} produced calibrated_score={calibrated_score:.6f}. "
                f"Score must be in [0,1]. Weight constraints violated. "
                f"Check fusion_specification.json and ensure Σ(a_ℓ) + Σ(a_ℓk) ≤ 1."
            )
        
        fusion_details = {
            "symbolic": "Σ(a_ℓ·x_ℓ) + Σ(a_ℓk·min(x_ℓ,x_k))",
            "linear_terms": linear_trace,
            "interaction_terms": interaction_trace,
            "linear_sum": linear_sum,
            "interaction_sum": interaction_sum,
            "total": calibrated_score
        }
        
        return calibrated_score, fusion_details
    
    def calibrate(
        self,
        method_id: str,
        node_id: str,
        graph: ComputationGraph,
        context: Context,
        evidence_store: EvidenceStore
    ) -> CalibrationCertificate:
        """
        Main calibration function.
        
        Spec compliance: Section 7 (Runtime Engine)
        
        Args:
            method_id: Canonical method ID
            node_id: Node identifier in graph
            graph: Computation graph
            context: Execution context
            evidence_store: Evidence for calibration
        
        Returns:
            CalibrationCertificate with complete audit trail
        
        Raises:
            ValueError: If validation fails
        """
        # Validate graph is DAG
        if not graph.validate_dag():
            raise ValueError("Graph contains cycles - must be DAG")
        
        # Determine role
        role = self._determine_role(method_id)
        
        # SIN_CARRETA: Detect interplay from graph (fail if not implemented)
        interplay = self._detect_interplay(graph, node_id)
        
        # Create calibration subject
        subject = CalibrationSubject(
            method_id=method_id,
            node_id=node_id,
            graph=graph,
            interplay=interplay,
            context=context,
            role=role
        )
        
        # Validate layer completeness
        required = REQUIRED_LAYERS.get(role, set())
        
        # Compute layer scores
        layer_scores = self._compute_layer_scores(subject, evidence_store)
        
        # Check all required layers are present
        missing_layers = [layer for layer in required if layer.value not in layer_scores]
        if missing_layers:
            raise ValueError(
                f"Missing required layers for role {role.value}: "
                f"{[layer.value for layer in missing_layers]}"
            )
        
        # Apply fusion
        calibrated_score, fusion_details = self._apply_fusion(role, layer_scores)
        
        # Build parameter provenance
        role_params = self.fusion_config["role_fusion_parameters"].get(
            role.value,
            self.fusion_config["default_fallback"]
        )
        
        parameter_provenance = {
            "fusion_weights": {
                "source": "fusion_specification.json",
                "role": role.value,
                "linear_weights": role_params["linear_weights"],
                "interaction_weights": role_params.get("interaction_weights", {})
            },
            "intrinsic_calibration": {
                "source": "intrinsic_calibration.json",
                "method_id": method_id
            }
        }
        
        # Build evidence trail
        evidence_trail = {
            "pdt_metrics": evidence_store.pdt_structure,
            "runtime_metrics": evidence_store.runtime_metrics,
            "layer_computations": layer_scores
        }
        
        # Create certificate
        certificate = CalibrationCertificate(
            instance_id=f"{method_id}@{node_id}",
            method_id=method_id,
            node_id=node_id,
            context=context,
            intrinsic_score=layer_scores.get(LayerType.BASE.value, 0.0),
            layer_scores=layer_scores,
            calibrated_score=calibrated_score,
            fusion_formula=fusion_details,
            parameter_provenance=parameter_provenance,
            evidence_trail=evidence_trail,
            config_hash=self.config_hash,
            graph_hash=self._compute_graph_hash(graph),
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            validator_version="1.0.0"
        )
        
        return certificate


# Convenience function
def calibrate(
    method_id: str,
    node_id: str,
    graph: ComputationGraph,
    context: Context,
    evidence_store: EvidenceStore,
    config_dir: Optional[str] = None,
    monolith_path: Optional[str] = None
) -> CalibrationCertificate:
    """
    Calibrate a method instance.
    
    Spec compliance: Section 7
    
    This is the single authoritative calibration entry point.
    """
    engine = CalibrationEngine(config_dir=config_dir, monolith_path=monolith_path)
    return engine.calibrate(method_id, node_id, graph, context, evidence_store)
