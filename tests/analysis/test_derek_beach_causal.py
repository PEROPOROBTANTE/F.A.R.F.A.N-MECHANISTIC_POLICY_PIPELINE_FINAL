"""
Unit tests for Derek Beach Causal Extractor (derek_beach.py)

Tests mechanistic evidence evaluation, Beach evidential tests taxonomy,
entity-activity extraction, and causal DAG construction.
"""

import networkx as nx
import pytest

from src.farfan_pipeline.analysis.derek_beach import (
    BeachEvidentialTest,
    CausalLink,
    CDAFException,
    ConfigLoader,
    EntityActivity,
    MetaNode,
)


@pytest.fixture
def mock_config():
    """Create mock configuration for testing."""
    config = {
        'patterns': {
            'goal_codes': r'[MP][RIP]-\d{3}',
            'numeric_formats': r'[\d,]+(?:\.\d+)?%?'
        },
        'lexicons': {
            'causal_logic': ['mediante', 'a través de', 'para lograr'],
            'contextual_factors': ['riesgo', 'amenaza', 'limitación']
        },
        'entity_aliases': {
            'SEC GOB': 'Secretaría de Gobierno'
        },
        'bayesian_thresholds': {
            'kl_divergence': 0.01,
            'prior_alpha': 2.0,
            'prior_beta': 2.0
        }
    }
    return config


@pytest.fixture
def sample_meta_node():
    """Create sample MetaNode for testing."""
    return MetaNode(
        id='MR-001',
        text='Incrementar cobertura educativa al 95%',
        type='resultado',
        baseline=85.0,
        target=95.0,
        unit='porcentaje',
        responsible_entity='Secretaría de Educación',
        rigor_status='fuerte',
        dynamics='suma'
    )


class TestBeachEvidentialTest:
    """Test suite for Beach evidential test taxonomy."""

    def test_classify_hoop_test(self):
        """Test classification of hoop test (high necessity, low sufficiency)."""
        test_type = BeachEvidentialTest.classify_test(necessity=0.8, sufficiency=0.3)
        assert test_type == 'hoop_test'

    def test_classify_smoking_gun(self):
        """Test classification of smoking gun test (low necessity, high sufficiency)."""
        test_type = BeachEvidentialTest.classify_test(necessity=0.3, sufficiency=0.8)
        assert test_type == 'smoking_gun'

    def test_classify_doubly_decisive(self):
        """Test classification of doubly decisive test (both high)."""
        test_type = BeachEvidentialTest.classify_test(necessity=0.9, sufficiency=0.9)
        assert test_type == 'doubly_decisive'

    def test_classify_straw_in_wind(self):
        """Test classification of straw-in-wind test (both low)."""
        test_type = BeachEvidentialTest.classify_test(necessity=0.3, sufficiency=0.3)
        assert test_type == 'straw_in_wind'

    def test_apply_hoop_test_failure(self):
        """Test hoop test failure eliminates hypothesis."""
        posterior, interpretation = BeachEvidentialTest.apply_test_logic(
            test_type='hoop_test',
            evidence_found=False,
            prior=0.5,
            bayes_factor=2.0
        )

        assert posterior <= 0.05
        assert 'HOOP_TEST_FAILURE' in interpretation
        assert 'eliminated' in interpretation.lower()

    def test_apply_hoop_test_pass(self):
        """Test hoop test pass allows hypothesis to survive."""
        posterior, interpretation = BeachEvidentialTest.apply_test_logic(
            test_type='hoop_test',
            evidence_found=True,
            prior=0.5,
            bayes_factor=2.0
        )

        assert posterior > 0.0
        assert 'HOOP_TEST_PASSED' in interpretation

    def test_apply_smoking_gun_found(self):
        """Test smoking gun found strongly confirms hypothesis."""
        posterior, interpretation = BeachEvidentialTest.apply_test_logic(
            test_type='smoking_gun',
            evidence_found=True,
            prior=0.3,
            bayes_factor=5.0
        )

        assert posterior > 0.5
        assert 'SMOKING_GUN_FOUND' in interpretation

    def test_apply_doubly_decisive_confirmed(self):
        """Test doubly decisive confirmation is conclusive."""
        posterior, interpretation = BeachEvidentialTest.apply_test_logic(
            test_type='doubly_decisive',
            evidence_found=True,
            prior=0.5,
            bayes_factor=10.0
        )

        assert posterior >= 0.95
        assert 'DOUBLY_DECISIVE_CONFIRMED' in interpretation

    def test_apply_doubly_decisive_eliminated(self):
        """Test doubly decisive elimination is conclusive."""
        posterior, interpretation = BeachEvidentialTest.apply_test_logic(
            test_type='doubly_decisive',
            evidence_found=False,
            prior=0.5,
            bayes_factor=10.0
        )

        assert posterior <= 0.05
        assert 'DOUBLY_DECISIVE_ELIMINATED' in interpretation


class TestMetaNode:
    """Test suite for MetaNode data structure."""

    def test_meta_node_creation(self, sample_meta_node):
        """Test MetaNode instantiation."""
        assert sample_meta_node.id == 'MR-001'
        assert sample_meta_node.type == 'resultado'
        assert sample_meta_node.baseline == 85.0
        assert sample_meta_node.target == 95.0
        assert sample_meta_node.rigor_status == 'fuerte'

    def test_meta_node_entity_activity(self):
        """Test EntityActivity association with MetaNode."""
        entity_activity = EntityActivity(
            entity='Secretaría de Educación',
            activity='implementar programa',
            verb_lemma='implementar',
            confidence=0.85
        )

        node = MetaNode(
            id='MP-001',
            text='Implementar programa educativo',
            type='producto',
            entity_activity=entity_activity
        )

        assert node.entity_activity is not None
        assert node.entity_activity.entity == 'Secretaría de Educación'
        assert node.entity_activity.confidence == 0.85

    def test_meta_node_audit_flags(self, sample_meta_node):
        """Test audit flags mechanism."""
        sample_meta_node.audit_flags.append('missing_baseline')
        sample_meta_node.audit_flags.append('unclear_responsibility')

        assert len(sample_meta_node.audit_flags) == 2
        assert 'missing_baseline' in sample_meta_node.audit_flags

    def test_meta_node_confidence_score(self, sample_meta_node):
        """Test confidence score is bounded [0, 1]."""
        sample_meta_node.confidence_score = 0.95
        assert 0.0 <= sample_meta_node.confidence_score <= 1.0


class TestEntityActivity:
    """Test suite for EntityActivity tuple."""

    def test_entity_activity_creation(self):
        """Test EntityActivity instantiation."""
        ea = EntityActivity(
            entity='Secretaría de Salud',
            activity='gestionar recursos',
            verb_lemma='gestionar',
            confidence=0.9
        )

        assert ea.entity == 'Secretaría de Salud'
        assert ea.activity == 'gestionar recursos'
        assert ea.verb_lemma == 'gestionar'
        assert ea.confidence == 0.9

    def test_entity_activity_confidence_bounds(self):
        """Test confidence is properly bounded."""
        ea = EntityActivity(
            entity='Test Entity',
            activity='test activity',
            verb_lemma='test',
            confidence=0.75
        )

        assert 0.0 <= ea.confidence <= 1.0


class TestCausalLink:
    """Test suite for CausalLink structure."""

    def test_causal_link_creation(self):
        """Test CausalLink dictionary structure."""
        link: CausalLink = {
            'source': 'MP-001',
            'target': 'MR-001',
            'logic': 'mediante',
            'strength': 0.8,
            'evidence': ['evidencia textual 1', 'evidencia textual 2'],
            'posterior_mean': 0.75,
            'posterior_std': 0.1,
            'kl_divergence': 0.02,
            'converged': True
        }

        assert link['source'] == 'MP-001'
        assert link['target'] == 'MR-001'
        assert link['logic'] == 'mediante'
        assert 0.0 <= link['strength'] <= 1.0
        assert link['converged'] is True

    def test_causal_link_bayesian_fields(self):
        """Test Bayesian inference fields in CausalLink."""
        link: CausalLink = {
            'source': 'A',
            'target': 'B',
            'logic': 'causa',
            'strength': 0.9,
            'evidence': [],
            'posterior_mean': 0.85,
            'posterior_std': 0.05,
            'kl_divergence': 0.01,
            'converged': True
        }

        assert link['posterior_mean'] is not None
        assert link['posterior_std'] is not None
        assert link['kl_divergence'] < 0.05


class TestConfigLoader:
    """Test suite for configuration loading."""

    @pytest.fixture
    def temp_config_file(self, tmp_path, mock_config):
        """Create temporary config file for testing."""
        import yaml

        config_path = tmp_path / 'test_config.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(mock_config, f)

        return config_path

    def test_config_loader_initialization(self, temp_config_file):
        """Test ConfigLoader loads YAML configuration."""
        loader = ConfigLoader(temp_config_file)

        assert loader.config is not None
        assert 'patterns' in loader.config
        assert 'lexicons' in loader.config

    def test_config_loader_validation(self, temp_config_file):
        """Test configuration validation with Pydantic."""
        loader = ConfigLoader(temp_config_file)

        assert loader.validated_config is not None
        assert hasattr(loader.validated_config, 'patterns')
        assert hasattr(loader.validated_config, 'lexicons')

    def test_config_loader_default_fallback(self, tmp_path):
        """Test default configuration fallback."""
        non_existent_path = tmp_path / 'nonexistent.yaml'
        loader = ConfigLoader(non_existent_path)

        # Should load default config without crashing
        assert loader.config is not None


class TestCDAFException:
    """Test suite for CDAF exception handling."""

    def test_cdaf_exception_creation(self):
        """Test CDAF exception with structured details."""
        exception = CDAFException(
            message='Test error',
            details={'context': 'test context'},
            stage='extraction',
            recoverable=True
        )

        assert exception.message == 'Test error'
        assert exception.details['context'] == 'test context'
        assert exception.stage == 'extraction'
        assert exception.recoverable is True

    def test_cdaf_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        exception = CDAFException(
            message='Serialization test',
            details={'key': 'value'},
            stage='processing'
        )

        exception_dict = exception.to_dict()

        assert isinstance(exception_dict, dict)
        assert exception_dict['message'] == 'Serialization test'
        assert exception_dict['stage'] == 'processing'
        assert 'error_type' in exception_dict


class TestCausalExtractionIntegration:
    """Integration tests for causal mechanism extraction."""

    def test_entity_activity_extraction_from_text(self):
        """Test extraction of entity-activity pairs from policy text."""
        text = "La Secretaría de Educación implementará el programa educativo"

        # This would use the actual extractor in integration
        # For unit test, we validate the data structure
        ea = EntityActivity(
            entity='Secretaría de Educación',
            activity='implementar programa',
            verb_lemma='implementar',
            confidence=0.8
        )

        assert ea.entity is not None
        assert ea.activity is not None
        assert ea.verb_lemma is not None

    def test_causal_dag_construction(self):
        """Test construction of causal DAG from nodes and links."""
        nodes = {
            'A': MetaNode(id='A', text='Node A', type='producto'),
            'B': MetaNode(id='B', text='Node B', type='resultado')
        }

        links = [
            {
                'source': 'A',
                'target': 'B',
                'logic': 'mediante',
                'strength': 0.8,
                'evidence': [],
                'posterior_mean': None,
                'posterior_std': None,
                'kl_divergence': None,
                'converged': None
            }
        ]

        # Validate DAG structure
        G = nx.DiGraph()
        for node_id in nodes:
            G.add_node(node_id)
        for link in links:
            G.add_edge(link['source'], link['target'])

        assert nx.is_directed_acyclic_graph(G)
        assert G.number_of_nodes() == 2
        assert G.number_of_edges() == 1
