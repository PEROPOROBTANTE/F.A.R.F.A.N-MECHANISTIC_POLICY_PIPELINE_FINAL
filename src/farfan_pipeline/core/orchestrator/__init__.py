"""Orchestrator utilities with contract validation on import."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.questionnaire import CanonicalQuestionnaire

from farfan_pipeline.core.types import ChunkData, PreprocessedDocument, Provenance
from farfan_pipeline.core.orchestrator.core import (
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
from farfan_pipeline.core.orchestrator.evidence_registry import (
    EvidenceRecord,
    EvidenceRegistry,
    ProvenanceDAG,
    ProvenanceNode,
    get_global_registry,
)
from farfan_pipeline.core.orchestrator.resource_manager import (
    AdaptiveResourceManager,
    CircuitBreaker,
    CircuitState,
    DegradationStrategy,
    ExecutorPriority,
    ResourceAllocationPolicy,
    ResourcePressureLevel,
)
from farfan_pipeline.core.orchestrator.resource_aware_executor import (
    ResourceAwareExecutor,
    ResourceConstraints,
)
from farfan_pipeline.core.orchestrator.resource_alerts import (
    AlertChannel,
    AlertSeverity,
    ResourceAlert,
    ResourceAlertManager,
)
from farfan_pipeline.core.orchestrator.resource_integration import (
    create_resource_manager,
    integrate_with_orchestrator,
    get_resource_status,
    reset_circuit_breakers,
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
    "AdaptiveResourceManager",
    "CircuitBreaker",
    "CircuitState",
    "DegradationStrategy",
    "ExecutorPriority",
    "ResourceAllocationPolicy",
    "ResourcePressureLevel",
    "ResourceAwareExecutor",
    "ResourceConstraints",
    "AlertChannel",
    "AlertSeverity",
    "ResourceAlert",
    "ResourceAlertManager",
    "create_resource_manager",
    "integrate_with_orchestrator",
    "get_resource_status",
    "reset_circuit_breakers",
]
