"""
Core Module Contracts - Type-safe API boundaries for pure library modules.

This module defines InputContract and OutputContract TypedDicts for each
core module to establish clear API boundaries and enable dependency injection.

Architectural Principles:
- Core modules receive all data via InputContract parameters
- Core modules return data via OutputContract structures
- No I/O operations within core modules
- All I/O happens in orchestrator/factory.py
- Type-safe contracts with strict typing

Version: 1.1.0
Schema Version: sem-1.0 (initial stable release)
Status: Active - Runtime validation available in contracts_runtime.py
"""

from typing import Any, TypedDict

try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python 3.9-3.10

# ============================================================================
# ANALYZER_ONE.PY CONTRACTS
# ============================================================================

class SemanticAnalyzerInputContract(TypedDict):
    """Input contract for SemanticAnalyzer methods.

    Example:
        {
            "text": "El plan de desarrollo municipal...",
            "segments": ["Segment 1", "Segment 2"],
            "ontology_params": {"domain": "municipal"}
        }
    """
    text: str
    segments: NotRequired[list[str]]
    ontology_params: NotRequired[dict[str, Any]]

class SemanticAnalyzerOutputContract(TypedDict):
    """Output contract for SemanticAnalyzer methods."""
    semantic_cube: dict[str, Any]
    coherence_score: float
    complexity_score: float
    domain_classification: dict[str, float]

# ============================================================================
# DERECK_BEACH.PY CONTRACTS
# ============================================================================

class CDAFFrameworkInputContract(TypedDict):
    """Input contract for CDAFFramework (Causal Deconstruction Audit Framework)."""
    document_text: str
    plan_metadata: dict[str, Any]
    config: NotRequired[dict[str, Any]]

class CDAFFrameworkOutputContract(TypedDict):
    """Output contract for CDAFFramework."""
    causal_mechanisms: list[dict[str, Any]]
    evidential_tests: dict[str, Any]
    bayesian_inference: dict[str, Any]
    audit_results: dict[str, Any]

# ============================================================================
# FINANCIERO_VIABILIDAD_TABLAS.PY CONTRACTS
# ============================================================================

class PDETAnalyzerInputContract(TypedDict):
    """Input contract for PDET (Programas de Desarrollo con Enfoque Territorial) Analyzer."""
    document_content: str
    extract_tables: NotRequired[bool]
    config: NotRequired[dict[str, Any]]

class PDETAnalyzerOutputContract(TypedDict):
    """Output contract for PDET Analyzer."""
    extracted_tables: list[dict[str, Any]]
    financial_indicators: dict[str, float]
    viability_score: float
    quality_scores: dict[str, float]

# ============================================================================
# TEORIA_CAMBIO.PY CONTRACTS
# ============================================================================

class TeoriaCambioInputContract(TypedDict):
    """Input contract for Theory of Change analysis."""
    document_text: str
    strategic_goals: NotRequired[list[str]]
    config: NotRequired[dict[str, Any]]

class TeoriaCambioOutputContract(TypedDict):
    """Output contract for Theory of Change analysis."""
    causal_dag: dict[str, Any]
    validation_results: dict[str, Any]
    monte_carlo_results: NotRequired[dict[str, Any]]
    graph_visualizations: NotRequired[list[dict[str, Any]]]

# ============================================================================
# CONTRADICTION_DETECCION.PY CONTRACTS
# ============================================================================

class ContradictionDetectorInputContract(TypedDict):
    """Input contract for PolicyContradictionDetector."""
    text: str
    plan_name: str
    dimension: NotRequired[str]  # PolicyDimension enum value
    config: NotRequired[dict[str, Any]]

class ContradictionDetectorOutputContract(TypedDict):
    """Output contract for PolicyContradictionDetector."""
    contradictions: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    temporal_conflicts: list[dict[str, Any]]
    severity_scores: dict[str, float]

# ============================================================================
# EMBEDDING_POLICY.PY CONTRACTS
# ============================================================================

class EmbeddingPolicyInputContract(TypedDict):
    """Input contract for embedding-based policy analysis."""
    text: str
    dimensions: NotRequired[list[str]]
    model_config: NotRequired[dict[str, Any]]

class EmbeddingPolicyOutputContract(TypedDict):
    """Output contract for embedding policy analysis."""
    embeddings: list[list[float]]
    similarity_scores: dict[str, float]
    bayesian_evaluation: dict[str, Any]
    policy_metrics: dict[str, float]

# ============================================================================
# SEMANTIC_CHUNKING_POLICY.PY CONTRACTS
# ============================================================================

class SemanticChunkingInputContract(TypedDict):
    """Input contract for semantic chunking and policy document analysis."""
    text: str
    preserve_structure: NotRequired[bool]
    config: NotRequired[dict[str, Any]]

class SemanticChunkingOutputContract(TypedDict):
    """Output contract for semantic chunking."""
    chunks: list[dict[str, Any]]
    causal_dimensions: dict[str, dict[str, Any]]
    key_excerpts: dict[str, list[str]]
    summary: dict[str, Any]

# ============================================================================
# POLICY_PROCESSOR.PY CONTRACTS
# ============================================================================

class PolicyProcessorInputContract(TypedDict):
    """Input contract for IndustrialPolicyProcessor."""
    data: Any
    text: str
    sentences: NotRequired[list[str]]
    tables: NotRequired[list[dict[str, Any]]]
    config: NotRequired[dict[str, Any]]

class PolicyProcessorOutputContract(TypedDict):
    """Output contract for IndustrialPolicyProcessor."""
    processed_data: dict[str, Any]
    evidence_bundles: list[dict[str, Any]]
    bayesian_scores: dict[str, float]
    matched_patterns: list[dict[str, Any]]

# ============================================================================
# SHARED DATA STRUCTURES
# ============================================================================

class DocumentData(TypedDict):
    """Standard document data structure from saaaaaa.core.orchestrator.

    This is what the orchestrator/factory provides to core modules.
    """
    raw_text: str
    sentences: list[str]
    tables: list[dict[str, Any]]
    metadata: dict[str, Any]

__all__ = [
    # Analyzer_one
    'SemanticAnalyzerInputContract',
    'SemanticAnalyzerOutputContract',

    # derek_beach
    'CDAFFrameworkInputContract',
    'CDAFFrameworkOutputContract',

    # financiero_viabilidad_tablas
    'PDETAnalyzerInputContract',
    'PDETAnalyzerOutputContract',

    # teoria_cambio
    'TeoriaCambioInputContract',
    'TeoriaCambioOutputContract',

    # contradiction_deteccion
    'ContradictionDetectorInputContract',
    'ContradictionDetectorOutputContract',

    # embedding_policy
    'EmbeddingPolicyInputContract',
    'EmbeddingPolicyOutputContract',

    # semantic_chunking_policy
    'SemanticChunkingInputContract',
    'SemanticChunkingOutputContract',

    # policy_processor
    'PolicyProcessorInputContract',
    'PolicyProcessorOutputContract',

    # Shared
    'DocumentData',
]
