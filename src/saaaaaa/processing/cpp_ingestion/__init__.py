"""
CPP Ingestion Package (Deprecated - Use SPC Ingestion)

This package provides backward compatibility for Canon Policy Package (CPP) ingestion.
The terminology has been migrated to Smart Policy Chunks (SPC).

For new code, use: saaaaaa.processing.spc_ingestion
"""

from .models import (
    CanonPolicyPackage,
    Chunk,
    ChunkGraph,
    ChunkResolution,
    Confidence,
    IntegrityIndex,
    PolicyFacet,
    PolicyManifest,
    ProvenanceMap,
    QualityMetrics,
    TextSpan,
    TimeFacet,
    GeoFacet,
    Budget,
    KPI,
    Entity,
)

__all__ = [
    "CanonPolicyPackage",
    "Chunk",
    "ChunkGraph",
    "ChunkResolution",
    "Confidence",
    "IntegrityIndex",
    "PolicyFacet",
    "PolicyManifest",
    "ProvenanceMap",
    "QualityMetrics",
    "TextSpan",
    "TimeFacet",
    "GeoFacet",
    "Budget",
    "KPI",
    "Entity",
]
