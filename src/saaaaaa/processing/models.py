"""
CPP Ingestion Models (Deprecated - Use SPC)

Data models for Canon Policy Package (CPP) ingestion pipeline.
These models define the structure of policy documents after phase-one ingestion.

NOTE: This is a compatibility layer. New code should use SPC (Smart Policy Chunks) terminology.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method


class ChunkResolution(Enum):
    """Granularity level for policy chunks."""
    MICRO = "MICRO"  # Fine-grained chunks (sentences, clauses)
    MESO = "MESO"    # Medium chunks (paragraphs, sections)
    MACRO = "MACRO"  # Coarse chunks (chapters, themes)


@dataclass
class TextSpan:
    """Represents a span of text in the original document."""
    start: int
    end: int


@dataclass
class Confidence:
    """Confidence scores for various extraction processes."""
    layout: float = 1.0
    ocr: float = 1.0
    typing: float = 1.0


@dataclass
class PolicyFacet:
    """Policy-related metadata facets."""
    programs: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    axes: list[str] = field(default_factory=list)


@dataclass
class TimeFacet:
    """Temporal metadata facets."""
    years: list[int] = field(default_factory=list)
    periods: list[str] = field(default_factory=list)


@dataclass
class GeoFacet:
    """Geographic metadata facets."""
    territories: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)


@dataclass
class ProvenanceMap:
    """Provenance information for chunk extraction."""
    source_page: int | None = None
    source_section: str | None = None
    extraction_method: str = "semantic_chunking"


@dataclass
class Budget:
    """Budget information extracted from policy document."""
    source: str
    use: str
    amount: float
    year: int
    currency: str = "COP"


# Alias for compatibility
BudgetInfo = Budget


@dataclass
class KPI:
    """Key Performance Indicator extracted from policy."""
    indicator_name: str
    target_value: float | None = None
    unit: str | None = None
    year: int | None = None


@dataclass
class Entity:
    """Named entity extracted from text."""
    text: str
    entity_type: str
    confidence: float = 1.0


@dataclass
class Chunk:
    """
    A semantic chunk of policy text with metadata.

    This is the fundamental unit of the CPP/SPC ingestion pipeline.
    """
    id: str
    text: str
    text_span: TextSpan
    resolution: ChunkResolution
    bytes_hash: str
    policy_area_id: str | None = None  # PA01-PA10 canonical code
    dimension_id: str | None = None    # DIM01-DIM06 canonical code

    # Facets and metadata
    policy_facets: PolicyFacet = field(default_factory=PolicyFacet)
    time_facets: TimeFacet = field(default_factory=TimeFacet)
    geo_facets: GeoFacet = field(default_factory=GeoFacet)
    confidence: Confidence = field(default_factory=Confidence)

    # Optional structured data
    provenance: ProvenanceMap | None = None
    budget: Budget | None = None
    kpi: KPI | None = None
    entities: list[Entity] = field(default_factory=list)


@dataclass
class ChunkGraph:
    """
    Graph structure containing all chunks and their relationships.
    """
    chunks: dict[str, Chunk] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)  # (from_id, to_id, relation_type)

    @calibrated_method("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_chunk")
    def add_chunk(self, chunk: Chunk) -> None:
        """Add a chunk to the graph."""
        self.chunks[chunk.id] = chunk

    @calibrated_method("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge")
    def add_edge(self, from_id: str, to_id: str, relation_type: str) -> None:
        """Add an edge to the graph."""
        self.edges.append((from_id, to_id, relation_type))


@dataclass
class PolicyManifest:
    """
    High-level manifest summarizing policy structure.
    """
    axes: list[str] = field(default_factory=list)
    programs: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)
    years: list[int] = field(default_factory=list)
    territories: list[str] = field(default_factory=list)
    indicators: list[str] = field(default_factory=list)
    budget_rows: int = 0


@dataclass
class QualityMetrics:
    """
    Quality metrics for the ingestion process.
    """
    boundary_f1: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L167_25", 0.0)
    kpi_linkage_rate: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L168_30", 0.0)
    budget_consistency_score: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L169_38", 0.0)
    provenance_completeness: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L170_37", 0.0)
    structural_consistency: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L171_36", 0.0)
    temporal_robustness: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L172_33", 0.0)
    chunk_context_coverage: float = get_parameter_loader().get("saaaaaa.processing.cpp_ingestion.models.ChunkGraph.add_edge").get("auto_param_L173_36", 0.0)


@dataclass
class IntegrityIndex:
    """
    Cryptographic integrity verification data.

    Uses BLAKE2b (not BLAKE3) for aggregate hash computation.
    Implementation uses hashlib.blake2b over JSON-serialized chunk hashes.
    """
    blake2b_root: str  # Aggregate hash (BLAKE2b-256) of all chunk hashes
    chunk_hashes: dict[str, str] = field(default_factory=dict)


@dataclass
class CanonPolicyPackage:
    """
    Canon Policy Package - Complete output from phase-one ingestion.

    This is the top-level container for all ingestion results.
    Also known as Smart Policy Chunks (SPC) in newer terminology.
    """
    schema_version: str
    chunk_graph: ChunkGraph

    # Optional high-level metadata
    policy_manifest: PolicyManifest | None = None
    quality_metrics: QualityMetrics | None = None
    integrity_index: IntegrityIndex | None = None

    # Raw metadata
    metadata: dict[str, Any] = field(default_factory=dict)
