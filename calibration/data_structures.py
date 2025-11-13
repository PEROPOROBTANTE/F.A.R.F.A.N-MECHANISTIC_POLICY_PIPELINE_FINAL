"""
Three-Pillar Calibration System - Core Data Structures

This module defines the fundamental data structures for the calibration system
as specified in the SUPERPROMPT Three-Pillar Calibration System.

Spec compliance: Section 1 (Core Objects), Section 7 (Certificates)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple
from enum import Enum


class CalibrationConfigError(Exception):
    """
    Raised when calibration configuration violates mathematical constraints.
    
    This error indicates:
    - Fusion weights don't sum to valid range
    - Weight constraints violated (must be ≥ 0)
    - Invalid layer configuration
    - Misconfigured calibration parameters
    
    SIN_CARRETA Policy: Fail loudly on misconfiguration, never silently clamp.
    """
    pass


class LayerType(Enum):
    """Eight fixed calibration layers - NO RENAMING ALLOWED"""
    BASE = "@b"                    # Intrinsic quality
    CHAIN = "@chain"               # Chain compatibility
    UNIT = "@u"                    # Unit-of-analysis sensitivity
    QUESTION = "@q"                # Question compatibility
    DIMENSION = "@d"               # Dimension compatibility
    POLICY = "@p"                  # Policy compatibility
    INTERPLAY = "@C"               # Interplay congruence
    META = "@m"                    # Meta/governance


class MethodRole(Enum):
    """Method roles with fixed required layer sets"""
    INGEST_PDM = "INGEST_PDM"
    STRUCTURE = "STRUCTURE"
    EXTRACT = "EXTRACT"
    SCORE_Q = "SCORE_Q"
    AGGREGATE = "AGGREGATE"
    REPORT = "REPORT"
    META_TOOL = "META_TOOL"
    TRANSFORM = "TRANSFORM"


# Role-based required layers (L_* from spec Section 4)
REQUIRED_LAYERS: Dict[MethodRole, Set[LayerType]] = {
    MethodRole.INGEST_PDM: {LayerType.BASE, LayerType.CHAIN, LayerType.UNIT, LayerType.META},
    MethodRole.STRUCTURE: {LayerType.BASE, LayerType.CHAIN, LayerType.UNIT, LayerType.META},
    MethodRole.EXTRACT: {LayerType.BASE, LayerType.CHAIN, LayerType.UNIT, LayerType.META},
    MethodRole.SCORE_Q: {LayerType.BASE, LayerType.CHAIN, LayerType.QUESTION, LayerType.DIMENSION, 
                         LayerType.POLICY, LayerType.INTERPLAY, LayerType.UNIT, LayerType.META},
    MethodRole.AGGREGATE: {LayerType.BASE, LayerType.CHAIN, LayerType.DIMENSION, LayerType.POLICY, 
                           LayerType.INTERPLAY, LayerType.META},
    MethodRole.REPORT: {LayerType.BASE, LayerType.CHAIN, LayerType.INTERPLAY, LayerType.META},
    MethodRole.META_TOOL: {LayerType.BASE, LayerType.CHAIN, LayerType.META},
    MethodRole.TRANSFORM: {LayerType.BASE, LayerType.CHAIN, LayerType.META},
}


@dataclass(frozen=True)
class Context:
    """
    Execution context: ctx = (Q, D, P, U)
    
    Spec compliance: Definition 1.2
    
    Q: Question ID or None
    D: Dimension ID (DIM01-DIM06)
    P: Policy area ID (PA01-PA10)
    U: Unit-of-analysis quality [0,1]
    """
    question_id: Optional[str] = None  # Q ∈ Questions ∪ {⊥}
    dimension_id: str = "DIM01"         # D ∈ Dimensions
    policy_id: str = "PA01"             # P ∈ Policies
    unit_quality: float = 0.85          # U ∈ [0,1]
    
    def __post_init__(self):
        """Validate context constraints"""
        if self.unit_quality < 0.0 or self.unit_quality > 1.0:
            raise ValueError(f"unit_quality must be in [0,1], got {self.unit_quality}")
        
        if self.dimension_id and not self.dimension_id.startswith("DIM"):
            raise ValueError(f"dimension_id must match DIM* pattern, got {self.dimension_id}")
        
        if self.policy_id and not self.policy_id.startswith("PA"):
            raise ValueError(f"policy_id must match PA* pattern, got {self.policy_id}")


@dataclass
class ComputationGraph:
    """
    Computation graph: Γ = (V, E, T, S)
    
    Spec compliance: Definition 1.1
    
    V: finite set of method instance nodes
    E: directed edges (must be DAG)
    T: edge typing function
    S: node signature function
    """
    nodes: Set[str] = field(default_factory=set)  # V
    edges: List[Tuple[str, str]] = field(default_factory=list)  # E ⊆ V × V
    edge_types: Dict[Tuple[str, str], Dict[str, Any]] = field(default_factory=dict)  # T
    node_signatures: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # S
    
    def validate_dag(self) -> bool:
        """Axiom 1.1: Graph must be acyclic"""
        # Simple cycle detection via DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for edge in self.edges:
                if edge[0] == node:
                    neighbor = edge[1]
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            return True
                    elif neighbor in rec_stack:
                        return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return False
        return True


@dataclass
class InterplaySubgraph:
    """
    Valid interplay: G = (V_G, E_G) ⊆ Γ
    
    Spec compliance: Definition 2.1
    
    Must satisfy:
    1. Single target property
    2. Declared fusion rule
    3. Type compatibility
    """
    nodes: Set[str]
    edges: List[Tuple[str, str]]
    target_output: str
    fusion_rule: str
    compatible: bool = True


@dataclass(frozen=True)
class CalibrationCertificate:
    """
    Complete calibration certificate with audit trail.
    
    Spec compliance: Section 7 (Definition 7.1)
    
    MUST allow exact reconstruction of Cal(I) from contents.
    Property 7.1: No hidden behavior - all computations must appear here.
    """
    # Identity
    instance_id: str
    method_id: str
    node_id: str
    context: Context
    
    # Scores
    intrinsic_score: float  # x_@b
    layer_scores: Dict[str, float]  # All x_ℓ(I)
    calibrated_score: float  # Cal(I)
    
    # Transparency
    fusion_formula: Dict[str, Any]  # symbolic, expanded, computation_trace
    parameter_provenance: Dict[str, Dict[str, Any]]  # Where each parameter came from
    evidence_trail: Dict[str, Any]  # Evidence used for layer computations
    
    # Integrity
    config_hash: str  # SHA256 of all config files
    graph_hash: str   # SHA256 of computation graph
    
    # Validation
    validation_checks: Dict[str, Any] = field(default_factory=dict)
    sensitivity_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Audit
    timestamp: str = ""
    validator_version: str = "1.0.0"
    
    def __post_init__(self):
        """Validate certificate constraints"""
        # Boundedness check
        if not (0.0 <= self.calibrated_score <= 1.0):
            raise ValueError(f"calibrated_score must be in [0,1], got {self.calibrated_score}")
        
        if not (0.0 <= self.intrinsic_score <= 1.0):
            raise ValueError(f"intrinsic_score must be in [0,1], got {self.intrinsic_score}")
        
        for layer, score in self.layer_scores.items():
            if not (0.0 <= score <= 1.0):
                raise ValueError(f"layer_scores[{layer}] must be in [0,1], got {score}")


@dataclass
class CalibrationSubject:
    """
    Calibration subject: I = (M, v, Γ, G, ctx)
    
    Spec compliance: Definition 1.3
    
    M: method artifact
    v: node instance
    Γ: containing graph
    G: interplay subgraph (or None)
    ctx: execution context
    """
    method_id: str  # M (canonical method ID)
    node_id: str    # v ∈ V
    graph: ComputationGraph  # Γ
    interplay: Optional[InterplaySubgraph]  # G
    context: Context  # ctx
    
    # Additional metadata
    role: Optional[MethodRole] = None
    active_layers: Set[LayerType] = field(default_factory=set)


@dataclass
class EvidenceStore:
    """
    Storage for evidence used in calibration computations.
    All evidence must be traceable and auditable.
    """
    pdt_structure: Dict[str, Any] = field(default_factory=dict)
    pdm_metrics: Dict[str, Any] = field(default_factory=dict)
    runtime_metrics: Dict[str, Any] = field(default_factory=dict)
    test_results: Dict[str, Any] = field(default_factory=dict)
    deployment_history: Dict[str, Any] = field(default_factory=dict)
    
    def get_evidence(self, key: str, default: Any = None) -> Any:
        """Retrieve evidence by key"""
        for store in [self.pdt_structure, self.pdm_metrics, self.runtime_metrics, 
                      self.test_results, self.deployment_history]:
            if key in store:
                return store[key]
        return default
