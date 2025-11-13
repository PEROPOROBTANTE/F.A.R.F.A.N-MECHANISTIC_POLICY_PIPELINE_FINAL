"""Core-layer contract aliases.

This module provides stable import paths for TypedDict contracts used across
core orchestration code.  The actual contract definitions live in
``saaaaaa.utils.core_contracts`` which centralises documentation and runtime
validation.  Re-exporting them here keeps core modules decoupled from the
utilities package and prevents circular imports when infrastructure code wants
to consume the same contracts.
"""

from saaaaaa.utils.core_contracts import (
    CDAFFrameworkInputContract,
    CDAFFrameworkOutputContract,
    ContradictionDetectorInputContract,
    ContradictionDetectorOutputContract,
    DocumentData,
    EmbeddingPolicyInputContract,
    EmbeddingPolicyOutputContract,
    PDETAnalyzerInputContract,
    PDETAnalyzerOutputContract,
    PolicyProcessorInputContract,
    PolicyProcessorOutputContract,
    SemanticAnalyzerInputContract,
    SemanticAnalyzerOutputContract,
    SemanticChunkingInputContract,
    SemanticChunkingOutputContract,
    TeoriaCambioInputContract,
    TeoriaCambioOutputContract,
)

__all__ = [
    "CDAFFrameworkInputContract",
    "CDAFFrameworkOutputContract",
    "ContradictionDetectorInputContract",
    "ContradictionDetectorOutputContract",
    "DocumentData",
    "EmbeddingPolicyInputContract",
    "EmbeddingPolicyOutputContract",
    "PDETAnalyzerInputContract",
    "PDETAnalyzerOutputContract",
    "PolicyProcessorInputContract",
    "PolicyProcessorOutputContract",
    "SemanticAnalyzerInputContract",
    "SemanticAnalyzerOutputContract",
    "SemanticChunkingInputContract",
    "SemanticChunkingOutputContract",
    "TeoriaCambioInputContract",
    "TeoriaCambioOutputContract",
]
