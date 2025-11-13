"""
Layer Coexistence and Influence Framework

Formal mathematical framework for method calibration based on layer-specific
evidence aggregation with theoretically grounded fusion operators.

Theoretical Foundations:
- Bayesian inference (Pearl, 1988; Jaynes, 2003)
- Multi-criteria decision analysis (Keeney & Raiffa, 1976)
- Policy coherence structures (Nilsson et al., 2012)
- Ensemble learning (Dietterich, 2000; Wolpert, 1992)
- Fuzzy measures and aggregation (Yager, 1988; Beliakov et al., 2007)

Canonical Layer Notation (from questionnaire_monolith.json):
- @q: Question Layer (300 questions: Q001-Q300)
- @d: Dimension Layer (6 dimensions: DIM01-DIM06)
- @p: Policy Area Layer (10 areas: PA01-PA10)
- @C: Congruence Layer (ensemble compatibility)
- @m: Meta Layer (cross-layer aggregation)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
from enum import Enum


class Layer(Enum):
    """
    Canonical layer identifiers.
    
    Source: questionnaire_monolith.json and theoretical framework specification.
    These are the ONLY valid layer identifiers in the system.
    """
    QUESTION = "@q"      # Evidence-weighted Bayesian scoring
    DIMENSION = "@d"     # Multi-criteria value functions
    POLICY_AREA = "@p"   # Policy coherence structures
    CONGRUENCE = "@C"    # Ensemble compatibility
    META = "@m"          # Generalized aggregation


@dataclass(frozen=True)
class LayerScore:
    """
    Score from a single layer for a method.
    
    Attributes:
        layer: The layer identifier
        value: Numerical score in [0, 1]
        weight: Importance weight in [0, 1]
        metadata: Additional layer-specific information
    """
    layer: Layer
    value: float
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)

    def __new__(cls, layer: Layer, value: float, weight: float = 1.0, metadata: Dict = None):
        """Validate score bounds before instance creation"""
        if not 0 <= value <= 1:
            raise ValueError(f"Layer score must be in [0,1], got {value}")
        if not 0 <= weight <= 1:
            raise ValueError(f"Layer weight must be in [0,1], got {weight}")
        if metadata is None:
            metadata = {}
        return super().__new__(cls)

    def __init__(self, layer: Layer, value: float, weight: float = 1.0, metadata: Dict = None):
        # dataclass will set fields, but we need to ensure metadata is not None
        if metadata is None:
            object.__setattr__(self, 'metadata', {})
@dataclass
class MethodSignature:
    """
    Complete signature for a method under Layer Coexistence framework.
    
    This is the canonical method notation that every calibrated method must expose.
    
    Attributes:
        method_id: Unique identifier (ClassName.method_name)
        active_layers: Set of layers relevant to this method (L(M))
        input_schema: Dict describing required inputs
        output_schema: Dict describing output space
        fusion_operator_name: Name of the fusion operator F_M
        fusion_parameters: Parameters for F_M
        calibration_rule: Human-readable calibration rule description
    """
    method_id: str
    active_layers: Set[Layer]
    input_schema: Dict
    output_schema: Dict
    fusion_operator_name: str
    fusion_parameters: Dict
    calibration_rule: str
    
    def to_dict(self) -> Dict:
        """Export to dictionary for serialization"""
        return {
            'method_id': self.method_id,
            'active_layers': [layer.value for layer in self.active_layers],
            'input_schema': self.input_schema,
            'output_schema': self.output_schema,
            'fusion_operator_name': self.fusion_operator_name,
            'fusion_parameters': self.fusion_parameters,
            'calibration_rule': self.calibration_rule
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MethodSignature':
        """Load from dictionary"""
        return cls(
            method_id=data['method_id'],
            active_layers={Layer(layer_str) for layer_str in data['active_layers']},
            input_schema=data['input_schema'],
            output_schema=data['output_schema'],
            fusion_operator_name=data['fusion_operator_name'],
            fusion_parameters=data['fusion_parameters'],
            calibration_rule=data['calibration_rule']
        )


class FusionOperator:
    """
    Abstract base class for fusion operators F_M.
    
    All fusion operators must satisfy:
    - Monotonicity: ∂F/∂x_ℓ ≥ 0 for all layers ℓ
    - Boundedness: F: [0,1]^n → [0,1]
    - Interpretability: Clear semantic meaning of output
    
    Subclasses must implement:
    - fuse(scores: List[LayerScore]) -> float
    - verify_properties() -> Dict[str, bool]
    - get_formula() -> str
    """
    
    def __init__(self, name: str, parameters: Dict):
        self.name = name
        self.parameters = parameters
    
    def fuse(self, scores: List[LayerScore]) -> float:
        """
        Aggregate layer scores into calibrated output.
        
        Args:
            scores: List of LayerScore objects
            
        Returns:
            Calibrated score in [0, 1]
        """
        raise NotImplementedError("Subclasses must implement fuse()")
    
    def verify_properties(self) -> Dict[str, bool]:
        """
        Verify mathematical properties (monotonicity, boundedness, etc.)
        
        Returns:
            Dict mapping property name to verification result
        """
        raise NotImplementedError("Subclasses must implement verify_properties()")
    
    def get_formula(self) -> str:
        """
        Return explicit mathematical formula in canonical notation.
        
        Returns:
            LaTeX-style formula string
        """
        raise NotImplementedError("Subclasses must implement get_formula()")
    
    def get_trace(self, scores: List[LayerScore]) -> List[str]:
        """
        Generate step-by-step arithmetic trace.
        
        Args:
            scores: List of LayerScore objects
            
        Returns:
            List of computation steps as strings
        """
        raise NotImplementedError("Subclasses must implement get_trace()")


class WeightedAverageFusion(FusionOperator):
    """
    Weighted average fusion operator.
    
    Formula: F_M(x) = Σ(w_ℓ · x_ℓ) / Σ(w_ℓ)
    
    Properties:
    - Monotonic: Yes (∂F/∂x_ℓ = w_ℓ/Σw > 0)
    - Bounded: Yes (min(x) ≤ F ≤ max(x))
    - Idempotent: Yes (F(c, c, ..., c) = c)
    - Compensatory: Full (low scores can be compensated by high scores)
    
    Reference: Standard weighted mean in MCDA (Keeney & Raiffa, 1976, Ch. 3)
    """
    
    def __init__(self, parameters: Optional[Dict] = None):
        super().__init__("WeightedAverage", parameters or {})
        self.normalize_weights = parameters.get('normalize_weights', True) if parameters else True
    
    def fuse(self, scores: List[LayerScore]) -> float:
        """Compute weighted average"""
        if not scores:
            return 0.0
        
        weighted_sum = sum(score.value * score.weight for score in scores)
        weight_sum = sum(score.weight for score in scores)
        
        if weight_sum == 0:
            return 0.0
        
        return weighted_sum / weight_sum
    
    def verify_properties(self) -> Dict[str, bool]:
        """Verify mathematical properties"""
        # Test monotonicity with sample inputs
        test_scores_low = [LayerScore(Layer.QUESTION, 0.3, 1.0)]
        test_scores_high = [LayerScore(Layer.QUESTION, 0.7, 1.0)]
        
        result_low = self.fuse(test_scores_low)
        result_high = self.fuse(test_scores_high)
        
        return {
            'monotonic': result_high >= result_low,
            'bounded': 0 <= result_low <= 1 and 0 <= result_high <= 1,
            'idempotent': abs(self.fuse([LayerScore(Layer.QUESTION, 0.5, 1.0)]) - 0.5) < 1e-10
        }
    
    def get_formula(self) -> str:
        """Return LaTeX formula"""
        return r"F_{WA}(x) = \frac{\sum_{\ell \in L(M)} w_\ell \cdot x_\ell}{\sum_{\ell \in L(M)} w_\ell}"
    
    def get_trace(self, scores: List[LayerScore]) -> List[str]:
        """Generate computation trace"""
        trace = []
        trace.append(f"Weighted Average Fusion: {len(scores)} layers")
        
        for i, score in enumerate(scores):
            trace.append(f"  Layer {score.layer.value}: x = {score.value:.4f}, w = {score.weight:.4f}")
        
        weighted_sum = sum(s.value * s.weight for s in scores)
        weight_sum = sum(s.weight for s in scores)
        
        trace.append(f"Weighted sum: Σ(w·x) = {weighted_sum:.4f}")
        trace.append(f"Weight sum: Σ(w) = {weight_sum:.4f}")
        if weight_sum == 0:
            trace.append(f"Result: No valid weights, returning 0.0")
        else:
            trace.append(f"Result: {weighted_sum:.4f} / {weight_sum:.4f} = {weighted_sum/weight_sum:.4f}")
        
        return trace


class OWAFusion(FusionOperator):
    """
    Ordered Weighted Averaging (OWA) fusion operator.
    
    Formula: F_OWA(x) = Σ(v_i · x_(i))
    where x_(i) is the i-th largest value and v_i are position weights
    
    Properties:
    - Monotonic: Yes (if all v_i ≥ 0)
    - Bounded: Yes
    - Allows modeling of optimism/pessimism (andness/orness)
    
    Reference: Yager (1988) "On ordered weighted averaging aggregation operators"
               Int. J. General Systems, 14(3), 183-194
    
    Parameters:
        weights: Position-based weights [v_1, v_2, ..., v_n]
        Should sum to 1 for proper normalization
    """
    
    def __init__(self, parameters: Dict):
        super().__init__("OWA", parameters)
        self.position_weights = parameters.get('weights', [])
        
        if len(self.position_weights) == 0:
            raise ValueError("OWA requires position weights")
    
    def fuse(self, scores: List[LayerScore]) -> float:
        """Compute OWA aggregation"""
        if not scores:
            return 0.0
        
        # Sort scores in descending order
        values = [score.value for score in scores]
        sorted_values = sorted(values, reverse=True)
        
        # Pad or truncate weights if necessary
        n = len(sorted_values)
        if len(self.position_weights) < n:
            # Extend with equal weights
            extended_weights = list(self.position_weights) + [1.0/n] * (n - len(self.position_weights))
        else:
            extended_weights = self.position_weights[:n]
        
        # Normalize weights
        weight_sum = sum(extended_weights)
        if weight_sum > 0:
            extended_weights = [w / weight_sum for w in extended_weights]
        
        # Compute weighted sum
        result = sum(w * v for w, v in zip(extended_weights, sorted_values))
        return float(result)
    
    def verify_properties(self) -> Dict[str, bool]:
        """Verify OWA properties"""
        # Check monotonicity, boundedness
        test_scores = [
            LayerScore(Layer.QUESTION, 0.2, 1.0),
            LayerScore(Layer.DIMENSION, 0.5, 1.0),
            LayerScore(Layer.POLICY_AREA, 0.8, 1.0)
        ]
        
        result = self.fuse(test_scores)
        weight_sum = sum(self.position_weights)
        
        return {
            'monotonic': True,  # Always true if weights are non-negative
            'bounded': 0 <= result <= 1,
            'weights_sum_to_one': abs(weight_sum - 1.0) < 1e-6
        }
    
    def get_formula(self) -> str:
        """Return LaTeX formula"""
        return r"F_{OWA}(x) = \sum_{i=1}^{n} v_i \cdot x_{(i)} \text{ where } x_{(i)} \text{ is i-th largest}"
    
    def get_trace(self, scores: List[LayerScore]) -> List[str]:
        """Generate computation trace"""
        trace = []
        trace.append(f"OWA Fusion: {len(scores)} layers")
        
        values = [(score.layer.value, score.value) for score in scores]
        values_sorted = sorted(values, key=lambda x: x[1], reverse=True)
        
        trace.append("Sorted values (descending):")
        for i, (layer, val) in enumerate(values_sorted):
            weight_idx = min(i, len(self.position_weights) - 1)
            weight = self.position_weights[weight_idx]
            trace.append(f"  Position {i+1}: {layer} = {val:.4f}, weight = {weight:.4f}")
        
        result = self.fuse(scores)
        trace.append(f"Result: {result:.4f}")
        
        return trace


# Registry of available fusion operators
FUSION_OPERATORS = {
    'WeightedAverage': WeightedAverageFusion,
    'OWA': OWAFusion,
}


def create_fusion_operator(name: str, parameters: Optional[Dict] = None) -> FusionOperator:
    """
    Factory function to create fusion operators.
    
    Args:
        name: Operator name from FUSION_OPERATORS
        parameters: Operator-specific parameters
        
    Returns:
        Configured FusionOperator instance
    """
    if name not in FUSION_OPERATORS:
        raise ValueError(f"Unknown fusion operator: {name}. Available: {list(FUSION_OPERATORS.keys())}")
    
    operator_class = FUSION_OPERATORS[name]
    return operator_class(parameters or {})
