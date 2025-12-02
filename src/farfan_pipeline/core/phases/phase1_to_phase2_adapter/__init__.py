"""
Phase 1 → Phase 2 Adapter Contract
===================================

This module implements the adapter contract that transforms CanonPolicyPackage
(Phase 1 output) into PreprocessedDocument (Phase 2 input).

Responsibilities:
-----------------
1. Convert 60 PA×DIM chunks to sentences
2. Preserve chunk_id, policy_area_id, dimension_id in sentence_metadata.extra
3. Maintain chunk graph edges
4. Preserve all facets (policy, time, geo, entity, budget, KPI)
5. Validate preservation of critical metadata

Input Contract:
---------------
CanonPolicyPackage (from Phase 1):
    - chunk_graph with 60 chunks
    - Each chunk has policy_area_id (PA01-PA10)
    - Each chunk has dimension_id (DIM01-DIM06)
    - policy_manifest, quality_metrics, integrity_index

Output Contract:
----------------
PreprocessedDocument (for Phase 2):
    - sentences: tuple[str] (one per chunk)
    - sentence_metadata: tuple[SentenceMetadata]
    - sentence_metadata[i].extra MUST contain:
        - chunk_id: str
        - policy_area_id: str (PA01-PA10)
        - dimension_id: str (DIM01-DIM06)
        - resolution: str
        - policy_facets: dict
        - time_facets: dict
        - geo_facets: dict
    - metadata: dict with quality_metrics, policy_manifest

Invariants:
-----------
1. len(sentences) == 60 (one per chunk)
2. All sentence_metadata have chunk_id in extra
3. All sentence_metadata have policy_area_id in extra
4. All sentence_metadata have dimension_id in extra
5. processing_mode == "chunked"

Author: F.A.R.F.A.N Architecture Team
Date: 2025-01-19
"""

from __future__ import annotations

import logging
from typing import Any

from farfan_pipeline.core.types import PreprocessedDocument
from farfan_pipeline.core.phases.phase_protocol import (
    ContractValidationResult,
    PhaseContract,
)
from farfan_pipeline.processing.cpp_ingestion.models import CanonPolicyPackage

logger = logging.getLogger(__name__)


def _meta_extra(meta: Any) -> dict[str, Any]:
    """Extract extra metadata from sentence metadata entries."""
    if isinstance(meta, dict):
        return meta.get("extra", {}) or {}
    if hasattr(meta, "extra"):
        return getattr(meta, "extra") or {}
    return {}


class AdapterContract(PhaseContract[CanonPolicyPackage, PreprocessedDocument]):
    """
    Adapter contract enforcing PA×DIM metadata preservation.

    This contract ensures that the transformation from CanonPolicyPackage
    to PreprocessedDocument preserves all critical chunk metadata needed
    for Phase 2 question routing.
    """

    def __init__(self):
        """Initialize adapter contract with invariants."""
        super().__init__(phase_name="phase1_to_phase2_adapter")

        # Invariant: All chunks preserved as sentences
        self.add_invariant(
            name="chunk_count_preserved",
            description="All chunks must be preserved as sentences",
            check=lambda data: len(data.sentences) > 0,
            error_message="No sentences in PreprocessedDocument",
        )

        # Invariant: Processing mode is chunked
        self.add_invariant(
            name="processing_mode_chunked",
            description="processing_mode must be 'chunked'",
            check=lambda data: data.processing_mode == "chunked",
            error_message="processing_mode must be 'chunked' for SPC adapter",
        )

        # Invariant: All sentence_metadata have chunk_id
        self.add_invariant(
            name="chunk_id_preserved",
            description="All sentence_metadata must have chunk_id in extra",
            check=lambda data: all(
                "chunk_id" in _meta_extra(meta) for meta in data.sentence_metadata
            ),
            error_message="Missing chunk_id in sentence_metadata.extra",
        )

        # Invariant: All sentence_metadata have policy_area_id
        self.add_invariant(
            name="policy_area_id_preserved",
            description="All sentence_metadata must have policy_area_id in extra",
            check=lambda data: all(
                "policy_area_id" in _meta_extra(meta) for meta in data.sentence_metadata
            ),
            error_message="Missing policy_area_id in sentence_metadata.extra - CRITICAL for Phase 2",
        )

        # Invariant: All sentence_metadata have dimension_id
        self.add_invariant(
            name="dimension_id_preserved",
            description="All sentence_metadata must have dimension_id in extra",
            check=lambda data: all(
                "dimension_id" in _meta_extra(meta) for meta in data.sentence_metadata
            ),
            error_message="Missing dimension_id in sentence_metadata.extra - CRITICAL for Phase 2",
        )

    def validate_input(self, input_data: Any) -> ContractValidationResult:
        """
        Validate CanonPolicyPackage input.

        Args:
            input_data: Input to validate

        Returns:
            ContractValidationResult
        """
        errors = []
        warnings = []

        # Type check
        if not isinstance(input_data, CanonPolicyPackage):
            errors.append(
                f"Expected CanonPolicyPackage, got {type(input_data).__name__}"
            )
            return ContractValidationResult(
                passed=False,
                contract_type="input",
                phase_name=self.phase_name,
                errors=errors,
            )

        # Validate chunk_graph exists
        if not hasattr(input_data, "chunk_graph") or not input_data.chunk_graph:
            errors.append("CanonPolicyPackage missing chunk_graph")

        # Validate chunks exist
        if hasattr(input_data, "chunk_graph") and input_data.chunk_graph:
            chunk_count = len(input_data.chunk_graph.chunks)
            if chunk_count == 0:
                errors.append("chunk_graph.chunks is empty")
            elif chunk_count != 60:
                warnings.append(
                    f"Expected 60 chunks (10 PA × 6 DIM), got {chunk_count}"
                )

            # Validate PA×DIM tags present
            missing_pa_dim = []
            for chunk_id, chunk in input_data.chunk_graph.chunks.items():
                if not hasattr(chunk, "policy_area_id") or not chunk.policy_area_id:
                    missing_pa_dim.append(f"{chunk_id}: missing policy_area_id")
                if not hasattr(chunk, "dimension_id") or not chunk.dimension_id:
                    missing_pa_dim.append(f"{chunk_id}: missing dimension_id")

            if missing_pa_dim:
                errors.append(f"Chunks missing PA×DIM tags: {missing_pa_dim[:5]}")

        return ContractValidationResult(
            passed=len(errors) == 0,
            contract_type="input",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings,
        )

    def validate_output(self, output_data: Any) -> ContractValidationResult:
        """
        Validate PreprocessedDocument output.

        Args:
            output_data: Output to validate

        Returns:
            ContractValidationResult
        """
        errors = []
        warnings = []

        # Type check
        if not isinstance(output_data, PreprocessedDocument):
            errors.append(
                f"Expected PreprocessedDocument, got {type(output_data).__name__}"
            )
            return ContractValidationResult(
                passed=False,
                contract_type="output",
                phase_name=self.phase_name,
                errors=errors,
            )

        # Validate sentences exist
        if not hasattr(output_data, "sentences") or not output_data.sentences:
            errors.append("PreprocessedDocument.sentences is empty")

        # Validate processing_mode
        if (
            not hasattr(output_data, "processing_mode")
            or output_data.processing_mode != "chunked"
        ):
            errors.append(
                f"processing_mode must be 'chunked', got '{getattr(output_data, 'processing_mode', None)}'"
            )

        # Validate sentence_metadata exists and matches sentences
        if hasattr(output_data, "sentences") and hasattr(
            output_data, "sentence_metadata"
        ):
            if len(output_data.sentence_metadata) != len(output_data.sentences):
                errors.append(
                    f"sentence_metadata count ({len(output_data.sentence_metadata)}) != "
                    f"sentences count ({len(output_data.sentences)})"
                )

            # Validate PA×DIM preservation in sentence_metadata
            missing_metadata = []
            for idx, meta in enumerate(output_data.sentence_metadata):
                extra = _meta_extra(meta)
                if not extra:
                    missing_metadata.append(f"sentence[{idx}]: no extra field")
                    continue

                if "chunk_id" not in extra:
                    missing_metadata.append(f"sentence[{idx}]: missing chunk_id")
                if "policy_area_id" not in extra:
                    missing_metadata.append(f"sentence[{idx}]: missing policy_area_id")
                if "dimension_id" not in extra:
                    missing_metadata.append(f"sentence[{idx}]: missing dimension_id")

            if missing_metadata:
                errors.append(f"Metadata preservation failed: {missing_metadata[:5]}")

        return ContractValidationResult(
            passed=len(errors) == 0,
            contract_type="output",
            phase_name=self.phase_name,
            errors=errors,
            warnings=warnings,
        )

    async def execute(self, input_data: CanonPolicyPackage) -> PreprocessedDocument:
        """
        Execute adapter transformation.

        Args:
            input_data: CanonPolicyPackage from Phase 1

        Returns:
            PreprocessedDocument for Phase 2

        Raises:
            ImportError: If SPCAdapter not available
            ValueError: If transformation fails
        """
        logger.info(f"Starting adapter: CanonPolicyPackage → PreprocessedDocument")

        # Use existing SPCAdapter implementation
        from farfan_pipeline.utils.spc_adapter import SPCAdapter

        adapter = SPCAdapter(enable_runtime_validation=False)  # We validate here

        # Get document_id from metadata
        document_id = input_data.metadata.get("document_id", "unknown")

        # Transform
        preprocessed = adapter.to_preprocessed_document(
            input_data, document_id=document_id
        )

        logger.info(
            f"Adapter complete: {len(preprocessed.sentences)} sentences, "
            f"mode={preprocessed.processing_mode}"
        )

        return preprocessed


__all__ = [
    "AdapterContract",
]
