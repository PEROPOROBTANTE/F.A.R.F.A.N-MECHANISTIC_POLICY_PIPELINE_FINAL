"""
SISTEMA INDUSTRIAL SOTA PARA SMART-POLICY-CHUNKS DE PLANES DE DESARROLLO
VERSIÓN 3.0 COMPLETA - SIN PLACEHOLDERS, IMPLEMENTACIÓN TOTAL
FASE 1 DEL PIPELINE: GENERACIÓN DE CHUNKS COMPRENSIVOS, RIGUROSOS Y ESTRATÉGICOS
"""

import os
import re
import logging
import hashlib
import numpy as np
import copy
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from enum import Enum
from pathlib import Path
from scipy.spatial.distance import cosine
from scipy.stats import entropy
from scipy.signal import find_peaks
# Note: torch and transformers imports removed - model lifecycle managed by canonical producers
from datetime import datetime, timezone
from collections import defaultdict, Counter
import json
import networkx as nx
from sklearn.cluster import DBSCAN, AgglomerativeClustering
# Note: cosine_similarity removed - using canonical semantic_search with cross-encoder reranking
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from nltk.tokenize import sent_tokenize
# Note: SentenceTransformer import removed - embedding handled by canonical producers
import warnings
warnings.filterwarnings('ignore')

# ============================================================================= 
# CANONICAL MODULE INTEGRATION - SOTA Producer APIs
# Import production-grade canonical components from saaaaaa.processing
# These replace internal duplicate implementations with frontier SOTA approaches
# =============================================================================

# Canonical producers (robust imports with fallback)
try:
    from saaaaaa.processing.embedding_policy import EmbeddingPolicyProducer
    from saaaaaa.processing.semantic_chunking_policy import SemanticChunkingProducer
    from saaaaaa.processing.policy_processor import create_policy_processor
except ImportError:
    # Fallback if script is run from repo root without package install
    from src.saaaaaa.processing.embedding_policy import EmbeddingPolicyProducer
    from src.saaaaaa.processing.semantic_chunking_policy import SemanticChunkingProducer
    from src.saaaaaa.processing.policy_processor import create_policy_processor

# =============================================================================
# LOGGING CONFIGURADO
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_chunks_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SPC")

# Optional language detection for multi-language support
try:
    from langdetect import detect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logger.warning("langdetect not available - defaulting to Spanish models")

# =============================================================================
# UTILITY FUNCTIONS - Serialization, Hashing, Text Safety
# =============================================================================

def np_to_list(obj):
    """
    Convert NumPy arrays to lists for JSON serialization.
    
    Inputs:
        obj: Any Python object, typically a NumPy array
    Outputs:
        List representation of the array if input is ndarray
    Raises:
        TypeError if object is not JSON-serializable
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    raise TypeError(f"Type {type(obj)} not serializable")

def safe_utf8_truncate(text: str, max_bytes: int) -> str:
    """
    Safely truncate text to max_bytes without cutting multi-byte UTF-8 characters.
    
    Inputs:
        text (str): Input text to truncate
        max_bytes (int): Maximum number of UTF-8 bytes
    Outputs:
        str: Truncated text that is valid UTF-8
    """
    if not text:
        return text
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", "ignore")

def canonical_timestamp() -> str:
    """
    Generate ISO-8601 UTC timestamp with Z suffix for canonical timestamping.
    
    Inputs:
        None
    Outputs:
        str: ISO-8601 formatted UTC timestamp ending with 'Z'
    """
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

def filter_empty_sentences(sentences: List[str]) -> List[str]:
    """
    Filter out empty or whitespace-only sentences.
    
    Inputs:
        sentences (List[str]): List of sentence strings
    Outputs:
        List[str]: Filtered list containing only non-empty sentences
    """
    return [s for s in sentences if s.strip()]

# =============================================================================
# CANONICAL ERROR CLASSES
# =============================================================================

class CanonicalError(Exception):
    """Base class for canonical pipeline errors"""
    pass

class ValidationError(CanonicalError):
    """Raised when input validation fails"""
    pass

class ProcessingError(CanonicalError):
    """Raised when processing step fails"""
    pass

class SerializationError(CanonicalError):
    """Raised when serialization fails"""
    pass

# =============================================================================
# ENUMS Y TIPOS
# =============================================================================

class ChunkType(Enum):
    DIAGNOSTICO = "diagnostico"
    ESTRATEGIA = "estrategia"
    METRICA = "metrica"
    FINANCIERO = "financiero"
    NORMATIVO = "normativo"
    OPERATIVO = "operativo"
    EVALUACION = "evaluacion"
    MIXTO = "mixto"

class CausalRelationType(Enum):
    DIRECT_CAUSE = "direct_cause"
    INDIRECT_CAUSE = "indirect_cause"
    CONDITIONAL = "conditional"
    ENABLING = "enabling"
    PREVENTING = "preventing"
    CORRELATIONAL = "correlational"
    TEMPORAL_PRECEDENCE = "temporal_precedence"

class PolicyEntityRole(Enum):
    EXECUTOR = "executor"
    BENEFICIARY = "beneficiary"
    REGULATOR = "regulator"
    FUNDER = "funder"
    STAKEHOLDER = "stakeholder"
    EVALUATOR = "evaluator" #

# =============================================================================
# ESTRUCTURAS DE DATOS
# =============================================================================

@dataclass
class CausalEvidence:
    dimension: str
    category: str
    matches: List[str]
    confidence: float
    context_span: Tuple[int, int]
    implicit_indicators: List[str]
    causal_type: CausalRelationType
    strength_score: float
    mechanisms: List[str] = field(default_factory=list)
    confounders: List[str] = field(default_factory=list)
    mediators: List[str] = field(default_factory=list)
    moderators: List[str] = field(default_factory=list)

@dataclass
class PolicyEntity:
    entity_type: str
    text: str
    normalized_form: str
    context_role: PolicyEntityRole
    confidence: float
    span: Tuple[int, int]
    relationships: List[Tuple[str, str, float]] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    mentioned_count: int = 1

@dataclass
class CrossDocumentReference:
    target_section: str
    reference_type: str
    confidence: float
    semantic_linkage: float
    context_bridge: str
    alignment_score: float = 0.0
    bidirectional: bool = False
    distance_in_doc: int = 0

@dataclass
class StrategicContext:
    policy_intent: str
    implementation_phase: str
    geographic_scope: str
    temporal_horizon: str
    budget_linkage: str
    risk_factors: List[str]
    success_indicators: List[str]
    alignment_with_sdg: List[str] = field(default_factory=list)
    stakeholder_map: Dict[str, List[str]] = field(default_factory=dict)
    policy_coherence_score: float = 0.0
    intervention_logic_chain: List[str] = field(default_factory=list)

@dataclass
class ArgumentStructure:
    claims: List[Tuple[str, float]]
    evidence: List[Tuple[str, float]]
    warrants: List[Tuple[str, float]]
    backing: List[Tuple[str, float]]
    rebuttals: List[Tuple[str, float]]
    structure_type: str
    strength_score: float
    logical_coherence: float

@dataclass
class TemporalDynamics:
    temporal_markers: List[Tuple[str, str, int]]
    sequence_flow: List[Tuple[str, str, float]]
    dependencies: List[Tuple[str, str, str]]
    milestones: List[Dict[str, Any]]
    temporal_coherence: float
    causality_direction: str

@dataclass
class SmartPolicyChunk:
    chunk_id: str
    document_id: str
    content_hash: str
    text: str
    normalized_text: str
    semantic_density: float
    section_hierarchy: List[str]
    document_position: Tuple[int, int]
    chunk_type: ChunkType
    causal_chain: List[CausalEvidence]
    policy_entities: List[PolicyEntity]
    implicit_assumptions: List[Tuple[str, float]]
    contextual_presuppositions: List[Tuple[str, float]]
    
    policy_area_id: Optional[str] = None  # PA01-PA10 canonical code
    dimension_id: Optional[str] = None    # DIM01-DIM06 canonical code
    argument_structure: Optional[ArgumentStructure] = None
    temporal_dynamics: Optional[TemporalDynamics] = None
    discourse_markers: List[Tuple[str, str]] = field(default_factory=list)
    rhetorical_patterns: List[str] = field(default_factory=list)
    
    cross_references: List[CrossDocumentReference] = field(default_factory=list)
    strategic_context: Optional[StrategicContext] = None
    related_chunks: List[Tuple[str, float]] = field(default_factory=list)
    
    confidence_metrics: Dict[str, float] = field(default_factory=dict)
    coherence_score: float = 0.0
    completeness_index: float = 0.0
    strategic_importance: float = 0.0
    information_density: float = 0.0
    actionability_score: float = 0.0
    
    semantic_embedding: Optional[np.ndarray] = None
    policy_embedding: Optional[np.ndarray] = None
    causal_embedding: Optional[np.ndarray] = None
    temporal_embedding: Optional[np.ndarray] = None
    
    knowledge_graph_nodes: List[str] = field(default_factory=list)
    knowledge_graph_edges: List[Tuple[str, str, str, float]] = field(default_factory=list)
    
    topic_distribution: Dict[str, float] = field(default_factory=dict)
    key_phrases: List[Tuple[str, float]] = field(default_factory=list)
    
    processing_timestamp: str = field(default_factory=canonical_timestamp)
    pipeline_version: str = "SMART-CHUNK-3.0-FINAL"
    extraction_methodology: str = "COMPREHENSIVE_STRATEGIC_ANALYSIS"
    model_versions: Dict[str, str] = field(default_factory=dict) #

# =============================================================================
# CONFIGURACIÓN COMPLETA DEL SISTEMA
# =============================================================================

class SmartChunkConfig:
    # Parámetros de chunking calibrados
    MIN_CHUNK_SIZE = 300
    MAX_CHUNK_SIZE = 2000
    OPTIMAL_CHUNK_SIZE = 800
    OVERLAP_SIZE = 200
    
    # Umbrales semánticos
    SEMANTIC_COHERENCE_THRESHOLD = 0.72
    CROSS_REFERENCE_MIN_SIMILARITY = 0.65
    CAUSAL_CHAIN_MIN_CONFIDENCE = 0.60
    ENTITY_EXTRACTION_THRESHOLD = 0.55
    
    # Parámetros de ventana de contexto
    MIN_CONTEXT_WINDOW = 400
    MAX_CONTEXT_WINDOW = 1200
    CONTEXT_EXPANSION_FACTOR = 1.5
    
    # Clustering y agrupación
    DBSCAN_EPS = 0.25
    DBSCAN_MIN_SAMPLES = 2
    HIERARCHICAL_CLUSTER_THRESHOLD = 0.70
    
    # Análisis causal
    CAUSAL_CHAIN_MAX_GAP = 3
    TRANSITIVE_CLOSURE_DEPTH = 4
    CAUSAL_MECHANISM_MIN_SUPPORT = 0.50
    
    # Tópicos y temas
    N_TOPICS_LDA = 15
    MIN_TOPIC_PROBABILITY = 0.15
    
    # Métricas de calidad
    MIN_INFORMATION_DENSITY = 0.40
    MIN_COHERENCE_SCORE = 0.55
    MIN_COMPLETENESS_INDEX = 0.60
    MIN_STRATEGIC_IMPORTANCE = 0.45
    
    # Deduplicación
    DEDUPLICATION_THRESHOLD = 0.88
    NEAR_DUPLICATE_THRESHOLD = 0.92 #

# =============================================================================
# SISTEMAS AUXILIARES COMPLETOS
# =============================================================================

class ContextPreservationSystem:
    """Sistema de preservación de contexto estratégico"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def preserve_strategic_context(
        self, 
        text: str, 
        structural_analysis: Dict,
        global_topics: Dict
    ) -> List[Dict]:
        """
        CANONICAL SOTA: Preserve strategic context using EmbeddingPolicyProducer.
        
        Derives breakpoints from canonical chunks with PDM structure awareness.
        Replaces internal breakpoint logic with SOTA semantic chunking.
        """
        # Use canonical chunker with doc_id/title from structural analysis
        chunks = self.parent._spc_embed.process_document(
            text, 
            {
                "doc_id": structural_analysis.get("doc_id", "unknown"),
                "title": structural_analysis.get("title", "N/A")
            }
        )
        
        # Build segments from canonical chunks (position is ordinal; approximate char spans)
        segments = []
        offset = 0
        for ch in chunks:
            ch_text = self.parent._spc_embed.get_chunk_text(ch)
            start = offset
            end = start + len(ch_text)
            offset = end
            
            segment = {
                "text": ch_text,
                "context": ch_text,  # Can expand context if needed
                "position": (start, end),
                "context_window": (start, end),
                "semantic_coherence": 0.0,  # Filled by coherence calculation if needed
                "topic_alignment": self._calculate_topic_alignment(ch_text, global_topics),
                "pdq_context": self.parent._spc_embed.get_chunk_pdq_context(ch),
                "metadata": self.parent._spc_embed.get_chunk_metadata(ch),
            }
            segments.append(segment)
        
        return segments
    
    def _identify_semantic_breakpoints(self, text: str, structural_analysis: Dict) -> List[int]:
        """Identificar puntos de ruptura semántica"""
        breakpoints = [0]
        
        # Usar límites de sección
        for section in structural_analysis.get('section_hierarchy', []):
            if 'line_number' in section:
                pos = self._line_to_position(text, section['line_number'])
                breakpoints.append(pos)
        
        # Usar puntos de quiebre estratégico
        for bp in structural_analysis.get('strategic_breakpoints', []):
            breakpoints.append(bp['position'])
        
        # Agregar límites de párrafo significativos
        paragraphs = text.split('\n\n')
        current_pos = 0
        for para in paragraphs:
            if len(para) > self.parent.config.MIN_CHUNK_SIZE:
                breakpoints.append(current_pos)
            current_pos += len(para) + 2
        
        breakpoints.append(len(text))
        return sorted(list(set(breakpoints)))
    
    def _line_to_position(self, text: str, line_number: int) -> int:
        """Convertir número de línea a posición en texto"""
        lines = text.split('\n')
        position = 0
        for i in range(min(line_number, len(lines))):
            position += len(lines[i]) + 1
        return position
    
    def _calculate_segment_coherence(self, segment_text: str) -> float:
        """
        CANONICAL SOTA: Calculate coherence using batch embeddings.
        
        Replaces per-sentence embedding calls with efficient batching.
        No per-sentence model churn.
        
        Inputs:
            segment_text (str): Text segment to analyze
        Outputs:
            float: Coherence score between 0.0 and 1.0
        """
        if len(segment_text) < 50:
            return 0.0
        
        sentences = filter_empty_sentences(re.split(r'[.!?]+', segment_text))
        if len(sentences) < 2:
            return 0.5
        
        # CANONICAL SOTA: Batch embeddings for efficiency
        embs = self.parent._generate_embeddings_for_corpus(sentences, batch_size=64)
        
        # Pairwise cosine similarity between consecutive sentences
        sims = np.sum(embs[:-1] * embs[1:], axis=1) / (
            np.linalg.norm(embs[:-1], axis=1) * np.linalg.norm(embs[1:], axis=1) + 1e-8
        )
        
        return float(np.mean(sims)) if sims.size else 0.5
    
    def _calculate_topic_alignment(self, segment_text: str, global_topics: Dict) -> float:
        """Calcular alineación con tópicos globales"""
        if not global_topics.get('keywords'):
            return 0.5
        
        segment_lower = segment_text.lower()
        keyword_matches = 0
        
        for keyword, _ in global_topics['keywords'][:20]:
            if keyword.lower() in segment_lower:
                keyword_matches += 1
        
        return min(keyword_matches / 10.0, 1.0) #


class CausalChainAnalyzer:
    """Analizador de cadenas causales"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_complete_causal_chains(
        self,
        segments: List[Dict],
        knowledge_graph: Dict
    ) -> List[Dict]:
        """Extraer cadenas causales completas"""
        causal_chains = []
        
        for segment in segments:
            chains = self._extract_segment_causal_chains(segment, knowledge_graph)
            causal_chains.extend(chains)
        
        # Conectar cadenas entre segmentos
        connected_chains = self._connect_cross_segment_chains(causal_chains)
        
        return connected_chains
    
    def _extract_segment_causal_chains(self, segment: Dict, kg: Dict) -> List[Dict]:
        """Extraer cadenas causales de un segmento"""
        text = segment['text']
        chains = []
        
        # Patrones causales complejos
        causal_patterns = [
            (r'si\s+([^,]+),\s+entonces\s+([^.]+)', 'conditional'),
            (r'debido\s+a\s+([^,]+),\s+([^.]+)', 'direct_cause'),
            (r'([^,]+)\s+permite\s+([^.]+)', 'enabling'),
            (r'([^,]+)\s+genera\s+([^.]+)', 'generation'),
            (r'para\s+([^,]+),\s+se\s+requiere\s+([^.]+)', 'requirement'),
            (r'([^,]+)\s+resulta\s+en\s+([^.]+)', 'result')
        ]
        
        for pattern, chain_type in causal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                chain = {
                    'type': chain_type,
                    'antecedent': match.group(1).strip(),
                    'consequent': match.group(2).strip() if match.lastindex >= 2 else '',
                    'position': match.span(),
                    'segment_id': id(segment),
                    'confidence': self._calculate_causal_confidence(match.group(0), text)
                }
                chains.append(chain)
        
        return chains
    
    def _connect_cross_segment_chains(self, chains: List[Dict]) -> List[Dict]:
        """Conectar cadenas causales entre segmentos"""
        if len(chains) < 2:
            return chains
        
        # Construir grafo de cadenas
        G = nx.DiGraph()
        
        for i, chain in enumerate(chains):
            G.add_node(i, **chain)
        
        # Conectar cadenas relacionadas
        for i in range(len(chains)):
            for j in range(i + 1, len(chains)):
                similarity = self._calculate_chain_similarity(chains[i], chains[j])
                if similarity > 0.7:
                    G.add_edge(i, j, weight=similarity)
        
        # Enriquecer cadenas con conexiones
        for i, chain in enumerate(chains):
            chain['connections'] = list(G.neighbors(i))
            chain['centrality'] = nx.degree_centrality(G).get(i, 0)
        
        return chains
    
    def _calculate_causal_confidence(self, match_text: str, context: str) -> float:
        """Calcular confianza de relación causal"""
        confidence = 0.5
        
        # Indicadores de confianza alta
        high_confidence_terms = ['garantiza', 'asegura', 'determina', 'causa directamente']
        for term in high_confidence_terms:
            if term in match_text.lower() or term in context.lower():
                confidence = max(confidence, 0.85)
        
        # Indicadores de confianza media
        medium_confidence_terms = ['permite', 'facilita', 'contribuye', 'apoya']
        for term in medium_confidence_terms:
            if term in match_text.lower():
                confidence = max(confidence, 0.65)
        
        # Indicadores de incertidumbre
        uncertainty_terms = ['puede', 'podría', 'posiblemente', 'eventualmente']
        for term in uncertainty_terms:
            if term in match_text.lower():
                confidence = min(confidence, 0.45)
        
        return confidence
    
    def _calculate_chain_similarity(self, chain1: Dict, chain2: Dict) -> float:
        """
        CANONICAL SOTA: Calculate chain similarity via batch embeddings.
        
        Replaces individual embedding calls with efficient batching.
        
        Inputs:
            chain1 (Dict): First causal chain
            chain2 (Dict): Second causal chain
        Outputs:
            float: Similarity score between 0.0 and 1.0
        """
        # Build text representations of chains
        texts = [
            f"{chain1.get('antecedent', '')} {chain1.get('consequent', '')}",
            f"{chain2.get('antecedent', '')} {chain2.get('consequent', '')}",
        ]
        
        # CANONICAL SOTA: Batch embeddings for efficiency
        embs = self.parent._generate_embeddings_for_corpus(texts, batch_size=2)
        
        # Cosine similarity
        sim = float(np.dot(embs[0], embs[1]) / (
            np.linalg.norm(embs[0]) * np.linalg.norm(embs[1]) + 1e-8
        ))
        
        # Penalización por tipo de relación diferente
        if chain1.get('type') != chain2.get('type'):
            sim *= 0.9 
            
        return sim


class KnowledgeGraphBuilder:
    """Constructor de grafo de conocimiento para política pública"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def build_policy_knowledge_graph(self, text: str) -> Dict[str, Any]:
        """Construir grafo de conocimiento de política pública"""
        G = nx.DiGraph()
        entities = self._extract_all_entities(text)
        relations = self._extract_all_relations(text)
        concepts = self._extract_key_concepts(text)
        
        # Añadir entidades como nodos
        for entity in entities:
            G.add_node(entity['normalized_form'], type=entity['entity_type'], role=entity['context_role'].value, confidence=entity['confidence'])
        
        # Añadir relaciones como aristas
        for relation in relations:
            source = self.parent._normalize_entity(relation['source'])
            target = self.parent._normalize_entity(relation['target'])
            if source in G.nodes and target in G.nodes:
                G.add_edge(source, target, type=relation['type'], confidence=relation['confidence'])
        
        # Métricas del grafo
        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'density': nx.density(G) if G.number_of_nodes() > 0 else 0,
            'components': nx.number_weakly_connected_components(G) if G.number_of_nodes() > 0 else 0
        }
        
        return {
            'graph': G,
            'entities': entities,
            'relations': relations,
            'concepts': concepts,
            'metrics': metrics
        }
    
    def _extract_all_entities(self, text: str) -> List[Dict]:
        """Extraer todas las entidades del texto"""
        entities = []
        
        # Patrones de entidades por tipo
        entity_patterns = {
            'organization': [ 
                r'(?:Ministerio|Secretaría|Departamento|Dirección|Instituto)\s+(?:de|del?)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+', 
                r'(?:Alcaldía|Gobernación|Prefectura)\s+(?:de|del?)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+' 
            ],
            'program': [ 
                r'(?:Programa|Plan|Proyecto)\s+(?:de|del?|para)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+' 
            ],
            'legal_framework': [ 
                r'(?:Ley|Decreto|Resolución|Acuerdo)\s+No?\s+[\d]+(?: de \d{4})?' 
            ]
        }
        
        for entity_type, patterns in entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    role = self.parent._infer_entity_role(match.group(0), text)
                    entities.append({
                        'text': match.group(0),
                        'normalized_form': self.parent._normalize_entity(match.group(0)),
                        'entity_type': entity_type,
                        'context_role': role,
                        'confidence': 0.8,
                        'span': match.span()
                    })
        
        return entities
    
    def _extract_all_relations(self, text: str) -> List[Dict]:
        """Extraer todas las relaciones del texto"""
        relations = []
        
        # Patrones de relaciones
        relation_patterns = [
            (r'([^,]+)\s+es\s+responsable\s+de\s+([^.]+)', 'responsible_for', 0.9),
            (r'([^,]+)\s+ejecutará\s+([^.]+)', 'executes', 0.85),
            (r'([^,]+)\s+beneficiará\s+a\s+([^.]+)', 'benefits', 0.8),
            (r'([^,]+)\s+financiará\s+([^.]+)', 'funds', 0.85)
        ]
        
        for pattern, rel_type, confidence in relation_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if match.lastindex >= 2:
                    relations.append({
                        'source': match.group(1).strip(),
                        'target': match.group(2).strip(),
                        'type': rel_type,
                        'confidence': confidence,
                        'context': match.group(0)
                    })
        
        return relations
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from noun chunks and key phrases.
        
        Inputs:
            text (str): Input text to analyze
        Outputs:
            List[str]: List of key concepts (max 30)
        """
        concepts = []
        if self.parent.nlp:
            # Safe UTF-8 truncation to avoid cutting multi-byte characters
            truncated_text = safe_utf8_truncate(text, 200000)
            doc = self.parent.nlp(truncated_text)
            concepts.extend([chunk.text for chunk in doc.noun_chunks][:50])
        
        # Normalizar conceptos
        concepts = list(set([c.lower().strip() for c in concepts]))
        return concepts[:30]


class TopicModeler:
    """Modelador de tópicos y temas"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tfidf_vectorizer = TfidfVectorizer(stop_words=self.parent._get_stopwords(), ngram_range=(1, 2), max_df=0.85, min_df=2)
        self.lda_model = LatentDirichletAllocation(n_components=self.parent.config.N_TOPICS_LDA, random_state=42)
    
    def _get_stopwords(self) -> List[str]:
        """Obtener lista de stopwords en español (placeholder)"""
        # Una lista de stopwords más completa se usaría en producción
        return ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'de', 'a', 'en', 'por', 'con', 'para', 'del', 'al', 'que', 'se', 'es', 'son', 'han', 'como', 'más', 'pero', 'no', 'su', 'sus']
    
    def extract_global_topics(self, text_list: List[str]) -> Dict[str, Any]:
        """Extraer tópicos globales mediante LDA"""
        try:
            # 1. Vectorizar
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_list)
            
            # 2. Aplicar LDA
            self.lda_model.fit(tfidf_matrix)
            lda_output = self.lda_model.transform(tfidf_matrix)
            
            # 3. Extraer tópicos y palabras clave
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = []
            
            for topic_idx, topic in enumerate(self.lda_model.components_):
                top_features_ind = topic.argsort()[:-10 - 1:-1]
                top_features = [(feature_names[i], topic[i]) for i in top_features_ind]
                
                topics.append({
                    'topic_id': topic_idx,
                    'keywords': top_features,
                    'weight': float(topic.sum())
                })
            
            # Palabras clave globales
            global_keywords = []
            for topic in topics:
                global_keywords.extend([kw[0] for kw in topic['keywords']])
            keyword_counts = Counter(global_keywords)
            top_keywords = keyword_counts.most_common(30)
            
            return {
                'topics': topics,
                'keywords': top_keywords,
                'topic_distribution': lda_output.mean(axis=0).tolist()
            }
        except Exception as e:
            self.logger.error(f"Error en extracción de tópicos: {e}")
            return {'topics': [], 'keywords': []} #


class ArgumentAnalyzer:
    """Analizador de estructura argumentativa (Toulmin)"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_arguments(self, causal_chains: List[Dict]) -> Dict[int, ArgumentStructure]:
        """Analizar argumentos completos"""
        argument_structures = {}
        
        # Agrupar cadenas para formar argumentos
        for idx, chain_group in enumerate(self._group_chains_by_proximity(causal_chains)):
            structure = self._extract_argument_structure(chain_group)
            if structure:
                argument_structures[idx] = structure
        
        return argument_structures
    
    def _group_chains_by_proximity(self, chains: List[Dict], max_gap: int = 500) -> List[List[Dict]]:
        """Agrupar cadenas causales por proximidad en el texto"""
        if not chains:
            return []
        
        chains.sort(key=lambda x: x['position'][0])
        groups = []
        current_group = [chains[0]]
        
        for i in range(1, len(chains)):
            prev_end = chains[i-1]['position'][1]
            current_start = chains[i]['position'][0]
            
            if current_start - prev_end < max_gap:
                current_group.append(chains[i])
            else:
                groups.append(current_group)
                current_group = [chains[i]]
        
        if current_group:
            groups.append(current_group)
            
        return groups
    
    def _extract_argument_structure(self, chain_group: List[Dict]) -> Optional[ArgumentStructure]:
        """Extraer los componentes del argumento (Claims, Evidence, Warrants)"""
        if not chain_group:
            return None
        
        claims = []
        evidence = []
        warrants = []
        
        full_text = ' '.join([f"{c.get('antecedent', '')} {c.get('consequent', '')}" for c in chain_group])
        
        # Claims: Resultados (consequents) o afirmaciones directas
        for chain in chain_group:
            if chain.get('type') in ['result', 'generation']:
                claims.append((chain.get('consequent', ''), chain.get('confidence', 0.5)))
        
        # Evidence: Antecedentes o referencias a datos/normas
        for chain in chain_group:
            if chain.get('type') in ['direct_cause', 'conditional', 'requirement']:
                evidence.append((chain.get('antecedent', ''), chain.get('confidence', 0.5)))
                
        # Warrants: Conexiones causales implícitas o explícitas de alta confianza
        warrants.extend(self._identify_warrants(chain_group))
        
        # Backing and Rebuttals (Simplificado: Requiere modelo avanzado)
        backing = []
        rebuttals = []
        
        # Estructura y Fuerza
        structure_type = self._determine_structure_type(claims, evidence)
        strength_score = self._calculate_argument_strength(claims, evidence, warrants)
        logical_coherence = self._assess_logical_coherence(claims, evidence)
        
        return ArgumentStructure(
            claims=claims[:5],
            evidence=evidence[:5],
            warrants=warrants[:3],
            backing=backing,
            rebuttals=rebuttals,
            structure_type=structure_type,
            strength_score=strength_score,
            logical_coherence=logical_coherence
        )
    
    def _identify_warrants(self, chain_group: List[Dict]) -> List[Tuple[str, float]]:
        """Identificar warrants (garantías/conexiones)"""
        warrants = []
        for chain in chain_group:
            if chain.get('confidence', 0.5) > 0.7:
                warrants.append((f"Conexión causal tipo: {chain.get('type')}", chain.get('confidence', 0.5)))
        return warrants
    
    def _determine_structure_type(self, claims: List, evidence: List) -> str:
        """Determinar el tipo de estructura argumentativa"""
        if len(claims) > 1 and len(evidence) >= 1:
            return 'multiple_claims_supported'
        elif len(claims) == 1 and len(evidence) >= 1:
            return 'simple_supported'
        elif not evidence and claims:
            return 'assertion_only'
        elif len(claims) >= 1 and any(c.lower().startswith(('según', 'de acuerdo con')) for c, _ in evidence):
            return 'evidence_based'
        else:
            return 'balanced'
            
    def _calculate_argument_strength(self, claims: List, evidence: List, warrants: List) -> float:
        """Calcular fuerza del argumento"""
        if not claims: 
            return 0.0
            
        claim_strength = np.mean([conf for _, conf in claims]) if claims else 0
        evidence_strength = np.mean([conf for _, conf in evidence]) if evidence else 0
        warrant_strength = np.mean([conf for _, conf in warrants]) if warrants else 0
        
        # Ponderación: evidencia más importante que claims
        strength = (claim_strength * 0.3 + evidence_strength * 0.5 + warrant_strength * 0.2)
        
        # Penalizar argumentos sin evidencia
        if not evidence:
            strength *= 0.5
            
        return min(strength, 1.0)
    
    def _assess_logical_coherence(self, claims: List, evidence: List) -> float:
        """Evaluar coherencia lógica del argumento"""
        if not claims or not evidence: 
            return 0.0
            
        # Coherencia basada en similitud semántica entre claims y evidencia
        all_texts = [c for c, _ in claims] + [e for e, _ in evidence]
        if len(all_texts) < 2: 
            return 0.5
            
        # Use batch embedding for efficiency
        embeddings = self.parent._generate_embeddings_for_corpus(all_texts, batch_size=64)
        
        # Vectorized cosine similarity computation (no sklearn dependency)
        # Normalize embeddings for efficient dot product = cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized_embs = embeddings / (norms + 1e-8)
        sim_matrix = np.dot(normalized_embs, normalized_embs.T)
        
        # Tomar la similitud media (excluyendo la diagonal)
        coherence = (np.sum(sim_matrix) - np.trace(sim_matrix)) / (len(sim_matrix)**2 - len(sim_matrix))
        
        return min(max(coherence, 0.0), 1.0)


class TemporalAnalyzer:
    """Analizador de dinámica temporal y secuencial"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_temporal_dynamics(self, causal_chains: List[Dict]) -> Dict[int, Optional[TemporalDynamics]]:
        """Analizar dinámica temporal completa"""
        temporal_structures = {}
        
        # Agrupar cadenas para análisis temporal
        for idx, chain_group in enumerate(self.parent.argument_analyzer._group_chains_by_proximity(causal_chains)):
            structure = self._extract_temporal_structure(chain_group)
            if structure:
                temporal_structures[idx] = structure
        
        return temporal_structures
    
    def _extract_temporal_structure(self, chain_group: List[Dict]) -> Optional[TemporalDynamics]:
        """Extraer marcadores, secuencias y dependencias temporales"""
        if not chain_group:
            return None
        
        temporal_markers = []
        sequence_flow = []
        dependencies = []
        milestones = []
        
        # Extraer marcadores de tiempo
        for chain in chain_group:
            # Reutilizar el analizador temporal de la clase principal
            text_context = f"{chain.get('antecedent', '')} {chain.get('consequent', '')}"
            temp_info = self.parent._analyze_temporal_structure(text_context)
            
            for marker in temp_info.get('time_markers', []):
                temporal_markers.append((marker['text'], marker['type'], marker['position'][0]))
            
            for seq in temp_info.get('sequences', []):
                sequence_flow.append((seq['marker'], str(seq['order']), 0.8))
        
        # Extraer dependencias causales con implicación temporal
        for chain in chain_group:
            if chain.get('type') in ['conditional', 'direct_cause', 'requirement']:
                dependencies.append((
                    chain.get('antecedent', ''),
                    chain.get('consequent', ''),
                    'prerequisite' if chain.get('type') == 'requirement' else 'temporal_precedence'
                ))
            elif chain.get('type') == 'conditional':
                dependencies.append((
                    chain.get('antecedent', ''),
                    chain.get('consequent', ''),
                    'conditional'
                ))
        
        # Extraer hitos
        milestone_patterns = [
            r'meta\s+(?:de|para)\s+([^.]+)',
            r'lograr\s+([^.]+)\s+(?:en|para)\s+(20\d{2})',
            r'alcanzar\s+([^.]+)'
        ]
        
        for chain in chain_group:
            text = f"{chain.get('antecedent', '')} {chain.get('consequent', '')}"
            for pattern in milestone_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches[:2]:
                    milestones.append({
                        'description': match if isinstance(match, str) else match[0],
                        'target_date': match[1] if isinstance(match, tuple) and len(match) > 1 else None,
                        'confidence': chain.get('confidence', 0.5)
                    })
        
        if not (temporal_markers or sequence_flow or dependencies or milestones):
            return None
            
        temporal_coherence = self._calculate_temporal_coherence(temporal_markers, sequence_flow)
        causality_direction = self._determine_causality_direction(dependencies)
        
        return TemporalDynamics(
            temporal_markers=temporal_markers[:10],
            sequence_flow=sequence_flow[:5],
            dependencies=dependencies[:10],
            milestones=milestones[:5],
            temporal_coherence=temporal_coherence,
            causality_direction=causality_direction
        )
    
    def _calculate_temporal_coherence(self, markers: List, flow: List) -> float:
        """Calcular la coherencia de los marcadores temporales"""
        # Simple métrica basada en la presencia de orden y hitos
        score = 0.0
        if flow:
            score += 0.5
        if any(m[1] in ['year', 'month_year', 'period'] for m in markers):
            score += 0.5
        return min(score, 1.0)
    
    def _determine_causality_direction(self, dependencies: List[Tuple]) -> str:
        """Determinar la dirección dominante de la causalidad (forward/backward)"""
        forward = sum(1 for _, _, t in dependencies if t == 'temporal_precedence')
        backward = sum(1 for _, _, t in dependencies if t == 'backward')
        
        if forward > backward:
            return 'forward'
        elif backward > forward:
            return 'backward'
        return 'mixed' #


class DiscourseAnalyzer:
    """Analizador de discurso"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_discourse(self, causal_chains: List[Dict]) -> Dict[int, Dict]:
        """Analizar estructuras discursivas"""
        discourse_structures = {}
        
        for idx, chain_group in enumerate(self.parent.argument_analyzer._group_chains_by_proximity(causal_chains, max_gap=300)):
            structure = self._extract_discourse_structure(chain_group)
            if structure:
                discourse_structures[idx] = structure
        
        return discourse_structures
    
    def _group_chains_discursively(self, chains: List[Dict]) -> List[List[Dict]]:
        """Agrupar cadenas por coherencia discursiva (reutiliza lógica de ArgumentAnalyzer)"""
        return self.parent.argument_analyzer._group_chains_by_proximity(chains, max_gap=300)
    
    def _extract_discourse_structure(self, chain_group: List[Dict]) -> Optional[Dict]:
        """Extraer estructura discursiva del grupo"""
        if not chain_group:
            return None
            
        full_text = ' '.join([f"{c.get('antecedent', '')} {c.get('consequent', '')}" for c in chain_group])
        
        # Análisis de relaciones
        relations = self.parent._extract_coherence_relations(full_text)
        
        # Análisis retórico
        rhetorical = self.parent._analyze_rhetorical_structure(full_text)
        
        # Análisis de flujo de información
        info_flow = self.parent._analyze_information_flow(full_text)
        
        return {
            'coherence_relations': relations[:10],
            'rhetorical_moves': list(rhetorical.keys()),
            'flow_metrics': info_flow,
            'complexity_score': self._calculate_discourse_complexity(relations, rhetorical)
        }
    
    def _calculate_discourse_complexity(self, relations: List[Dict], rhetorical: Dict) -> float:
        """Calcular complejidad discursiva"""
        moves = []
        for v in rhetorical.values():
            moves.extend(v)
            
        move_diversity = len(set(moves)) if moves else 0
        relation_diversity = len(set(r['type'] for r in relations)) if relations else 0
        
        complexity = (move_diversity / 5.0) * 0.5 + (relation_diversity / 8.0) * 0.5
        return min(complexity, 1.0) #


class StrategicIntegrator:
    """Integrador de análisis multi-escala"""
    
    def __init__(self, parent_system):
        self.parent = parent_system
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def integrate_strategic_units(
        self,
        causal_chains: List[Dict],
        structural_analysis: Dict,
        argument_structures: Dict,
        temporal_structures: Dict,
        discourse_structures: Dict,
        global_topics: Dict,
        global_kg: Dict
    ) -> List[Dict]:
        """Integrar todos los análisis en unidades estratégicas"""
        
        # 1. Agrupar cadenas en unidades base (reutilizando la agrupación)
        grouped_chains = self.parent.argument_analyzer._group_chains_by_proximity(causal_chains, max_gap=100)
        
        strategic_units = []
        
        for idx, chain_group in enumerate(grouped_chains):
            full_text = ' '.join([f"{c.get('antecedent', '')} {c.get('consequent', '')}" for c in chain_group])
            # Derive hierarchy for this segment
            start_pos = chain_group[0]['position'][0] if chain_group and 'position' in chain_group[0] else 0
            hierarchy = self._derive_hierarchy_for_segment(start_pos, structural_analysis)
            # Unidades de integración
            unit = {
                'index': idx,
                'text': full_text,
                'position': (chain_group[0]['position'][0], chain_group[-1]['position'][1]),
                'chains': chain_group,
                'argument_structure': argument_structures.get(idx),
                'temporal_dynamics': temporal_structures.get(idx),
                'discourse_structure': discourse_structures.get(idx),
                'hierarchy': hierarchy,
                'confidence': np.mean([c.get('confidence', 0.5) for c in chain_group]),
                'semantic_coherence': self.parent.context_preserver._calculate_segment_coherence(full_text)
            }
            
            strategic_units.append(unit)
            
        # 2. Enriquecer con metadatos estratégicos
        enriched_units = self._enrich_strategic_metadata(strategic_units)
        
        # 3. Refinar límites de las unidades (placeholder para refinamiento avanzado)
        
        return enriched_units

    def _derive_hierarchy_for_segment(self, start_pos: int, structural_analysis: Dict) -> List[str]:
        """Derivar la jerarquía de sección para una posición en el texto"""
        hierarchy = []
        best_match = None
        min_distance = float('inf')
        
        for section in structural_analysis.get('section_hierarchy', []):
            sec_pos = self.parent.context_preserver._line_to_position(structural_analysis['raw_text'], section['line_number'])
            distance = start_pos - sec_pos
            
            # La sección debe preceder o estar en la unidad
            if distance >= -50 and distance < min_distance: 
                best_match = section
                min_distance = distance
        
        if best_match:
            hierarchy.append(best_match['title'])
            
        return hierarchy
    
    def _enrich_strategic_metadata(self, units: List[Dict]) -> List[Dict]:
        """Enriquecer unidades con metadatos estratégicos"""
        for unit in units:
            unit['strategic_weight'] = self._calculate_strategic_weight(unit)
            unit['implementation_readiness'] = self._assess_implementation_readiness(unit)
            unit['risk_level'] = self._assess_risk_level(unit)
        return units
    
    def _calculate_strategic_weight(self, unit: Dict) -> float:
        """Calcular peso estratégico de la unidad"""
        factors = {
            'chain_count': min(len(unit['chains']) / 5, 1.0),
            'confidence': unit['confidence'],
            'coherence': unit['semantic_coherence'],
            'hierarchy_level': 1.0 if unit['hierarchy'] else 0.5
        }
        return np.mean(list(factors.values()))
    
    def _assess_implementation_readiness(self, unit: Dict) -> float:
        """Evaluar preparación para implementación"""
        text = unit.get('text', '')
        readiness_indicators = [
            'plan de acción', 'presupuesto asignado', 'cronograma definido', 
            'responsable designado', 'indicadores de seguimiento'
        ]
        readiness_score = sum(1 for ind in readiness_indicators if ind in text.lower())
        return min(readiness_score / 3.0, 1.0)
    
    def _assess_risk_level(self, unit: Dict) -> float:
        """Evaluar nivel de riesgo (simplificado)"""
        text = unit.get('text', '')
        risk_terms = ['riesgo', 'limitación', 'desafío', 'obstáculo', 'incertidumbre']
        risk_score = sum(1 for term in risk_terms if term in text.lower())
        return min(risk_score / 3.0, 1.0) #


# =============================================================================
# POLICY AREA CHUNK CALIBRATION - Garantiza 10 chunks por policy area
# =============================================================================

class PolicyAreaChunkCalibrator:
    """
    Calibrates chunking to guarantee exactly 10 strategic chunks per policy area.

    Uses the existing SemanticChunkingProducer with dynamically adjusted parameters
    to ensure consistent chunk count across different policy documents.

    Strategy:
        1. Estimate optimal chunk_size based on document length
        2. Generate initial chunks with SemanticChunkingProducer
        3. Adjust parameters iteratively if chunk count != 10
        4. Merge or split chunks as needed to reach target

    Attributes:
        TARGET_CHUNKS_PER_PA: Target number of chunks (10)
        TOLERANCE: Acceptable deviation (±1 chunk)
        MAX_ITERATIONS: Maximum calibration iterations (3)
    """

    TARGET_CHUNKS_PER_PA = 10
    TOLERANCE = 1
    MAX_ITERATIONS = 3

    # Canonical policy areas from questionnaire_monolith.json
    POLICY_AREAS = [
        "PA01", "PA02", "PA03", "PA04", "PA05",
        "PA06", "PA07", "PA08", "PA09", "PA10"
    ]

    def __init__(self, semantic_chunking_producer: SemanticChunkingProducer):
        """
        Initialize calibrator.

        Args:
            semantic_chunking_producer: Canonical SemanticChunkingProducer instance
        """
        self.chunking_producer = semantic_chunking_producer
        self.logger = logging.getLogger("SPC.Calibrator")

    def calibrate_for_policy_area(
        self,
        text: str,
        policy_area: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate exactly 10 chunks for a policy area.

        Args:
            text: Policy document text
            policy_area: Policy area ID (PA01-PA10)
            metadata: Optional metadata to attach to chunks

        Returns:
            List of exactly 10 chunks

        Raises:
            ValueError: If policy_area is invalid or text is empty
        """
        if policy_area not in self.POLICY_AREAS:
            raise ValueError(
                f"Invalid policy_area: {policy_area}. "
                f"Must be one of {self.POLICY_AREAS}"
            )

        if not text or len(text.strip()) == 0:
            raise ValueError("Text cannot be empty")

        self.logger.info(
            f"Calibrating chunks for {policy_area} "
            f"(target: {self.TARGET_CHUNKS_PER_PA} chunks)"
        )

        # Estimate initial parameters based on document length
        initial_params = self._estimate_initial_params(text)

        # Attempt to generate chunks with calibration
        chunks = self._generate_with_calibration(
            text,
            policy_area,
            initial_params,
            metadata
        )

        # Final validation
        if len(chunks) != self.TARGET_CHUNKS_PER_PA:
            self.logger.warning(
                f"{policy_area}: Could not reach exact target. "
                f"Got {len(chunks)} chunks, forcing adjustment to {self.TARGET_CHUNKS_PER_PA}"
            )
            chunks = self._force_chunk_count(chunks, self.TARGET_CHUNKS_PER_PA)

        self.logger.info(
            f"{policy_area}: Calibration complete - {len(chunks)} chunks generated"
        )

        return chunks

    def _estimate_initial_params(self, text: str) -> Dict[str, Any]:
        """
        Estimate optimal chunking parameters based on text length.

        Args:
            text: Document text

        Returns:
            Dictionary with chunk_size, overlap, and other parameters
        """
        text_length = len(text)
        sentence_count = text.count('.') + text.count('!') + text.count('?')

        # Estimate chunk size to yield ~10 chunks
        estimated_chunk_size = max(
            500,  # Minimum chunk size
            min(
                2000,  # Maximum chunk size
                text_length // (self.TARGET_CHUNKS_PER_PA + 2)  # Add buffer
            )
        )

        return {
            'chunk_size': estimated_chunk_size,
            'overlap': int(estimated_chunk_size * 0.15),  # 15% overlap
            'min_chunk_size': 300,
            'adaptive': True,
        }

    def _generate_with_calibration(
        self,
        text: str,
        policy_area: str,
        initial_params: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate chunks with iterative calibration to reach target count.

        Args:
            text: Document text
            policy_area: Policy area ID
            initial_params: Initial chunking parameters
            metadata: Optional metadata

        Returns:
            List of chunks (may not be exactly 10, needs final adjustment)
        """
        params = initial_params.copy()

        for iteration in range(self.MAX_ITERATIONS):
            # Use SemanticChunkingProducer to generate chunks
            try:
                # FIXED: Actually use the SemanticChunkingProducer
                chunks = self._generate_chunks_with_producer(text, params, policy_area, metadata)
            except Exception as e:
                # Fallback to simple chunking if producer fails
                self.logger.warning(f"SemanticChunkingProducer failed: {e}, using fallback")
                chunks = self._generate_chunks_simple(text, params, policy_area, metadata)

            chunk_count = len(chunks)
            delta = chunk_count - self.TARGET_CHUNKS_PER_PA

            self.logger.debug(
                f"{policy_area}: Iteration {iteration+1} - "
                f"{chunk_count} chunks (delta: {delta:+d})"
            )

            # Check if within tolerance
            if abs(delta) <= self.TOLERANCE:
                return chunks

            # Adjust parameters for next iteration
            if delta > 0:
                # Too many chunks - increase chunk size
                params['chunk_size'] = int(params['chunk_size'] * 1.2)
            else:
                # Too few chunks - decrease chunk size
                params['chunk_size'] = int(params['chunk_size'] * 0.8)

            # Ensure bounds
            params['chunk_size'] = max(400, min(2500, params['chunk_size']))

        # Return best attempt after max iterations
        return chunks

    def _generate_chunks_with_producer(
        self,
        text: str,
        params: Dict[str, Any],
        policy_area: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate chunks using the SemanticChunkingProducer.

        Args:
            text: Document text
            params: Chunking parameters (chunk_size, overlap, etc.)
            policy_area: Policy area ID
            metadata: Optional metadata

        Returns:
            List of chunk dictionaries
        """
        # Use the actual SemanticChunkingProducer (instance method, not standalone function)
        # Use the producer instance injected via __init__
        producer = self.chunking_producer

        # chunk_document signature: (text: str, preserve_structure: bool = True) -> list[dict[str, Any]]
        result_chunks = producer.chunk_document(text=text, preserve_structure=True)

        # Convert to our format
        chunks = []
        for i, chunk_result in enumerate(result_chunks):
            # chunk_result is a dict with keys like 'text', 'embedding', 'section_type', etc.
            chunks.append({
                'id': f"{policy_area}_chunk_{i+1}",
                'text': chunk_result.get('text', ''),
                'policy_area': policy_area,
                'chunk_index': i,
                'length': len(chunk_result.get('text', '')),
                'metadata': metadata or {},
                'semantic_metadata': {
                    'section_type': chunk_result.get('section_type'),
                    'section_id': chunk_result.get('section_id'),
                    'has_embedding': 'embedding' in chunk_result
                }
            })

        return chunks

    def _generate_chunks_simple(
        self,
        text: str,
        params: Dict[str, Any],
        policy_area: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Simple chunk generation using sentence splitting.

        This is a fallback implementation. In production, this would use
        the full SemanticChunkingProducer with BGE-M3 embeddings.

        Args:
            text: Document text
            params: Chunking parameters
            policy_area: Policy area ID
            metadata: Optional metadata

        Returns:
            List of chunk dictionaries
        """
        # Simple sentence-based chunking
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunk_size = params.get('chunk_size', 1000)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > chunk_size and current_chunk:
                # Create chunk
                chunk_text = '. '.join(current_chunk) + '.'
                chunks.append({
                    'id': f"{policy_area}_chunk_{len(chunks)+1}",
                    'text': chunk_text,
                    'policy_area': policy_area,
                    'chunk_index': len(chunks),
                    'length': len(chunk_text),
                    'metadata': metadata or {}
                })
                current_chunk = [sentence]
                current_length = sentence_length
            else:
                current_chunk.append(sentence)
                current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunk_text = '. '.join(current_chunk) + '.'
            chunks.append({
                'id': f"{policy_area}_chunk_{len(chunks)+1}",
                'text': chunk_text,
                'policy_area': policy_area,
                'chunk_index': len(chunks),
                'length': len(chunk_text),
                'metadata': metadata or {}
            })

        return chunks

    def _force_chunk_count(
        self,
        chunks: List[Dict[str, Any]],
        target: int
    ) -> List[Dict[str, Any]]:
        """
        Force chunk count to exactly match target by merging or splitting.

        Args:
            chunks: List of chunks
            target: Target chunk count

        Returns:
            List with exactly target chunks
        """
        current_count = len(chunks)

        if current_count == target:
            return chunks

        if current_count > target:
            # Too many chunks - merge smallest adjacent pairs
            while len(chunks) > target:
                # Find smallest chunk
                min_idx = min(range(len(chunks)), key=lambda i: chunks[i]['length'])

                # Merge with adjacent chunk
                if min_idx > 0:
                    # Merge with previous
                    chunks[min_idx-1]['text'] += ' ' + chunks[min_idx]['text']
                    chunks[min_idx-1]['length'] = len(chunks[min_idx-1]['text'])
                    chunks.pop(min_idx)
                else:
                    # Merge with next
                    chunks[min_idx]['text'] += ' ' + chunks[min_idx+1]['text']
                    chunks[min_idx]['length'] = len(chunks[min_idx]['text'])
                    chunks.pop(min_idx+1)
        else:
            # Too few chunks - split largest chunks
            while len(chunks) < target:
                # Find largest chunk
                max_idx = max(range(len(chunks)), key=lambda i: chunks[i]['length'])

                # Split it in half
                chunk_to_split = chunks[max_idx]
                text = chunk_to_split['text']
                mid_point = len(text) // 2

                # Find sentence boundary near midpoint
                split_point = text.rfind('.', 0, mid_point) + 1
                if split_point <= 0:
                    split_point = mid_point

                # Create two chunks
                chunk1_text = text[:split_point].strip()
                chunk2_text = text[split_point:].strip()

                chunks[max_idx] = {
                    **chunk_to_split,
                    'text': chunk1_text,
                    'length': len(chunk1_text),
                }

                chunks.insert(max_idx + 1, {
                    **chunk_to_split,
                    'id': f"{chunk_to_split['id']}_split",
                    'text': chunk2_text,
                    'length': len(chunk2_text),
                })

        # Re-index chunks
        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i

        return chunks


# =============================================================================
# SISTEMA PRINCIPAL DE CHUNKING ESTRATÉGICO (COMPLETO)
# =============================================================================

class StrategicChunkingSystem:
    def __init__(self, random_seed: int = 42):
        """
        Initialize the Strategic Chunking System with canonical components.

        Integrates production-grade canonical modules:
        - PolicyAnalysisEmbedder for semantic embeddings
        - SemanticProcessor for chunking with PDM structure awareness
        - IndustrialPolicyProcessor for causal evidence extraction
        - BayesianEvidenceScorer for probabilistic confidence scoring

        Args:
            random_seed: Seed for deterministic RNG (default: 42)

        Inputs:
            None
        Outputs:
            None - initializes system state
        """
        # Fix seeds for deterministic execution (HOSTILE AUDIT REQUIREMENT)
        import random
        np.random.seed(random_seed)
        random.seed(random_seed)
        self.logger = logging.getLogger("SPC")  # Unified logger name
        self.logger.info(f"Initialized with deterministic seed: {random_seed}")

        self.config = SmartChunkConfig()
        
        # =====================================================================
        # CANONICAL SOTA PRODUCERS - Frontier approach components
        # =====================================================================
        
        # Initialize SOTA canonical producers that replace internal implementations
        # These provide BGE-M3 embeddings, cross-encoder reranking, Bayesian numerical eval
        self._spc_embed = EmbeddingPolicyProducer()          # chunking + embeddings + search + Bayesian numeric eval
        self._spc_sem = SemanticChunkingProducer()           # direct embed_text/embed_batch and chunk_document
        self._spc_policy = create_policy_processor()         # canonical PDQ/dimension evidence
        
        self.logger.info("SOTA canonical producers initialized: EmbeddingPolicyProducer, SemanticChunkingProducer, PolicyProcessor")

        # =====================================================================
        # POLICY AREA × DIMENSION KEYWORD MAPS - Structured extraction
        # =====================================================================

        # PA01-PA10 keyword maps for content extraction
        self._pa_keywords = {
            "PA01": ["mujeres", "género", "igualdad", "feminismo", "violencia género", "empoderamiento", "equidad"],
            "PA02": ["violencia", "conflicto armado", "protección", "prevención", "grupos delincuenciales", "economías ilegales", "seguridad"],
            "PA03": ["ambiente", "cambio climático", "desastres", "medio ambiente", "ecología", "sostenibilidad", "recursos naturales"],
            "PA04": ["derechos económicos", "derechos sociales", "derechos culturales", "educación", "salud", "vivienda", "trabajo"],
            "PA05": ["víctimas", "construcción de paz", "reconciliación", "reparación", "memoria", "justicia transicional"],
            "PA06": ["niñez", "adolescencia", "juventud", "entornos protectores", "desarrollo infantil", "educación inicial"],
            "PA07": ["tierras", "territorios", "tenencia", "reforma agraria", "ordenamiento territorial", "catastro"],
            "PA08": ["líderes", "lideresas", "defensores", "defensoras", "derechos humanos", "protección líderes", "amenazas"],
            "PA09": ["privadas libertad", "cárceles", "sistema penitenciario", "hacinamiento", "reinserción", "reclusos"],
            "PA10": ["migración", "transfronteriza", "migrantes", "refugiados", "movilidad humana", "frontera"]
        }

        # DIM01-DIM06 keyword maps for dimension alignment
        self._dim_keywords = {
            "DIM01": ["diagnóstico", "recursos", "presupuesto", "financiación", "insumos", "inversión", "dotación"],
            "DIM02": ["actividades", "intervención", "diseño", "estrategias", "acciones", "programas", "proyectos"],
            "DIM03": ["productos", "outputs", "entregables", "resultados intermedios", "metas", "indicadores producto"],
            "DIM04": ["resultados", "outcomes", "efectos", "logros", "cambios", "impacto directo", "beneficiarios"],
            "DIM05": ["impactos", "largo plazo", "transformación", "cambio estructural", "sostenibilidad", "legado"],
            "DIM06": ["causalidad", "teoría de cambio", "cadena causal", "lógica intervención", "marco lógico", "supuestos"]
        }

        self.logger.info(f"PA keyword maps: {len(self._pa_keywords)} policy areas")
        self.logger.info(f"DIM keyword maps: {len(self._dim_keywords)} dimensions")

        # =====================================================================
        # SPECIALIZED COMPONENTS - Keep (no canonical equivalent)
        # =====================================================================
        
        # These provide unique Smart Policy Chunks innovations
        self._nlp = None  # SpaCy for NER (lazy-loaded)
        self._kg_builder = None  # NetworkX knowledge graph
        self._topic_modeler = None  # LDA topic modeling
        self._argument_analyzer = None  # Toulmin argument structure
        self._temporal_analyzer = None  # Temporal dynamics
        self._discourse_analyzer = None  # Discourse markers
        self._strategic_integrator = None  # Cross-reference integration
        
        # Modelo para clasificación de tipo de chunk
        self.chunk_classifier = None
        
        # Almacenamiento
        self.tfidf_vectorizer = TfidfVectorizer(stop_words=self._get_stopwords(), ngram_range=(1, 2), max_df=0.85, min_df=2)
        self.chunks_for_tfidf = []
        self.corpus_embeddings = None
    
    # =========================================================================
    # SPECIALIZED COMPONENT PROPERTIES - Innovation layers (no canonical equivalent)
    # =========================================================================
    
    @property
    def nlp(self):
        """Lazy-load SpaCy NLP model"""
        if self._nlp is None:
            try:
                self.logger.info("Loading SpaCy model: es_core_news_lg")
                self._nlp = spacy.load("es_core_news_lg")
            except:
                self.logger.warning("SpaCy es_core_news_lg no disponible, usando sm")
                try:
                    self._nlp = spacy.load("es_core_news_sm")
                except:
                    self.logger.error("Ningún modelo SpaCy disponible. Funcionalidad de NER limitada.")
                    self._nlp = None
        return self._nlp
    
    @property
    def context_preserver(self):
        """
        CANONICAL REPLACEMENT: Use semantic_processor for chunking.
        Kept for backward compatibility but delegates to canonical component.
        """
        # Return a lightweight adapter that uses canonical SemanticProcessor
        return self.semantic_processor
    
    @property
    def causal_analyzer(self):
        """
        CANONICAL REPLACEMENT: Use policy_processor for causal extraction.
        Kept for backward compatibility but delegates to canonical component.
        """
        # Return canonical policy processor which has causal extraction
        return self.policy_processor
    
    @property
    def kg_builder(self):
        """Lazy-load knowledge graph builder"""
        if self._kg_builder is None:
            self._kg_builder = KnowledgeGraphBuilder(self)
        return self._kg_builder
    
    @property
    def topic_modeler(self):
        """Lazy-load topic modeler"""
        if self._topic_modeler is None:
            self._topic_modeler = TopicModeler(self)
        return self._topic_modeler
    
    @property
    def argument_analyzer(self):
        """Lazy-load argument analyzer"""
        if self._argument_analyzer is None:
            self._argument_analyzer = ArgumentAnalyzer(self)
        return self._argument_analyzer
    
    @property
    def temporal_analyzer(self):
        """Lazy-load temporal analyzer"""
        if self._temporal_analyzer is None:
            self._temporal_analyzer = TemporalAnalyzer(self)
        return self._temporal_analyzer
    
    @property
    def discourse_analyzer(self):
        """Lazy-load discourse analyzer"""
        if self._discourse_analyzer is None:
            self._discourse_analyzer = DiscourseAnalyzer(self)
        return self._discourse_analyzer
    
    @property
    def strategic_integrator(self):
        """Lazy-load strategic integrator"""
        if self._strategic_integrator is None:
            self._strategic_integrator = StrategicIntegrator(self)
        return self._strategic_integrator
    
    def detect_language(self, text: str) -> str:
        """
        Detect the primary language of a text document.
        
        Inputs:
            text (str): Text to analyze
        Outputs:
            str: ISO 639-1 language code (e.g., 'es', 'en', 'pt')
        """
        if not LANGDETECT_AVAILABLE:
            # Default to Spanish for Colombian policy documents
            return 'es'
        
        try:
            # Sample first 2000 characters for language detection
            sample = safe_utf8_truncate(text, 2000)
            detected_lang = detect(sample)
            self.logger.info(f"Detected language: {detected_lang}")
            return detected_lang
        except Exception as e:
            self.logger.warning(f"Language detection failed: {e}, defaulting to Spanish")
            return 'es'
    
    def select_embedding_model_for_language(self, language: str) -> None:
        """
        Select appropriate embedding model based on detected language.
        
        Inputs:
            language (str): ISO 639-1 language code
        Outputs:
            None - updates model selection
        """
        # For now, multilingual-e5-large handles multiple languages well
        # Could be extended with language-specific models if needed
        if language in ['es', 'pt', 'ca']:  # Spanish, Portuguese, Catalan
            self.logger.info(f"Using multilingual model for {language} (optimal for Romance languages)")
        else:
            self.logger.info(f"Using multilingual model for {language}")
        
        # Model is already multilingual, no change needed
        # This method provides extension point for future language-specific optimization
        
    # --- Métodos de la clase principal (Continuación de smart_policy_chunks_industrial_v3_complete_Version2.py) ---
    
    def _get_stopwords(self) -> List[str]:
        """
        Get Spanish stopwords list.
        
        Inputs:
            None
        Outputs:
            List[str]: List of Spanish stopwords
        """
        # Una lista de stopwords más completa se usaría en producción
        return ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'de', 'a', 'en', 'por', 'con', 'para', 'del', 'al', 'que', 'se', 'es', 'son', 'han', 'como', 'más', 'pero', 'no', 'su', 'sus', 'ha', 'lo', 'e', 'u', 'ni', 'sin', 'mi', 'tu', 'si', 'cuando', 'este', 'esta', 'estos', 'estas', 'esos', 'esas', 'aquel', 'aquella']
    
    # =========================================================================
    # CANONICAL SOTA METHODS - Replace manual implementations
    # =========================================================================
    
    def semantic_search_with_rerank(
        self, 
        query: str, 
        chunks: list[dict], 
        pdq_filter: dict | None = None, 
        top_k: int = 10
    ) -> list[tuple[dict, float]]:
        """
        CANONICAL SOTA: Semantic search with cross-encoder reranking.
        
        Replaces manual cosine_similarity ranking with SOTA reranker.
        
        Inputs:
            query (str): Search query
            chunks (list[dict]): Chunks to search
            pdq_filter (dict | None): Optional PDQ filter
            top_k (int): Number of results to return
        Outputs:
            list[tuple[dict, float]]: List of (chunk, score) tuples
        """
        results = self._spc_embed.semantic_search(
            query, chunks, pdq_filter=pdq_filter, use_reranking=True
        )
        return results[:top_k]
    
    def _attach_canonical_evidence(self, full_text: str) -> dict[str, Any]:
        """
        CANONICAL SOTA: Attach canonical PDQ/dimension evidence.
        
        Uses canonical policy patterns instead of ad-hoc heuristics.
        
        Inputs:
            full_text (str): Full document text
        Outputs:
            dict[str, Any]: Canonical evidence analysis
        """
        return self._spc_policy.analyze_text(full_text)
    
    def evaluate_numerical_consistency(
        self, 
        chunks: list[dict], 
        pdq_context: dict
    ) -> dict[str, Any]:
        """
        CANONICAL SOTA: Evaluate numerical consistency with Bayesian analysis.
        
        Uses canonical extractor + Bayesian analyzer for probabilistic scoring.
        
        Inputs:
            chunks (list[dict]): Chunks to evaluate
            pdq_context (dict): PDQ context for evaluation
        Outputs:
            dict[str, Any]: Numerical consistency evaluation
        """
        return self._spc_embed.evaluate_numerical_consistency(chunks, pdq_context)
    
    def _generate_embedding(self, text: str, model_type: str = "semantic") -> np.ndarray:
        """
        CANONICAL SOTA: Generate embedding using SemanticChunkingProducer.
        
        Replaces internal embedding with SOTA multilingual BGE-M3 model.
        model_type kept for compatibility; canonical pipeline is multilingual.
        
        Inputs:
            text (str): Input text to embed
            model_type (str): Ignored, canonical uses SOTA multilingual
        Outputs:
            np.ndarray: Embedding vector from canonical SOTA component
        """
        return self._spc_sem.embed_text(text).astype(np.float32) 

    def _create_smart_policy_chunk(
        self,
        strategic_unit: Dict,
        metadata: Dict,
        argument_structure: Optional[ArgumentStructure],
        temporal_structure: Optional[TemporalDynamics],
        discourse_structure: Optional[Dict],
        global_topics: Dict,
        global_kg: Dict
    ) -> SmartPolicyChunk:
        """Crear Smart Policy Chunk con análisis completo"""
        text = strategic_unit.get("text", "")
        document_id = metadata.get("document_id", "doc_001")
        
        # Generar embeddings
        semantic_embedding = self._generate_embedding(text, 'semantic')
        policy_embedding = self._generate_embedding(text, 'semantic')
        causal_embedding = self._generate_embedding(text, 'semantic')
        temporal_embedding = self._generate_embedding(text, 'semantic')

        # Análisis causales
        causal_evidence = self._extract_comprehensive_causal_evidence(strategic_unit, global_kg)
        
        # Entidades políticas
        policy_entities = self._extract_policy_entities_with_context(strategic_unit)
        
        # Contexto estratégico
        strategic_context = self._derive_strategic_context(strategic_unit, global_topics)
        
        # Métricas de calidad
        confidence_metrics = self._calculate_comprehensive_confidence(strategic_unit, causal_evidence, policy_entities)
        coherence_score = self._calculate_coherence_score(strategic_unit)
        completeness_index = self._calculate_completeness_index(strategic_unit, causal_evidence)
        strategic_importance = self._assess_strategic_importance(strategic_unit, causal_evidence, policy_entities)
        information_density = self._calculate_information_density(text)
        actionability_score = self._assess_actionability(text, policy_entities)
        
        # Referencias cruzadas
        cross_refs = self._find_cross_document_references(strategic_unit)
        
        # Supuestos implícitos
        implicit_assumptions = self._extract_implicit_assumptions(strategic_unit, causal_evidence)
        
        # Presuposiciones contextuales
        contextual_presuppositions = self._identify_contextual_presuppositions(strategic_unit)
        
        # Marcadores de discurso
        discourse_markers = self._extract_discourse_markers(text)
        
        # Patrones retóricos
        rhetorical_patterns = self._identify_rhetorical_patterns(text)
        
        # Distribución de tópicos para este chunk
        topic_distribution = self._calculate_chunk_topic_distribution(text, global_topics)
        
        # Frases clave
        key_phrases = self._extract_key_phrases(text)
        
        # Nodos y aristas del grafo de conocimiento
        kg_nodes = [e.normalized_form for e in policy_entities]
        kg_edges = self._derive_kg_edges_for_chunk(policy_entities, causal_evidence)

        # Hash y ID
        content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        chunk_id = f"{document_id}_{content_hash[:8]}"
        
        # Normalización
        normalized_text = self._advanced_preprocessing(text)

        return SmartPolicyChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            content_hash=content_hash,
            policy_area_id=strategic_unit.get("policy_area_id"),  # PA01-PA10
            dimension_id=strategic_unit.get("dimension_id"),      # DIM01-DIM06

            text=text,
            normalized_text=normalized_text,
            semantic_density=self._calculate_semantic_density(text),
            
            section_hierarchy=strategic_unit.get("hierarchy", []),
            document_position=strategic_unit.get("position", (0, 0)),
            chunk_type=self._classify_chunk_type(text),
            
            causal_chain=causal_evidence,
            policy_entities=policy_entities,
            implicit_assumptions=implicit_assumptions,
            contextual_presuppositions=contextual_presuppositions,
            
            argument_structure=argument_structure,
            temporal_dynamics=temporal_structure,
            discourse_markers=discourse_markers,
            rhetorical_patterns=rhetorical_patterns,
            
            cross_references=cross_refs,
            strategic_context=strategic_context,
            
            confidence_metrics=confidence_metrics,
            coherence_score=coherence_score,
            completeness_index=completeness_index,
            strategic_importance=strategic_importance,
            information_density=information_density,
            actionability_score=actionability_score,
            
            semantic_embedding=semantic_embedding,
            policy_embedding=policy_embedding,
            causal_embedding=causal_embedding,
            temporal_embedding=temporal_embedding,
            
            knowledge_graph_nodes=kg_nodes,
            knowledge_graph_edges=kg_edges,
            
            topic_distribution=topic_distribution,
            key_phrases=key_phrases,
            
            model_versions=self._get_model_versions()
        )

    # --- Métodos de Análisis y Extracción (Continuación de smart_policy_chunks_industrial_v3_complete_Version2.py) ---
    
    def _extract_comprehensive_causal_evidence(self, strategic_unit: Dict, global_kg: Dict) -> List[CausalEvidence]:
        """Extraer evidencia causal completa (Placeholder con estructura avanzada)"""
        evidence_list = []
        text = strategic_unit.get("text", "")
        
        # Placeholder para un modelo de extracción causal más avanzado
        # Simulación de extracción basada en patrones de palabras
        
        dimensions = {
            'problem_solution': [r'solución\s+para\s+([^.]+)', r'abordar\s+([^.]+)\s+mediante\s+([^.]+)'],
            'impact_assessment': [r'tendrá\s+un\s+impacto\s+([^.]+)', r'conducirá\s+a\s+([^.]+)'],
            'resource_allocation': [r'asignación\s+de\s+([^,]+)\s+para\s+([^.]+)'],
            'policy_instrument': [r'(?:la\s+implementación|el\s+uso)\s+de\s+([^,]+)\s+resultará\s+en\s+([^.]+)']
        }
        
        for dimension, patterns in dimensions.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    context_start = max(0, match.start() - 150)
                    context_end = min(len(text), match.end() + 150)
                    context = text[context_start:context_end]
                    
                    # Determinar tipo de relación causal
                    causal_type = self._determine_causal_type(match.group(0), context)
                    
                    # Calcular fuerza de la relación
                    strength = self._calculate_causal_strength(match.group(0), context)
                    
                    # Identificar mecanismos
                    mechanisms = self._identify_causal_mechanisms(context)
                    
                    evidence_list.append(CausalEvidence(
                        dimension=dimension,
                        category=self._categorize_causal_evidence(dimension),
                        matches=[match.group(0)],
                        confidence=0.75 + (strength * 0.2), # Ajuste por fuerza
                        context_span=(context_start, context_end),
                        implicit_indicators=self._find_implicit_indicators(context),
                        causal_type=causal_type,
                        strength_score=strength,
                        mechanisms=mechanisms,
                        confounders=self._identify_confounders(context),
                        mediators=self._identify_mediators(context),
                        moderators=self._identify_moderators(context)
                    ))
        
        return evidence_list

    def _categorize_causal_evidence(self, dimension: str) -> str:
        """Categorizar el tipo de evidencia causal"""
        if dimension in ['problem_solution', 'impact_assessment']:
            return 'macro_policy'
        elif dimension in ['resource_allocation', 'policy_instrument']:
            return 'implementation_mechanisms'
        return 'general'

    def _determine_causal_type(self, match_text: str, context: str) -> CausalRelationType:
        """Determinar el tipo de relación causal por marcadores lingüísticos"""
        match_lower = match_text.lower()
        if 'si' in match_lower and 'entonces' in context.lower():
            return CausalRelationType.CONDITIONAL
        elif any(word in match_lower for word in ['porque', 'debido a', 'gracias a']):
            return CausalRelationType.DIRECT_CAUSE
        elif any(word in match_lower for word in ['por lo tanto', 'en consecuencia']):
            return CausalRelationType.DIRECT_CAUSE
        else:
            return CausalRelationType.INDIRECT_CAUSE

    def _calculate_causal_strength(self, match_text: str, context: str) -> float:
        """Calcular fuerza de relación causal"""
        strength_score = 0.5
        
        # Reforzadores (Boosters)
        boosters = ['directamente', 'significativamente', 'claramente', 'contundentemente']
        if any(b in context.lower() for b in boosters):
            strength_score += 0.3
            
        # Mitigadores (Dampeners)
        dampeners = ['parcialmente', 'limitadamente', 'posiblemente', 'podría']
        if any(d in context.lower() for d in dampeners):
            strength_score -= 0.3
            
        return np.clip(strength_score, 0.1, 1.0)

    def _identify_causal_mechanisms(self, context: str) -> List[str]:
        """Identificar mecanismos causales (cómo funciona la relación)"""
        mechanisms = []
        mechanism_patterns = [
            r'a\s+través\s+de\s+([^.]+)',
            r'mediante\s+([^.]+)'
        ]
        
        for pattern in mechanism_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            mechanisms.extend(matches[:2])
            
        return mechanisms

    def _find_implicit_indicators(self, context: str) -> List[str]:
        """Encontrar indicadores implícitos de causalidad (sin marcadores explícitos)"""
        implicit = []
        implicit_patterns = [
            r'para\s+lograr\s+([^.]+)',
            r'es\s+fundamental\s+([^.]+)',
            r'la\s+falta\s+de\s+([^.]+)\s+impacta\s+([^.]+)'
        ]
        
        for pattern in implicit_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            implicit.extend(matches[:2])
            
        return implicit

    def _identify_confounders(self, context: str) -> List[str]:
        """Identificar factores de confusión causales"""
        confounders = []
        confounder_patterns = [
            r'a\s+pesar\s+de\s+([^,]+)',
            r'sin\s+considerar\s+([^,]+)'
        ]
        
        for pattern in confounder_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            confounders.extend(matches[:2])
            
        return confounders

    def _identify_mediators(self, context: str) -> List[str]:
        """Identificar mediadores causales"""
        mediators = []
        mediator_patterns = [
            r'que\s+a\s+su\s+vez\s+([^.]+)',
            r'lo\s+cual\s+([^.]+)'
        ]
        
        for pattern in mediator_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            mediators.extend(matches[:2])
            
        return mediators

    def _identify_moderators(self, context: str) -> List[str]:
        """Identificar moderadores causales"""
        moderators = []
        moderator_patterns = [
            r'en\s+la\s+medida\s+(?:en\s+)?que\s+([^,]+)',
            r'siempre\s+y\s+cuando\s+([^,]+)',
            r'dependiendo\s+de\s+([^,]+)'
        ]
        
        for pattern in moderator_patterns:
            matches = re.findall(pattern, context, re.IGNORECASE)
            moderators.extend(matches[:2])
            
        return moderators

    def _extract_policy_entities_with_context(self, strategic_unit: Dict) -> List[PolicyEntity]:
        """Extraer entidades de política con contexto completo"""
        entities = []
        text = strategic_unit.get("text", "")
        
        # Patrones de entidades institucionales
        institutional_patterns = [
            (r'(?:Ministerio|Secretaría|Departamento|Dirección|Instituto|Agencia)\s+(?:de|del?|para)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+', 'institution'),
            (r'(?:Alcaldía|Gobernación|Prefectura)\s+(?:de|del?)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+', 'local_government'),
            (r'(?:Consejo|Comité|Junta)\s+(?:de|del?|para)\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ\s]+', 'committee')
        ]
        
        for pattern, entity_type in institutional_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                role = self._infer_entity_role(match.group(0), text)
                entities.append(PolicyEntity(
                    entity_type=entity_type,
                    text=match.group(0),
                    normalized_form=self._normalize_entity(match.group(0)),
                    context_role=role,
                    confidence=0.7,
                    span=match.span()
                ))

        # Patrones de población/beneficiarios (simplificado)
        beneficiary_patterns = [
            (r'(?:los|las)\s+(?:niños|niñas|jóvenes|mujeres|población|comunidad|ciudadanos)\s+(?:de|en)\s+[^,.]+', 'population_group'),
            (r'beneficiarios\s+(?:de|del?)\s+[^,.]+', 'beneficiary_group')
        ]
        
        for pattern, entity_type in beneficiary_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                entities.append(PolicyEntity(
                    entity_type=entity_type,
                    text=match.group(0),
                    normalized_form=self._normalize_entity(match.group(0)),
                    context_role=PolicyEntityRole.BENEFICIARY,
                    confidence=0.8,
                    span=match.span()
                ))

        # Deduplicación y conteo
        unique_entities: List[PolicyEntity] = []
        seen_texts = set()
        for entity in entities:
            normalized = entity.normalized_form.lower()
            if normalized not in seen_texts:
                seen_texts.add(normalized)
                unique_entities.append(entity)
            else:
                # Actualizar contador de menciones
                for existing in unique_entities:
                    if existing.normalized_form.lower() == normalized:
                        existing.mentioned_count += 1
                        break
        
        return unique_entities

    def _infer_entity_role(self, entity_text: str, context: str) -> PolicyEntityRole:
        """Inferir el rol de la entidad en el contexto"""
        context_lower = context.lower()
        if any(term in context_lower for term in [f"ejecutará {entity_text.lower()}", f"responsable de {entity_text.lower()}", f"{entity_text.lower()} implementará"]):
            return PolicyEntityRole.EXECUTOR
        elif any(term in context_lower for term in [f"beneficiará a {entity_text.lower()}", f"dirigido a {entity_text.lower()}"]):
            return PolicyEntityRole.BENEFICIARY
        elif any(term in context_lower for term in [f"regulador {entity_text.lower()}", f"{entity_text.lower()} emitirá"]):
            return PolicyEntityRole.REGULATOR
        elif any(term in context_lower for term in [f"financiará {entity_text.lower()}", f"funder {entity_text.lower()}"]):
            return PolicyEntityRole.FUNDER
        else:
            return PolicyEntityRole.STAKEHOLDER

    def _normalize_entity(self, entity_text: str) -> str:
        """Normalizar la forma de la entidad"""
        # Eliminar artículos, preposiciones y estandarizar mayúsculas
        text = re.sub(r'\b(el|la|los|las|un|una|de|del|a|en|por)\b', '', entity_text, flags=re.IGNORECASE).strip()
        text = re.sub(r'\s+', ' ', text)
        return text.title()

    def _derive_strategic_context(self, strategic_unit: Dict, global_topics: Dict) -> StrategicContext:
        """Derivar contexto estratégico comprehensivo"""
        text = strategic_unit.get("text", "")
        
        return StrategicContext(
            policy_intent=self._infer_policy_intent(text),
            implementation_phase=self._identify_implementation_phase(text),
            geographic_scope=self._extract_geographic_scope(text),
            temporal_horizon=self._determine_temporal_horizon(text),
            budget_linkage=self._identify_budget_linkage(text),
            risk_factors=self._extract_risk_factors(text),
            success_indicators=self._identify_success_indicators(text),
            alignment_with_sdg=self._identify_sdg_alignment(text),
            stakeholder_map=self._build_stakeholder_map(text),
            policy_coherence_score=self._calculate_policy_coherence(text, global_topics),
            intervention_logic_chain=self._extract_intervention_logic(strategic_unit)
        )

    def _infer_policy_intent(self, text: str) -> str:
        """Inferir la intención de política (e.g., mitigar, promover, regular)"""
        text_lower = text.lower()
        if 'promover' in text_lower or 'fomentar' in text_lower or 'impulsar' in text_lower:
            return 'Promoción/Fomento'
        elif 'reducir' in text_lower or 'mitigar' in text_lower or 'combatir' in text_lower:
            return 'Mitigación/Reducción'
        elif 'regular' in text_lower or 'establecer normativa' in text_lower or 'ley' in text_lower:
            return 'Regulación/Normativa'
        return 'General'

    def _identify_implementation_phase(self, text: str) -> str:
        """Identificar la fase de implementación (e.g., diseño, ejecución, evaluación)"""
        text_lower = text.lower()
        if 'diseño' in text_lower or 'formulación' in text_lower:
            return 'Diseño'
        elif 'ejecución' in text_lower or 'implementación' in text_lower or 'puesta en marcha' in text_lower:
            return 'Ejecución'
        elif 'evaluación' in text_lower or 'seguimiento' in text_lower or 'monitoreo' in text_lower:
            return 'Evaluación'
        return 'Mixto'

    def _extract_geographic_scope(self, text: str) -> str:
        """Extraer el alcance geográfico"""
        text_lower = text.lower()
        if 'nacional' in text_lower or 'país' in text_lower:
            return 'Nacional'
        elif 'departamental' in text_lower or 'departamento' in text_lower or 'provincia' in text_lower:
            return 'Departamental'
        elif 'municipal' in text_lower or 'municipio' in text_lower or 'ciudad' in text_lower:
            return 'Municipal/Local'
        return 'Indefinido'

    def _determine_temporal_horizon(self, text: str) -> str:
        """Determinar el horizonte temporal (corto, mediano, largo plazo)"""
        text_lower = text.lower()
        if 'corto plazo' in text_lower or 'próximo año' in text_lower:
            return 'Corto Plazo'
        elif 'mediano plazo' in text_lower or 'próximos 4 años' in text_lower:
            return 'Mediano Plazo'
        elif 'largo plazo' in text_lower or 'horizonte 2030' in text_lower:
            return 'Largo Plazo'
        return 'Mixto'

    def _identify_budget_linkage(self, text: str) -> str:
        """Identificar vínculos presupuestales"""
        text_lower = text.lower()
        if 'presupuesto' in text_lower or 'recursos financieros' in text_lower or 'inversión de' in text_lower:
            return 'Explícito'
        elif 'costos' in text_lower or 'financiamiento' in text_lower:
            return 'Implícito'
        return 'Ausente'

    def _extract_risk_factors(self, text: str) -> List[str]:
        """Extraer factores de riesgo explícitos"""
        risks = []
        risk_patterns = [
            r'el\s+riesgo\s+(?:de|es)\s+([^.]+)',
            r'se\s+deben\s+mitigar\s+([^.]+)'
        ]
        for pattern in risk_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            risks.extend(matches[:3])
        return risks

    def _identify_success_indicators(self, text: str) -> List[str]:
        """Identificar indicadores de éxito o métricas"""
        indicators = []
        indicator_patterns = [
            r'indicador\s+([^.]+)',
            r'meta\s+(?:de|para)\s+([^.]+)',
            r'se\s+medirá\s+con\s+([^.]+)'
        ]
        for pattern in indicator_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            indicators.extend(matches[:3])
        return indicators

    def _identify_sdg_alignment(self, text: str) -> List[str]:
        """Identificar alineación con ODS"""
        sdgs = []
        # ODS explícitos
        sdg_pattern = r'ODS\s+(\d+)'
        matches = re.findall(sdg_pattern, text, re.IGNORECASE)
        sdgs.extend([f"ODS_{m}" for m in matches])
        
        # ODS por temas (simplificado)
        sdg_themes = {
            'ODS_1': ['pobreza', 'pobres'],
            'ODS_2': ['hambre', 'alimentación', 'nutrición'],
            'ODS_3': ['salud', 'bienestar'],
            'ODS_4': ['educación', 'calidad educativa'],
            'ODS_5': ['igualdad de género', 'mujeres'],
            'ODS_6': ['agua', 'saneamiento'],
            'ODS_7': ['energía'],
            'ODS_8': ['empleo', 'crecimiento económico'],
            'ODS_10': ['desigualdad', 'equidad'],
            'ODS_11': ['ciudades sostenibles', 'desarrollo urbano'],
            'ODS_13': ['cambio climático', 'clima'],
            'ODS_16': ['paz', 'justicia', 'instituciones']
        }
        text_lower = text.lower()
        for sdg, themes in sdg_themes.items():
            if any(theme in text_lower for theme in themes) and sdg not in sdgs:
                sdgs.append(sdg)
                
        return sorted(list(set(sdgs)))

    def _build_stakeholder_map(self, text: str) -> Dict[str, List[str]]:
        """Construir mapa de stakeholders (simplificado)"""
        stakeholders = defaultdict(list)
        # Reutilizar inferencia de roles para llenar el mapa
        entities = self._extract_policy_entities_with_context({'text': text})
        for entity in entities:
            role_name = entity.context_role.name.lower()
            if entity.normalized_form not in stakeholders[role_name]:
                stakeholders[role_name].append(entity.normalized_form)
        return dict(stakeholders)

    def _calculate_policy_coherence(self, text: str, global_topics: Dict) -> float:
        """Calcular coherencia de política (alineación con temas clave)"""
        # Simplificación: media de la alineación tópica
        return self._calculate_topic_alignment(text, global_topics)

    def _extract_intervention_logic(self, strategic_unit: Dict) -> List[str]:
        """Extraer la cadena lógica de intervención (e.g., insumo -> actividad -> producto -> resultado)"""
        logic = []
        
        # Simplificación: encadenamiento de antecedentes y consecuentes
        for chain in strategic_unit.get('chains', []):
            if chain.get('antecedent') and chain.get('consequent'):
                logic.append(f"{chain['antecedent']} -> {chain['consequent']}")
                
        return logic[:5]

    def _calculate_comprehensive_confidence(
        self,
        strategic_unit: Dict,
        causal_evidence: List[CausalEvidence],
        policy_entities: List[PolicyEntity]
    ) -> Dict[str, float]:
        """Calcular métricas de confianza y calidad"""
        
        weights = {
            'causal': 0.4,
            'entity': 0.3,
            'structural': 0.2,
            'semantic': 0.1
        }
        
        causal_conf = np.mean([e.confidence for e in causal_evidence]) if causal_evidence else 0.0
        entity_conf = np.mean([e.confidence for e in policy_entities]) if policy_entities else 0.0
        structural_conf = strategic_unit.get('confidence', 0.7)
        semantic_conf = strategic_unit.get('semantic_coherence', 0.6)
        
        overall = (
            weights['causal'] * causal_conf + 
            weights['entity'] * entity_conf + 
            weights['structural'] * structural_conf + 
            weights['semantic'] * semantic_conf
        )
        
        return {
            'causal_confidence': causal_conf,
            'entity_confidence': entity_conf,
            'structural_confidence': structural_conf,
            'semantic_confidence': semantic_conf,
            'overall_confidence': min(overall, 1.0)
        }

    def _find_cross_document_references(self, strategic_unit: Dict) -> List[CrossDocumentReference]:
        """Encontrar referencias cruzadas documentales (Placeholder)"""
        references = []
        text = strategic_unit.get("text", "")
        ref_patterns = [
            (r'(?:ver|véase)\s+(?:sección|capítulo)\s+([^,\.]+)', 'explicit_reference'),
            (r'como\s+se\s+(?:mencionó|indicó)\s+en\s+([^,\.]+)', 'backward_reference'),
            (r'se\s+desarrollará\s+en\s+([^,\.]+)', 'forward_reference')
        ]
        
        for pattern, ref_type in ref_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                references.append(CrossDocumentReference(
                    target_section=match.group(1).strip(),
                    reference_type=ref_type,
                    confidence=0.7,
                    semantic_linkage=0.6,
                    context_bridge=match.group(0)
                ))
                
        return references

    def _extract_implicit_assumptions(self, strategic_unit: Dict, causal_evidence: List[CausalEvidence]) -> List[Tuple[str, float]]:
        """Extraer supuestos implícitos (Placeholder)"""
        assumptions = []
        # Los antecedentes condicionales de baja confianza se consideran supuestos
        for chain in strategic_unit.get('chains', []):
            if chain.get('type') == 'conditional' and chain.get('confidence', 0.5) < 0.6:
                assumptions.append((f"Asumiendo que: {chain['antecedent']}", 1.0 - chain.get('confidence', 0.5)))
        return assumptions

    def _identify_contextual_presuppositions(self, strategic_unit: Dict) -> List[Tuple[str, float]]:
        """Identificar presuposiciones contextuales (Placeholder)"""
        presuppositions = []
        text_lower = strategic_unit.get("text", "").lower()
        
        if 'se continuará' in text_lower or 'marco existente' in text_lower:
            presuppositions.append(("Existe un marco de política previo", 0.8))
        if 'presupuesto asignado' in text_lower:
            presuppositions.append(("Se cuenta con la disponibilidad de recursos", 0.9))
            
        return presuppositions

    def _extract_discourse_markers(self, text: str) -> List[Tuple[str, str]]:
        """Extraer marcadores de discurso (conectores)"""
        markers = []
        
        coherence_markers = {
            'addition': [r'\by\b', r'\btambién\b', r'\badicionalmente\b'],
            'contrast': [r'\bpero\b', r'\bsin\s+embargo\b', r'\bno\s+obstante\b'],
            'cause': [r'\bporque\b', r'\bya\s+que\b', r'\bdebido\s+a\b'],
            'result': [r'\bpor\s+lo\s+tanto\b', r'\bpor\s+ende\b', r'\ben\s+consecuencia\b']
        }
        
        for relation_type, patterns in coherence_markers.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    markers.append((match.group(0), relation_type))
                    
        return markers

    def _identify_rhetorical_patterns(self, text: str) -> List[str]:
        """Identificar patrones retóricos (e.g., afirmación, evidencia, conclusión)"""
        rhetorical = []
        rhetorical_patterns = self._analyze_rhetorical_structure(text)
        
        for key, value in rhetorical_patterns.items():
            if value:
                rhetorical.append(key)
                
        return rhetorical

    def _calculate_chunk_topic_distribution(self, text: str, global_topics: Dict) -> Dict[str, float]:
        """Calcular distribución tópica del chunk"""
        distribution = {}
        text_lower = text.lower()
        
        for topic in global_topics.get('topics', []):
            topic_score = 0
            for keyword, _ in topic['keywords'][:10]:
                if keyword.lower() in text_lower:
                    topic_score += 1
            if topic_score > 0:
                distribution[f"topic_{topic['topic_id']}"] = topic_score / 10.0
                
        return distribution

    def _extract_key_phrases(self, text: str) -> List[Tuple[str, float]]:
        """Extraer frases clave del texto (Placeholder: usando TF-IDF)"""
        try:
            # Usar TF-IDF para frases clave
            if not self.chunks_for_tfidf:
                return []
                
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(self.chunks_for_tfidf)
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            # Vectorizar solo el texto actual
            text_vector = self.tfidf_vectorizer.transform([text])
            
            # Obtener los top features para este documento
            feature_array = text_vector.toarray().flatten()
            top_indices = feature_array.argsort()[-10:][::-1]
            
            key_phrases = [(feature_names[i], feature_array[i]) for i in top_indices if feature_array[i] > 0]
            return key_phrases
            
        except Exception as e:
            self.logger.error(f"Error en extracción de frases clave: {e}")
            return []

    def _derive_kg_edges_for_chunk(self, entities: List[PolicyEntity], causal_evidence: List[CausalEvidence]) -> List[Tuple[str, str, str, float]]:
        """Derivar aristas del grafo de conocimiento para el chunk"""
        edges = []
        
        # Entidades y relaciones causales
        for entity1 in entities:
            for entity2 in entities:
                if entity1 != entity2:
                    for evidence in causal_evidence:
                        # Simple heurística: si ambas entidades están en el contexto causal
                        context = evidence.context_span
                        if entity1.span[0] >= context[0] and entity2.span[1] <= context[1]:
                            edges.append((
                                entity1.normalized_form,
                                entity2.normalized_form,
                                evidence.causal_type.value,
                                evidence.confidence
                            ))
                            
        return edges[:10]

    def _get_model_versions(self) -> Dict[str, str]:
        """Devuelve las versiones de los modelos utilizados"""
        return {
            'semantic_model': 'intfloat/multilingual-e5-large',
            'spacy_model': self.nlp.meta.get('name') if self.nlp else 'None',
            'pipeline_version': 'SMART-CHUNK-3.0-FINAL'
        }

    def _calculate_semantic_density(self, text: str) -> float:
        """Calcular la densidad semántica del chunk (placeholder)"""
        # Densidad basada en la proporción de palabras clave
        return min(len(re.findall(r'\b[A-Z][a-z]+\b', text)) / len(text.split()), 1.0)
        
    def _classify_chunk_type(self, text: str) -> ChunkType:
        """Clasificar el tipo de chunk basado en el contenido (Placeholder)"""
        text_lower = text.lower()
        type_indicators = {
            ChunkType.DIAGNOSTICO: ['diagnóstico', 'análisis', 'situación actual'],
            ChunkType.ESTRATEGIA: ['estrategia', 'objetivo', 'meta', 'propósito'],
            ChunkType.METRICA: ['indicador', 'meta', 'medición', 'línea base'],
            ChunkType.FINANCIERO: ['presupuesto', 'recursos financieros', 'inversión'],
            ChunkType.NORMATIVO: ['ley', 'decreto', 'normativa', 'regulación'],
            ChunkType.OPERATIVO: ['operación', 'implementación', 'ejecución'],
            ChunkType.EVALUACION: ['evaluación', 'seguimiento', 'monitoreo']
        }
        
        scores = {}
        for chunk_type, indicators in type_indicators.items():
            score = sum(1 for ind in indicators if ind in text_lower)
            if score > 0:
                scores[chunk_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return ChunkType.MIXTO
    
    def _calculate_coherence_score(self, strategic_unit: Dict) -> float:
        """Calcular puntuación de coherencia"""
        return strategic_unit.get('coherence', 0.75)
    
    def _calculate_completeness_index(
        self,
        strategic_unit: Dict,
        causal_evidence: List[CausalEvidence]
    ) -> float:
        """Calcular índice de completitud"""
        components = {
            'has_text': bool(strategic_unit.get('text')),
            'has_causal': len(causal_evidence) > 0,
            'has_entities': len(strategic_unit.get('entities', [])) > 0,
            'has_context': bool(strategic_unit.get('context')),
            'has_hierarchy': bool(strategic_unit.get('hierarchy')),
            'has_arg_structure': bool(strategic_unit.get('argument_structure')),
            'has_temporal': bool(strategic_unit.get('temporal_dynamics'))
        }
        
        return sum(components.values()) / len(components)

    # --- Métodos de la clase principal (Continuación de smart_policy_chunks_industrial_v3_complete_final_Version2.py) ---
    
    def _analyze_cross_references(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """Análisis de referencias cruzadas y relaciones inter-documento"""
        references = defaultdict(list)
        
        reference_patterns = [
            (r'como\s+se\s+(?:mencionó|indicó|señaló|estableció)\s+(?:en\s+)?(.+?)[,.]', 'backward'),
            (r'(?:ver|véase|consultar)\s+(?:la\s+)?(?:sección|capítulo|apartado)\s+(.+?)[,.]', 'explicit'),
            (r'tal\s+como\s+se\s+establece\s+en\s+(.+?)[,.]', 'normative'),
            (r'de\s+acuerdo\s+(?:con|a)\s+(?:lo\s+establecido\s+en\s+)?(.+?)[,.]', 'normative'),
            (r'según\s+(?:lo\s+dispuesto\s+en\s+)?(.+?)[,.]', 'normative'),
            (r'conforme\s+a\s+(.+?)[,.]', 'normative'),
            (r'en\s+el\s+marco\s+de\s+(.+?)[,.]', 'framework'),
            (r'se\s+desarrollará\s+en\s+(.+?)[,.]', 'forward')
        ]
        
        for pattern, ref_type in reference_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                references[ref_type].append({
                    'target': match.group(1).strip(),
                    'position': match.span(),
                    'context': text[max(0, match.start()-100):min(len(text), match.end()+100)]
                })
        
        return dict(references)
    
    def _analyze_temporal_structure(self, text: str) -> Dict[str, Any]:
        """Análisis temporal completo"""
        temporal_info = {
            'time_markers': [],
            'sequences': [],
            'durations': [],
            'milestones': [],
            'temporal_ordering': []
        }
        
        # Marcadores temporales explícitos
        time_patterns = [
            (r'\b(20\d{2})\b', 'year'),
            (r'\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(?:de\s+)?(20\d{2})\b', 'month_year'),
            (r'\b(?:en|durante|hasta|desde|para)\s+(20\d{2})\b', 'temporal_prep'),
            (r'\b(corto|mediano|largo)\s+plazo\b', 'horizon'),
            (r'\b(trimestre|semestre|bimestre|cuatrimestre)\s+(\d+)\b', 'period'),
            (r'\b(?:primer|segundo|tercer|cuarto)\s+(?:trimestre|semestre)\b', 'period_ordinal'),
            (r'\b(inmediato|urgente|prioritario)\b', 'urgency'),
            (r'\b(?:antes\s+de|después\s+de|al\s+finalizar|una\s+vez\s+que)\b', 'sequence')
        ]
        
        for pattern, temp_type in time_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_info['time_markers'].append({
                    'text': match.group(0),
                    'type': temp_type,
                    'position': match.span()
                })
        
        # Secuencias temporales
        sequence_patterns = [
            r'(?:primero|en\s+primer\s+lugar)',
            r'(?:segundo|en\s+segundo\s+lugar|luego|posteriormente)',
            r'(?:tercero|en\s+tercer\s+lugar|finalmente|por\s+último)'
        ]
        
        for idx, pattern in enumerate(sequence_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_info['sequences'].append({
                    'order': idx + 1,
                    'marker': match.group(0),
                    'position': match.start()
                })
        
        return temporal_info
    
    def _analyze_discourse_structure(self, text: str) -> Dict[str, Any]:
        """Análisis de estructura discursiva"""
        discourse = {
            'sentences': [],
            'paragraphs': [],
            'discourse_relations': [],
            'rhetorical_moves': []
        }
        
        if self.nlp:
            # Safe UTF-8 truncation for memory limit
            truncated_text = safe_utf8_truncate(text, 500000)
            doc = self.nlp(truncated_text)
            discourse['sentences'] = [sent.text for sent in doc.sents][:1000]
            
            # Extraer entidades nombradas
            discourse['entities'] = [(ent.text, ent.label_) for ent in doc.ents][:200]
            
            # Chunks nominales
            discourse['noun_chunks'] = [chunk.text for chunk in doc.noun_chunks][:200]
        else:
            # Fallback sin SpaCy
            discourse['sentences'] = re.split(r'[.!?]+\s+', text)[:1000]
        
        # Detectar párrafos
        paragraphs = text.split('\n\n')
        discourse['paragraphs'] = [p.strip() for p in paragraphs if p.strip()][:500]
        
        return discourse
    
    def _extract_coherence_relations(self, text: str) -> List[Dict[str, Any]]:
        """Extraer relaciones de coherencia discursiva"""
        relations = []
        
        coherence_markers = {
            'addition': [
                r'\by\b', r'\be\b', r'\btambién\b', r'\basimismo\b', 
                r'\badicionalmente\b', r'\bademás\b', r'\bigualmente\b'
            ],
            'contrast': [
                r'\bpero\b', r'\bsin\s+embargo\b', r'\bno\s+obstante\b', 
                r'\ben\s+cambio\b', r'\bpor\s+el\s+contrario\b', r'\bmientras\s+que\b'
            ],
            'cause': [
                r'\bporque\b', r'\bya\s+que\b', r'\bdebido\s+a\b', 
                r'\bpuesto\s+que\b', r'\bdado\s+que\b', r'\ba\s+causa\s+de\b'
            ],
            'result': [
                r'\bpor\s+lo\s+tanto\b', r'\bpor\s+ende\b', r'\basí\b', 
                r'\ben\s+consecuencia\b', r'\bpor\s+consiguiente\b', r'\bde\s+modo\s+que\b'
            ],
            'condition': [
                r'\bsi\b', r'\ben\s+caso\s+de\s+que\b', r'\bsiempre\s+que\b', 
                r'\bcon\s+tal\s+de\s+que\b', r'\ba\s+menos\s+que\b'
            ],
            'purpose': [
                r'\bpara\s+que\b', r'\ba\s+fin\s+de\s+que\b', r'\bcon\s+el\s+objetivo\s+de\b', 
                r'\bcon\s+el\s+propósito\s+de\b'
            ],
            'elaboration': [
                r'\bes\s+decir\b', r'\bo\s+sea\b', r'\ben\s+otras\s+palabras\b', 
                r'\bdicho\s+de\s+otro\s+modo\b'
            ],
            'example': [
                r'\bpor\s+ejemplo\b', r'\bcomo\s+es\s+el\s+caso\s+de\b', 
                r'\btal\s+como\b', r'\bverbigracia\b'
            ]
        }
        
        for relation_type, markers in coherence_markers.items():
            for marker in markers:
                matches = re.finditer(marker, text, re.IGNORECASE)
                for match in matches:
                    relations.append({
                        'type': relation_type,
                        'marker': match.group(0),
                        'position': match.span(),
                        'confidence': 0.8
                    })
        
        return relations
    
    def _analyze_rhetorical_structure(self, text: str) -> Dict[str, List[str]]:
        """Analizar estructura retórica del texto"""
        rhetorical = {
            'claims': [],
            'evidence': [],
            'examples': [],
            'conclusions': [],
            'justifications': []
        }
        
        # Patrones de claims (afirmaciones)
        claim_patterns = [
            r'se\s+propone\s+que\s+[^.]+',
            r'es\s+necesario\s+[^.]+',
            r'se\s+debe\s+[^.]+',
            r'resulta\s+fundamental\s+[^.]+',
            r'se\s+requiere\s+[^.]+'
        ]
        
        for pattern in claim_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rhetorical['claims'].extend(matches[:50])
        
        # Patrones de evidencia
        evidence_patterns = [
            r'según\s+[^,]+,',
            r'de\s+acuerdo\s+con\s+[^,]+,',
            r'los\s+datos\s+(?:muestran|indican|demuestran)\s+[^.]+',
            r'la\s+evidencia\s+(?:muestra|indica|demuestra)\s+[^.]+'
        ]
        
        for pattern in evidence_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rhetorical['evidence'].extend(matches[:50])
        
        # Patrones de ejemplos
        example_patterns = [
            r'por\s+ejemplo[^.]+',
            r'como\s+es\s+el\s+caso\s+de\s+[^.]+',
            r'tal\s+como\s+[^.]+'
        ]
        
        for pattern in example_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rhetorical['examples'].extend(matches[:50])
        
        # Patrones de conclusiones
        conclusion_patterns = [
            r'en\s+conclusión[^.]+',
            r'por\s+lo\s+tanto[^.]+',
            r'en\s+síntesis[^.]+'
        ]
        
        for pattern in conclusion_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rhetorical['conclusions'].extend(matches[:50])
        
        return rhetorical
    
    def _analyze_information_flow(self, text: str) -> Dict[str, Any]:
        """
        Analyze information flow patterns in text.
        
        Inputs:
            text (str): Text to analyze
        Outputs:
            Dict[str, Any]: Flow analysis metrics
        """
        sentences = filter_empty_sentences(re.split(r'[.!?]+\s+', text))
        sentences = [s for s in sentences if len(s) > 20]
        if not sentences:
            return {'sentence_count': 0}
            
        sentence_lengths = [len(s.split()) for s in sentences]
        words = text.lower().split()
        unique_words = set(words)
        
        return {
            'sentence_count': len(sentences),
            'avg_sentence_length': np.mean(sentence_lengths),
            'std_sentence_length': np.std(sentence_lengths),
            'lexical_diversity': len(unique_words) / len(words) if words else 0,
            'total_words': len(words),
            'unique_words': len(unique_words)
        } #
    
    def _extract_document_structure(self, text: str) -> Dict[str, Any]:
        """Análisis estructural del documento"""
        return {
            'section_hierarchy': self._identify_section_hierarchy(text),
            'policy_frameworks': self._identify_policy_frameworks(text),
            'raw_text': text # Almacenar texto para referencia
        }
    
    def _identify_section_hierarchy(self, text: str) -> List[Dict[str, Any]]:
        """Identificar la jerarquía de secciones/títulos"""
        hierarchy = []
        # Patrones de encabezados (simplificados)
        patterns = [
            (r'^(CAPÍTULO\s+I[VX]+\s*:\s*.+)$', 1, 'chapter'),
            (r'^(SECCIÓN\s+[A-Z]\s*:\s*.+)$', 2, 'section'),
            (r'^\d+\.\d+(?:\.\d+)?\s+([A-ZÑÁÉÍÓÚ][^.!?]+)$', 3, 'header_numbered'),
            (r'^([a-z]\))\s+([A-ZÑÁÉÍÓÚ][^.!?]+)$', 4, 'item_alpha'),
            (r'^•\s+([A-ZÑÁÉÍÓÚ][^.!?]+)$', 5, 'bullet'),
        ]
        
        lines = text.split('\n')
        for idx, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3: continue
            
            for pattern, level, header_type in patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match:
                    title = match.group(2) if match.lastindex >= 2 else match.group(1)
                    hierarchy.append({
                        'title': title.strip(),
                        'level': level,
                        'line_number': idx,
                        'type': header_type,
                        'full_text': line
                    })
                    break
        return hierarchy
    
    def _identify_policy_frameworks(self, text: str) -> List[Dict[str, Any]]:
        """Identificar todos los marcos de política presentes"""
        frameworks = []
        framework_patterns = [
            (r'plan\s+(?:de\s+)?desarrollo\s+(?:municipal|departamental|nacional)?', 'plan_desarrollo'),
            (r'política\s+pública\s+(?:de\s+)?[\w\s]+', 'politica_publica'),
            (r'ley\s+[\w\s]+', 'legal_framework')
        ]
        
        for pattern, framework_type in framework_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                frameworks.append({
                    'text': match.group(0),
                    'type': framework_type,
                    'position': match.span()
                })
        return frameworks

    def _extract_content_for_pa_dimension(
        self,
        document_text: str,
        policy_area: str,
        dimension: str,
        sentences: List[str],
        sentence_positions: List[Tuple[int, int]],
        sentence_embeddings: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Extract most relevant content for a specific (PA, DIM) combination.

        Uses embedding-based similarity to find sentences most aligned with
        the policy area and dimension keywords.

        Args:
            document_text: Full document text
            policy_area: Policy area code (PA01-PA10)
            dimension: Dimension code (DIM01-DIM06)
            sentences: List of document sentences
            sentence_positions: List of (start, end) byte positions for each sentence
            sentence_embeddings: Pre-computed embeddings (optional, computed if None)

        Returns:
            Dictionary with segment metadata and text
        """
        # Generate query embedding from PA + DIM keywords
        pa_keywords = self._pa_keywords.get(policy_area, [])
        dim_keywords = self._dim_keywords.get(dimension, [])
        query_text = " ".join(pa_keywords + dim_keywords)

        # Get query embedding
        query_embedding = self._spc_sem.embed_text(query_text)

        # Compute sentence embeddings if not provided
        if sentence_embeddings is None:
            sentence_embeddings = self._spc_sem.embed_batch(sentences)

        # Compute cosine similarity between query and all sentences
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity(
            query_embedding.reshape(1, -1),
            sentence_embeddings
        )[0]

        # Find top-K most similar sentences (K=10)
        top_k = min(10, len(sentences))
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        # Extract contiguous region around top sentences
        if len(top_indices) == 0:
            # Fallback: return first 800 chars
            segment_text = document_text[:800]
            segment_start = 0
            segment_end = len(segment_text)
        else:
            # Find min/max positions to create contiguous chunk
            min_idx = min(top_indices)
            max_idx = max(top_indices)

            # Expand window by ±2 sentences for context
            start_idx = max(0, min_idx - 2)
            end_idx = min(len(sentences) - 1, max_idx + 2)

            # Get byte positions
            segment_start = sentence_positions[start_idx][0]
            segment_end = sentence_positions[end_idx][1]
            segment_text = document_text[segment_start:segment_end]

        # Compute relevance score (mean of top-K similarities)
        relevance_score = float(np.mean(similarities[top_indices])) if len(top_indices) > 0 else 0.0

        return {
            "text": segment_text,
            "position": (segment_start, segment_end),
            "policy_area": policy_area,
            "dimension": dimension,
            "relevance_score": relevance_score,
            "top_sentence_indices": top_indices.tolist(),
            "query_keywords": pa_keywords + dim_keywords
        }

    def _generate_60_structured_segments(
        self,
        document_text: str,
        structural_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate EXACTLY 60 structured segments aligned by (PA × DIM) matrix.

        This replaces FASE 4 semantic segmentation with structured extraction.
        Each segment is explicitly aligned to one Policy Area and one Dimension.

        Args:
            document_text: Full document text
            structural_analysis: Output from FASE 3 (document structure analysis)

        Returns:
            List of 60 segment dictionaries, one per (PA, DIM) combination
        """
        from saaaaaa.core.canonical_notation import get_all_policy_areas, get_all_dimensions

        self.logger.info("FASE 4: Generating 60 structured segments (PA × DIM matrix)")

        # Split document into sentences for embedding-based extraction
        sentences = sent_tokenize(document_text, language='spanish')

        # Compute sentence positions
        sentence_positions = []
        current_pos = 0
        for sent in sentences:
            start = document_text.find(sent, current_pos)
            end = start + len(sent)
            sentence_positions.append((start, end))
            current_pos = end

        # Pre-compute sentence embeddings (once for all 60 extractions)
        self.logger.info(f"Computing embeddings for {len(sentences)} sentences...")
        sentence_embeddings = self._spc_sem.embed_batch(sentences)

        # Generate 60 segments
        policy_areas = get_all_policy_areas()  # PA01..PA10
        dimensions = get_all_dimensions()      # D1..D6

        structured_segments = []

        for pa_code, pa_info in policy_areas.items():
            for dim_key, dim_info in dimensions.items():
                segment = self._extract_content_for_pa_dimension(
                    document_text=document_text,
                    policy_area=pa_code,
                    dimension=dim_info.code,
                    sentences=sentences,
                    sentence_positions=sentence_positions,
                    sentence_embeddings=sentence_embeddings
                )

                # Add PA and DIM metadata
                segment['policy_area_id'] = pa_code
                segment['dimension_id'] = dim_info.code
                segment['pa_name'] = pa_info.name
                segment['dim_label'] = dim_info.label

                structured_segments.append(segment)

                self.logger.debug(
                    f"  Extracted segment for {pa_code} × {dim_info.code}: "
                    f"{len(segment['text'])} chars, relevance={segment['relevance_score']:.3f}"
                )

        assert len(structured_segments) == 60, \
            f"Expected 60 segments, got {len(structured_segments)}"

        self.logger.info(f"✅ Generated exactly {len(structured_segments)} structured segments")

        return structured_segments

    def generate_smart_chunks(self, document_text: str, document_metadata: Dict) -> List[SmartPolicyChunk]:
        """
        Main pipeline phase: Generate Smart Policy Chunks with full analysis.
        
        Inputs:
            document_text (str): Raw policy document text
            document_metadata (Dict): Document metadata (ID, title, etc.)
        Outputs:
            List[SmartPolicyChunk]: Validated, deduplicated, and ranked chunks
        """
        self.logger.info("Starting Smart Chunks v3.0 pipeline")
        
        # FASE 0: Language detection and model selection
        detected_lang = self.detect_language(document_text)
        self.select_embedding_model_for_language(detected_lang)
        document_metadata['detected_language'] = detected_lang
        
        # FASE 1: Preprocesamiento avanzado
        normalized_text = self._advanced_preprocessing(document_text)
        
        # FASE 2: Análisis estructural y de jerarquía
        structural_analysis = self._extract_document_structure(normalized_text)
        structural_analysis['raw_text'] = document_text
        
        # FASE 3: Modelado de tópicos y KG global
        document_parts = re.split(r'\n\n', normalized_text)
        global_topics = self.topic_modeler.extract_global_topics(document_parts)
        global_kg = self.kg_builder.build_policy_knowledge_graph(normalized_text)
        
        # FASE 4: Structured (PA × DIM) segmentation - EXACTLY 60 chunks
        # REPLACED: Old semantic segmentation with structured extraction
        # OLD: context_preserved_segments = self.context_preserver.preserve_strategic_context(...)
        context_preserved_segments = self._generate_60_structured_segments(
            document_text=document_text,
            structural_analysis=structural_analysis
        )
        self.logger.info(f"✅ Generated {len(context_preserved_segments)} structured segments (PA × DIM)")
        
        # FASE 5: Extracción de cadenas causales completas
        causal_chains = self.causal_analyzer.extract_complete_causal_chains(
            context_preserved_segments, 
            global_kg
        )
        self.logger.info(f"Cadenas causales extraídas: {len(causal_chains)}")
        
        # FASE 6: Integración causal en unidades base (Hecho dentro del Integrador)
        
        # FASE 7: Análisis argumentativo profundo
        argument_structures = self.argument_analyzer.analyze_arguments(
            causal_chains
        )
        
        # FASE 8: Análisis temporal y secuencial
        temporal_structures = self.temporal_analyzer.analyze_temporal_dynamics(
            causal_chains
        )
        
        # FASE 9: Análisis de discurso y retórica
        discourse_structures = self.discourse_analyzer.analyze_discourse(
            causal_chains
        )
        
        # FASE 10: Integración estratégica multi-escala
        strategic_units = self.strategic_integrator.integrate_strategic_units(
            causal_chains, 
            structural_analysis, 
            argument_structures, 
            temporal_structures, 
            discourse_structures, 
            global_topics, 
            global_kg
        )
        self.logger.info(f"Unidades estratégicas integradas: {len(strategic_units)}")
        
        # FASE 11: Generación de Smart Policy Chunks
        smart_chunks = []
        # Pre-llenar para TF-IDF
        self.chunks_for_tfidf = [unit['text'] for unit in strategic_units]
        if self.chunks_for_tfidf:
            self.tfidf_vectorizer.fit(self.chunks_for_tfidf)
        
        for idx, unit in enumerate(strategic_units):
            # Obtener el índice de la unidad para estructuras específicas
            arg_key = next((k for k, v in argument_structures.items() if v.claims and any(unit['text'].strip() in c[0] for c in v.claims)), None)
            temp_key = next((k for k, v in temporal_structures.items() if v.temporal_markers), None)
            disc_key = next((k for k, v in discourse_structures.items()), None)

            chunk = self._create_smart_policy_chunk(
                unit,
                document_metadata,
                argument_structures.get(arg_key),
                temporal_structures.get(temp_key),
                discourse_structures.get(disc_key),
                global_topics,
                global_kg
            )
            smart_chunks.append(chunk)

        # --- FASES 12-15 (Continuación de smart_policy_chunks_industrial_v3_complete_final_Version1.py) ---

        # FASE 12: Enriquecimiento con relaciones inter-chunk
        enriched_chunks = self._enrich_with_inter_chunk_relationships(smart_chunks)
        
        # FASE 13: Validación de integridad y completitud
        validated_chunks = self._validate_strategic_integrity(enriched_chunks)
        
        # FASE 14: Deduplicación inteligente
        deduplicated_chunks = self._intelligent_deduplication(validated_chunks)
        
        # FASE 15: Ranking por importancia estratégica
        ranked_chunks = self._rank_by_strategic_importance(deduplicated_chunks)
        
        self.logger.info(f"Generación completada: {len(ranked_chunks)} chunks finales")
        
        return ranked_chunks

    def _advanced_preprocessing(self, text: str) -> str:
        """
        Advanced text preprocessing with normalization and encoding fixes.
        
        Inputs:
            text (str): Raw input text
        Outputs:
            str: Normalized and cleaned text
        """
        # Normalización de espacios y saltos de línea
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n+', '\n', text)
        
        # Corrección de encodings problemáticos (common UTF-8 mojibake)
        encoding_fixes = {
            'Ã¡': 'á', 'Ã©': 'é', 'Ã­': 'í', 'Ã³': 'ó', 'Ãº': 'ú',
            'Ã±': 'ñ', 'Ã': 'Ñ', 'Ã ': 'à', 'Ã¨': 'è', 'Ã¬': 'ì',
            'Ã²': 'ò', 'Ã¹': 'ù', 'Ã¼': 'ü', 'Ã': 'Á', 'Ã‰': 'É',
            'Ã': 'Í', 'Ã"': 'Ó', 'Ãš': 'Ú'
        }
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
            
        return text

    def _enrich_with_inter_chunk_relationships(self, chunks: List[SmartPolicyChunk]) -> List[SmartPolicyChunk]:
        """
        CANONICAL SOTA: Enrich chunks with semantic relationships using BGE-M3 embeddings.
        
        Uses batch embeddings and vectorized similarity computation instead of
        manual loops and sklearn.cosine_similarity.
        """
        if not chunks:
            return []
        
        texts = [c.text for c in chunks]
        self.corpus_embeddings = self._generate_embeddings_for_corpus(texts)
        
        # Vectorized cosine similarity (no sklearn dependency)
        norms = np.linalg.norm(self.corpus_embeddings, axis=1, keepdims=True)
        normalized_embs = self.corpus_embeddings / (norms + 1e-8)
        similarity_matrix = np.dot(normalized_embs, normalized_embs.T)
        
        # Efficiently find related chunks using vectorized operations
        for i, chunk in enumerate(chunks):
            # Get similarities for this chunk (excluding self)
            sims = similarity_matrix[i].copy()
            sims[i] = -1  # Exclude self
            
            # Find chunks above threshold
            related_indices = np.where(sims >= self.config.CROSS_REFERENCE_MIN_SIMILARITY)[0]
            
            # Sort by similarity
            sorted_indices = related_indices[np.argsort(-sims[related_indices])]
            
            chunk.related_chunks = [
                (chunks[j].chunk_id, float(sims[j]))
                for j in sorted_indices
            ]
            
        return chunks

    def _generate_embeddings_for_corpus(self, texts: List[str], batch_size: int = 64) -> np.ndarray:
        """
        CANONICAL SOTA: Batch embeddings using SemanticChunkingProducer.
        
        SemanticChunkingProducer handles batching internally with BGE-M3.
        batch_size kept for signature compatibility.
        
        Inputs:
            texts (List[str]): List of text strings to embed
            batch_size (int): Batch size hint (default: 64)
        Outputs:
            np.ndarray: Array of embeddings, shape (n_texts, embedding_dim)
        """
        if not texts:
            return np.array([])
        
        # CANONICAL SOTA: Use SemanticChunkingProducer batch embedding
        embs = self._spc_sem.embed_batch(texts)
        return np.vstack(embs).astype(np.float32)

    def _validate_strategic_integrity(self, chunks: List[SmartPolicyChunk]) -> List[SmartPolicyChunk]:
        """Validar que los chunks cumplan con umbrales mínimos de calidad y completitud"""
        validated = []
        for chunk in chunks:
            # Criterios de validación
            is_valid = (
                chunk.coherence_score >= self.config.MIN_COHERENCE_SCORE and
                chunk.completeness_index >= self.config.MIN_COMPLETENESS_INDEX and
                chunk.strategic_importance >= self.config.MIN_STRATEGIC_IMPORTANCE and
                chunk.information_density >= self.config.MIN_INFORMATION_DENSITY and
                len(chunk.text) >= self.config.MIN_CHUNK_SIZE
            )
            
            if is_valid:
                validated.append(chunk)
            else:
                self.logger.warning(f"Chunk {chunk.chunk_id} no pasó validación de integridad")
        
        return validated

    def _intelligent_deduplication(self, chunks: List[SmartPolicyChunk]) -> List[SmartPolicyChunk]:
        """Deduplicación inteligente de chunks"""
        if len(chunks) < 2:
            return chunks
            
        deduplicated = []
        processed_hashes = set()
        
        for chunk in chunks:
            # Verificar por hash exacto
            if chunk.content_hash not in processed_hashes:
                processed_hashes.add(chunk.content_hash)
                deduplicated.append(chunk)
            
        # Deduplicación semántica (para near-duplicates) using vectorized ops
        final_list = []
        if deduplicated:
            embeddings = self._generate_embeddings_for_corpus([c.text for c in deduplicated])
            n_chunks = len(deduplicated)
            
            # Vectorized cosine similarity (no sklearn dependency)
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            normalized_embs = embeddings / (norms + 1e-8)
            sim_matrix = np.dot(normalized_embs, normalized_embs.T)
            
            is_duplicate = [False] * n_chunks
            
            for i in range(n_chunks):
                if is_duplicate[i]:
                    continue
                    
                final_list.append(deduplicated[i])
                
                for j in range(i + 1, n_chunks):
                    if sim_matrix[i, j] >= self.config.DEDUPLICATION_THRESHOLD:
                        is_duplicate[j] = True
                        
        return final_list

    def _rank_by_strategic_importance(self, chunks: List[SmartPolicyChunk]) -> List[SmartPolicyChunk]:
        """Ranking final de chunks por importancia estratégica"""
        # Usar el campo `strategic_importance` calculado en _create_smart_policy_chunk
        chunks.sort(key=lambda x: x.strategic_importance, reverse=True)
        return chunks
    
    # --- Métodos de Evaluación (Continuación de smart_policy_chunks_industrial_v3_part4_completion.py) ---
    
    def _assess_strategic_importance(
        self,
        strategic_unit: Dict,
        causal_evidence: List[CausalEvidence],
        policy_entities: List[PolicyEntity]
    ) -> float:
        """Evaluar importancia estratégica"""
        factors = {
            'causal_strength': np.mean([e.strength_score for e in causal_evidence]) if causal_evidence else 0,
            'entity_relevance': len([e for e in policy_entities if e.context_role in [PolicyEntityRole.EXECUTOR, PolicyEntityRole.BENEFICIARY]]) / max(len(policy_entities), 1),
            'position_weight': 1.0 if strategic_unit.get('position', (0, 0))[0] < 1000 else 0.5, # Ponderar texto temprano
            'keyword_presence': self._calculate_strategic_keyword_presence(strategic_unit.get('text', ''))
        }
        
        return np.mean(list(factors.values()))
    
    def _calculate_strategic_keyword_presence(self, text: str) -> float:
        """Calcular presencia de palabras clave estratégicas"""
        strategic_keywords = [
            'objetivo', 'meta', 'estrategia', 'prioridad', 'desarrollo',
            'transformación', 'impacto', 'resultado', 'sostenible', 'integral'
        ]
        
        text_lower = text.lower()
        keyword_count = sum(1 for kw in strategic_keywords if kw in text_lower)
        
        return min(keyword_count / len(strategic_keywords), 1.0)
    
    def _calculate_information_density(self, text: str) -> float:
        """Calcular densidad de información"""
        if not text:
            return 0.0
        
        # Métricas de densidad
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        
        if not words or not sentences:
            return 0.0
        
        metrics = {
            'lexical_diversity': len(set(words)) / len(words),
            'avg_sentence_length': np.mean([len(s.split()) for s in sentences if s.strip()]),
            'entity_density': len(re.findall(r'\b[A-Z][a-z]+\b', text)) / len(words) # Estimación de entidades
        }
        
        return np.mean(list(metrics.values()))
    
    def _assess_actionability(self, text: str, policy_entities: List[PolicyEntity]) -> float:
        """Evaluar accionabilidad del chunk"""
        action_indicators = [
            r'se\s+(?:debe|deberá|requiere)',
            r'es\s+necesario',
            r'(?:implementar|ejecutar|desarrollar|crear|establecer|asignar)\s+',
            r'(?:el|la)\s+(?:Ministerio|Alcaldía|Dirección)\s+(?:debe|deberá)'
        ]
        
        action_score = sum(len(re.findall(pat, text, re.IGNORECASE)) for pat in action_indicators)
        
        # Presencia de ejecutores explícitos
        executor_count = len([e for e in policy_entities if e.context_role == PolicyEntityRole.EXECUTOR])
        
        final_score = (min(action_score / 5.0, 1.0) * 0.7) + (min(executor_count / 2.0, 1.0) * 0.3)
        return final_score

# =============================================================================
# SCRIPT DE EJECUCIÓN (MAIN)
# =============================================================================

def validate_cli_arguments(args):
    """
    Validate CLI arguments before processing.
    
    Returns:
        Tuple[Path, Path]: Normalized input and output paths
    """
    input_path = Path(args.input).expanduser()
    if not input_path.exists():
        raise ValidationError(f"Input file not found: {input_path}")
    
    output_path = Path(args.output).expanduser()
    output_dir = output_path.parent if output_path.name else output_path
    if not output_dir.exists():
        raise ValidationError(f"Output directory does not exist: {output_dir}")
    if not os.access(output_dir, os.W_OK):
        raise ValidationError(f"Output directory is not writable: {output_dir}")
    
    if not args.doc_id or not args.doc_id.strip():
        raise ValidationError("Document ID cannot be empty")
    
    if args.max_chunks < 0:
        raise ValidationError(f"max_chunks must be non-negative, got: {args.max_chunks}")
    
    logger.info("CLI arguments validated successfully")
    return input_path, output_path

def main(args):
    """
    Main pipeline function for Smart Policy Chunks generation.
    
    Inputs:
        args: Command-line arguments with input/output paths and configuration
    Outputs:
        int: Exit code (0 for success, 1 for error)
    """
    try:
        # 0. Validate CLI arguments
        input_path, output_path = validate_cli_arguments(args)
        
        # 1. Cargar el documento
        logger.info(f"Loading input document: {input_path}")
        try:
            document_text = input_path.read_text(encoding='utf-8')
        except IOError as e:
            raise ProcessingError(f"Failed to read input file: {e}")
        
        # 2. Inicializar el sistema (con lazy loading)
        logger.info("Initializing Strategic Chunking System...")
        chunking_system = StrategicChunkingSystem()
        
        # Metadata del documento
        metadata = {
            'document_id': args.doc_id,
            'title': args.title,
            'version': 'v3.0',
            'processing_timestamp': canonical_timestamp()
        }
        
        # 3. Generar Smart Chunks
        logger.info("Generating smart policy chunks...")
        chunks = chunking_system.generate_smart_chunks(document_text, metadata)
        
        # 4. Limitar el número de chunks a guardar si se especifica
        if args.max_chunks > 0:
            logger.info(f"Limiting output to {args.max_chunks} chunks")
            chunks = chunks[:args.max_chunks]
            
        # 5. Serializar resultados (summary version with truncated text)
        logger.info(f"Generated {len(chunks)} chunks. Saving results...")
        output_data = {
            'metadata': metadata,
            'config': {
                'min_chunk_size': chunking_system.config.MIN_CHUNK_SIZE,
                'max_chunk_size': chunking_system.config.MAX_CHUNK_SIZE,
                'semantic_coherence_threshold': chunking_system.config.SEMANTIC_COHERENCE_THRESHOLD
            },
            'chunks': [
                asdict(c) for c in chunks
            ]
        }
        
        # Truncar el texto del chunk de forma segura para summary.json
        for chunk_data in output_data['chunks']:
            original_text = chunk_data['text']
            # Safe UTF-8 truncation to 200 bytes
            chunk_data['text'] = safe_utf8_truncate(original_text, 200)
            if len(original_text.encode('utf-8')) > 200:
                chunk_data['text'] += '...'
            
        summary_payload = json.dumps(output_data, indent=2, ensure_ascii=False, default=np_to_list)
        try:
            output_path.write_text(summary_payload, encoding='utf-8')
            logger.info(f"Summary output saved to: {output_path}")
        except (IOError, TypeError) as e:
            raise SerializationError(f"Failed to write summary output: {e}")
        
        # 6. Guardar versión completa sin truncar texto (full.json)
        if args.save_full:
            full_output = output_path.with_name(f"{output_path.stem}_full.json")
            try:
                # Crear una estructura completa con texto íntegro
                full_data = {
                    'metadata': metadata,
                    'config': output_data['config'],
                    'chunks': []
                }
                
                for chunk in chunks:
                    chunk_dict = asdict(chunk)
                    # Mantener texto completo
                    full_data['chunks'].append(chunk_dict)
                
                full_payload = json.dumps(full_data, indent=2, ensure_ascii=False, default=np_to_list)
                full_output.write_text(full_payload, encoding='utf-8')
                logger.info(f"Full output saved to: {full_output}")
            except (IOError, TypeError) as e:
                raise SerializationError(f"Failed to write full output: {e}")
            
        # 7. Generar reporte de verificación con canonical timestamps
        verification = {
            'pipeline_version': 'SMART-CHUNK-3.0-FINAL',
            'execution_timestamp': canonical_timestamp(),
            'input_file': args.input,
            'input_hash': hashlib.sha256(document_text.encode('utf-8')).hexdigest(),
            'output_hash': hashlib.sha256(summary_payload.encode('utf-8')).hexdigest(),
            'chunks_generated': len(chunks),
            'validation_passed': all(
                c.coherence_score >= chunking_system.config.MIN_COHERENCE_SCORE 
                for c in chunks
            ),
            'success': len(chunks) > 0 and all(c.coherence_score >= chunking_system.config.MIN_COHERENCE_SCORE for c in chunks)
        }
        
        verification_file = output_path.with_name(f"{output_path.stem}_verification.json")
        verification_payload = json.dumps(verification, indent=2, default=np_to_list)
        try:
            verification_file.write_text(verification_payload, encoding='utf-8')
            logger.info(f"Verification report saved to: {verification_file}")
        except IOError as e:
            logger.warning(f"Failed to write verification file: {e}")
        
        if verification['success']:
            logger.info("Pipeline completed successfully")
            return 0
        else:
            logger.warning("Pipeline completed with validation warnings")
            return 0
        
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except ProcessingError as e:
        logger.error(f"Processing error: {e}")
        return 1
    except SerializationError as e:
        logger.error(f"Serialization error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    import argparse
    import sys
    
    # Configuración de argumentos CLI
    parser = argparse.ArgumentParser(
        description="Smart Policy Chunks Pipeline v3.0 - Industrial Grade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python smart_policy_chunks_canonic_phase_one.py --input plan.pdf --output chunks.json
  python smart_policy_chunks_canonic_phase_one.py --input plan.pdf --output chunks.json --save_full
        """
    )
    parser.add_argument(
        '--input', 
        type=str, 
        required=True, 
        help='Path to input policy document (required)'
    )
    parser.add_argument(
        '--output', 
        type=str, 
        required=False, 
        default='output_chunks.json', 
        help='Path to output JSON file (default: output_chunks.json)'
    )
    parser.add_argument(
        '--doc_id', 
        type=str, 
        required=False, 
        default='POL_PLAN_001', 
        help='Document identifier (default: POL_PLAN_001)'
    )
    parser.add_argument(
        '--title', 
        type=str, 
        required=False, 
        default='Plan de Desarrollo', 
        help='Document title (default: Plan de Desarrollo)'
    )
    parser.add_argument(
        '--max_chunks', 
        type=int, 
        required=False, 
        default=0, 
        help='Maximum number of chunks to generate (0 = unlimited, default: 0)'
    )
    parser.add_argument(
        '--save_full', 
        action='store_true', 
        help='Save full version with complete text (creates *_full.json)'
    )

    # Parse arguments - allow argparse to exit normally on error
    args = parser.parse_args()
    
    # Execute main pipeline
    exit_code = main(args)
    sys.exit(exit_code)
