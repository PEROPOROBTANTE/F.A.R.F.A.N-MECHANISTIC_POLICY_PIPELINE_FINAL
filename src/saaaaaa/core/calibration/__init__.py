"""
SAAAAAA Calibration System.

This package implements the 7-layer method calibration framework:
- @b (Base): Intrinsic method quality
- @u (Unit): PDT quality
- @q, @d, @p (Contextual): Method-context compatibility
- @C (Congruence): Method ensemble validation
- @chain (Chain): Data flow integrity
- @m (Meta): Governance and observability

Final scores are produced via Choquet 2-Additive aggregation.
"""

from .base_layer import BaseLayerEvaluator
from .chain_layer import ChainLayerEvaluator
from .choquet_aggregator import ChoquetAggregator
from .compatibility import (
    CompatibilityRegistry,
    ContextualLayerEvaluator,
)
from .config import (
    DEFAULT_CALIBRATION_CONFIG,
    CalibrationSystemConfig,
    ChoquetAggregationConfig,
    MetaLayerConfig,
    UnitLayerConfig,
)
from .congruence_layer import CongruenceLayerEvaluator
from .data_structures import (
    CalibrationResult,
    CalibrationSubject,
    CompatibilityMapping,
    ContextTuple,
    InteractionTerm,
    LayerID,
    LayerScore,
)
from .meta_layer import MetaLayerEvaluator
from .orchestrator import CalibrationOrchestrator
from .pdt_structure import PDTStructure
from .validator import (
    CalibrationValidator,
    ValidationDecision,
    ValidationResult,
    ValidationReport,
    FailureReason,
)

# Import protocols for type checking
from .protocols import (
    BaseLayerEvaluatorProtocol,
    ChainLayerEvaluatorProtocol,
    CongruenceLayerEvaluatorProtocol,
    ContextualLayerEvaluatorProtocol,
    LayerEvaluator,
    MetaLayerEvaluatorProtocol,
    UnitLayerEvaluatorProtocol,
    validate_evaluator_protocol,
)
from .unit_layer import UnitLayerEvaluator

__all__ = [
    # Data structures
    "LayerID",
    "LayerScore",
    "ContextTuple",
    "CalibrationSubject",
    "CompatibilityMapping",
    "InteractionTerm",
    "CalibrationResult",
    "PDTStructure",
    # Configuration
    "UnitLayerConfig",
    "MetaLayerConfig",
    "ChoquetAggregationConfig",
    "CalibrationSystemConfig",
    "DEFAULT_CALIBRATION_CONFIG",
    # Layer Evaluators
    "BaseLayerEvaluator",
    "UnitLayerEvaluator",
    "CompatibilityRegistry",
    "ContextualLayerEvaluator",
    "CongruenceLayerEvaluator",
    "ChainLayerEvaluator",
    "MetaLayerEvaluator",
    # Aggregation & Orchestration
    "ChoquetAggregator",
    "CalibrationOrchestrator",
    # Validation
    "CalibrationValidator",
    "ValidationDecision",
    "ValidationResult",
    "ValidationReport",
    "FailureReason",
    # Protocols
    "LayerEvaluator",
    "BaseLayerEvaluatorProtocol",
    "UnitLayerEvaluatorProtocol",
    "ContextualLayerEvaluatorProtocol",
    "CongruenceLayerEvaluatorProtocol",
    "ChainLayerEvaluatorProtocol",
    "MetaLayerEvaluatorProtocol",
    "validate_evaluator_protocol",
]
