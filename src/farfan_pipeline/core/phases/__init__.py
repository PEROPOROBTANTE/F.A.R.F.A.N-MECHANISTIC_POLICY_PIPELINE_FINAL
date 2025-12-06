"""
Canonical Phase Implementations - F.A.R.F.A.N Pipeline
======================================================

This package contains the canonical implementations of all pipeline phases:

Phase 0: Input Validation (Raw input → Validated CanonicalInput)
Phase 1: SPC Ingestion (CanonicalInput → CanonPolicyPackage)
Phase 2: Micro Questions (PreprocessedDocument → Phase2Result)
Phase 3: Chunk Routing (Phase2Result → Phase3Result)
Phase 6: Schema Validation (Raw data → Validated schemas)
Phase 7: Task Construction (Validated schemas → ExecutableTask set)
Phase 8: Execution Plan Assembly (ExecutableTask set → ExecutionPlan)

All phases follow the PhaseContract protocol with:
- Explicit input/output contracts
- Mandatory field validation
- Error propagation semantics
- Deterministic execution
- Provenance tracking
"""

from farfan_pipeline.core.phases.phase0_input_validation import (
    CanonicalInput,
    Phase0Input,
    Phase0ValidationContract,
)
from farfan_pipeline.core.phases.phase1_spc_ingestion import (
    Phase1SPCIngestionContract,
)
from farfan_pipeline.core.phases.phase2_types import (
    Phase2QuestionResult,
    Phase2Result,
    validate_phase2_result,
)
from farfan_pipeline.core.phases.phase3_chunk_routing import (
    ChunkRoutingResult,
    Phase3ChunkRoutingContract,
    Phase3Input,
    Phase3Result,
)
from src.farfan_pipeline.core.phases.phase6_schema_validation import (
    Phase6SchemaValidationOutput,
    ValidatedChunkSchema,
    ValidatedQuestionSchema,
    phase6_schema_validation,
)
from src.farfan_pipeline.core.phases.phase7_task_construction import (
    Phase7TaskConstructionOutput,
    phase7_task_construction,
)
from src.farfan_pipeline.core.phases.phase8_execution_plan import (
    ExecutionPlan,
    Phase8ExecutionPlanOutput,
    phase8_execution_plan_assembly,
)
from farfan_pipeline.core.phases.phase_orchestrator import (
    PhaseOrchestrator,
    PipelineResult,
)
from farfan_pipeline.core.phases.phase_protocol import (
    ContractValidationResult,
    PhaseArtifact,
    PhaseContract,
    PhaseInvariant,
    PhaseManifestBuilder,
    PhaseMetadata,
    compute_contract_hash,
)

__all__ = [
    # Phase 0
    "CanonicalInput",
    "Phase0Input",
    "Phase0ValidationContract",
    # Phase 1
    "Phase1SPCIngestionContract",
    # Phase 2
    "Phase2QuestionResult",
    "Phase2Result",
    "validate_phase2_result",
    # Phase 3
    "ChunkRoutingResult",
    "Phase3ChunkRoutingContract",
    "Phase3Input",
    "Phase3Result",
    # Phase 6
    "Phase6SchemaValidationOutput",
    "ValidatedQuestionSchema",
    "ValidatedChunkSchema",
    "phase6_schema_validation",
    # Phase 7
    "Phase7TaskConstructionOutput",
    "phase7_task_construction",
    # Phase 8
    "ExecutionPlan",
    "Phase8ExecutionPlanOutput",
    "phase8_execution_plan_assembly",
    # Orchestrator
    "PhaseOrchestrator",
    "PipelineResult",
    # Protocol
    "ContractValidationResult",
    "PhaseArtifact",
    "PhaseContract",
    "PhaseInvariant",
    "PhaseManifestBuilder",
    "PhaseMetadata",
    "compute_contract_hash",
]
