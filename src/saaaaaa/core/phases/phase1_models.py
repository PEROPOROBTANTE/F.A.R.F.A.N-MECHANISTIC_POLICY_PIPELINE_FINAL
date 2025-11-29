"""
Phase 1 Models - Strict Data Structures
=======================================

Data models for the Phase 1 SPC Ingestion Execution Contract.
These models enforce strict typing and validation for the pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

@dataclass
class LanguageData:
    """
    Output of SP0 - Language Detection.
    """
    primary_language: str
    secondary_languages: List[str]
    confidence_scores: Dict[str, float]
    detection_method: str
    normalized_text: Optional[str] = None
    _sealed: bool = False

@dataclass
class PreprocessedDoc:
    """
    Output of SP1 - Advanced Preprocessing.
    """
    tokens: List[Any] = field(default_factory=list)
    sentences: List[Any] = field(default_factory=list)
    paragraphs: List[Any] = field(default_factory=list)
    normalized_text: str = ""
    original_to_normalized_mapping: Dict[Tuple[int, int], Tuple[int, int]] = field(default_factory=dict)
    _hash: str = ""

@dataclass
class StructureData:
    """
    Output of SP2 - Structural Analysis.
    """
    sections: List[Any] = field(default_factory=list)
    hierarchy: Dict[str, Optional[str]] = field(default_factory=dict)
    paragraph_mapping: Dict[int, str] = field(default_factory=dict)
    unassigned_paragraphs: List[int] = field(default_factory=list)
    tables: List[Any] = field(default_factory=list)
    lists: List[Any] = field(default_factory=list)

@dataclass
class KGNode:
    """Node in the Knowledge Graph."""
    id: str
    type: str
    text: str
    signal_tags: List[str] = field(default_factory=list)
    signal_importance: float = 0.0
    policy_area_relevance: Dict[str, float] = field(default_factory=dict)

@dataclass
class KGEdge:
    """Edge in the Knowledge Graph."""
    source: str
    target: str
    type: str
    weight: float = 1.0

@dataclass
class KnowledgeGraph:
    """
    Output of SP3 - Knowledge Graph Construction.
    """
    nodes: List[KGNode] = field(default_factory=list)
    edges: List[KGEdge] = field(default_factory=list)
    span_to_node_mapping: Dict[Tuple[int, int], str] = field(default_factory=dict)

@dataclass
class CausalGraph:
    """Local causal graph for a chunk."""
    events: List[Any] = field(default_factory=list)
    causes: List[Any] = field(default_factory=list)
    effects: List[Any] = field(default_factory=list)

@dataclass
class Chunk:
    """
    Intermediate chunk representation (SP4-SP10).
    """
    chunk_id: str = ""
    policy_area_id: str = ""
    dimension_id: str = ""
    chunk_index: int = -1
    
    text_spans: List[Tuple[int, int]] = field(default_factory=list)
    sentence_ids: List[int] = field(default_factory=list)
    paragraph_ids: List[int] = field(default_factory=list)
    
    signal_tags: List[str] = field(default_factory=list)
    signal_scores: Dict[str, float] = field(default_factory=dict)
    
    overlap_flag: bool = False
    segmentation_metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Enrichment fields (populated in SP5-SP10)
    causal_graph: Optional[CausalGraph] = None
    arguments: Optional[Dict[str, Any]] = None
    temporal_markers: Optional[Dict[str, Any]] = None
    discourse_mode: str = ""
    rhetorical_strategies: List[str] = field(default_factory=list)
    signal_patterns: List[str] = field(default_factory=list)
    
    signal_weighted_importance: float = 0.0
    policy_area_priority: float = 0.0
    risk_weight: float = 0.0
    governance_threshold: float = 0.0

@dataclass
class CausalChains:
    """Output of SP5."""
    chains: List[Any] = field(default_factory=list)

@dataclass
class IntegratedCausal:
    """Output of SP6."""
    global_graph: Any = None

@dataclass
class Arguments:
    """Output of SP7."""
    arguments_map: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Temporal:
    """Output of SP8."""
    timeline: List[Any] = field(default_factory=list)

@dataclass
class Discourse:
    """Output of SP9."""
    patterns: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Strategic:
    """Output of SP10."""
    priorities: Dict[str, float] = field(default_factory=dict)

@dataclass
class SmartChunk:
    """
    Final chunk representation (SP11-SP15).
    """
    policy_area_id: str = ""
    dimension_id: str = ""
    chunk_index: int = -1
    
    causal_graph: CausalGraph = field(default_factory=CausalGraph)
    temporal_markers: Dict[str, Any] = field(default_factory=dict)
    arguments: Dict[str, Any] = field(default_factory=dict)
    discourse_mode: str = "unknown"
    strategic_rank: int = -1
    irrigation_links: List[Any] = field(default_factory=list)
    
    signal_tags: List[str] = field(default_factory=list)
    signal_scores: Dict[str, float] = field(default_factory=dict)
    signal_version: str = "v1.0.0"
    
    rank_score: float = 0.0
    signal_weighted_score: float = 0.0

@dataclass
class ValidationResult:
    """Output of SP13 - Integrity Validation."""
    status: str = "INVALID"
    chunk_count: int = 0
    violations: List[str] = field(default_factory=list)
    pa_dim_coverage: str = "INCOMPLETE"
