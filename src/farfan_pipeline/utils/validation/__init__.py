"""Validation module for pre-execution checks and preconditions."""

from .aggregation_models import (
    AggregationWeights,
    AreaAggregationConfig,
    ClusterAggregationConfig,
    DimensionAggregationConfig,
    MacroAggregationConfig,
    validate_dimension_config,
    validate_weights,
)
from .architecture_validator import (
    ArchitectureValidationResult,
    validate_architecture,
    write_validation_report,
)
from .golden_rule import GoldenRuleValidator, GoldenRuleViolation
from .schema_validator import (
    MonolithIntegrityReport,
    MonolithSchemaValidator,
    SchemaInitializationError,
    validate_monolith_schema,
)

__all__ = [
    "ArchitectureValidationResult",
    "GoldenRuleValidator",
    "GoldenRuleViolation",
    "validate_architecture",
    "write_validation_report",
    "AggregationWeights",
    "DimensionAggregationConfig",
    "AreaAggregationConfig",
    "ClusterAggregationConfig",
    "MacroAggregationConfig",
    "validate_weights",
    "validate_dimension_config",
    "MonolithSchemaValidator",
    "MonolithIntegrityReport",
    "SchemaInitializationError",
    "validate_monolith_schema",
]
