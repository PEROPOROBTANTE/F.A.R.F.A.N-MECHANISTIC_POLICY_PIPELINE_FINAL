"""
SmartChunk to CanonPolicyPackage Converter
==========================================

This module provides the critical bridge layer between the SPC (Smart Policy Chunks)
phase-one output and the CanonPolicyPackage format expected by the orchestrator.

Architecture:
    SmartPolicyChunk (from StrategicChunkingSystem)
        ↓
    SmartChunkConverter (this module)
        ↓
    CanonPolicyPackage (for SPCAdapter and Orchestrator)

Key Responsibilities:
1. Convert SmartPolicyChunk dataclass to Chunk dataclass
2. Map chunk_type (8 types) to resolution (MICRO/MESO/MACRO)
3. Extract policy/time/geo facets from SPC rich data
4. Build ChunkGraph with edges from related_chunks
5. Preserve SPC rich data in metadata for executor access
6. Generate quality metrics and integrity index
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import TYPE_CHECKING, Any

from saaaaaa.processing.cpp_ingestion.models import (
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method
    KPI,
    Budget,
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    Entity,
    GeoFacet,
    IntegrityIndex,
    PolicyFacet,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
    TimeFacet,
)

if TYPE_CHECKING:
    # Avoid runtime import of SmartPolicyChunk (heavy dependencies)
    from typing import Protocol

    class SmartPolicyChunkProtocol(Protocol):
        """Protocol for SmartPolicyChunk to avoid circular imports"""
        chunk_id: str
        document_id: str
        content_hash: str
        text: str
        normalized_text: str
        semantic_density: float
        section_hierarchy: list[str]
        document_position: tuple[int, int]
        chunk_type: Any  # ChunkType enum
        causal_chain: list[Any]
        policy_entities: list[Any]
        related_chunks: list[tuple[str, float]]
        confidence_metrics: dict[str, float]
        coherence_score: float
        completeness_index: float
        strategic_importance: float

logger = logging.getLogger(__name__)


class SmartChunkConverter:
    """
    Converts SmartPolicyChunk instances to CanonPolicyPackage format.

    This converter is the critical bridge that enables SPC phase-one output
    to be consumed by the orchestrator and its executors.
    """

    # Mapping from ChunkType to ChunkResolution
    CHUNK_TYPE_TO_RESOLUTION = {
        'DIAGNOSTICO': ChunkResolution.MESO,
        'ESTRATEGIA': ChunkResolution.MACRO,
        'METRICA': ChunkResolution.MICRO,
        'FINANCIERO': ChunkResolution.MICRO,
        'NORMATIVO': ChunkResolution.MESO,
        'OPERATIVO': ChunkResolution.MICRO,
        'EVALUACION': ChunkResolution.MESO,
        'MIXTO': ChunkResolution.MESO,
    }

    def __init__(self) -> None:
        """Initialize the converter."""
        self.logger = logging.getLogger(self.__class__.__name__)

    def convert_to_canon_package(
        self,
        smart_chunks: list[Any],  # List[SmartPolicyChunk]
        document_metadata: dict[str, Any]
    ) -> CanonPolicyPackage:
        """
        Convert list of SmartPolicyChunk to CanonPolicyPackage.

        Args:
            smart_chunks: List of SmartPolicyChunk instances from StrategicChunkingSystem
            document_metadata: Document-level metadata (id, title, version, etc.)

        Returns:
            CanonPolicyPackage ready for orchestrator consumption

        Raises:
            ValueError: If smart_chunks is empty or invalid
        """
        # Defensive validation: ensure smart_chunks is non-empty
        if not smart_chunks or len(smart_chunks) == 0:
            raise ValueError(
                "Cannot convert empty smart_chunks list to CanonPolicyPackage. "
                "Minimum 1 chunk required from StrategicChunkingSystem."
            )

        # Defensive validation: check critical attributes on first chunk
        first_chunk = smart_chunks[0]
        required_attrs = ['chunk_id', 'document_id', 'text', 'document_position', 'chunk_type']
        missing_attrs = [attr for attr in required_attrs if not hasattr(first_chunk, attr)]

        if missing_attrs:
            raise ValueError(
                f"SmartPolicyChunk missing critical attributes: {missing_attrs}. "
                f"Ensure StrategicChunkingSystem produced valid SmartPolicyChunk instances. "
                f"Chunk type: {type(first_chunk)}"
            )

        self.logger.info(f"Converting {len(smart_chunks)} SmartPolicyChunks to CanonPolicyPackage")

        # Build ChunkGraph
        chunk_graph = ChunkGraph()

        # Convert each SmartPolicyChunk to Chunk
        chunk_hashes = {}
        all_axes = set()
        all_programs = set()
        all_projects = set()
        all_years = set()
        all_territories = set()

        for smart_chunk in smart_chunks:
            # Convert to Chunk
            chunk = self._convert_smart_chunk_to_chunk(smart_chunk)

            # Add to ChunkGraph
            chunk_graph.chunks[chunk.id] = chunk
            chunk_hashes[chunk.id] = chunk.bytes_hash

            # Collect manifest data
            all_axes.update(chunk.policy_facets.axes)
            all_programs.update(chunk.policy_facets.programs)
            all_projects.update(chunk.policy_facets.projects)
            all_years.update(chunk.time_facets.years)
            all_territories.update(chunk.geo_facets.territories)

        # Build edges from related_chunks
        for smart_chunk in smart_chunks:
            if hasattr(smart_chunk, 'related_chunks') and smart_chunk.related_chunks:
                for related_id, similarity in smart_chunk.related_chunks[:5]:  # Top 5
                    # Only add edge if target chunk exists
                    if related_id in chunk_graph.chunks:
                        edge = (smart_chunk.chunk_id, related_id, f"semantic_similarity_{similarity:.2f}")
                        chunk_graph.edges.append(edge)

        self.logger.info(f"Built ChunkGraph with {len(chunk_graph.chunks)} chunks and {len(chunk_graph.edges)} edges")

        # Create PolicyManifest
        policy_manifest = PolicyManifest(
            axes=sorted(all_axes),
            programs=sorted(all_programs),
            projects=sorted(all_projects),
            years=sorted(all_years),
            territories=sorted(all_territories),
            indicators=[],  # Would extract from KPIs if available
            budget_rows=sum(1 for c in chunk_graph.chunks.values() if c.budget is not None)
        )

        # Calculate QualityMetrics
        quality_metrics = self._calculate_quality_metrics(smart_chunks, chunk_graph)

        # Generate IntegrityIndex
        integrity_index = self._generate_integrity_index(chunk_hashes, document_metadata)

        # Preserve SPC rich data in metadata
        enriched_metadata = self._preserve_spc_rich_data(smart_chunks, document_metadata)

        # Build CanonPolicyPackage
        canon_package = CanonPolicyPackage(
            schema_version="SPC-2025.1",
            chunk_graph=chunk_graph,
            policy_manifest=policy_manifest,
            quality_metrics=quality_metrics,
            integrity_index=integrity_index,
            metadata=enriched_metadata
        )

        self.logger.info("Successfully converted to CanonPolicyPackage")
        return canon_package

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._convert_smart_chunk_to_chunk")
    def _convert_smart_chunk_to_chunk(self, smart_chunk: Any) -> Chunk:
        """
        Convert a single SmartPolicyChunk to Chunk.

        Maps fields from SPC rich format to orchestrator-compatible format.
        """
        # Determine resolution from chunk_type
        chunk_type_str = smart_chunk.chunk_type.value if hasattr(smart_chunk.chunk_type, 'value') else str(smart_chunk.chunk_type)
        resolution = self.CHUNK_TYPE_TO_RESOLUTION.get(chunk_type_str.upper(), ChunkResolution.MESO)

        # Extract policy facets
        policy_facets = self._extract_policy_facets(smart_chunk)

        # Extract time facets
        time_facets = self._extract_time_facets(smart_chunk)

        # Extract geo facets
        geo_facets = self._extract_geo_facets(smart_chunk)

        # Build confidence from SPC metrics
        confidence = Confidence(
            layout=get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._convert_smart_chunk_to_chunk").get("auto_param_L232_19", 1.0),  # SPC doesn't distinguish these
            ocr=smart_chunk.confidence_metrics.get('extraction_confidence', get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._convert_smart_chunk_to_chunk").get("auto_param_L233_76", 0.95)),
            typing=smart_chunk.coherence_score
        )

        # Create provenance
        provenance = self._build_provenance(smart_chunk)

        # Extract entities
        entities = self._extract_entities(smart_chunk)

        # Extract budget if available
        budget = self._extract_budget(smart_chunk)

        # Extract KPI if available
        kpi = self._extract_kpi(smart_chunk)

        # Build Chunk
        return Chunk(
            id=smart_chunk.chunk_id,
            text=smart_chunk.text,
            text_span=TextSpan(
                start=smart_chunk.document_position[0],
                end=smart_chunk.document_position[1]
            ),
            resolution=resolution,
            bytes_hash=smart_chunk.content_hash,
            policy_area_id=getattr(smart_chunk, 'policy_area_id', None),  # PA01-PA10
            dimension_id=getattr(smart_chunk, 'dimension_id', None),      # DIM01-DIM06
            policy_facets=policy_facets,
            time_facets=time_facets,
            geo_facets=geo_facets,
            confidence=confidence,
            provenance=provenance,
            budget=budget,
            kpi=kpi,
            entities=entities
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_policy_facets")
    def _extract_policy_facets(self, smart_chunk: Any) -> PolicyFacet:
        """Extract policy facets from SPC strategic_context and section_hierarchy."""
        axes = []
        programs = []
        projects = []

        # Extract from strategic_context if available
        if hasattr(smart_chunk, 'strategic_context') and smart_chunk.strategic_context:
            ctx = smart_chunk.strategic_context
            # strategic_context might have policy_intent, implementation_phase
            if hasattr(ctx, 'policy_intent'):
                axes.append(ctx.policy_intent[:50])  # Truncate if too long
            if hasattr(ctx, 'implementation_phase'):
                programs.append(ctx.implementation_phase[:50])

        # Extract from section_hierarchy
        if hasattr(smart_chunk, 'section_hierarchy') and smart_chunk.section_hierarchy:
            hierarchy = smart_chunk.section_hierarchy
            if len(hierarchy) > 0:
                axes.append(hierarchy[0])  # Top-level = axis
            if len(hierarchy) > 1:
                programs.append(hierarchy[1])  # Second level = program
            if len(hierarchy) > 2:
                projects.append(hierarchy[2])  # Third level = project

        return PolicyFacet(
            axes=axes[:3],  # Limit to avoid bloat
            programs=programs[:5],
            projects=projects[:5]
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_time_facets")
    def _extract_time_facets(self, smart_chunk: Any) -> TimeFacet:
        """Extract temporal information from SPC temporal_dynamics."""
        years = []
        periods = []

        if hasattr(smart_chunk, 'temporal_dynamics') and smart_chunk.temporal_dynamics:
            temp = smart_chunk.temporal_dynamics
            # Extract years from temporal_markers
            if hasattr(temp, 'temporal_markers'):
                for marker in temp.temporal_markers[:10]:
                    # marker format: (text, marker_type, position)
                    marker_text = marker[0] if isinstance(marker, (list, tuple)) else str(marker)
                    # Try to extract years (4-digit numbers between 2020-2030)
                    import re
                    year_matches = re.findall(r'\b(202[0-9]|203[0-9])\b', marker_text)
                    years.extend(int(y) for y in year_matches)

        # Also check strategic_context for temporal_horizon
        if hasattr(smart_chunk, 'strategic_context') and smart_chunk.strategic_context:
            ctx = smart_chunk.strategic_context
            if hasattr(ctx, 'temporal_horizon'):
                periods.append(ctx.temporal_horizon)

        return TimeFacet(
            years=sorted(set(years))[:10],  # Unique and sorted
            periods=periods[:5]
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_geo_facets")
    def _extract_geo_facets(self, smart_chunk: Any) -> GeoFacet:
        """Extract geographic information from SPC strategic_context."""
        territories = []
        regions = []

        if hasattr(smart_chunk, 'strategic_context') and smart_chunk.strategic_context:
            ctx = smart_chunk.strategic_context
            if hasattr(ctx, 'geographic_scope'):
                territories.append(ctx.geographic_scope)
            # Could also parse from policy_entities with location types

        return GeoFacet(
            territories=territories[:5],
            regions=regions[:5]
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._build_provenance")
    def _build_provenance(self, smart_chunk: Any) -> ProvenanceMap:
        """Build provenance from SPC metadata."""
        # Extract section info from section_hierarchy
        source_section = None
        if hasattr(smart_chunk, 'section_hierarchy') and smart_chunk.section_hierarchy:
            source_section = " > ".join(smart_chunk.section_hierarchy[:3])

        return ProvenanceMap(
            source_page=None,  # SPC doesn't track page numbers
            source_section=source_section,
            extraction_method="smart_policy_chunking_v3.0"
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_entities")
    def _extract_entities(self, smart_chunk: Any) -> list[Entity]:
        """Extract entities from SPC policy_entities."""
        entities = []

        if hasattr(smart_chunk, 'policy_entities') and smart_chunk.policy_entities:
            for pe in smart_chunk.policy_entities[:20]:  # Limit to 20
                entity = Entity(
                    text=pe.text if hasattr(pe, 'text') else str(pe),
                    entity_type=pe.entity_type if hasattr(pe, 'entity_type') else 'unknown',
                    confidence=pe.confidence if hasattr(pe, 'confidence') else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_entities").get("auto_param_L373_79", 0.8)
                )
                entities.append(entity)

        return entities

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_budget")
    def _extract_budget(self, smart_chunk: Any) -> Budget | None:
        """
        Extract budget with comprehensive error handling and logging (H1.4).

        Implements 4 regex patterns and robust year extraction with 4 fallback strategies.
        """
        if not (hasattr(smart_chunk, 'strategic_context') and smart_chunk.strategic_context):
            return None

        ctx = smart_chunk.strategic_context
        if not (hasattr(ctx, 'budget_linkage') and ctx.budget_linkage):
            return None

        import re
        budget_text = ctx.budget_linkage

        # H1.4: 4 regex patterns for robust budget extraction
        patterns = [
            # Pattern 1: Currency symbol with optional scale
            r'[\$]?\s*([0-9,]+(?:\.[0-9]+)?)\s*(millones|mil millones|billion|billones)?',
            # Pattern 2: "X millones de pesos"
            r'(\d+(?:\.\d+)?)\s*millones?\s+de\s+pesos',
            # Pattern 3: COP currency code
            r'COP\s*\$?\s*([0-9,]+(?:\.[0-9]+)?)',
            # Pattern 4: "presupuesto de $X"
            r'presupuesto\s+de\s+\$?\s*([0-9,]+(?:\.[0-9]+)?)',
        ]

        amount = None
        scale_multiplier = 1

        for pattern in patterns:
            match = re.search(pattern, budget_text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)

                    # Detect scale from second group or text
                    scale_text = budget_text.lower()
                    if 'millones' in scale_text or 'million' in scale_text:
                        scale_multiplier = 1_000_000
                    elif 'mil millones' in scale_text or 'billion' in scale_text or 'billones' in scale_text:
                        scale_multiplier = 1_000_000_000

                    amount *= scale_multiplier
                    break  # Stop at first match

                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Budget pattern matched but parsing failed: {e}")
                    continue

        if amount is None:
            return None

        # H1.4: Extract year with 4 fallback strategies
        year = self._extract_budget_year(budget_text, smart_chunk)

        # Build Budget object
        use = ctx.policy_intent if hasattr(ctx, 'policy_intent') else "General"

        self.logger.debug(
            f"Extracted budget: amount={amount:,.2f}, year={year}, "
            f"source='Strategic Context', use='{use[:30]}'"
        )

        return Budget(
            source="Strategic Context",
            use=use,
            amount=amount,
            year=year,
            currency="COP"
        )

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_budget_year")
    def _extract_budget_year(self, budget_text: str, smart_chunk: Any) -> int:
        """
        Extract budget year with 4 fallback strategies (H1.4).

        Strategy 1: Extract from budget_text itself
        Strategy 2: Extract from temporal_dynamics markers
        Strategy 3: Use temporal_horizon from strategic_context
        Strategy 4: Default to 2024
        """
        import re

        # Strategy 1: Look for year in budget_text
        year_match = re.search(r'\b(202[0-9]|203[0-9])\b', budget_text)
        if year_match:
            return int(year_match.group(1))

        # Strategy 2: Check temporal_dynamics markers
        if hasattr(smart_chunk, 'temporal_dynamics') and smart_chunk.temporal_dynamics:
            temp = smart_chunk.temporal_dynamics
            if hasattr(temp, 'temporal_markers') and temp.temporal_markers:
                for marker in temp.temporal_markers:
                    marker_text = marker[0] if isinstance(marker, (list, tuple)) else str(marker)
                    year_match = re.search(r'\b(202[0-9]|203[0-9])\b', marker_text)
                    if year_match:
                        return int(year_match.group(1))

        # Strategy 3: Check strategic_context temporal_horizon
        if hasattr(smart_chunk, 'strategic_context') and smart_chunk.strategic_context:
            ctx = smart_chunk.strategic_context
            if hasattr(ctx, 'temporal_horizon') and ctx.temporal_horizon:
                horizon_match = re.search(r'\b(202[0-9]|203[0-9])\b', ctx.temporal_horizon)
                if horizon_match:
                    return int(horizon_match.group(1))

        # Strategy 4: Default to 2024
        self.logger.debug("No year found in budget context, defaulting to 2024")
        return 2024

    @calibrated_method("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi")
    def _extract_kpi(self, smart_chunk: Any) -> KPI | None:
        """Extract KPI if chunk contains indicator information."""
        # Check if chunk_type suggests this is a metric
        chunk_type_str = smart_chunk.chunk_type.value if hasattr(smart_chunk.chunk_type, 'value') else str(smart_chunk.chunk_type)

        if 'METRICA' in chunk_type_str.upper() or 'EVALUACION' in chunk_type_str.upper():
            # Try to extract indicator from text
            import re
            text = smart_chunk.text
            # Look for percentage targets (e.g., "90%", "meta del 85%")
            target_match = re.search(r'meta.*?([0-9]+(?:\.[0-9]+)?)\s*%', text, re.IGNORECASE)
            if target_match:
                return KPI(
                    indicator_name=smart_chunk.text[:80],  # Use chunk text as indicator name
                    target_value=float(target_match.group(1)),
                    unit="%",
                    year=None
                )

        return None

    def _calculate_quality_metrics(
        self,
        smart_chunks: list[Any],
        chunk_graph: ChunkGraph
    ) -> QualityMetrics:
        """Calculate quality metrics from SPC data."""
        # Provenance completeness
        chunks_with_provenance = sum(
            1 for c in chunk_graph.chunks.values()
            if c.provenance and c.provenance.source_section
        )
        provenance_completeness = chunks_with_provenance / len(chunk_graph.chunks) if chunk_graph.chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L526_110", 0.0)

        # Average coherence from SPC coherence_score
        avg_coherence = sum(sc.coherence_score for sc in smart_chunks) / len(smart_chunks) if smart_chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L529_112", 0.0)

        # Average completeness from SPC completeness_index
        avg_completeness = sum(sc.completeness_index for sc in smart_chunks) / len(smart_chunks) if smart_chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L532_118", 0.0)

        # Budget consistency
        chunks_with_budget = sum(1 for c in chunk_graph.chunks.values() if c.budget)
        budget_consistency = chunks_with_budget / len(chunk_graph.chunks) if chunk_graph.chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L536_101", 0.0)

        # Temporal robustness
        chunks_with_time = sum(1 for c in chunk_graph.chunks.values() if c.time_facets.years)
        temporal_robustness = chunks_with_time / len(chunk_graph.chunks) if chunk_graph.chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L540_100", 0.0)

        # Chunk context coverage (from edges)
        chunks_with_edges = len({e[0] for e in chunk_graph.edges} | {e[1] for e in chunk_graph.edges})
        chunk_context_coverage = chunks_with_edges / len(chunk_graph.chunks) if chunk_graph.chunks else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L544_104", 0.0)

        return QualityMetrics(
            provenance_completeness=provenance_completeness,
            structural_consistency=avg_coherence,
            boundary_f1=avg_completeness,
            kpi_linkage_rate=get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L550_29", 0.0),  # Would need KPI analysis
            budget_consistency_score=budget_consistency,
            temporal_robustness=temporal_robustness,
            chunk_context_coverage=chunk_context_coverage
        )

    def _generate_integrity_index(
        self,
        chunk_hashes: dict[str, str],
        document_metadata: dict[str, Any]
    ) -> IntegrityIndex:
        """
        Generate cryptographic integrity index.

        Uses BLAKE2b-256 to compute aggregate hash of all chunk hashes.
        NOT a true Merkle tree - simply hashes sorted JSON representation.
        """
        # Generate root hash from all chunk hashes (sorted for determinism)
        combined = json.dumps(chunk_hashes, sort_keys=True).encode('utf-8')
        blake2b_root = hashlib.blake2b(combined, digest_size=32).hexdigest()

        return IntegrityIndex(
            blake2b_root=blake2b_root,
            chunk_hashes=chunk_hashes
        )

    def _preserve_spc_rich_data(
        self,
        smart_chunks: list[Any],
        document_metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Preserve SPC rich data in metadata for executor access.

        This is critical for enabling executors to access the full SPC analysis:
        - Embeddings (semantic, policy, causal, temporal)
        - Causal chains with evidence
        - Strategic context
        - Quality scores
        """
        enriched = dict(document_metadata)

        # Store serializable SPC data
        spc_rich_data = {}

        for sc in smart_chunks:
            chunk_data = {
                'chunk_id': sc.chunk_id,
                'semantic_density': sc.semantic_density,
                'coherence_score': sc.coherence_score,
                'completeness_index': sc.completeness_index,
                'strategic_importance': sc.strategic_importance,
                'information_density': sc.information_density,
                'actionability_score': sc.actionability_score,
            }

            # Add embeddings if available (as lists for JSON serialization)
            # CRITICAL: Fail-fast if embeddings cannot be preserved (no silent data loss)
            if hasattr(sc, 'semantic_embedding') and sc.semantic_embedding is not None:
                try:
                    import numpy as np
                except ImportError as e:
                    self.logger.error(
                        f"Chunk {sc.chunk_id}: NumPy is required for embedding preservation but not available"
                    )
                    raise RuntimeError(
                        "NumPy is required for SPC embedding preservation. "
                        "Install with: pip install numpy>=1.26.0"
                    ) from e

                # Validate embedding type
                if not isinstance(sc.semantic_embedding, np.ndarray):
                    self.logger.error(
                        f"Chunk {sc.chunk_id}: semantic_embedding is not np.ndarray, "
                        f"got {type(sc.semantic_embedding)}"
                    )
                    raise TypeError(
                        f"Expected semantic_embedding to be np.ndarray, got {type(sc.semantic_embedding)}"
                    )

                # Convert to list for JSON serialization
                try:
                    chunk_data['semantic_embedding'] = sc.semantic_embedding.tolist()
                    chunk_data['embedding_dim'] = sc.semantic_embedding.shape[0]
                    self.logger.debug(
                        f"Chunk {sc.chunk_id}: Preserved embedding with dimension {sc.semantic_embedding.shape[0]}"
                    )
                except (AttributeError, IndexError) as e:
                    self.logger.error(
                        f"Chunk {sc.chunk_id}: Failed to convert embedding to list: {e}"
                    )
                    raise RuntimeError(
                        f"Embedding conversion failed for chunk {sc.chunk_id}: {e}"
                    ) from e

            # Add causal chain summary
            if hasattr(sc, 'causal_chain') and sc.causal_chain:
                chunk_data['causal_chain_count'] = len(sc.causal_chain)
                chunk_data['causal_evidence'] = [
                    {
                        'dimension': ce.dimension if hasattr(ce, 'dimension') else 'unknown',
                        'confidence': ce.confidence if hasattr(ce, 'confidence') else get_parameter_loader().get("saaaaaa.processing.spc_ingestion.converter.SmartChunkConverter._extract_kpi").get("auto_param_L651_86", 0.0),
                    }
                    for ce in sc.causal_chain[:5]  # Top 5
                ]

            # Add strategic context summary
            if hasattr(sc, 'strategic_context') and sc.strategic_context:
                ctx = sc.strategic_context
                chunk_data['strategic_context'] = {
                    'policy_intent': ctx.policy_intent if hasattr(ctx, 'policy_intent') else None,
                    'implementation_phase': ctx.implementation_phase if hasattr(ctx, 'implementation_phase') else None,
                    'temporal_horizon': ctx.temporal_horizon if hasattr(ctx, 'temporal_horizon') else None,
                }

            # Add topic distribution
            if hasattr(sc, 'topic_distribution') and sc.topic_distribution:
                chunk_data['topic_distribution'] = dict(sc.topic_distribution)

            spc_rich_data[sc.chunk_id] = chunk_data

        enriched['spc_rich_data'] = spc_rich_data
        enriched['spc_version'] = 'SMART-CHUNK-3.0-FINAL'
        enriched['conversion_timestamp'] = document_metadata.get('processing_timestamp', 'unknown')

        self.logger.info(f"Preserved rich SPC data for {len(spc_rich_data)} chunks")

        return enriched
