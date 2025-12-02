"""Orchestrator utilities with contract validation on import."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .questionnaire import CanonicalQuestionnaire

from ..types import ChunkData, PreprocessedDocument, Provenance
from .core import (
    AbortRequested,
    AbortSignal,
    Evidence,
    MethodExecutor,
    MicroQuestionRun,
    Orchestrator,
    PhaseInstrumentation,
    PhaseResult,
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
    "ChunkData",
    "Provenance",
    "Evidence",
    "AbortSignal",
    "AbortRequested",
    "ResourceLimits",
    "PhaseInstrumentation",
    "PhaseResult",
    "MicroQuestionRun",
    "ScoredMicroQuestion",
]
