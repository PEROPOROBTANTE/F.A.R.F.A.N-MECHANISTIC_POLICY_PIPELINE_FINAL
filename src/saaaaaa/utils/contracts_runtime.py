"""
Runtime Contract Validation using Pydantic.

This module provides runtime validators for all TypedDict contracts defined
in core_contracts.py. These validators enforce:
- Value bounds and constraints
- Required vs optional fields with strict validation
- Schema versioning for backward compatibility
- Round-trip serialization guarantees

The validators mirror the TypedDict shapes exactly but add runtime enforcement.
Use these at public API boundaries and orchestrator edges.

Version: 1.0.0
Schema Version Format: sem-{major}.{minor}
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# CONFIGURATION
# ============================================================================

class StrictModel(BaseModel):
    """Base model with strict configuration for all contract validators."""

    model_config = ConfigDict(
        extra='forbid',  # Refuse unknown fields
        validate_assignment=True,
        str_strip_whitespace=True,
        validate_default=True,
        populate_by_name=True,  # Allow both field name and alias
    )

# ============================================================================
# ANALYZER_ONE.PY CONTRACTS
# ============================================================================

class SemanticAnalyzerInputModel(StrictModel):
    """Runtime validator for SemanticAnalyzerInputContract.

    Validates:
    - text is non-empty
    - schema_version follows sem-X.Y pattern
    - segments is a list of strings
    - ontology_params is a valid dict

    Example:
        >>> model = SemanticAnalyzerInputModel(
        ...     text="El plan de desarrollo municipal...",
        ...     schema_version="sem-1.0"
        ... )
    """
    text: str = Field(min_length=1, description="Document text to analyze")
    segments: list[str] = Field(
        default_factory=list,
        description="Pre-segmented text chunks"
    )
    ontology_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Domain-specific ontology parameters"
    )
    schema_version: str = Field(
        default="sem-1.0",
        pattern=r"^sem-\d+\.\d+$",
        description="Contract schema version"
    )

    @field_validator('text')
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("text must contain non-whitespace characters")
        return v

class SemanticAnalyzerOutputModel(StrictModel):
    """Runtime validator for SemanticAnalyzerOutputContract."""
    semantic_cube: dict[str, Any] = Field(description="Semantic analysis results")
    coherence_score: float = Field(ge=0.0, le=1.0, description="Coherence metric")
    complexity_score: float = Field(ge=0.0, description="Complexity metric")
    domain_classification: dict[str, float] = Field(
        description="Domain probability distribution"
    )
    schema_version: str = Field(
        default="sem-1.0",
        pattern=r"^sem-\d+\.\d+$"
    )

    @field_validator('domain_classification')
    @classmethod
    def validate_probabilities(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all domain probabilities are in [0, 1]."""
        for domain, prob in v.items():
            if not (0.0 <= prob <= 1.0):
                raise ValueError(f"Probability for {domain} must be in [0, 1], got {prob}")
        return v

# ============================================================================
# DERECK_BEACH.PY CONTRACTS
# ============================================================================

class CDAFFrameworkInputModel(StrictModel):
    """Runtime validator for CDAFFrameworkInputContract."""
    document_text: str = Field(min_length=1, description="Document to analyze")
    plan_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Metadata about the plan"
    )
    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Framework configuration"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class CDAFFrameworkOutputModel(StrictModel):
    """Runtime validator for CDAFFrameworkOutputContract."""
    causal_mechanisms: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Identified causal mechanisms"
    )
    evidential_tests: dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical test results"
    )
    bayesian_inference: dict[str, Any] = Field(
        default_factory=dict,
        description="Bayesian analysis results"
    )
    audit_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit findings and recommendations"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# FINANCIERO_VIABILIDAD_TABLAS.PY CONTRACTS
# ============================================================================

class PDETAnalyzerInputModel(StrictModel):
    """Runtime validator for PDETAnalyzerInputContract."""
    document_content: str = Field(min_length=1, description="Document content")
    extract_tables: bool = Field(default=True, description="Whether to extract tables")
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration")
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class PDETAnalyzerOutputModel(StrictModel):
    """Runtime validator for PDETAnalyzerOutputContract."""
    extracted_tables: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted financial tables"
    )
    financial_indicators: dict[str, float] = Field(
        default_factory=dict,
        description="Calculated financial metrics"
    )
    viability_score: float = Field(
        ge=0.0, le=1.0,
        description="Overall viability score"
    )
    quality_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Quality assessment scores"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# TEORIA_CAMBIO.PY CONTRACTS
# ============================================================================

class TeoriaCambioInputModel(StrictModel):
    """Runtime validator for TeoriaCambioInputContract."""
    document_text: str = Field(min_length=1, description="Document to analyze")
    strategic_goals: list[str] = Field(
        default_factory=list,
        description="Identified strategic goals"
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration")
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class TeoriaCambioOutputModel(StrictModel):
    """Runtime validator for TeoriaCambioOutputContract."""
    causal_dag: dict[str, Any] = Field(
        default_factory=dict,
        description="Causal directed acyclic graph"
    )
    validation_results: dict[str, Any] = Field(
        default_factory=dict,
        description="Model validation results"
    )
    monte_carlo_results: dict[str, Any] | None = Field(
        default=None,
        description="Monte Carlo simulation results"
    )
    graph_visualizations: list[dict[str, Any]] | None = Field(
        default=None,
        description="Graph visualization data"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# CONTRADICTION_DETECCION.PY CONTRACTS
# ============================================================================

class ContradictionDetectorInputModel(StrictModel):
    """Runtime validator for ContradictionDetectorInputContract."""
    text: str = Field(min_length=1, description="Text to analyze for contradictions")
    plan_name: str = Field(min_length=1, description="Name of the plan")
    dimension: str | None = Field(
        default=None,
        description="PolicyDimension enum value"
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration")
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class ContradictionDetectorOutputModel(StrictModel):
    """Runtime validator for ContradictionDetectorOutputContract."""
    contradictions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Detected contradictions"
    )
    confidence_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Confidence in each detection"
    )
    temporal_conflicts: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Temporal inconsistencies"
    )
    severity_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Severity ratings"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# EMBEDDING_POLICY.PY CONTRACTS
# ============================================================================

class EmbeddingPolicyInputModel(StrictModel):
    """Runtime validator for EmbeddingPolicyInputContract."""
    text: str = Field(min_length=1, description="Text to embed")
    dimensions: list[str] = Field(
        default_factory=list,
        description="Policy dimensions to analyze"
    )
    embedding_model_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Embedding model configuration",
        alias="model_config"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class EmbeddingPolicyOutputModel(StrictModel):
    """Runtime validator for EmbeddingPolicyOutputContract."""
    embeddings: list[list[float]] = Field(
        default_factory=list,
        description="Generated embeddings"
    )
    similarity_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Similarity metrics"
    )
    bayesian_evaluation: dict[str, Any] = Field(
        default_factory=dict,
        description="Bayesian evaluation results"
    )
    policy_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Policy-specific metrics"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# SEMANTIC_CHUNKING_POLICY.PY CONTRACTS
# ============================================================================

class SemanticChunkingInputModel(StrictModel):
    """Runtime validator for SemanticChunkingInputContract."""
    text: str = Field(min_length=1, description="Text to chunk")
    preserve_structure: bool = Field(
        default=True,
        description="Whether to preserve document structure"
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration")
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class SemanticChunkingOutputModel(StrictModel):
    """Runtime validator for SemanticChunkingOutputContract."""
    chunks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Semantic chunks"
    )
    causal_dimensions: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Causal dimension analysis"
    )
    key_excerpts: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Key excerpts by category"
    )
    summary: dict[str, Any] = Field(
        default_factory=dict,
        description="Summary statistics"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# POLICY_PROCESSOR.PY CONTRACTS
# ============================================================================

class PolicyProcessorInputModel(StrictModel):
    """Runtime validator for PolicyProcessorInputContract."""
    data: Any = Field(description="Raw data to process")
    text: str = Field(min_length=1, description="Text content")
    sentences: list[str] = Field(
        default_factory=list,
        description="Pre-segmented sentences"
    )
    tables: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Extracted tables"
    )
    config: dict[str, Any] = Field(default_factory=dict, description="Configuration")
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

class PolicyProcessorOutputModel(StrictModel):
    """Runtime validator for PolicyProcessorOutputContract."""
    processed_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Processed results"
    )
    evidence_bundles: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Evidence bundles"
    )
    bayesian_scores: dict[str, float] = Field(
        default_factory=dict,
        description="Bayesian scores"
    )
    matched_patterns: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Matched patterns"
    )
    schema_version: str = Field(default="sem-1.0", pattern=r"^sem-\d+\.\d+$")

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Base
    'StrictModel',

    # Analyzer_one
    'SemanticAnalyzerInputModel',
    'SemanticAnalyzerOutputModel',

    # derek_beach
    'CDAFFrameworkInputModel',
    'CDAFFrameworkOutputModel',

    # financiero_viabilidad_tablas
    'PDETAnalyzerInputModel',
    'PDETAnalyzerOutputModel',

    # teoria_cambio
    'TeoriaCambioInputModel',
    'TeoriaCambioOutputModel',

    # contradiction_deteccion
    'ContradictionDetectorInputModel',
    'ContradictionDetectorOutputModel',

    # embedding_policy
    'EmbeddingPolicyInputModel',
    'EmbeddingPolicyOutputModel',

    # semantic_chunking_policy
    'SemanticChunkingInputModel',
    'SemanticChunkingOutputModel',

    # policy_processor
    'PolicyProcessorInputModel',
    'PolicyProcessorOutputModel',
]
