"""Orchestrator utilities with contract validation on import."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .questionnaire import CanonicalQuestionnaire

# Import core classes from the refactored package
from .core import (
    AbortRequested,
    AbortSignal,
    Evidence,
    MethodExecutor,
    MicroQuestionRun,
    Orchestrator,
    PhaseInstrumentation,
    PhaseResult,
    PreprocessedDocument,
    ResourceLimits,
    ScoredMicroQuestion,
)
from .evidence_registry import (
    EvidenceRecord,
    EvidenceRegistry,
    ProvenanceDAG,
    ProvenanceNode,
    get_global_registry,
)

__all__ = [
    "EvidenceRecord",
    "EvidenceRegistry",
    "ProvenanceDAG",
    "ProvenanceNode",
    "get_global_registry",
    "Orchestrator",
    "MethodExecutor",
    "PreprocessedDocument",
    "Evidence",
    "AbortSignal",
    "AbortRequested",
    "ResourceLimits",
    "PhaseInstrumentation",
    "PhaseResult",
    "MicroQuestionRun",
    "ScoredMicroQuestion",
]
