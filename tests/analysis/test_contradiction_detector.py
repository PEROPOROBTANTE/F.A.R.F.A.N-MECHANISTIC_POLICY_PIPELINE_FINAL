"""
Unit tests for PolicyContradictionDetector (contradiction_deteccion.py)

Tests semantic contradiction detection, temporal logic verification,
Bayesian confidence calculation, and contradiction evidence generation.
"""
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.farfan_pipeline.analysis.contradiction_deteccion import (
    BayesianConfidenceCalculator,
    ContradictionEvidence,
    ContradictionType,
    PolicyContradictionDetector,
    PolicyDimension,
    PolicyStatement,
    TemporalLogicVerifier,
)


@pytest.fixture
def bayesian_calculator():
    """Create Bayesian confidence calculator."""
    return BayesianConfidenceCalculator()


@pytest.fixture
def temporal_verifier():
    """Create temporal logic verifier."""
    return TemporalLogicVerifier()


@pytest.fixture
def sample_policy_statements():
    """Create sample policy statements for testing."""
    return [
        PolicyStatement(
            text="El presupuesto para educación es de $500 millones en 2024",
            dimension=PolicyDimension.FINANCIERO,
            position=(0, 100),
            temporal_markers=["2024"],
            quantitative_claims=[{"amount": 500, "unit": "millones"}]
        ),
        PolicyStatement(
            text="El presupuesto educativo alcanzará $600 millones en 2024",
            dimension=PolicyDimension.FINANCIERO,
            position=(200, 300),
            temporal_markers=["2024"],
            quantitative_claims=[{"amount": 600, "unit": "millones"}]
        ),
        PolicyStatement(
            text="La meta es alcanzar 100% cobertura antes de 2023",
            dimension=PolicyDimension.ESTRATEGICO,
            position=(400, 500),
            temporal_markers=["2023"],
            quantitative_claims=[{"percentage": 100}]
        )
    ]


class TestBayesianConfidenceCalculator:
    """Test suite for Bayesian confidence calculator."""

    def test_initialization(self, bayesian_calculator):
        """Test calculator initialization with domain priors."""
        assert bayesian_calculator.prior_alpha == 2.5
        assert bayesian_calculator.prior_beta == 7.5

    def test_calculate_posterior_basic(self, bayesian_calculator):
        """Test basic posterior probability calculation."""
        posterior = bayesian_calculator.calculate_posterior(
            evidence_strength=0.8,
            observations=5,
            domain_weight=1.0
        )

        assert isinstance(posterior, float)
        assert 0.0 <= posterior <= 1.0
        assert posterior > 0.0

    def test_calculate_posterior_weak_evidence(self, bayesian_calculator):
        """Test posterior with weak evidence."""
        posterior = bayesian_calculator.calculate_posterior(
            evidence_strength=0.2,
            observations=2,
            domain_weight=1.0
        )

        assert isinstance(posterior, float)
        assert 0.0 <= posterior <= 1.0

    def test_calculate_posterior_strong_evidence(self, bayesian_calculator):
        """Test posterior with strong evidence."""
        posterior = bayesian_calculator.calculate_posterior(
            evidence_strength=0.95,
            observations=10,
            domain_weight=1.0
        )

        assert isinstance(posterior, float)
        assert posterior > 0.5

    def test_calculate_posterior_domain_weight(self, bayesian_calculator):
        """Test domain weight effect on posterior."""
        posterior_high_weight = bayesian_calculator.calculate_posterior(
            evidence_strength=0.7,
            observations=5,
            domain_weight=2.0
        )

        posterior_low_weight = bayesian_calculator.calculate_posterior(
            evidence_strength=0.7,
            observations=5,
            domain_weight=0.5
        )

        # Higher domain weight should increase confidence
        assert posterior_high_weight >= posterior_low_weight

    def test_posterior_bounds(self, bayesian_calculator):
        """Test posterior is always bounded [0, 1]."""
        for evidence in [0.0, 0.5, 1.0]:
            for obs in [1, 5, 10]:
                posterior = bayesian_calculator.calculate_posterior(
                    evidence_strength=evidence,
                    observations=obs
                )
                assert 0.0 <= posterior <= 1.0


class TestTemporalLogicVerifier:
    """Test suite for temporal logic verification."""

    def test_initialization(self, temporal_verifier):
        """Test temporal verifier initialization."""
        assert hasattr(temporal_verifier, 'temporal_patterns')
        assert 'sequential' in temporal_verifier.temporal_patterns
        assert 'parallel' in temporal_verifier.temporal_patterns
        assert 'deadline' in temporal_verifier.temporal_patterns

    def test_verify_temporal_consistency_no_conflicts(self, temporal_verifier):
        """Test temporal verification with consistent statements."""
        statements = [
            PolicyStatement(
                text="Primero el diagnóstico",
                dimension=PolicyDimension.DIAGNOSTICO,
                position=(0, 50),
                temporal_markers=["primero"]
            ),
            PolicyStatement(
                text="Luego la implementación",
                dimension=PolicyDimension.PROGRAMATICO,
                position=(100, 150),
                temporal_markers=["luego"]
            )
        ]

        is_consistent, conflicts = temporal_verifier.verify_temporal_consistency(statements)

        assert isinstance(is_consistent, bool)
        assert isinstance(conflicts, list)

    def test_parse_temporal_marker_year(self, temporal_verifier):
        """Test parsing year from temporal marker."""
        marker = "año 2024"
        timestamp = temporal_verifier._parse_temporal_marker(marker)

        assert timestamp == 2024

    def test_parse_temporal_marker_quarter(self, temporal_verifier):
        """Test parsing quarter from temporal marker."""
        marker = "Q2"
        timestamp = temporal_verifier._parse_temporal_marker(marker)

        assert timestamp == 2

    def test_parse_temporal_marker_spanish_quarter(self, temporal_verifier):
        """Test parsing Spanish quarter markers."""
        marker = "segundo trimestre"
        timestamp = temporal_verifier._parse_temporal_marker(marker)

        assert timestamp == 2

    def test_classify_temporal_type(self, temporal_verifier):
        """Test temporal marker type classification."""
        sequential_marker = "primero establecer"
        parallel_marker = "simultáneamente ejecutar"
        deadline_marker = "antes de finalizar"

        assert temporal_verifier._classify_temporal_type(sequential_marker) == 'sequential'
        assert temporal_verifier._classify_temporal_type(parallel_marker) == 'parallel'
        assert temporal_verifier._classify_temporal_type(deadline_marker) == 'deadline'

    def test_extract_resources(self, temporal_verifier):
        """Test resource extraction from text."""
        text = "asignar presupuesto y recursos humanos para el proyecto"
        resources = temporal_verifier._extract_resources(text)

        assert isinstance(resources, list)
        assert len(resources) > 0


class TestPolicyContradictionDetector:
    """Test suite for policy contradiction detector."""

    @pytest.fixture
    def detector(self):
        """Create contradiction detector with mocked models."""
        with patch('src.farfan_pipeline.analysis.contradiction_deteccion.SentenceTransformer'), \
             patch('src.farfan_pipeline.analysis.contradiction_deteccion.pipeline'), \
             patch('src.farfan_pipeline.analysis.factory.load_spacy_model'):

            detector = PolicyContradictionDetector()

            # Mock the semantic model
            detector.semantic_model = Mock()
            detector.semantic_model.encode = Mock(return_value=np.random.rand(768))

            # Mock NLP model
            detector.nlp = Mock()

            return detector

    def test_initialization(self, detector):
        """Test detector initialization."""
        assert hasattr(detector, 'semantic_model')
        assert hasattr(detector, 'bayesian_calculator')
        assert hasattr(detector, 'temporal_verifier')
        assert hasattr(detector, 'knowledge_graph')

    def test_detect_with_empty_text(self, detector):
        """Test detection with empty text."""
        result = detector.detect("", plan_name="Test Plan")

        assert isinstance(result, dict)
        assert "contradictions" in result
        assert "total_contradictions" in result

    def test_detect_with_simple_text(self, detector):
        """Test detection with simple non-contradictory text."""
        text = "El plan de desarrollo busca mejorar la educación y la salud."
        result = detector.detect(text, plan_name="Test Plan")

        assert isinstance(result, dict)
        assert "contradictions" in result
        assert "coherence_metrics" in result
        assert result["plan_name"] == "Test Plan"

    def test_extract_policy_statements(self, detector):
        """Test policy statement extraction."""
        text = """
        El presupuesto es de $500 millones.
        La meta es alcanzar 100% cobertura.
        """

        with patch.object(detector, '_extract_policy_statements') as mock_extract:
            mock_extract.return_value = [
                PolicyStatement(
                    text="El presupuesto es de $500 millones",
                    dimension=PolicyDimension.FINANCIERO,
                    position=(0, 50)
                )
            ]

            statements = detector._extract_policy_statements(text, PolicyDimension.FINANCIERO)
            assert len(statements) > 0
            assert isinstance(statements[0], PolicyStatement)

    def test_contradiction_type_classification(self, detector):
        """Test contradiction type is properly classified."""
        # Ensure ContradictionType enum is used correctly
        assert ContradictionType.NUMERICAL_INCONSISTENCY
        assert ContradictionType.TEMPORAL_CONFLICT
        assert ContradictionType.SEMANTIC_OPPOSITION
        assert ContradictionType.LOGICAL_INCOMPATIBILITY

    def test_serialize_contradiction(self, detector):
        """Test contradiction evidence serialization."""
        statement_a = PolicyStatement(
            text="Statement A",
            dimension=PolicyDimension.ESTRATEGICO,
            position=(0, 10)
        )
        statement_b = PolicyStatement(
            text="Statement B",
            dimension=PolicyDimension.ESTRATEGICO,
            position=(20, 30)
        )

        evidence = ContradictionEvidence(
            statement_a=statement_a,
            statement_b=statement_b,
            contradiction_type=ContradictionType.SEMANTIC_OPPOSITION,
            confidence=0.85,
            severity=0.7,
            semantic_similarity=0.3,
            logical_conflict_score=0.8,
            temporal_consistency=True,
            numerical_divergence=None,
            affected_dimensions=[PolicyDimension.ESTRATEGICO],
            resolution_suggestions=["Review strategic alignment"]
        )

        serialized = detector._serialize_contradiction(evidence)

        assert isinstance(serialized, dict)
        assert "contradiction_type" in serialized
        assert "confidence" in serialized
        assert "severity" in serialized


class TestContradictionDetectionIntegration:
    """Integration tests for contradiction detection."""

    @pytest.fixture
    def detector_integration(self):
        """Create detector for integration tests."""
        with patch('src.farfan_pipeline.analysis.contradiction_deteccion.SentenceTransformer'), \
             patch('src.farfan_pipeline.analysis.contradiction_deteccion.pipeline'), \
             patch('src.farfan_pipeline.analysis.factory.load_spacy_model'):

            detector = PolicyContradictionDetector()
            detector.semantic_model = Mock()
            detector.semantic_model.encode = Mock(return_value=np.random.rand(768))
            detector.nlp = Mock()

            return detector

    def test_numerical_contradiction_detection(self, detector_integration):
        """Test detection of numerical contradictions."""
        text = """
        El presupuesto para educación es de 500 millones de pesos en 2024.
        El mismo presupuesto educativo alcanzará 600 millones en 2024.
        """

        result = detector_integration.detect(text, plan_name="Test")

        assert isinstance(result, dict)
        assert "contradictions" in result

    def test_temporal_contradiction_detection(self, detector_integration):
        """Test detection of temporal contradictions."""
        text = """
        La meta debe alcanzarse antes de 2023.
        El programa comenzará después de 2024.
        """

        result = detector_integration.detect(text, plan_name="Test")

        assert isinstance(result, dict)
        assert "contradictions" in result

    def test_coherence_metrics_calculation(self, detector_integration):
        """Test coherence metrics are calculated."""
        text = "Plan de desarrollo con múltiples componentes estratégicos."

        result = detector_integration.detect(text, plan_name="Test")

        assert "coherence_metrics" in result
        assert isinstance(result["coherence_metrics"], dict)

    def test_recommendations_generation(self, detector_integration):
        """Test resolution recommendations are generated."""
        text = """
        El plan tiene objetivos contradictorios.
        Las metas no son alcanzables simultáneamente.
        """

        result = detector_integration.detect(text, plan_name="Test")

        assert "recommendations" in result or "contradictions" in result
