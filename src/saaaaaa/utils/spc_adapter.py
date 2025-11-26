"""SPC to Orchestrator Adapter.

This adapter converts Smart Policy Chunks (SPC) / Canon Policy Package (CPP)
documents from the ingestion pipeline into the orchestrator's PreprocessedDocument format.

Note: SPC is the new terminology for CPP (Canon Policy Package).

Design Principles:
- Preserves complete provenance information
- Orders chunks by text_span.start for deterministic ordering
- Computes provenance_completeness metric
- Provides prescriptive error messages on failure
- Supports micro, meso, and macro chunk resolutions
- Optional dependencies handled gracefully (pyarrow, structlog)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any

from saaaaaa.core.orchestrator.core import PreprocessedDocument

logger = logging.getLogger(__name__)

_EMPTY_MAPPING = MappingProxyType({})


class SPCAdapterError(Exception):
    """Raised when SPC to PreprocessedDocument conversion fails."""
    pass


class SPCAdapter:
    """
    Adapter to convert CanonPolicyPackage (SPC output) to PreprocessedDocument.

    This is the canonical adapter for the FARFAN pipeline, converting the rich
    SmartPolicyChunk data into the format expected by the orchestrator.
    """

    def __init__(self, enable_runtime_validation: bool = True) -> None:
        """Initialize the SPC adapter.

        Args:
            enable_runtime_validation: Enable WiringValidator for runtime contract checking
        """
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize WiringValidator for runtime contract validation
        self.enable_runtime_validation = enable_runtime_validation
        if enable_runtime_validation:
            try:
                from saaaaaa.core.wiring.validation import WiringValidator
                self.wiring_validator = WiringValidator()
                self.logger.info("WiringValidator enabled for runtime contract checking")
            except ImportError:
                self.logger.warning(
                    "WiringValidator not available. Runtime validation disabled."
                )
                self.wiring_validator = None
        else:
            self.wiring_validator = None

    def to_preprocessed_document(
        self,
        canon_package: Any,
        document_id: str
    ) -> PreprocessedDocument:
        """
        Convert CanonPolicyPackage to PreprocessedDocument.

        Args:
            canon_package: CanonPolicyPackage from SPC ingestion
            document_id: Unique document identifier

        Returns:
            PreprocessedDocument ready for orchestrator

        Raises:
            SPCAdapterError: If conversion fails or data is invalid

        CanonPolicyPackage Expected Attributes:
            Required:
                - chunk_graph: ChunkGraph with .chunks dict
                - chunk_graph.chunks: dict of chunk objects with .text and .text_span

            Optional (handled with hasattr checks):
                - schema_version: str (default: 'SPC-2025.1')
                - quality_metrics: object with metrics like provenance_completeness,
                  structural_consistency, boundary_f1, kpi_linkage_rate,
                  budget_consistency_score, temporal_robustness, chunk_context_coverage
                - policy_manifest: object with axes, programs, projects, years, territories
                - metadata: dict with optional 'spc_rich_data' key

            Chunk Optional Attributes (handled with hasattr checks):
                - entities: list of entity objects with .text attribute
                - time_facets: object with .years list
                - budget: object with amount, currency, year, use, source attributes
        """
        self.logger.info(f"Converting CanonPolicyPackage to PreprocessedDocument: {document_id}")

        # === COMPREHENSIVE VALIDATION PHASE (H1.5) ===
        # 6-layer validation for robust phase-one output processing

        # V1: Validate canon_package exists
        if not canon_package:
            raise SPCAdapterError(
                "canon_package is None or empty. "
                "Ensure SPC ingestion completed successfully."
            )

        # V2: Validate document_id
        if not document_id or not isinstance(document_id, str) or not document_id.strip():
            raise SPCAdapterError(
                f"document_id must be a non-empty string. "
                f"Received: {repr(document_id)}"
            )

        # V3: Validate chunk_graph exists
        if not hasattr(canon_package, 'chunk_graph') or not canon_package.chunk_graph:
            raise SPCAdapterError(
                "canon_package must have a valid chunk_graph. "
                "Check that SmartChunkConverter produced valid output."
            )

        chunk_graph = canon_package.chunk_graph

        # V4: Validate chunks dict is non-empty
        if not chunk_graph.chunks:
            raise SPCAdapterError(
                "chunk_graph.chunks is empty - no chunks to process. "
                "Minimum 1 chunk required from phase-one."
            )

        # V5: Validate individual chunks have required attributes
        validation_failures = []
        for chunk_id, chunk in chunk_graph.chunks.items():
            if not hasattr(chunk, 'text'):
                validation_failures.append(f"Chunk {chunk_id}: missing 'text' attribute")
            elif not chunk.text or not chunk.text.strip():
                validation_failures.append(f"Chunk {chunk_id}: text is empty or whitespace")

            if not hasattr(chunk, 'text_span'):
                validation_failures.append(f"Chunk {chunk_id}: missing 'text_span' attribute")
            elif not hasattr(chunk.text_span, 'start') or not hasattr(chunk.text_span, 'end'):
                validation_failures.append(f"Chunk {chunk_id}: invalid text_span (missing start/end)")

        # V6: Report validation failures with context
        if validation_failures:
            failure_summary = "\n  - ".join(validation_failures)
            raise SPCAdapterError(
                f"Chunk validation failed ({len(validation_failures)} errors):\n  - {failure_summary}\n"
                f"Total chunks: {len(chunk_graph.chunks)}\n"
                f"This indicates SmartChunkConverter produced invalid output."
            )

        # Sort chunks by document position for deterministic ordering
        sorted_chunks = sorted(
            chunk_graph.chunks.values(),
            key=lambda c: c.text_span.start if hasattr(c, 'text_span') and c.text_span else 0
        )

        self.logger.info(f"Processing {len(sorted_chunks)} chunks")

        # Build full text by concatenating chunks
        full_text_parts: list[str] = []
        sentences: list[dict[str, Any]] = []
        sentence_metadata: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        chunk_index: dict[str, int] = {}
        chunk_summaries: list[dict[str, Any]] = []

        # Track indices for building indexes
        term_index: dict[str, list[int]] = {}
        numeric_index: dict[str, list[int]] = {}
        temporal_index: dict[str, list[int]] = {}
        entity_index: dict[str, list[int]] = {}

        # Track running offset that matches how full_text is built
        current_offset = 0

        provenance_with_data = 0

        for idx, chunk in enumerate(sorted_chunks):
            chunk_text = chunk.text
            chunk_start = current_offset
            chunk_index[chunk.id] = idx

            # Add to full text
            full_text_parts.append(chunk_text)

            # Create sentence entry (each chunk is represented as a sentence for orchestrator compatibility)
            sentences.append(
                {
                    "text": chunk_text,
                    "chunk_id": chunk.id,
                    "resolution": (chunk.resolution.value.lower() if hasattr(chunk, "resolution") else None),
                }
            )

            # Create chunk metadata for per-sentence tracking
            chunk_end = chunk_start + len(chunk_text)

            # CRITICAL: Preserve PA×DIM metadata for Phase 2 question routing
            extra_metadata = {
                "chunk_id": chunk.id,
                "policy_area_id": chunk.policy_area_id if hasattr(chunk, "policy_area_id") else None,
                "dimension_id": chunk.dimension_id if hasattr(chunk, "dimension_id") else None,
                "resolution": chunk.resolution.value.lower() if hasattr(chunk, "resolution") else None,
            }

            # Add facets if available
            if hasattr(chunk, "policy_facets") and chunk.policy_facets:
                extra_metadata["policy_facets"] = {
                    "axes": chunk.policy_facets.axes if hasattr(chunk.policy_facets, "axes") else [],
                    "programs": chunk.policy_facets.programs if hasattr(chunk.policy_facets, "programs") else [],
                    "projects": chunk.policy_facets.projects if hasattr(chunk.policy_facets, "projects") else [],
                }

            if hasattr(chunk, "time_facets") and chunk.time_facets:
                extra_metadata["time_facets"] = {
                    "years": chunk.time_facets.years if hasattr(chunk.time_facets, "years") else [],
                    "periods": chunk.time_facets.periods if hasattr(chunk.time_facets, "periods") else [],
                }

            if hasattr(chunk, "geo_facets") and chunk.geo_facets:
                extra_metadata["geo_facets"] = {
                    "territories": chunk.geo_facets.territories if hasattr(chunk.geo_facets, "territories") else [],
                    "regions": chunk.geo_facets.regions if hasattr(chunk.geo_facets, "regions") else [],
                }

            sentence_metadata.append(
                {
                    "index": idx,
                    "page_number": None,
                    "start_char": chunk_start,
                    "end_char": chunk_end,
                    "extra": dict(extra_metadata),
                }
            )

            chunk_summary = {
                "id": chunk.id,
                "resolution": (chunk.resolution.value.lower() if hasattr(chunk, "resolution") else None),
                "text_span": {"start": chunk_start, "end": chunk_end},
                "policy_area_id": extra_metadata["policy_area_id"],
                "dimension_id": extra_metadata["dimension_id"],
                "has_kpi": hasattr(chunk, "kpi") and chunk.kpi is not None,
                "has_budget": hasattr(chunk, "budget") and chunk.budget is not None,
                "confidence": {
                    "layout": getattr(chunk.confidence, "layout", 0.0) if hasattr(chunk, "confidence") else 0.0,
                    "ocr": getattr(chunk.confidence, "ocr", 0.0) if hasattr(chunk, "confidence") else 0.0,
                    "typing": getattr(chunk.confidence, "typing", 0.0) if hasattr(chunk, "confidence") else 0.0,
                },
            }
            chunk_summaries.append(chunk_summary)

            if hasattr(chunk, "provenance") and chunk.provenance:
                provenance_with_data += 1

            # Advance offset by chunk length + 1 space separator
            current_offset = chunk_end + 1

            # Extract entities for entity_index
            if hasattr(chunk, "entities") and chunk.entities:
                for entity in chunk.entities:
                    entity_text = entity.text if hasattr(entity, "text") else str(entity)
                    if entity_text not in entity_index:
                        entity_index[entity_text] = []
                    entity_index[entity_text].append(idx)

            # Extract temporal markers for temporal_index
            if hasattr(chunk, "time_facets") and chunk.time_facets:
                if hasattr(chunk.time_facets, "years") and chunk.time_facets.years:
                    for year in chunk.time_facets.years:
                        year_key = str(year)
                        if year_key not in temporal_index:
                            temporal_index[year_key] = []
                        temporal_index[year_key].append(idx)

            # Extract budget for tables
            if hasattr(chunk, "budget") and chunk.budget:
                budget = chunk.budget
                tables.append(
                    {
                        "table_id": f"budget_{idx}",
                        "label": f"Budget: {budget.source if hasattr(budget, 'source') else 'Unknown'}",
                        "amount": getattr(budget, "amount", 0),
                        "currency": getattr(budget, "currency", "COP"),
                        "year": getattr(budget, "year", None),
                        "use": getattr(budget, "use", None),
                        "source": getattr(budget, "source", None),
                    }
                )

        # Join full text
        full_text = " ".join(full_text_parts)

        if not full_text:
            raise SPCAdapterError("Generated full_text is empty")

        # Build document indexes
        indexes = {
            "term_index": {k: tuple(v) for k, v in term_index.items()},
            "numeric_index": {k: tuple(v) for k, v in numeric_index.items()},
            "temporal_index": {k: tuple(v) for k, v in temporal_index.items()},
            "entity_index": {k: tuple(v) for k, v in entity_index.items()},
        }

        # Build metadata from canon_package
        metadata_dict = {
            'adapter_source': 'SPCAdapter',
            'schema_version': canon_package.schema_version if hasattr(canon_package, 'schema_version') else 'SPC-2025.1',
            'chunk_count': len(sorted_chunks),
            'processing_mode': 'chunked',
            'chunks': chunk_summaries,
        }

        # Add quality metrics if available
        if hasattr(canon_package, 'quality_metrics') and canon_package.quality_metrics:
            qm = canon_package.quality_metrics
            metadata_dict['quality_metrics'] = {
                'provenance_completeness': qm.provenance_completeness if hasattr(qm, 'provenance_completeness') else 0.0,
                'structural_consistency': qm.structural_consistency if hasattr(qm, 'structural_consistency') else 0.0,
                'boundary_f1': qm.boundary_f1 if hasattr(qm, 'boundary_f1') else 0.0,
                'kpi_linkage_rate': qm.kpi_linkage_rate if hasattr(qm, 'kpi_linkage_rate') else 0.0,
                'budget_consistency_score': qm.budget_consistency_score if hasattr(qm, 'budget_consistency_score') else 0.0,
                'temporal_robustness': qm.temporal_robustness if hasattr(qm, 'temporal_robustness') else 0.0,
                'chunk_context_coverage': qm.chunk_context_coverage if hasattr(qm, 'chunk_context_coverage') else 0.0,
            }

        # Add policy manifest if available
        if hasattr(canon_package, 'policy_manifest') and canon_package.policy_manifest:
            pm = canon_package.policy_manifest
            metadata_dict['policy_manifest'] = {
                'axes': pm.axes if hasattr(pm, 'axes') else [],
                'programs': pm.programs if hasattr(pm, 'programs') else [],
                'projects': pm.projects if hasattr(pm, 'projects') else [],
                'years': pm.years if hasattr(pm, 'years') else [],
                'territories': pm.territories if hasattr(pm, 'territories') else [],
            }

        # Add SPC rich data if available in metadata
        if hasattr(canon_package, 'metadata') and canon_package.metadata:
            if 'spc_rich_data' in canon_package.metadata:
                metadata_dict['spc_rich_data'] = canon_package.metadata['spc_rich_data']

        if len(sorted_chunks) > 0:
            metadata_dict['provenance_completeness'] = provenance_with_data / len(sorted_chunks)

        metadata = MappingProxyType(metadata_dict)

        # Detect language (default to Spanish for Colombian policy documents)
        language = "es"

        # Create PreprocessedDocument (canonical orchestrator dataclass)
        preprocessed_doc = PreprocessedDocument(
            document_id=document_id,
            raw_text=full_text,
            sentences=sentences,
            tables=tables,
            metadata=dict(metadata),
            sentence_metadata=sentence_metadata,
            indexes=indexes,
            structured_text={"full_text": full_text, "sections": (), "page_boundaries": ()},
            language=language,
            ingested_at=datetime.now(timezone.utc),
            full_text=full_text,
            chunks=[],
            chunk_index=chunk_index,
            chunk_graph={
                "chunks": {cid: chunk_index[cid] for cid in chunk_index},
                "edges": list(getattr(chunk_graph, "edges", [])),
            },
            processing_mode="chunked",
        )

        self.logger.info(
            f"Conversion complete: {len(sentences)} sentences, "
            f"{len(tables)} tables, {len(entity_index)} entities indexed"
        )

        # RUNTIME VALIDATION: Validate Adapter → Orchestrator contract
        if self.wiring_validator is not None:
            self.logger.info("Validating Adapter → Orchestrator contract (runtime)")
            try:
                # Convert PreprocessedDocument to dict for validation
                preprocessed_dict = {
                    "document_id": preprocessed_doc.document_id,
                    "sentence_metadata": preprocessed_doc.sentence_metadata,
                    "resolution_index": {},  # Placeholder, as it's not generated by the adapter
                    "provenance_completeness": metadata_dict.get('provenance_completeness', 0.0),
                }
                self.wiring_validator.validate_adapter_to_orchestrator(preprocessed_dict)
                self.logger.info("✓ Adapter → Orchestrator contract validation passed")
            except Exception as e:
                self.logger.error(f"Adapter → Orchestrator contract validation failed: {e}")
                raise ValueError(
                    f"Runtime contract violation at Adapter → Orchestrator boundary: {e}"
                ) from e

        return preprocessed_doc


def adapt_spc_to_orchestrator(
    canon_package: Any,
    document_id: str
) -> PreprocessedDocument:
    """
    Convenience function to adapt SPC to PreprocessedDocument.

    Args:
        canon_package: CanonPolicyPackage from SPC ingestion
        document_id: Unique document identifier

    Returns:
        PreprocessedDocument for orchestrator

    Raises:
        SPCAdapterError: If conversion fails
    """
    adapter = SPCAdapter()
    return adapter.to_preprocessed_document(canon_package, document_id)


__all__ = [
    'SPCAdapter',
    'SPCAdapterError',
    'adapt_spc_to_orchestrator',
]
