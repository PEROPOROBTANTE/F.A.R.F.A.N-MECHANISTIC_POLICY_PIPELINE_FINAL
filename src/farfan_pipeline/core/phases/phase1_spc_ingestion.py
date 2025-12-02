"""
Phase 1: SPC Ingestion - Constitutional Implementation
======================================================

This module implements Phase 1 of the canonical pipeline:
    CanonicalInput → CanonPolicyPackage

Responsibilities:
-----------------
1. Load and validate document from CanonicalInput
2. Execute 15 subfases of Strategic Chunking System
3. Generate exactly 60 chunks structured as 10 PA × 6 DIM
4. Validate quality metrics and integrity
5. Package results into CanonPolicyPackage

Input Contract:
---------------
CanonicalInput (from Phase 0):
    - document_id, pdf_path, pdf_sha256
    - questionnaire_path
    - All validation passed

Output Contract:
----------------
CanonPolicyPackage:
    - schema_version: str ("SPC-2025.1")
    - document_id: str (preserved from input)
    - chunk_graph: ChunkGraph (60 chunks, PA×DIM)
    - policy_manifest: PolicyManifest
    - quality_metrics: QualityMetrics
    - integrity_index: IntegrityIndex
    - metadata: dict

15 Subfases (Internal to Phase 1):
-----------------------------------
Subfase 0:  Language detection & model selection
Subfase 1:  Advanced preprocessing
Subfase 2:  Structural analysis & hierarchy extraction
Subfase 3:  Topic modeling & global KG construction
Subfase 4:  Structured (PA×DIM) segmentation → 60 chunks
Subfase 5:  Complete causal chain extraction
Subfase 6:  Causal integration
Subfase 7:  Deep argumentative analysis
Subfase 8:  Temporal and sequential analysis
Subfase 9:  Discourse and rhetorical analysis
Subfase 10: Multi-scale strategic integration
Subfase 11: Smart Policy Chunk generation
Subfase 12: Inter-chunk relationship enrichment
Subfase 13: Strategic integrity validation
Subfase 14: Intelligent deduplication
Subfase 15: Strategic importance ranking

Invariants:
-----------
1. chunk_count == 60 (10 PA × 6 DIM)
2. All chunks have policy_area_id (PA01-PA10)
3. All chunks have dimension_id (DIM01-DIM06)
4. quality_metrics.provenance_completeness >= 0.8
5. quality_metrics.structural_consistency >= 0.85
6. All chunks pass integrity validation

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-19
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from farfan_pipeline.core.phases.phase_protocol import (
    ContractValidationResult,
    PhaseContract,
)
from farfan_pipeline.core.phases.phase0_input_validation import CanonicalInput
from farfan_pipeline.processing.cpp_ingestion.models import CanonPolicyPackage

logger = logging.getLogger(__name__)

# Schema version for Phase 1
PHASE1_VERSION = "SPC-2025.1"

# Expected chunk count (10 PA × 6 DIM)
EXPECTED_CHUNK_COUNT = 60

# Policy Areas (PA01-PA10)
POLICY_AREAS = [
    "PA01",  # Mujeres y equidad de género
    "PA02",  # Paz, seguridad y convivencia
    "PA03",  # Ambiente y cambio climático
    "PA04",  # Derechos económicos, sociales y culturales
    "PA05",  # Víctimas y construcción de paz
    "PA06",  # Niñez, adolescencia y juventud
    "PA07",  # Tierras y territorios
    "PA08",  # Líderes y defensores de DDHH
    "PA09",  # Privadas de libertad
    "PA10",  # Migración transfronteriza
]

# Dimensions (DIM01-DIM06)
DIMENSIONS = [
    "DIM01",  # Diagnóstico y recursos
    "DIM02",  # Actividades e intervenciones
    "DIM03",  # Productos (outputs)
    "DIM04",  # Resultados (outcomes)
    "DIM05",  # Impactos de largo plazo
    "DIM06",  # Causalidad y teoría de cambio
]


# ============================================================================
# SUBFASE TRACKING
# ============================================================================


@dataclass
class SubfaseMetadata:
    """Metadata for a single subfase execution."""

    subfase_number: int
    subfase_name: str
    started_at: str
    finished_at: str | None = None
    duration_ms: float | None = None
    success: bool = False
    error: str | None = None


# ============================================================================
# OUTPUT CONTRACT VALIDATOR
# ============================================================================


class CanonPolicyPackageValidator(BaseModel):
    """Pydantic validator for CanonPolicyPackage."""

    schema_version: str = Field(description="Must be SPC-2025.1")
    document_id: str = Field(min_length=1)
    chunk_count: int = Field(ge=1, description="Number of chunks in chunk_graph")
    has_policy_manifest: bool
    has_quality_metrics: bool
    has_integrity_index: bool
    provenance_completeness: float = Field(ge=0.0, le=1.0)
    structural_consistency: float = Field(ge=0.0, le=1.0)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        """Ensure schema version is correct."""
        if v != PHASE1_VERSION:
            raise ValueError(
                f"schema_version must be '{PHASE1_VERSION}', got '{v}'"
            )
        return v

    @field_validator("chunk_count")
    @classmethod
    def validate_chunk_count(cls, v: int) -> int:
        """Validate chunk count."""
        if v != EXPECTED_CHUNK_COUNT:
            raise ValueError(
                f"Expected {EXPECTED_CHUNK_COUNT} chunks (10 PA × 6 DIM), got {v}"
            )
        return v

    @field_validator("provenance_completeness")
    @classmethod
    def validate_provenance(cls, v: float) -> float:
        """Ensure provenance completeness meets threshold."""
        if v < 0.8:
            raise ValueError(
                f"provenance_completeness must be >= 0.8, got {v:.2f}"
            )
        return v

    @field_validator("structural_consistency")
    @classmethod
    def validate_structural(cls, v: float) -> float:
        """Ensure structural consistency meets threshold."""
        if v < 0.85:
            raise ValueError(
                f"structural_consistency must be >= 0.85, got {v:.2f}"
            )
        return v


# ============================================================================
# PHASE 1 CONTRACT IMPLEMENTATION
# ============================================================================


class Phase1SPCIngestionContract(PhaseContract[CanonicalInput, CanonPolicyPackage]):
    """
    Phase 1: SPC Ingestion Contract.

    This class enforces the constitutional constraint that Phase 1:
    1. Accepts ONLY CanonicalInput (from Phase 0)
    2. Produces ONLY CanonPolicyPackage
    3. Executes all 15 subfases in order
    4. Generates exactly 60 chunks (10 PA × 6 DIM)
    5. Validates all quality metrics
    """

    def __init__(self):
        """Initialize Phase 1 contract with invariants."""
        super().__init__(phase_name="phase1_spc_ingestion")

        # Track subfases
        self.subfases: list[SubfaseMetadata] = []

        # Register invariants
        self.add_invariant(
            name="chunk_count_60",
            description="Must have exactly 60 chunks (10 PA × 6 DIM)",
            check=lambda data: len(data.chunk_graph.chunks) == EXPECTED_CHUNK_COUNT,
            error_message=f"chunk_count must be {EXPECTED_CHUNK_COUNT}",
        )

        self.add_invariant(
            name="all_chunks_have_pa",
            description="All chunks must have policy_area_id (PA01-PA10)",
            check=lambda data: all(
                chunk.policy_area_id in POLICY_AREAS
                for chunk in data.chunk_graph.chunks.values()
            ),
            error_message="All chunks must have valid policy_area_id",
        )

        self.add_invariant(
            name="all_chunks_have_dim",
            description="All chunks must have dimension_id (DIM01-DIM06)",
            check=lambda data: all(
                chunk.dimension_id in DIMENSIONS
                for chunk in data.chunk_graph.chunks.values()
            ),
            error_message="All chunks must have valid dimension_id",
        )

        self.add_invariant(
            name="provenance_threshold",
            description="Provenance completeness >= 0.8",
            check=lambda data: (
                data.quality_metrics is not None
                and data.quality_metrics.provenance_completeness >= 0.8
            ),
            error_message="provenance_completeness must be >= 0.8",
        )

        self.add_invariant(
            name="structural_threshold",
            description="Structural consistency >= 0.85",
            check=lambda data: (
                data.quality_metrics is not None
                and data.quality_metrics.structural_consistency >= 0.85
            ),
            error_message="structural_consistency must be >= 0.85",
        )

    def validate_input(self, input_data: Any) -> ContractValidationResult:
        """
        Validate CanonicalInput contract.

        Args:
            input_data: Input to validate

        Returns:
            ContractValidationResult
        """
        errors = []
        warnings = []

        # Type check
        if not isinstance(input_data, CanonicalInput):
            errors.append(
                f"Expected CanonicalInput, got {type(input_data).__name__}"
            )
            return ContractValidationResult(
                passed=False,
                contract_type="input",
                phase_name=self.phase_name,
                errors=errors,
            )

        # Validate fields
        if not input_data.validation_passed:
            errors.append(
                f"CanonicalInput has validation_passed=False: {input_data.validation_errors}"
            )

        if not input_data.pdf_path.exists():
            errors.append(f"PDF path does not exist: {input_data.pdf_path}")

        if input_data.pdf_page_count <= 0:
            errors.append(
                f"Invalid pdf_page_count: {input_data.pdf_page_count}"
            )

        return ContractValidationResult(
            passed=len(errors) == 0,
            contract_type="input",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings,
        )

    def validate_output(self, output_data: Any) -> ContractValidationResult:
        """
        Validate CanonPolicyPackage contract.

        Args:
            output_data: Output to validate

        Returns:
            ContractValidationResult
        """
        errors = []
        warnings = []

        # Type check
        if not isinstance(output_data, CanonPolicyPackage):
            errors.append(
                f"Expected CanonPolicyPackage, got {type(output_data).__name__}"
            )
            return ContractValidationResult(
                passed=False,
                contract_type="output",
                phase_name=self.phase_name,
                errors=errors,
            )

        # Validate using Pydantic
        try:
            CanonPolicyPackageValidator(
                schema_version=output_data.schema_version,
                document_id=output_data.metadata.get("document_id", ""),
                chunk_count=len(output_data.chunk_graph.chunks),
                has_policy_manifest=output_data.policy_manifest is not None,
                has_quality_metrics=output_data.quality_metrics is not None,
                has_integrity_index=output_data.integrity_index is not None,
                provenance_completeness=(
                    output_data.quality_metrics.provenance_completeness
                    if output_data.quality_metrics
                    else 0.0
                ),
                structural_consistency=(
                    output_data.quality_metrics.structural_consistency
                    if output_data.quality_metrics
                    else 0.0
                ),
            )
        except Exception as e:
            errors.append(f"Pydantic validation failed: {e}")

        return ContractValidationResult(
            passed=len(errors) == 0,
            contract_type="output",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings,
        )

    async def execute(self, input_data: CanonicalInput) -> CanonPolicyPackage:
        """
        Execute Phase 1: SPC Ingestion with 15 subfases.

        Args:
            input_data: CanonicalInput from Phase 0

        Returns:
            CanonPolicyPackage with 60 chunks

        Raises:
            ImportError: If SPC pipeline not available
            ValueError: If ingestion fails
        """
        logger.info(f"Starting Phase 1: SPC Ingestion for {input_data.document_id}")

        # Import SPC pipeline
        try:
            from farfan_pipeline.processing.spc_ingestion import CPPIngestionPipeline
        except ImportError as e:
            raise ImportError(
                "SPC ingestion pipeline not available. "
                "Ensure farfan_core.processing.spc_ingestion is installed."
            ) from e

        # Initialize pipeline with questionnaire
        pipeline = CPPIngestionPipeline(
            questionnaire_path=input_data.questionnaire_path,
            enable_runtime_validation=True,
        )

        # The pipeline.process() method internally executes all 15 subfases:
        # Subfase 0:  Language detection (in generate_smart_chunks)
        # Subfase 1:  Advanced preprocessing
        # Subfase 2:  Structural analysis
        # Subfase 3:  Topic modeling & KG
        # Subfase 4:  PA×DIM segmentation (60 chunks)
        # Subfase 5:  Causal chain extraction
        # Subfase 6:  Causal integration
        # Subfase 7:  Argumentative analysis
        # Subfase 8:  Temporal analysis
        # Subfase 9:  Discourse analysis
        # Subfase 10: Strategic integration
        # Subfase 11: Chunk generation
        # Subfase 12: Inter-chunk enrichment
        # Subfase 13: Integrity validation
        # Subfase 14: Deduplication
        # Subfase 15: Strategic ranking

        logger.info("Executing 15 subfases of Strategic Chunking System...")

        cpp = await pipeline.process(
            document_path=input_data.pdf_path,
            document_id=input_data.document_id,
            title=input_data.pdf_path.name,
            max_chunks=EXPECTED_CHUNK_COUNT,
        )

        logger.info(
            f"Phase 1 complete: {len(cpp.chunk_graph.chunks)} chunks generated"
        )

        # Validate chunk count
        actual_count = len(cpp.chunk_graph.chunks)
        if actual_count != EXPECTED_CHUNK_COUNT:
            logger.warning(
                f"Expected {EXPECTED_CHUNK_COUNT} chunks, got {actual_count}. "
                f"PA×DIM structure may be incomplete."
            )

        return cpp


__all__ = [
    "Phase1SPCIngestionContract",
    "PHASE1_VERSION",
    "EXPECTED_CHUNK_COUNT",
    "POLICY_AREAS",
    "DIMENSIONS",
    "SubfaseMetadata",
]
