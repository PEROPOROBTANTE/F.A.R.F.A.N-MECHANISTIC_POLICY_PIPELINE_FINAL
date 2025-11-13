"""
Calibration system data structures.

These dataclasses define the EXACT structure of calibration outputs.
NO fields should be added or removed without updating this spec.

Design Principles:
1. Immutability: All dataclasses are frozen
2. Validation: __post_init__ checks invariants
3. Type Safety: Use type hints everywhere
4. Serializability: Support to_dict() for JSON export
"""
from dataclasses import dataclass, field
from typing import Any
from enum import Enum


class LayerID(str, Enum):
    """
    Exact identifier for each calibration layer.
    
    These correspond to the 7 layers in the theoretical model.
    """
    BASE = "b"          # @b - Intrinsic quality (COMPLETE)
    UNIT = "u"          # @u - PDT quality
    QUESTION = "q"      # @q - Question compatibility
    DIMENSION = "d"     # @d - Dimension compatibility  
    POLICY = "p"        # @p - Policy area compatibility
    CONGRUENCE = "C"    # @C - Ensemble validity
    CHAIN = "chain"     # @chain - Data flow integrity
    META = "m"          # @m - Governance


@dataclass(frozen=True)
class LayerScore:
    """
    Single layer evaluation result.
    
    This represents the output of evaluating ONE layer for ONE subject.
    
    Attributes:
        layer: Which layer this score belongs to
        score: Numerical score in [0.0, 1.0]
        components: Breakdown of sub-scores (e.g., for @u: {S, M, I, P})
        rationale: Human-readable explanation of the score
        metadata: Additional debug/audit information
    
    Example:
        LayerScore(
            layer=LayerID.UNIT,
            score=0.75,
            components={"S": 0.8, "M": 0.7, "I": 0.75, "P": 0.75},
            rationale="Unit quality: robusto (S=0.80, M=0.70, I=0.75, P=0.75)",
            metadata={"aggregation_method": "geometric_mean"}
        )
    """
    layer: LayerID
    score: float  # MUST be in [0.0, 1.0]
    components: dict[str, float] = field(default_factory=dict)
    rationale: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate score is in valid range."""
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                f"Layer {self.layer.value} score {self.score} out of range [0.0, 1.0]"
            )
    
    def to_dict(self) -> dict:
        """Export as dictionary for JSON serialization."""
        return {
            "layer": self.layer.value,
            "score": self.score,
            "components": self.components,
            "rationale": self.rationale,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ContextTuple:
    """
    Execution context for a micro-question: ctx = (Q, D, P, U).
    
    This is the (Q, D, P, U) tuple that defines WHERE a method is being used.
    The context determines which compatibility scores apply.
    
    Attributes:
        question_id: e.g., "Q001", "Q031" (from questionnaire monolith)
        dimension: e.g., "DIM01" (canonical code, not "D1")
        policy_area: e.g., "PA01" (canonical code, not "P1")
        unit_quality: Pre-computed U score from PDT analysis, range [0.0, 1.0]
    
    Example:
        ContextTuple(
            question_id="Q001",
            dimension="DIM01",
            policy_area="PA01",
            unit_quality=0.75
        )
    """
    question_id: str
    dimension: str
    policy_area: str
    unit_quality: float
    
    def __post_init__(self):
        """Validate canonical notation and ranges."""
        # Validate dimension uses canonical notation
        if not self.dimension.startswith("DIM"):
            raise ValueError(
                f"Dimension must use canonical code (DIM01-DIM06), got {self.dimension}"
            )
        
        # Validate policy area uses canonical notation
        if not self.policy_area.startswith("PA"):
            raise ValueError(
                f"Policy must use canonical code (PA01-PA10), got {self.policy_area}"
            )
        
        # Validate question ID format
        if not self.question_id.startswith("Q"):
            raise ValueError(
                f"Question ID must start with 'Q', got {self.question_id}"
            )
        
        # Validate unit quality range
        if not 0.0 <= self.unit_quality <= 1.0:
            raise ValueError(
                f"Unit quality must be in [0.0, 1.0], got {self.unit_quality}"
            )
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            "question_id": self.question_id,
            "dimension": self.dimension,
            "policy_area": self.policy_area,
            "unit_quality": self.unit_quality,
        }


@dataclass(frozen=True)
class CalibrationSubject:
    """
    Subject of calibration I = (M, v, Γ, G, ctx).
    
    This represents ONE method being evaluated in ONE context.
    
    From theoretical model:
    - M: Method artifact (code)
    - v: Version
    - Γ: Computational graph (how methods connect)
    - G: Interplay subgraph (methods working together)
    - ctx: Context tuple (Q, D, P, U)
    
    Attributes:
        method_id: e.g., "pattern_extractor_v2"
        method_version: e.g., "v2.1.0"
        graph_config: Hash of the computational graph Γ
        subgraph_id: Identifier for the interplay subgraph G
        context: The (Q, D, P, U) context
    
    Example:
        CalibrationSubject(
            method_id="pattern_extractor_v2",
            method_version="v2.1.0",
            graph_config="abc123def456",
            subgraph_id="Q001_analyzer_validator",
            context=ContextTuple(...)
        )
    """
    method_id: str
    method_version: str
    graph_config: str
    subgraph_id: str
    context: ContextTuple
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            "method_id": self.method_id,
            "method_version": self.method_version,
            "graph_config": self.graph_config,
            "subgraph_id": self.subgraph_id,
            "context": self.context.to_dict(),
        }


@dataclass(frozen=True)
class CompatibilityMapping:
    """
    Defines how compatible a method is with questions/dimensions/policies.
    
    This implements the Q_f, D_f, P_f functions from the theoretical model.
    
    Compatibility Scores (from theoretical model):
        1.0 = Primary (designed specifically for this context)
        0.7 = Secondary (works well, but not optimal)
        0.3 = Compatible (can work, limited effectiveness)
        0.1 = Undeclared (penalty, not validated for this context)
    
    Example:
        CompatibilityMapping(
            method_id="pattern_extractor_v2",
            questions={"Q001": 1.0, "Q031": 0.7, "Q091": 0.3},
            dimensions={"DIM01": 1.0, "DIM03": 0.7},
            policies={"PA01": 1.0, "PA10": 0.7}
        )
    """
    method_id: str
    questions: dict[str, float]   # question_id -> score ∈ {1.0, 0.7, 0.3, 0.1}
    dimensions: dict[str, float]  # dimension_code -> score
    policies: dict[str, float]    # policy_code -> score
    
    def get_question_score(self, question_id: str) -> float:
        """
        Get compatibility score for a question.
        
        Returns 0.1 (penalty) if question not declared.
        """
        return self.questions.get(question_id, 0.1)
    
    def get_dimension_score(self, dimension: str) -> float:
        """
        Get compatibility score for a dimension.
        
        Returns 0.1 (penalty) if dimension not declared.
        """
        return self.dimensions.get(dimension, 0.1)
    
    def get_policy_score(self, policy: str) -> float:
        """
        Get compatibility score for a policy area.
        
        Returns 0.1 (penalty) if policy not declared.
        """
        return self.policies.get(policy, 0.1)
    
    def check_anti_universality(self, threshold: float = 0.9) -> bool:
        """
        Check Anti-Universality Theorem compliance.
        
        The theorem states: NO method can have average compatibility ≥ 0.9
        across ALL questions, dimensions, AND policies simultaneously.
        
        Returns:
            True if compliant (method is NOT universal)
            False if violation detected
        """
        if not self.questions or not self.dimensions or not self.policies:
            return True  # Incomplete mapping, cannot be universal
        
        avg_q = sum(self.questions.values()) / len(self.questions)
        avg_d = sum(self.dimensions.values()) / len(self.dimensions)
        avg_p = sum(self.policies.values()) / len(self.policies)
        
        is_universal = (avg_q >= threshold and 
                       avg_d >= threshold and 
                       avg_p >= threshold)
        
        return not is_universal
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            "method_id": self.method_id,
            "questions": self.questions,
            "dimensions": self.dimensions,
            "policies": self.policies,
        }


@dataclass(frozen=True)
class InteractionTerm:
    """
    Represents a synergy between two layers in Choquet aggregation.
    
    Formula: a_ℓk · min(x_ℓ, x_k)
    
    This captures the "weakest link" principle: the contribution of the
    interaction is limited by whichever layer scored lower.
    
    Standard Interactions (from theoretical model):
        (@u, @chain): weight=0.15, "Plan quality only matters with sound wiring"
        (@chain, @C): weight=0.12, "Ensemble validity requires chain integrity"
        (@q, @d): weight=0.08, "Question-dimension alignment synergy"
        (@d, @p): weight=0.05, "Dimension-policy coherence synergy"
    
    Example:
        InteractionTerm(
            layer_1=LayerID.UNIT,
            layer_2=LayerID.CHAIN,
            weight=0.15,
            rationale="Plan quality only matters with sound wiring"
        )
    """
    layer_1: LayerID
    layer_2: LayerID
    weight: float  # a_ℓk coefficient
    rationale: str  # Why this interaction exists
    
    def compute(self, scores: dict[LayerID, float]) -> float:
        """
        Compute interaction contribution.
        
        Formula: a_ℓk · min(x_ℓ, x_k)
        
        Args:
            scores: Dictionary mapping LayerID to score
        
        Returns:
            Interaction contribution (can be 0 if layer missing)
        """
        score_1 = scores.get(self.layer_1, 0.0)
        score_2 = scores.get(self.layer_2, 0.0)
        return self.weight * min(score_1, score_2)
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            "layer_1": self.layer_1.value,
            "layer_2": self.layer_2.value,
            "weight": self.weight,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class CalibrationResult:
    """
    Complete calibration output for a subject I.
    
    This is the FINAL result of the calibration pipeline.
    
    Formula: Cal(I) = Σ a_ℓ·x_ℓ + Σ a_ℓk·min(x_ℓ, x_k)
    
    Attributes:
        subject: The calibration subject I = (M, v, Γ, G, ctx)
        layer_scores: Individual scores for each layer
        linear_contribution: Σ a_ℓ · x_ℓ
        interaction_contribution: Σ a_ℓk · min(x_ℓ, x_k)
        final_score: Cal(I) = linear + interaction ∈ [0.0, 1.0]
        computation_metadata: Timestamps, hashes, config_hash, etc.
    
    Example:
        CalibrationResult(
            subject=CalibrationSubject(...),
            layer_scores={
                LayerID.BASE: LayerScore(..., score=0.9),
                LayerID.UNIT: LayerScore(..., score=0.75),
                ...
            },
            linear_contribution=0.65,
            interaction_contribution=0.15,
            final_score=0.80,
            computation_metadata={
                "config_hash": "abc123",
                "timestamp": "2025-11-11T10:30:00Z"
            }
        )
    """
    subject: CalibrationSubject
    layer_scores: dict[LayerID, LayerScore]
    linear_contribution: float
    interaction_contribution: float
    final_score: float
    computation_metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate calibration result integrity."""
        # Validate final score range
        if not 0.0 <= self.final_score <= 1.0:
            raise ValueError(
                f"Final calibration score {self.final_score} out of range [0.0, 1.0]"
            )
        
        # Verify linear + interaction = final (within numerical tolerance)
        computed = self.linear_contribution + self.interaction_contribution
        if abs(computed - self.final_score) > 1e-6:
            raise ValueError(
                f"Final score {self.final_score} != "
                f"linear {self.linear_contribution} + "
                f"interaction {self.interaction_contribution} = {computed}"
            )
        
        # Verify all layer scores are in valid range
        for layer_id, layer_score in self.layer_scores.items():
            if not 0.0 <= layer_score.score <= 1.0:
                raise ValueError(
                    f"Layer {layer_id.value} score {layer_score.score} out of range"
                )
    
    def to_certificate_dict(self) -> dict:
        """
        Export as a calibration certificate for auditing.
        
        This is the format that gets saved to audit logs and can be
        used to reproduce the calibration result.
        """
        return {
            "certificate_version": "1.0",
            "method": {
                "id": self.subject.method_id,
                "version": self.subject.method_version,
                "graph_config": self.subject.graph_config,
                "subgraph_id": self.subject.subgraph_id,
            },
            "context": self.subject.context.to_dict(),
            "layer_scores": {
                layer_id.value: layer_score.to_dict()
                for layer_id, layer_score in self.layer_scores.items()
            },
            "aggregation": {
                "linear_contribution": self.linear_contribution,
                "interaction_contribution": self.interaction_contribution,
                "final_score": self.final_score,
                "formula": "Cal(I) = Σ a_ℓ·x_ℓ + Σ a_ℓk·min(x_ℓ, x_k)",
            },
            "metadata": self.computation_metadata,
        }
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return self.to_certificate_dict()
