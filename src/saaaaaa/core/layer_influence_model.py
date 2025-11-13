"""
Layer Coexistence and Influence Model - Formal Specification

This module encodes the mathematical relationships between layers,
including:
- Conditional activation rules (when a layer becomes relevant)
- Influence relationships (how layers weight/transform each other)
- Coexistence constraints (compatibility requirements)

All rules are explicit, verifiable, and derived from theoretical foundations.

References:
- Pearl (1988): Probabilistic Reasoning in Intelligent Systems (conditional independence)
- Keeney & Raiffa (1976): Decisions with Multiple Objectives (preference independence)
- Grabisch (1997): k-order additive discrete fuzzy measures (interaction indices)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Callable, Tuple
from enum import Enum
import json

from .layer_coexistence import Layer, LayerScore


class LayerInfluenceType(Enum):
    """Types of influence one layer can have on another."""
    WEIGHTING = "weighting"          # Layer A modifies weight of Layer B
    TRANSFORMATION = "transformation"  # Layer A transforms values from Layer B
    ACTIVATION = "activation"          # Layer A determines if Layer B is active
    CONSTRAINT = "constraint"          # Layer A constrains valid values of Layer B


@dataclass
class LayerInfluence:
    """
    Formal specification of how one layer influences another.
    
    Attributes:
        source_layer: The influencing layer
        target_layer: The influenced layer
        influence_type: Type of influence relationship
        strength: Strength of influence in [0, 1]
        functional_form: Mathematical description of influence
        conditions: When this influence applies
    """
    source_layer: Layer
    target_layer: Layer
    influence_type: LayerInfluenceType
    strength: float
    functional_form: str
    conditions: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate influence specification"""
        if not 0 <= self.strength <= 1:
            raise ValueError(f"Influence strength must be in [0,1], got {self.strength}")
        if self.source_layer == self.target_layer:
            raise ValueError("Self-influence not permitted in current model")


@dataclass
class LayerActivationRule:
    """
    Rule determining when a layer becomes active for a method.
    
    This encodes the endogenous determination of L(M) from method characteristics.
    
    Attributes:
        layer: The layer this rule applies to
        triggers: Conditions that activate this layer
        prerequisites: Other layers that must be active first
        priority: Activation priority (higher = checked first)
    """
    layer: Layer
    triggers: List[Callable]  # Functions that return bool
    prerequisites: Set[Layer] = field(default_factory=set)
    priority: int = 0
    
    def check_activation(self, method_characteristics: Dict) -> bool:
        """
        Check if this layer should be active given method characteristics.
        
        Args:
            method_characteristics: Dict describing method properties
            
        Returns:
            True if layer should be active
        """
        return any(trigger(method_characteristics) for trigger in self.triggers)


class LayerCoexistenceModel:
    """
    Formal model of layer interactions and dependencies.
    
    This encodes the complete "Layer Coexistence and Influence" system,
    including:
    - How to determine L(M) from method properties
    - How layers influence each other
    - Valid coexistence patterns
    - Composition rules for multi-layer fusion
    
    Design Principle: All layer interactions are explicit, not implicit.
    No hidden dependencies or undocumented couplings permitted.
    """
    
    def __init__(self):
        self.influences: List[LayerInfluence] = []
        self.activation_rules: Dict[Layer, LayerActivationRule] = {}
        self.compatibility_matrix: Dict[Tuple[Layer, Layer], float] = {}
        
        # Initialize canonical layer relationships
        self._initialize_canonical_relationships()
    
    def _initialize_canonical_relationships(self):
        """
        Define canonical layer relationships based on theoretical model.
        
        Canonical Relationships:
        
        1. @q → @d (WEIGHTING): Question-level evidence weights dimension scores
           - High certainty at @q increases weight of @d
           - Functional form: w_d' = w_d · (1 + α·certainty_q)
        
        2. @d → @p (ACTIVATION): Dimensions determine relevant policy areas
           - If dimension scores exist, policy coherence becomes relevant
           - Functional form: active(@p) ⟺ |scored_dimensions| ≥ threshold
        
        3. @p → @C (CONSTRAINT): Policy areas constrain ensemble methods
           - Policy structure limits valid ensemble combinations
           - Functional form: valid_ensembles ⊆ compatible_with_policy_structure
        
        4. {@q, @d, @p} → @m (TRANSFORMATION): Base layers feed meta-aggregation
           - Meta layer synthesizes across evidence levels
           - Functional form: x_m = g(x_q, x_d, x_p) where g is aggregation
        
        5. @C → @m (WEIGHTING): Congruence modulates meta-layer confidence
           - Ensemble agreement increases meta-layer weight
           - Functional form: w_m' = w_m · congruence_score
        """
        
        # @q → @d influence
        self.add_influence(LayerInfluence(
            source_layer=Layer.QUESTION,
            target_layer=Layer.DIMENSION,
            influence_type=LayerInfluenceType.WEIGHTING,
            strength=0.5,
            functional_form="w_d' = w_d * (1 + 0.5 * certainty_q)",
            conditions={'requires': 'question_certainty_available'}
        ))
        
        # @d → @p influence
        self.add_influence(LayerInfluence(
            source_layer=Layer.DIMENSION,
            target_layer=Layer.POLICY_AREA,
            influence_type=LayerInfluenceType.ACTIVATION,
            strength=1.0,
            functional_form="active(@p) ⟺ |scored_dimensions| ≥ 3",
            conditions={'threshold': 3}
        ))
        
        # @p → @C influence
        self.add_influence(LayerInfluence(
            source_layer=Layer.POLICY_AREA,
            target_layer=Layer.CONGRUENCE,
            influence_type=LayerInfluenceType.CONSTRAINT,
            strength=0.7,
            functional_form="valid_ensembles ⊆ policy_compatible_ensembles",
            conditions={'requires': 'policy_structure_defined'}
        ))
        
        # Base layers → @m influence
        for base_layer in [Layer.QUESTION, Layer.DIMENSION, Layer.POLICY_AREA]:
            self.add_influence(LayerInfluence(
                source_layer=base_layer,
                target_layer=Layer.META,
                influence_type=LayerInfluenceType.TRANSFORMATION,
                strength=0.33,
                functional_form="x_m = weighted_mean(x_q, x_d, x_p)",
                conditions={'aggregation_type': 'weighted_mean'}
            ))
        
        # @C → @m influence
        self.add_influence(LayerInfluence(
            source_layer=Layer.CONGRUENCE,
            target_layer=Layer.META,
            influence_type=LayerInfluenceType.WEIGHTING,
            strength=0.6,
            functional_form="w_m' = w_m * congruence_score",
            conditions={'requires': 'ensemble_agreement'}
        ))
        
        # Initialize compatibility matrix (all pairs compatible by default)
        for layer1 in Layer:
            for layer2 in Layer:
                # Diagonal: perfect self-compatibility
                if layer1 == layer2:
                    self.compatibility_matrix[(layer1, layer2)] = 1.0
                # Off-diagonal: initialize to compatible
                else:
                    self.compatibility_matrix[(layer1, layer2)] = 0.8
        
        # Adjust specific incompatibilities if any
        # (Currently all layers are mutually compatible)
    
    def add_influence(self, influence: LayerInfluence):
        """Register a layer influence relationship."""
        self.influences.append(influence)
    
    def add_activation_rule(self, rule: LayerActivationRule):
        """Register a layer activation rule."""
        self.activation_rules[rule.layer] = rule
    
    def determine_active_layers(
        self, 
        method_characteristics: Dict
    ) -> Set[Layer]:
        """
        Determine L(M) endogenously from method characteristics.
        
        This is the key function that derives active layers from method
        properties rather than requiring manual specification.
        
        Args:
            method_characteristics: Dict with keys like:
                - 'operates_on_questions': bool
                - 'aggregates_dimensions': bool
                - 'addresses_policy_areas': bool
                - 'uses_ensemble': bool
                - 'performs_meta_aggregation': bool
                - 'question_count': int
                - 'dimension_count': int
                - 'policy_area_count': int
                
        Returns:
            Set of active layers for this method
        """
        active = set()
        
        # Sort rules by priority
        sorted_rules = sorted(
            self.activation_rules.items(),
            key=lambda x: x[1].priority,
            reverse=True
        )
        
        # Check each rule
        for layer, rule in sorted_rules:
            # Check prerequisites
            if not rule.prerequisites.issubset(active):
                continue
            
            # Check triggers
            if rule.check_activation(method_characteristics):
                active.add(layer)
        
        return active
    
    def get_layer_influences(
        self, 
        target_layer: Layer,
        active_layers: Set[Layer]
    ) -> List[LayerInfluence]:
        """
        Get all influences affecting a target layer from active layers.
        
        Args:
            target_layer: Layer being influenced
            active_layers: Set of currently active layers
            
        Returns:
            List of applicable LayerInfluence objects
        """
        return [
            inf for inf in self.influences
            if inf.target_layer == target_layer 
            and inf.source_layer in active_layers
        ]
    
    def compute_effective_weight(
        self,
        target_layer: Layer,
        base_weight: float,
        layer_scores: Dict[Layer, LayerScore],
        active_layers: Set[Layer]
    ) -> float:
        """
        Compute effective weight for a layer after applying influences.
        
        Args:
            target_layer: Layer whose weight is being computed
            base_weight: Initial weight
            layer_scores: Scores for all active layers
            active_layers: Set of active layers
            
        Returns:
            Effective weight after influence application
        """
        effective_weight = base_weight
        
        # Get weighting influences
        influences = [
            inf for inf in self.get_layer_influences(target_layer, active_layers)
            if inf.influence_type == LayerInfluenceType.WEIGHTING
        ]
        
        for influence in influences:
            source_score = layer_scores.get(influence.source_layer)
            if source_score:
                # Apply influence (simplified model)
                modifier = 1.0 + influence.strength * (source_score.value - 0.5)
                effective_weight *= modifier
        
        # Ensure weight stays in valid range
        return max(0.0, min(1.0, effective_weight))
    
    def check_compatibility(
        self,
        layer_set: Set[Layer]
    ) -> Tuple[bool, float]:
        """
        Check if a set of layers is compatible for coexistence.
        
        Args:
            layer_set: Set of layers to check
            
        Returns:
            (is_compatible, compatibility_score)
            where compatibility_score in [0, 1]
        """
        if len(layer_set) <= 1:
            return True, 1.0
        
        # Compute minimum pairwise compatibility
        min_compatibility = 1.0
        layer_list = list(layer_set)
        
        for i, layer1 in enumerate(layer_list):
            for layer2 in layer_list[i+1:]:
                compat = self.compatibility_matrix.get((layer1, layer2), 0.8)
                min_compatibility = min(min_compatibility, compat)
        
        # Compatible if minimum exceeds threshold
        is_compatible = min_compatibility >= 0.5
        return is_compatible, min_compatibility
    
    def export_model(self) -> Dict:
        """Export model to JSON-serializable format."""
        return {
            'influences': [
                {
                    'source': inf.source_layer.value,
                    'target': inf.target_layer.value,
                    'type': inf.influence_type.value,
                    'strength': inf.strength,
                    'formula': inf.functional_form,
                    'conditions': inf.conditions
                }
                for inf in self.influences
            ],
            'compatibility_matrix': {
                f"{l1.value},{l2.value}": score
                for (l1, l2), score in self.compatibility_matrix.items()
            }
        }


def initialize_canonical_activation_rules() -> Dict[Layer, LayerActivationRule]:
    """
    Initialize canonical activation rules for all layers.
    
    These rules encode when each layer becomes relevant based on
    method characteristics.
    
    Returns:
        Dict mapping Layer to LayerActivationRule
    """
    rules = {}
    
    # @q activation: Method operates on individual questions
    rules[Layer.QUESTION] = LayerActivationRule(
        layer=Layer.QUESTION,
        triggers=[
            lambda mc: mc.get('operates_on_questions', False),
            lambda mc: mc.get('question_count', 0) > 0,
        ],
        priority=100  # Highest priority - foundational layer
    )
    
    # @d activation: Method aggregates across dimensions
    rules[Layer.DIMENSION] = LayerActivationRule(
        layer=Layer.DIMENSION,
        triggers=[
            lambda mc: mc.get('aggregates_dimensions', False),
            lambda mc: mc.get('dimension_count', 0) > 0,
        ],
        prerequisites={Layer.QUESTION},  # Requires question layer
        priority=90
    )
    
    # @p activation: Method addresses policy areas
    rules[Layer.POLICY_AREA] = LayerActivationRule(
        layer=Layer.POLICY_AREA,
        triggers=[
            lambda mc: mc.get('addresses_policy_areas', False),
            lambda mc: mc.get('policy_area_count', 0) > 0,
            lambda mc: mc.get('dimension_count', 0) >= 3,  # @d → @p influence
        ],
        prerequisites={Layer.DIMENSION},  # Requires dimension layer
        priority=80
    )
    
    # @C activation: Method uses ensemble techniques
    rules[Layer.CONGRUENCE] = LayerActivationRule(
        layer=Layer.CONGRUENCE,
        triggers=[
            lambda mc: mc.get('uses_ensemble', False),
            lambda mc: mc.get('ensemble_method_count', 0) > 1,
        ],
        priority=70
    )
    
    # @m activation: Method performs cross-layer meta-aggregation
    rules[Layer.META] = LayerActivationRule(
        layer=Layer.META,
        triggers=[
            lambda mc: mc.get('performs_meta_aggregation', False),
            lambda mc: len(mc.get('active_base_layers', set())) >= 2,
        ],
        priority=60  # Lowest priority - synthesizes other layers
    )
    
    return rules


# Global canonical model instance
CANONICAL_LAYER_MODEL = LayerCoexistenceModel()

# Register activation rules
for layer, rule in initialize_canonical_activation_rules().items():
    CANONICAL_LAYER_MODEL.add_activation_rule(rule)
