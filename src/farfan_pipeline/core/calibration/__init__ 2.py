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

from farfan_pipeline.core.calibration.data_structures import (
    LayerID,
    LayerScore,
    ContextTuple,
    CalibrationSubject,
    CompatibilityMapping,
    InteractionTerm,
    CalibrationResult,
)

from farfan_pipeline.core.calibration.config import (
    UnitLayerConfig,
    MetaLayerConfig,
    ChoquetAggregationConfig,
    CalibrationSystemConfig,
    DEFAULT_CALIBRATION_CONFIG,
)

from farfan_pipeline.core.calibration.pdt_structure import PDTStructure

from farfan_pipeline.core.calibration.compatibility import (
    CompatibilityRegistry,
    ContextualLayerEvaluator,
)

from farfan_pipeline.core.calibration.unit_layer import UnitLayerEvaluator
from farfan_pipeline.core.calibration.congruence_layer import CongruenceLayerEvaluator
from farfan_pipeline.core.calibration.chain_layer import ChainLayerEvaluator
from farfan_pipeline.core.calibration.meta_layer import MetaLayerEvaluator
from farfan_pipeline.core.calibration.choquet_aggregator import ChoquetAggregator
from farfan_pipeline.core.calibration.orchestrator import CalibrationOrchestrator

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
    "UnitLayerEvaluator",
    "CompatibilityRegistry",
    "ContextualLayerEvaluator",
    "CongruenceLayerEvaluator",
    "ChainLayerEvaluator",
    "MetaLayerEvaluator",
    # Aggregation & Orchestration
    "ChoquetAggregator",
    "CalibrationOrchestrator",
]
