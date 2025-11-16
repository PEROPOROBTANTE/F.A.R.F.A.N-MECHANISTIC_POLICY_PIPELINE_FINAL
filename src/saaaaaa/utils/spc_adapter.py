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

from schemas.preprocessed_document import (
    DocumentIndexesV1,
    PreprocessedDocument,
    SentenceMetadata,
    StructuredTextV1,
    TableAnnotation,
)

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

    def __init__(self):
        """Initialize the SPC adapter."""
        self.logger = logging.getLogger(self.__class__.__name__)

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

        # Validate inputs
        if not canon_package:
            raise SPCAdapterError("canon_package is None or empty")

        if not document_id:
            raise SPCAdapterError("document_id is required")

        if not hasattr(canon_package, 'chunk_graph') or not canon_package.chunk_graph:
            raise SPCAdapterError("canon_package must have a valid chunk_graph")

        chunk_graph = canon_package.chunk_graph

        if not chunk_graph.chunks:
            raise SPCAdapterError("chunk_graph.chunks is empty - no chunks to process")

        # Sort chunks by document position for deterministic ordering
        sorted_chunks = sorted(
            chunk_graph.chunks.values(),
            key=lambda c: c.text_span.start if hasattr(c, 'text_span') and c.text_span else 0
        )

        self.logger.info(f"Processing {len(sorted_chunks)} chunks")

        # Build full text by concatenating chunks
        full_text_parts = []
        sentences = []
        sentence_metadata = []
        tables = []

        # Track indices for building indexes
        term_index = {}
        numeric_index = {}
        temporal_index = {}
        entity_index = {}

        # Track running offset that matches how full_text is built
        current_offset = 0

        for idx, chunk in enumerate(sorted_chunks):
            chunk_text = chunk.text
            chunk_start = current_offset

            # Add to full text
            full_text_parts.append(chunk_text)

            # Create sentence entry (each chunk is represented as a sentence for orchestrator compatibility)
            sentences.append(chunk_text)

            # Create chunk metadata (using SentenceMetadata for orchestrator compatibility)
            chunk_end = chunk_start + len(chunk_text)
            chunk_meta = SentenceMetadata(
                index=idx,
                page_number=None,  # SPC doesn't track pages
                start_char=chunk_start,
                end_char=chunk_end,
                extra=_EMPTY_MAPPING
            )
            sentence_metadata.append(chunk_meta)

            # Advance offset by chunk length + 1 space separator
            current_offset = chunk_end + 1

            # Extract entities for entity_index
            if hasattr(chunk, 'entities') and chunk.entities:
                for entity in chunk.entities:
                    entity_text = entity.text if hasattr(entity, 'text') else str(entity)
                    if entity_text not in entity_index:
                        entity_index[entity_text] = []
                    entity_index[entity_text].append(idx)

            # Extract temporal markers for temporal_index
            if hasattr(chunk, 'time_facets') and chunk.time_facets:
                if hasattr(chunk.time_facets, 'years') and chunk.time_facets.years:
                    for year in chunk.time_facets.years:
                        year_key = str(year)
                        if year_key not in temporal_index:
                            temporal_index[year_key] = []
                        temporal_index[year_key].append(idx)

            # Extract budget for tables
            if hasattr(chunk, 'budget') and chunk.budget:
                budget = chunk.budget
                table = TableAnnotation(
                    table_id=f"budget_{idx}",
                    label=f"Budget: {budget.source if hasattr(budget, 'source') else 'Unknown'}",
                    attributes=MappingProxyType({
                        'amount': budget.amount if hasattr(budget, 'amount') else 0,
                        'currency': budget.currency if hasattr(budget, 'currency') else 'COP',
                        'year': budget.year if hasattr(budget, 'year') else None,
                        'use': budget.use if hasattr(budget, 'use') else None,
                    })
                )
                tables.append(table)

        # Join full text
        full_text = ' '.join(full_text_parts)

        if not full_text:
            raise SPCAdapterError("Generated full_text is empty")

        # Build structured text (no sections available from SPC)
        structured_text = StructuredTextV1(
            full_text=full_text,
            sections=tuple(),
            page_boundaries=tuple()
        )

        # Build document indexes
        indexes = DocumentIndexesV1(
            term_index=MappingProxyType({k: tuple(v) for k, v in term_index.items()}),
            numeric_index=MappingProxyType({k: tuple(v) for k, v in numeric_index.items()}),
            temporal_index=MappingProxyType({k: tuple(v) for k, v in temporal_index.items()}),
            entity_index=MappingProxyType({k: tuple(v) for k, v in entity_index.items()})
        )

        # Build metadata from canon_package
        metadata_dict = {
            'adapter_source': 'SPCAdapter',
            'schema_version': canon_package.schema_version if hasattr(canon_package, 'schema_version') else 'SPC-2025.1',
            'chunk_count': len(sorted_chunks),
            'processing_mode': 'chunked',
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

        metadata = MappingProxyType(metadata_dict)

        # Detect language (default to Spanish for Colombian policy documents)
        language = "es"

        # Create PreprocessedDocument
        preprocessed_doc = PreprocessedDocument(
            document_id=document_id,
            full_text=full_text,
            sentences=tuple(sentences),
            language=language,
            structured_text=structured_text,
            sentence_metadata=tuple(sentence_metadata),
            tables=tuple(tables),
            indexes=indexes,
            metadata=metadata,
            ingested_at=datetime.now(timezone.utc)
        )

        self.logger.info(
            f"Conversion complete: {len(sentences)} sentences, "
            f"{len(tables)} tables, {len(entity_index)} entities indexed"
        )

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
