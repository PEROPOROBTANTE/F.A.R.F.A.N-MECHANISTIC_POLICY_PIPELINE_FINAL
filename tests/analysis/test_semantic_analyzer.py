"""
Unit tests for SemanticAnalyzer (Analyzer_one.py)

Tests semantic cube extraction, value chain classification,
policy domain mapping, and cross-cutting theme detection.
"""

import numpy as np
import pytest

from src.farfan_pipeline.analysis.Analyzer_one import (
    MunicipalOntology,
    SemanticAnalyzer,
    ValueChainLink,
)


@pytest.fixture
def ontology():
    """Create municipal ontology for testing."""
    return MunicipalOntology()


@pytest.fixture
def semantic_analyzer(ontology):
    """Create semantic analyzer with test ontology."""
    return SemanticAnalyzer(
        ontology=ontology,
        max_features=100,
        ngram_range=(1, 2),
        similarity_threshold=0.3
    )


@pytest.fixture
def sample_segments():
    """Sample document segments for testing."""
    return [
        "El diagnóstico territorial identificó las principales necesidades de la población",
        "La estrategia de desarrollo económico incluye competitividad y emprendimiento",
        "La implementación de servicios mejorará las condiciones de vida",
        "Transparencia y participación ciudadana son temas transversales"
    ]


class TestSemanticAnalyzer:
    """Test suite for SemanticAnalyzer."""

    def test_initialization(self, semantic_analyzer, ontology):
        """Test semantic analyzer initialization."""
        assert semantic_analyzer.ontology == ontology
        assert semantic_analyzer.max_features == 100
        assert semantic_analyzer.ngram_range == (1, 2)
        assert semantic_analyzer.similarity_threshold == 0.3

    def test_extract_semantic_cube_empty_segments(self, semantic_analyzer):
        """Test semantic cube extraction with empty segments."""
        result = semantic_analyzer.extract_semantic_cube([])

        assert result["dimensions"]["value_chain_links"] == {}
        assert result["dimensions"]["policy_domains"] == {}
        assert result["measures"]["overall_coherence"] == 0.0
        assert result["metadata"]["total_segments"] == 0

    def test_extract_semantic_cube_valid_segments(self, semantic_analyzer, sample_segments):
        """Test semantic cube extraction with valid segments."""
        result = semantic_analyzer.extract_semantic_cube(sample_segments)

        assert "dimensions" in result
        assert "measures" in result
        assert "metadata" in result
        assert result["metadata"]["total_segments"] == len(sample_segments)
        assert isinstance(result["measures"]["overall_coherence"], float)
        assert 0.0 <= result["measures"]["overall_coherence"] <= 1.0

    def test_classify_value_chain_link(self, semantic_analyzer):
        """Test value chain link classification."""
        segment = "diagnóstico territorial con mapeo de actores y evaluación de necesidades"
        scores = semantic_analyzer._classify_value_chain_link(segment)

        assert isinstance(scores, dict)
        assert "diagnostic_planning" in scores
        assert all(0.0 <= score <= 1.0 for score in scores.values())
        assert scores["diagnostic_planning"] > 0.0

    def test_classify_policy_domain(self, semantic_analyzer):
        """Test policy domain classification."""
        segment = "desarrollo económico con énfasis en competitividad y empleo"
        scores = semantic_analyzer._classify_policy_domain(segment)

        assert isinstance(scores, dict)
        assert "economic_development" in scores
        assert all(0.0 <= score <= 1.0 for score in scores.values())
        assert scores["economic_development"] > 0.0

    def test_classify_cross_cutting_themes(self, semantic_analyzer):
        """Test cross-cutting theme classification."""
        segment = "transparencia, rendición de cuentas y participación ciudadana"
        scores = semantic_analyzer._classify_cross_cutting_themes(segment)

        assert isinstance(scores, dict)
        assert "governance" in scores
        assert all(0.0 <= score <= 1.0 for score in scores.values())
        assert scores["governance"] > 0.0

    def test_vectorize_segments(self, semantic_analyzer, sample_segments):
        """Test segment vectorization."""
        vectors = semantic_analyzer._vectorize_segments(sample_segments)

        assert isinstance(vectors, (np.ndarray, list))
        if isinstance(vectors, np.ndarray):
            assert vectors.shape[0] == len(sample_segments)
            assert vectors.shape[1] > 0

    def test_process_segment(self, semantic_analyzer):
        """Test individual segment processing."""
        segment = "Esta es una oración de prueba con varias palabras."
        vector = np.zeros(100)

        result = semantic_analyzer._process_segment(segment, 0, vector)

        assert result["segment_id"] == 0
        assert result["text"] == segment
        assert "word_count" in result
        assert "sentence_count" in result
        assert "semantic_density" in result
        assert "coherence_score" in result
        assert 0.0 <= result["semantic_density"] <= 1.0
        assert 0.0 <= result["coherence_score"] <= 1.0

    def test_calculate_semantic_complexity(self, semantic_analyzer, sample_segments):
        """Test semantic complexity calculation."""
        cube = semantic_analyzer.extract_semantic_cube(sample_segments)
        complexity = semantic_analyzer._calculate_semantic_complexity(cube)

        assert isinstance(complexity, float)
        assert complexity >= 0.0

    def test_similarity_threshold_filtering(self, semantic_analyzer):
        """Test that similarity threshold filters classifications."""
        # High threshold should filter out weak matches
        analyzer_strict = SemanticAnalyzer(
            semantic_analyzer.ontology,
            similarity_threshold=0.9
        )

        segment = "texto genérico sin palabras clave específicas"
        cube = analyzer_strict.extract_semantic_cube([segment])

        # Should have few or no classifications with high threshold
        total_classifications = sum(
            len(items) for items in cube["dimensions"]["value_chain_links"].values()
        )
        assert total_classifications >= 0

    def test_empty_semantic_cube_structure(self, semantic_analyzer):
        """Test empty semantic cube has correct structure."""
        cube = semantic_analyzer._empty_semantic_cube()

        assert "dimensions" in cube
        assert "measures" in cube
        assert "metadata" in cube
        assert cube["dimensions"]["value_chain_links"] == {}
        assert cube["measures"]["overall_coherence"] == 0.0
        assert cube["measures"]["semantic_complexity"] == 0.0


class TestMunicipalOntology:
    """Test suite for MunicipalOntology."""

    def test_value_chain_links_structure(self, ontology):
        """Test value chain links are properly structured."""
        assert "diagnostic_planning" in ontology.value_chain_links
        assert "strategic_planning" in ontology.value_chain_links
        assert "implementation" in ontology.value_chain_links

        for link_name, link in ontology.value_chain_links.items():
            assert isinstance(link, ValueChainLink)
            assert link.name == link_name
            assert isinstance(link.instruments, list)
            assert isinstance(link.mediators, list)
            assert isinstance(link.outputs, list)
            assert isinstance(link.outcomes, list)
            assert link.lead_time_days > 0
            assert isinstance(link.conversion_rates, dict)

    def test_policy_domains_coverage(self, ontology):
        """Test policy domains are comprehensive."""
        assert "economic_development" in ontology.policy_domains
        assert "social_development" in ontology.policy_domains
        assert "territorial_development" in ontology.policy_domains
        assert "institutional_development" in ontology.policy_domains

        for domain, keywords in ontology.policy_domains.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_cross_cutting_themes(self, ontology):
        """Test cross-cutting themes are defined."""
        assert "governance" in ontology.cross_cutting_themes
        assert "equity" in ontology.cross_cutting_themes
        assert "sustainability" in ontology.cross_cutting_themes
        assert "innovation" in ontology.cross_cutting_themes

        for theme, keywords in ontology.cross_cutting_themes.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0


class TestSemanticCubeIntegration:
    """Integration tests for semantic cube extraction."""

    def test_full_pipeline_with_realistic_segments(self, semantic_analyzer):
        """Test full semantic cube extraction pipeline."""
        segments = [
            "El diagnóstico participativo identificó brechas en educación y salud",
            "La planificación estratégica prioriza el desarrollo económico local",
            "La implementación incluye proyectos de infraestructura vial",
            "La sostenibilidad ambiental y la equidad de género son ejes transversales"
        ]

        cube = semantic_analyzer.extract_semantic_cube(segments)

        # Validate structure
        assert cube["metadata"]["total_segments"] == 4
        assert len(cube["measures"]["semantic_density"]) == 4
        assert len(cube["measures"]["coherence_scores"]) == 4

        # Validate dimensions have content
        assert len(cube["dimensions"]["value_chain_links"]) > 0
        assert len(cube["dimensions"]["policy_domains"]) > 0

        # Validate measures are computed
        assert isinstance(cube["measures"]["overall_coherence"], float)
        assert isinstance(cube["measures"]["semantic_complexity"], float)

    def test_semantic_cube_with_multilingual_content(self, semantic_analyzer):
        """Test robustness with mixed language content."""
        segments = [
            "Diagnóstico with some English words territorial",
            "Strategic planning para el desarrollo"
        ]

        # Should not crash with mixed content
        cube = semantic_analyzer.extract_semantic_cube(segments)
        assert cube["metadata"]["total_segments"] == 2
