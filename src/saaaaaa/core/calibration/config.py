"""
Calibration configuration schema.

This defines ALL parameters needed for the 7-layer calibration system.

Design Principles:
1. Single Source of Truth: All parameters defined here
2. Immutability: All configs are frozen dataclasses
3. Validation: __post_init__ enforces mathematical constraints
4. Hashability: Support deterministic config hashing for SIN_CARRETA
5. Environment Support: Can load from env vars
"""
from dataclasses import dataclass, field
from typing import Literal
import hashlib
import json
import os


@dataclass(frozen=True)
class UnitLayerConfig:
    """
    Configuration for @u (Unit/PDT Quality Layer).
    
    Theoretical Formula:
        U(pdt) = aggregator(w_S·S, w_M·M, w_I·I, w_P·P)
    
    Where:
        S = Structural compliance
        M = Mandatory sections ratio
        I = Indicator quality
        P = PPI completeness
    
    with hard gates that can force U = 0.0.
    """
    # ========================================
    # Component Weights (MUST sum to 1.0)
    # ========================================
    w_S: float = 0.25  # Structural compliance weight
    w_M: float = 0.25  # Mandatory sections weight
    w_I: float = 0.25  # Indicator quality weight
    w_P: float = 0.25  # PPI completeness weight
    
    # ========================================
    # Aggregation Method
    # ========================================
    aggregation_type: Literal["geometric_mean", "harmonic_mean", "weighted_average"] = "geometric_mean"
    
    # ========================================
    # Hard Gates (any failure → U = 0.0)
    # ========================================
    require_ppi_presence: bool = True
    require_indicator_matrix: bool = True
    min_structural_compliance: float = 0.5  # S must be >= this or U = 0.0
    
    # ========================================
    # Anti-Gaming Thresholds
    # ========================================
    max_placeholder_ratio: float = 0.10  # Max proportion of "S/D" placeholders
    min_unique_values_ratio: float = 0.5  # Min proportion of unique cost values in PPI
    min_number_density: float = 0.02  # Min proportion of numeric tokens in critical sections
    gaming_penalty_cap: float = 0.3  # Maximum total penalty
    
    # ========================================
    # S (Structural Compliance) Sub-Weights
    # ========================================
    w_block_coverage: float = 0.5   # Block presence/quality
    w_hierarchy: float = 0.25       # Header numbering validity
    w_order: float = 0.25           # Sequential order correctness
    
    # Block requirements
    min_block_tokens: int = 50      # Min tokens for block to count as "present"
    min_block_numbers: int = 1      # Min numbers for block validity
    
    # Hierarchy thresholds
    hierarchy_excellent_threshold: float = 0.8  # ≥80% valid → score 1.0
    hierarchy_acceptable_threshold: float = 0.5  # ≥50% valid → score 0.5
    
    # ========================================
    # M (Mandatory Sections) Requirements
    # ========================================
    # Section-specific minimums (can be overridden per section type)
    diagnostico_min_tokens: int = 500
    diagnostico_min_keywords: int = 3
    diagnostico_min_numbers: int = 5
    diagnostico_min_sources: int = 2
    
    estrategica_min_tokens: int = 400
    estrategica_min_keywords: int = 3
    estrategica_min_numbers: int = 3
    
    ppi_section_min_tokens: int = 300
    ppi_section_min_keywords: int = 2
    ppi_section_min_numbers: int = 10
    
    seguimiento_min_tokens: int = 200
    seguimiento_min_keywords: int = 2
    seguimiento_min_numbers: int = 2
    
    marco_normativo_min_tokens: int = 150
    marco_normativo_min_keywords: int = 1
    
    # Critical sections get double weight
    critical_sections_weight: float = 2.0
    
    # ========================================
    # I (Indicator Quality) Configuration
    # ========================================
    w_i_struct: float = 0.4   # Structure/completeness
    w_i_link: float = 0.3     # Traceability
    w_i_logic: float = 0.3    # Chain coherence
    
    # Hard gate for indicator structure
    i_struct_hard_gate: float = 0.7  # If I_struct < this, I = 0.0
    
    # Structure sub-parameters
    i_critical_fields_weight: float = 2.0  # Weight for critical fields
    i_placeholder_penalty_multiplier: float = 3.0  # Penalty multiplier for "S/D"
    
    # Link sub-parameters
    i_fuzzy_match_threshold: float = 0.85  # Levenshtein threshold for traceability
    i_mga_code_pattern: str = r"^\d{7}$"  # Valid MGA code format
    
    # Logic sub-parameters
    i_valid_lb_year_min: int = 2019  # Min valid baseline year
    i_valid_lb_year_max: int = 2024  # Max valid baseline year
    i_valid_meta_year_min: int = 2024  # Min valid target year
    i_valid_meta_year_max: int = 2027  # Max valid target year
    
    # ========================================
    # P (PPI Completeness) Configuration
    # ========================================
    w_p_presence: float = 0.2      # Matrix exists
    w_p_structure: float = 0.4     # Field completeness
    w_p_consistency: float = 0.4   # Accounting closure
    
    # Hard gate for PPI structure
    p_struct_hard_gate: float = 0.7  # If P_struct < this, P = 0.0
    
    # Structure requirements
    p_min_nonzero_rows: float = 0.8  # Min proportion of rows with non-zero costs
    
    # Consistency tolerances
    p_accounting_tolerance: float = 0.01  # 1% tolerance for sum checks
    p_traceability_threshold: float = 0.80  # Min fuzzy match for strategic link
    
    def __post_init__(self):
        """Validate configuration constraints."""
        # Check top-level weights sum to 1.0
        weight_sum = self.w_S + self.w_M + self.w_I + self.w_P
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"Unit layer weights (w_S + w_M + w_I + w_P) must sum to 1.0, "
                f"got {weight_sum}"
            )
        
        # Check all weights are non-negative
        for attr in ['w_S', 'w_M', 'w_I', 'w_P']:
            value = getattr(self, attr)
            if value < 0:
                raise ValueError(f"{attr} must be non-negative, got {value}")
        
        # Check S sub-weights sum to 1.0
        s_weight_sum = self.w_block_coverage + self.w_hierarchy + self.w_order
        if abs(s_weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"S sub-weights must sum to 1.0, got {s_weight_sum}"
            )
        
        # Check I sub-weights sum to 1.0
        i_weight_sum = self.w_i_struct + self.w_i_link + self.w_i_logic
        if abs(i_weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"I sub-weights must sum to 1.0, got {i_weight_sum}"
            )
        
        # Check P sub-weights sum to 1.0
        p_weight_sum = self.w_p_presence + self.w_p_structure + self.w_p_consistency
        if abs(p_weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"P sub-weights must sum to 1.0, got {p_weight_sum}"
            )
        
        # Validate thresholds are in [0, 1]
        for attr in ['min_structural_compliance', 'i_struct_hard_gate', 'p_struct_hard_gate']:
            value = getattr(self, attr)
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{attr} must be in [0.0, 1.0], got {value}")
    
    @classmethod
    def from_env(cls, prefix: str = "UNIT_LAYER_") -> "UnitLayerConfig":
        """
        Load configuration from environment variables.
        
        Example:
            export UNIT_LAYER_W_S=0.3
            export UNIT_LAYER_W_M=0.25
            ...
        """
        kwargs = {}
        
        # Map of env var names to field names
        env_map = {
            "W_S": "w_S",
            "W_M": "w_M",
            "W_I": "w_I",
            "W_P": "w_P",
            "AGGREGATION_TYPE": "aggregation_type",
            # Add more as needed
        }
        
        for env_key, field_name in env_map.items():
            env_value = os.getenv(f"{prefix}{env_key}")
            if env_value is not None:
                # Parse based on type
                if field_name in ["w_S", "w_M", "w_I", "w_P"]:
                    kwargs[field_name] = float(env_value)
                elif field_name == "aggregation_type":
                    kwargs[field_name] = env_value
        
        return cls(**kwargs) if kwargs else cls()


@dataclass(frozen=True)
class MetaLayerConfig:
    """
    Configuration for @m (Meta/Governance Layer).
    
    Theoretical Formula:
        x_@m = w_transp·m_transp + w_gov·m_gov + w_cost·m_cost
    
    Where:
        m_transp = Transparency (formula export, trace, logs)
        m_gov = Governance (version, config hash, signature)
        m_cost = Cost (runtime, memory)
    """
    # ========================================
    # Component Weights (MUST sum to 1.0)
    # ========================================
    w_transparency: float = 0.5
    w_governance: float = 0.4
    w_cost: float = 0.1
    
    # ========================================
    # Transparency Requirements (Boolean)
    # ========================================
    require_formula_export: bool = True
    require_full_trace: bool = True
    require_log_conformance: bool = True
    
    # ========================================
    # Governance Requirements (Boolean)
    # ========================================
    require_tagged_version: bool = True
    require_config_hash_match: bool = True
    require_valid_signature: bool = False  # Optional for initial rollout
    
    # ========================================
    # Cost Thresholds
    # ========================================
    # Runtime thresholds (seconds)
    threshold_fast: float = 1.0  # Excellent performance
    threshold_acceptable: float = 5.0  # Acceptable performance
    # If runtime > threshold_acceptable → score drops to 0.5
    # If timeout or out_of_memory → score = 0.0
    
    # Memory thresholds (MB)
    threshold_memory_normal: int = 512
    threshold_memory_high: int = 1024
    
    def __post_init__(self):
        """Validate configuration."""
        weight_sum = self.w_transparency + self.w_governance + self.w_cost
        if abs(weight_sum - 1.0) > 1e-6:
            raise ValueError(
                f"Meta layer weights must sum to 1.0, got {weight_sum}"
            )


@dataclass(frozen=True)
class ChoquetAggregationConfig:
    """
    Configuration for Choquet 2-Additive aggregation.
    
    Theoretical Formula:
        Cal(I) = Σ a_ℓ·x_ℓ + Σ a_ℓk·min(x_ℓ, x_k)
    
    Where:
        - First sum: linear terms (one per layer)
        - Second sum: interaction terms (synergies between layers)
    
    Mathematical Constraint:
        Σ a_ℓ + Σ a_ℓk = 1.0 (normalization)
    """
    # ========================================
    # Linear Weights (one per layer)
    # ========================================
    # These weights were calibrated using optimization to fit historical
    # policy evaluation data, subject to the normalization constraint:
    # Σ a_ℓ + Σ a_ℓk = 1.0
    # 
    # The six decimal places reflect the precision of the optimization process.
    # To recalibrate or reproduce these values, see the calibration methodology
    # in the project documentation.
    # ========================================
    linear_weights: dict[str, float] = field(default_factory=lambda: {
        "b": 0.122951,      # Base layer (intrinsic quality)
        "u": 0.098361,      # Unit layer (PDT quality)
        "q": 0.081967,      # Question compatibility
        "d": 0.065574,      # Dimension compatibility
        "p": 0.049180,      # Policy compatibility
        "C": 0.081967,      # Congruence (ensemble)
        "chain": 0.065574,  # Chain integrity (data flow)
        "m": 0.034426,      # Meta (governance)
    })
    
    # ========================================
    # Interaction Weights (synergy terms)
    # ========================================
    # These implement the min(x_ℓ, x_k) "weakest link" principle
    interaction_weights: dict[tuple[str, str], float] = field(default_factory=lambda: {
        ("u", "chain"): 0.15,   # Plan quality × Chain integrity
        ("chain", "C"): 0.12,   # Chain integrity × Congruence
        ("q", "d"): 0.08,       # Question × Dimension
        ("d", "p"): 0.05,       # Dimension × Policy
    })
    
    # ========================================
    # Rationales (for audit trail)
    # ========================================
    interaction_rationales: dict[tuple[str, str], str] = field(default_factory=lambda: {
        ("u", "chain"): "Plan quality only matters with sound wiring",
        ("chain", "C"): "Ensemble validity requires chain integrity",
        ("q", "d"): "Question-dimension alignment synergy",
        ("d", "p"): "Dimension-policy coherence synergy",
    })
    
    def __post_init__(self):
        """Validate normalization constraint."""
        # Compute total weight
        linear_sum = sum(self.linear_weights.values())
        interaction_sum = sum(self.interaction_weights.values())
        total = linear_sum + interaction_sum
        
        # Check normalization (must equal 1.0 within numerical tolerance)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Choquet weights must sum to 1.0:\n"
                f"  Linear sum: {linear_sum:.6f}\n"
                f"  Interaction sum: {interaction_sum:.6f}\n"
                f"  Total: {total:.6f}\n"
                f"  Error: {abs(total - 1.0):.6e}"
            )
        
        # Verify all weights are non-negative
        for layer, weight in self.linear_weights.items():
            if weight < 0:
                raise ValueError(f"Linear weight for {layer} must be non-negative, got {weight}")
        
        for (l1, l2), weight in self.interaction_weights.items():
            if weight < 0:
                raise ValueError(f"Interaction weight for ({l1}, {l2}) must be non-negative, got {weight}")
    
    def compute_hash(self) -> str:
        """
        Compute deterministic hash of aggregation configuration.
        
        This is critical for the SIN_CARRETA doctrine (determinism).
        The hash must be stable across runs.
        """
        config_dict = {
            "linear": dict(sorted(self.linear_weights.items())),
            "interaction": {
                f"{k[0]}_{k[1]}": v 
                for k, v in sorted(self.interaction_weights.items())
            }
        }
        # Use separators with no spaces for deterministic JSON
        config_json = json.dumps(config_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(config_json.encode('utf-8')).hexdigest()[:16]


@dataclass(frozen=True)
class CalibrationSystemConfig:
    """
    Master configuration for the entire calibration system.
    
    This is the SINGLE SOURCE OF TRUTH for ALL calibration parameters.
    
    Usage:
        # Use defaults
        config = CalibrationSystemConfig()
        
        # Or customize
        config = CalibrationSystemConfig(
            unit_layer=UnitLayerConfig(w_S=0.3, w_M=0.25, ...),
            enable_anti_universality_check=True
        )
    """
    # ========================================
    # Layer Configurations
    # ========================================
    unit_layer: UnitLayerConfig = field(default_factory=UnitLayerConfig)
    meta_layer: MetaLayerConfig = field(default_factory=MetaLayerConfig)
    choquet: ChoquetAggregationConfig = field(default_factory=ChoquetAggregationConfig)
    
    # ========================================
    # System-Level Settings
    # ========================================
    # Anti-Universality Theorem enforcement
    enable_anti_universality_check: bool = True
    max_avg_compatibility: float = 0.9  # Threshold for universality detection
    
    # Determinism (SIN_CARRETA doctrine)
    random_seed: int = 42
    enforce_determinism: bool = True
    
    # Logging
    log_all_layer_scores: bool = True
    log_gate_failures: bool = True
    log_gaming_penalties: bool = True
    
    def compute_system_hash(self) -> str:
        """
        Compute hash of entire configuration for reproducibility.
        
        This hash is included in CalibrationResult metadata and
        proves which configuration was used.
        """
        config_dict = {
            "unit": {
                "weights": [self.unit_layer.w_S, self.unit_layer.w_M, 
                           self.unit_layer.w_I, self.unit_layer.w_P],
                "aggregation": self.unit_layer.aggregation_type,
                "gates": {
                    "ppi": self.unit_layer.require_ppi_presence,
                    "indicators": self.unit_layer.require_indicator_matrix,
                    "min_s": self.unit_layer.min_structural_compliance,
                    "i_struct": self.unit_layer.i_struct_hard_gate,
                    "p_struct": self.unit_layer.p_struct_hard_gate,
                }
            },
            "meta": {
                "weights": [self.meta_layer.w_transparency, 
                           self.meta_layer.w_governance,
                           self.meta_layer.w_cost],
            },
            "choquet": {
                "hash": self.choquet.compute_hash(),
            },
            "seed": self.random_seed,
            "anti_universality": self.enable_anti_universality_check,
        }
        config_json = json.dumps(config_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(config_json.encode('utf-8')).hexdigest()
    
    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        return {
            "system_hash": self.compute_system_hash(),
            "unit_layer": {
                "weights": {
                    "S": self.unit_layer.w_S,
                    "M": self.unit_layer.w_M,
                    "I": self.unit_layer.w_I,
                    "P": self.unit_layer.w_P,
                },
                "aggregation_type": self.unit_layer.aggregation_type,
                "hard_gates": {
                    "require_ppi": self.unit_layer.require_ppi_presence,
                    "require_indicators": self.unit_layer.require_indicator_matrix,
                    "min_structural": self.unit_layer.min_structural_compliance,
                }
            },
            "meta_layer": {
                "weights": {
                    "transparency": self.meta_layer.w_transparency,
                    "governance": self.meta_layer.w_governance,
                    "cost": self.meta_layer.w_cost,
                }
            },
            "choquet": {
                "linear_weights": self.choquet.linear_weights,
                "interaction_count": len(self.choquet.interaction_weights),
                "config_hash": self.choquet.compute_hash(),
            },
            "system": {
                "anti_universality_enabled": self.enable_anti_universality_check,
                "deterministic": self.enforce_determinism,
                "random_seed": self.random_seed,
            }
        }


# ========================================
# Default Configuration Instance
# ========================================
DEFAULT_CALIBRATION_CONFIG = CalibrationSystemConfig()
