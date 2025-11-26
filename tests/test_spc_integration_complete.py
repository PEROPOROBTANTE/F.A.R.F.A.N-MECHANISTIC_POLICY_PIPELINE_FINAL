"""
Integration Test: SPC Phase 1 to Orchestrator Pipeline
=======================================================

This test verifies the complete integration between:
1. SmartPolicyChunk output from StrategicChunkingSystem
2. SmartChunkConverter conversion layer
3. CanonPolicyPackage format for orchestrator
4. PreprocessedDocument.ensure() acceptance

Tests the critical data flow identified in the audit.
"""

import pytest
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from saaaaaa.processing.cpp_ingestion.models import (
    CanonPolicyPackage,
    ChunkGraph,
    Chunk,
    ChunkResolution,
    TextSpan,
    PolicyFacet,
    TimeFacet,
    GeoFacet,
    Confidence,
)
from saaaaaa.processing.spc_ingestion.converter import SmartChunkConverter
from saaaaaa.core.orchestrator.core import PreprocessedDocument


# Mock SmartPolicyChunk for testing (simplified version)
class ChunkType(Enum):
    DIAGNOSTICO = "diagnostico"
    ESTRATEGIA = "estrategia"
    METRICA = "metrica"
    FINANCIERO = "financiero"
    MIXTO = "mixto"


@dataclass
class MockCausalEvidence:
    dimension: str
    confidence: float


@dataclass
class MockPolicyEntity:
    text: str
    entity_type: str
    confidence: float


@dataclass
class MockStrategicContext:
    policy_intent: str
    implementation_phase: str
    geographic_scope: str
    temporal_horizon: str
    budget_linkage: str


@dataclass
class MockSmartPolicyChunk:
    """Simplified mock of SmartPolicyChunk for testing."""
    chunk_id: str
    document_id: str
    content_hash: str
    text: str
    normalized_text: str
    semantic_density: float
    section_hierarchy: List[str]
    document_position: Tuple[int, int]
    chunk_type: ChunkType
    causal_chain: List[MockCausalEvidence] = field(default_factory=list)
    policy_entities: List[MockPolicyEntity] = field(default_factory=list)
    related_chunks: List[Tuple[str, float]] = field(default_factory=list)
    confidence_metrics: Dict[str, float] = field(default_factory=dict)
    coherence_score: float = 0.8
    completeness_index: float = 0.85
    strategic_importance: float = 0.75
    information_density: float = 0.7
    actionability_score: float = 0.8
    strategic_context: Optional[MockStrategicContext] = None
    temporal_dynamics: Any = None


def create_mock_smart_chunks() -> List[MockSmartPolicyChunk]:
    """Create mock SmartPolicyChunk instances for testing."""
    chunks = []

    # Macro-level strategic chunk
    chunks.append(MockSmartPolicyChunk(
        chunk_id="strategic_axis_1",
        document_id="test_plan_2024",
        content_hash="hash_001",
        text="EJE ESTRATÉGICO 1: DESARROLLO SOCIAL. Visión 2028: Garantizar acceso universal a educación y salud de calidad.",
        normalized_text="eje estrategico desarrollo social",
        semantic_density=0.85,
        section_hierarchy=["Desarrollo Social", "Objetivos Estratégicos"],
        document_position=(0, 120),
        chunk_type=ChunkType.ESTRATEGIA,
        causal_chain=[
            MockCausalEvidence(dimension="impactos", confidence=0.9)
        ],
        policy_entities=[
            MockPolicyEntity(text="Ministerio de Educación", entity_type="institution", confidence=0.95)
        ],
        related_chunks=[("programa_educacion", 0.82)],
        confidence_metrics={"extraction_confidence": 0.95},
        coherence_score=0.92,
        completeness_index=0.88,
        strategic_importance=0.95,
        strategic_context=MockStrategicContext(
            policy_intent="Desarrollo Social Universal",
            implementation_phase="2024-2028",
            geographic_scope="Departamental",
            temporal_horizon="2024-2028",
            budget_linkage="$150,000 millones COP"
        )
    ))

    # Meso-level program chunk
    chunks.append(MockSmartPolicyChunk(
        chunk_id="programa_educacion",
        document_id="test_plan_2024",
        content_hash="hash_002",
        text="Programa: Educación para Todos. Objetivo: Cobertura del 95% en educación primaria para 2026.",
        normalized_text="programa educacion para todos",
        semantic_density=0.78,
        section_hierarchy=["Desarrollo Social", "Educación", "Programa"],
        document_position=(121, 220),
        chunk_type=ChunkType.METRICA,
        causal_chain=[
            MockCausalEvidence(dimension="productos", confidence=0.85)
        ],
        policy_entities=[
            MockPolicyEntity(text="Secretaría de Educación", entity_type="institution", confidence=0.90)
        ],
        related_chunks=[("strategic_axis_1", 0.82), ("proyecto_escuelas", 0.75)],
        confidence_metrics={"extraction_confidence": 0.90},
        coherence_score=0.85,
        completeness_index=0.82,
        strategic_importance=0.80
    ))

    # Micro-level project chunk
    chunks.append(MockSmartPolicyChunk(
        chunk_id="proyecto_escuelas",
        document_id="test_plan_2024",
        content_hash="hash_003",
        text="Proyecto: Construcción de 20 escuelas rurales. Presupuesto: $45,000 millones. Plazo: 2024-2026.",
        normalized_text="proyecto construccion escuelas rurales",
        semantic_density=0.82,
        section_hierarchy=["Desarrollo Social", "Educación", "Proyectos", "Escuelas Rurales"],
        document_position=(221, 340),
        chunk_type=ChunkType.FINANCIERO,
        causal_chain=[
            MockCausalEvidence(dimension="actividades", confidence=0.88)
        ],
        policy_entities=[
            MockPolicyEntity(text="población rural", entity_type="beneficiary", confidence=0.85)
        ],
        related_chunks=[("programa_educacion", 0.75)],
        confidence_metrics={"extraction_confidence": 0.92},
        coherence_score=0.87,
        completeness_index=0.90,
        strategic_importance=0.70,
        strategic_context=MockStrategicContext(
            policy_intent="Infraestructura Educativa Rural",
            implementation_phase="2024-2026",
            geographic_scope="Zonas Rurales",
            temporal_horizon="2024-2026",
            budget_linkage="$45,000 millones COP"
        )
    ))

    return chunks


class TestSPCIntegrationComplete:
    """Test complete SPC to Orchestrator integration."""

    def test_converter_initialization(self):
        """Test that SmartChunkConverter can be initialized."""
        converter = SmartChunkConverter()
        assert converter is not None
        assert hasattr(converter, 'convert_to_canon_package')

    def test_smart_chunk_to_canon_package_conversion(self):
        """Test conversion from SmartPolicyChunk to CanonPolicyPackage."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {
            'document_id': 'test_plan_2024',
            'title': 'Plan de Desarrollo 2024-2028',
            'version': 'v3.0'
        }
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Assert - Package structure
        assert isinstance(canon_package, CanonPolicyPackage)
        assert canon_package.schema_version == "SPC-2025.1"
        assert canon_package.chunk_graph is not None
        assert canon_package.policy_manifest is not None
        assert canon_package.quality_metrics is not None
        assert canon_package.integrity_index is not None

    def test_chunk_graph_structure(self):
        """Test that ChunkGraph is properly constructed."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)
        chunk_graph = canon_package.chunk_graph

        # Assert - Chunks
        assert isinstance(chunk_graph, ChunkGraph)
        assert len(chunk_graph.chunks) == 3
        assert "strategic_axis_1" in chunk_graph.chunks
        assert "programa_educacion" in chunk_graph.chunks
        assert "proyecto_escuelas" in chunk_graph.chunks

        # Assert - Chunk structure
        for chunk_id, chunk in chunk_graph.chunks.items():
            assert isinstance(chunk, Chunk)
            assert chunk.id == chunk_id
            assert chunk.text is not None and len(chunk.text) > 0
            assert isinstance(chunk.text_span, TextSpan)
            assert isinstance(chunk.resolution, ChunkResolution)
            assert chunk.bytes_hash is not None

        # Assert - Edges
        assert len(chunk_graph.edges) > 0
        for edge in chunk_graph.edges:
            assert len(edge) == 3  # (from, to, relation_type)
            assert edge[0] in chunk_graph.chunks  # from_id exists
            assert edge[1] in chunk_graph.chunks  # to_id exists

    def test_resolution_mapping(self):
        """Test that chunk_type is correctly mapped to ChunkResolution."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Assert - Resolution mapping
        strategic_chunk = canon_package.chunk_graph.chunks["strategic_axis_1"]
        assert strategic_chunk.resolution == ChunkResolution.MACRO  # ESTRATEGIA → MACRO

        program_chunk = canon_package.chunk_graph.chunks["programa_educacion"]
        assert program_chunk.resolution == ChunkResolution.MICRO  # METRICA → MICRO

        project_chunk = canon_package.chunk_graph.chunks["proyecto_escuelas"]
        assert project_chunk.resolution == ChunkResolution.MICRO  # FINANCIERO → MICRO

    def test_policy_facets_extraction(self):
        """Test that policy facets are extracted from SPC data."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Assert
        strategic_chunk = canon_package.chunk_graph.chunks["strategic_axis_1"]
        assert isinstance(strategic_chunk.policy_facets, PolicyFacet)
        assert len(strategic_chunk.policy_facets.axes) > 0

        project_chunk = canon_package.chunk_graph.chunks["proyecto_escuelas"]
        assert len(project_chunk.policy_facets.programs) > 0 or len(project_chunk.policy_facets.projects) > 0

    def test_quality_metrics_calculation(self):
        """Test that quality metrics are calculated from SPC data."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)
        metrics = canon_package.quality_metrics

        # Assert
        assert metrics.provenance_completeness >= 0.0
        assert metrics.structural_consistency >= 0.0
        assert metrics.structural_consistency <= 1.0
        assert metrics.chunk_context_coverage >= 0.0

    def test_spc_rich_data_preservation(self):
        """Test that SPC rich data is preserved in metadata."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Assert - Rich data in metadata
        assert 'spc_rich_data' in canon_package.metadata
        assert 'spc_version' in canon_package.metadata
        assert canon_package.metadata['spc_version'] == 'SMART-CHUNK-3.0-FINAL'

        spc_data = canon_package.metadata['spc_rich_data']
        assert len(spc_data) == 3  # One entry per chunk

        # Check that quality scores are preserved
        for chunk_id in ['strategic_axis_1', 'programa_educacion', 'proyecto_escuelas']:
            assert chunk_id in spc_data
            chunk_spc_data = spc_data[chunk_id]
            assert 'coherence_score' in chunk_spc_data
            assert 'strategic_importance' in chunk_spc_data
            assert 'completeness_index' in chunk_spc_data

    def test_orchestrator_compatibility(self):
        """Test that CanonPolicyPackage is accepted by PreprocessedDocument.ensure()."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Act - Try to convert to PreprocessedDocument
        try:
            preprocessed = PreprocessedDocument.ensure(
                canon_package,
                document_id="test_plan_2024",
                use_spc_ingestion=True
            )

            # Assert - Orchestrator acceptance
            assert isinstance(preprocessed, PreprocessedDocument)
            assert preprocessed.document_id == "test_plan_2024"
            assert len(preprocessed.raw_text) > 0
            assert len(preprocessed.sentences) > 0

        except Exception as e:
            pytest.fail(f"PreprocessedDocument.ensure() rejected CanonPolicyPackage: {e}")

    def test_policy_manifest_completeness(self):
        """Test that PolicyManifest is properly populated."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)
        manifest = canon_package.policy_manifest

        # Assert
        assert len(manifest.axes) > 0
        assert len(manifest.programs) > 0
        assert len(manifest.projects) > 0
        # Years might be empty if not extracted from temporal dynamics

    def test_integrity_index_generation(self):
        """Test that IntegrityIndex is generated with valid hashes."""
        # Arrange
        smart_chunks = create_mock_smart_chunks()
        metadata = {'document_id': 'test_plan_2024', 'title': 'Test', 'version': 'v3.0'}
        converter = SmartChunkConverter()

        # Act
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)
        integrity = canon_package.integrity_index

        # Assert
        assert integrity.blake2b_root is not None
        assert len(integrity.blake2b_root) > 0
        assert len(integrity.chunk_hashes) == 3
        for chunk_id in ['strategic_axis_1', 'programa_educacion', 'proyecto_escuelas']:
            assert chunk_id in integrity.chunk_hashes

    def test_end_to_end_data_flow(self):
        """
        End-to-end test: SmartPolicyChunk → CanonPolicyPackage → PreprocessedDocument

        This test validates the complete data flow identified in the audit.
        """
        # Phase 1: SPC produces SmartPolicyChunks
        smart_chunks = create_mock_smart_chunks()
        metadata = {
            'document_id': 'test_plan_2024',
            'title': 'Plan de Desarrollo Departamental 2024-2028',
            'version': 'v3.0'
        }

        # Phase 2: Converter bridges to CanonPolicyPackage
        converter = SmartChunkConverter()
        canon_package = converter.convert_to_canon_package(smart_chunks, metadata)

        # Phase 3: Orchestrator accepts CanonPolicyPackage
        preprocessed = PreprocessedDocument.ensure(
            canon_package,
            document_id="test_plan_2024",
            use_spc_ingestion=True
        )

        # Validate end-to-end flow
        assert preprocessed.document_id == "test_plan_2024"
        assert len(preprocessed.sentences) == 3  # One per chunk
        assert 'spc_rich_data' in preprocessed.metadata
        assert preprocessed.metadata['chunk_count'] == 3

        # Verify data preservation through pipeline
        assert 'policy_manifest' in preprocessed.metadata
        assert 'quality_metrics' in preprocessed.metadata

        # Success: Complete pipeline verified!


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
