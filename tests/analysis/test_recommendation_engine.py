"""
Unit tests for Recommendation Engine (recommendation_engine.py)

Tests rule-based recommendation generation at MICRO, MESO, and MACRO levels,
template rendering, and condition evaluation.
"""
from datetime import datetime

import pytest

from src.farfan_pipeline.analysis.recommendation_engine import (
    Recommendation,
    RecommendationEngine,
    RecommendationSet,
)


@pytest.fixture
def mock_rules():
    """Create mock recommendation rules."""
    return {
        'version': '2.0',
        'rules': [
            {
                'rule_id': 'MICRO-001',
                'level': 'MICRO',
                'when': {
                    'pa_id': 'PA01',
                    'dim_id': 'DIM01',
                    'score_lt': 2.0
                },
                'template': {
                    'problem': 'Problema en {{PAxx}}-{{DIMxx}}',
                    'intervention': 'Implementar mejoras',
                    'indicator': {'name': 'Indicador test'},
                    'responsible': {'entity': 'Secretaría'},
                    'horizon': {'short': '3 meses'},
                    'verification': ['Verificar resultados']
                }
            },
            {
                'rule_id': 'MESO-001',
                'level': 'MESO',
                'when': {
                    'cluster_id': 'CL01',
                    'score_band': 'BAJO',
                    'variance_level': 'ALTA'
                },
                'template': {
                    'problem': 'Cluster {{cluster_id}} con alto riesgo',
                    'intervention': 'Intervención cluster',
                    'indicator': {'name': 'Indicador cluster'},
                    'responsible': {'entity': 'Equipo'},
                    'horizon': {'medium': '6 meses'},
                    'verification': ['Verificar cluster']
                }
            },
            {
                'rule_id': 'MACRO-001',
                'level': 'MACRO',
                'when': {
                    'overall_score_lt': 65.0
                },
                'template': {
                    'problem': 'Plan con calificación baja',
                    'intervention': 'Revisión estratégica',
                    'indicator': {'name': 'Indicador macro'},
                    'responsible': {'entity': 'Alcaldía'},
                    'horizon': {'long': '12 meses'},
                    'verification': ['Auditoría externa']
                }
            }
        ]
    }


@pytest.fixture
def mock_schema():
    """Create mock JSON schema."""
    return {
        'type': 'object',
        'properties': {
            'version': {'type': 'string'},
            'rules': {'type': 'array'}
        },
        'required': ['version', 'rules']
    }


@pytest.fixture
def recommendation_engine(tmp_path, mock_rules, mock_schema):
    """Create recommendation engine with mock files."""
    # Create temporary rules file
    rules_path = tmp_path / 'rules.json'
    schema_path = tmp_path / 'schema.json'

    import json
    with open(rules_path, 'w') as f:
        json.dump(mock_rules, f)
    with open(schema_path, 'w') as f:
        json.dump(mock_schema, f)

    return RecommendationEngine(
        rules_path=str(rules_path),
        schema_path=str(schema_path)
    )


class TestRecommendationEngine:
    """Test suite for RecommendationEngine."""

    def test_initialization(self, recommendation_engine):
        """Test engine initialization."""
        assert recommendation_engine is not None
        assert len(recommendation_engine.rules_by_level['MICRO']) > 0
        assert len(recommendation_engine.rules_by_level['MESO']) > 0
        assert len(recommendation_engine.rules_by_level['MACRO']) > 0

    def test_generate_micro_recommendations_no_match(self, recommendation_engine):
        """Test MICRO recommendations with no matching rules."""
        scores = {
            'PA01-DIM01': 3.0,  # Above threshold
            'PA02-DIM01': 2.5
        }

        result = recommendation_engine.generate_micro_recommendations(scores)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MICRO'
        assert len(result.recommendations) == 0

    def test_generate_micro_recommendations_with_match(self, recommendation_engine):
        """Test MICRO recommendations with matching rule."""
        scores = {
            'PA01-DIM01': 1.5,  # Below threshold of 2.0
            'PA02-DIM01': 2.5
        }

        result = recommendation_engine.generate_micro_recommendations(scores)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MICRO'
        assert len(result.recommendations) > 0
        assert result.recommendations[0].rule_id == 'MICRO-001'

    def test_micro_recommendation_metadata(self, recommendation_engine):
        """Test MICRO recommendation includes metadata."""
        scores = {'PA01-DIM01': 1.0}

        result = recommendation_engine.generate_micro_recommendations(scores)

        rec = result.recommendations[0]
        assert 'score_key' in rec.metadata
        assert 'actual_score' in rec.metadata
        assert 'threshold' in rec.metadata
        assert rec.metadata['score_key'] == 'PA01-DIM01'

    def test_generate_meso_recommendations_no_match(self, recommendation_engine):
        """Test MESO recommendations with no matching rules."""
        cluster_data = {
            'CL01': {
                'score': 75.0,  # ALTO
                'variance': 0.05,  # BAJA
                'weak_pa': 'PA01'
            }
        }

        result = recommendation_engine.generate_meso_recommendations(cluster_data)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MESO'

    def test_generate_meso_recommendations_with_match(self, recommendation_engine):
        """Test MESO recommendations with matching rule."""
        cluster_data = {
            'CL01': {
                'score': 50.0,  # BAJO
                'variance': 0.25,  # ALTA
                'weak_pa': 'PA02'
            }
        }

        result = recommendation_engine.generate_meso_recommendations(cluster_data)

        assert isinstance(result, RecommendationSet)
        assert len(result.recommendations) > 0

    def test_generate_macro_recommendations(self, recommendation_engine):
        """Test MACRO recommendations generation."""
        plan_metrics = {
            'overall_score': 60.0,  # Below threshold
            'coverage': 0.75,
            'coherence': 0.80
        }

        result = recommendation_engine.generate_macro_recommendations(plan_metrics)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MACRO'

    def test_template_rendering_micro(self, recommendation_engine):
        """Test MICRO template variable substitution."""
        template = {
            'problem': 'Problema en {{PAxx}}-{{DIMxx}}',
            'intervention': 'Intervención',
            'indicator': {},
            'responsible': {},
            'horizon': {},
            'verification': []
        }

        rendered = recommendation_engine._render_micro_template(
            template, 'PA01', 'DIM02', {}
        )

        assert 'PA01' in rendered['problem']
        assert 'DIM02' in rendered['problem']

    def test_reload_rules(self, recommendation_engine):
        """Test hot-reloading of rules."""
        initial_count = len(recommendation_engine.rules_by_level['MICRO'])

        # Reload should work without error
        recommendation_engine.reload_rules()

        reloaded_count = len(recommendation_engine.rules_by_level['MICRO'])
        assert reloaded_count == initial_count


class TestRecommendation:
    """Test suite for Recommendation data structure."""

    def test_recommendation_creation(self):
        """Test recommendation creation."""
        rec = Recommendation(
            rule_id='TEST-001',
            level='MICRO',
            problem='Test problem',
            intervention='Test intervention',
            indicator={'name': 'Test indicator'},
            responsible={'entity': 'Test entity'},
            horizon={'short': '3 months'},
            verification=['Test verification']
        )

        assert rec.rule_id == 'TEST-001'
        assert rec.level == 'MICRO'
        assert rec.problem == 'Test problem'

    def test_recommendation_to_dict(self):
        """Test recommendation serialization."""
        rec = Recommendation(
            rule_id='TEST-001',
            level='MICRO',
            problem='Test problem',
            intervention='Test intervention',
            indicator={'name': 'Test indicator'},
            responsible={'entity': 'Test entity'},
            horizon={'short': '3 months'},
            verification=['Test verification']
        )

        rec_dict = rec.to_dict()

        assert isinstance(rec_dict, dict)
        assert rec_dict['rule_id'] == 'TEST-001'
        assert rec_dict['level'] == 'MICRO'

    def test_recommendation_enhanced_fields(self):
        """Test recommendation with v2.0 enhanced fields."""
        rec = Recommendation(
            rule_id='TEST-001',
            level='MICRO',
            problem='Test',
            intervention='Test',
            indicator={},
            responsible={},
            horizon={},
            verification=[],
            execution={'steps': ['step1', 'step2']},
            budget={'estimated': 1000000}
        )

        assert rec.execution is not None
        assert rec.budget is not None
        assert rec.execution['steps'][0] == 'step1'


class TestRecommendationSet:
    """Test suite for RecommendationSet."""

    def test_recommendation_set_creation(self):
        """Test recommendation set creation."""
        rec_set = RecommendationSet(
            level='MICRO',
            recommendations=[],
            generated_at=datetime.now().isoformat(),
            total_rules_evaluated=10,
            rules_matched=3
        )

        assert rec_set.level == 'MICRO'
        assert rec_set.total_rules_evaluated == 10
        assert rec_set.rules_matched == 3

    def test_recommendation_set_to_dict(self):
        """Test recommendation set serialization."""
        rec = Recommendation(
            rule_id='TEST-001',
            level='MICRO',
            problem='Test',
            intervention='Test',
            indicator={},
            responsible={},
            horizon={},
            verification=[]
        )

        rec_set = RecommendationSet(
            level='MICRO',
            recommendations=[rec],
            generated_at=datetime.now().isoformat(),
            total_rules_evaluated=5,
            rules_matched=1
        )

        rec_set_dict = rec_set.to_dict()

        assert isinstance(rec_set_dict, dict)
        assert rec_set_dict['level'] == 'MICRO'
        assert len(rec_set_dict['recommendations']) == 1


class TestConditionEvaluation:
    """Test suite for condition evaluation logic."""

    def test_check_meso_conditions_score_band(self, recommendation_engine):
        """Test MESO score band condition checking."""
        # BAJO band: score < 55
        assert recommendation_engine._check_meso_conditions(
            score=50.0, variance=0.1, weak_pa='PA01',
            score_band='BAJO', variance_level='MEDIA',
            variance_threshold=None, weak_pa_id=None
        )

        # Should fail for score >= 55
        assert not recommendation_engine._check_meso_conditions(
            score=60.0, variance=0.1, weak_pa='PA01',
            score_band='BAJO', variance_level='MEDIA',
            variance_threshold=None, weak_pa_id=None
        )

    def test_check_meso_conditions_variance(self, recommendation_engine):
        """Test MESO variance level condition checking."""
        # ALTA variance: variance >= 0.18
        assert recommendation_engine._check_meso_conditions(
            score=50.0, variance=0.20, weak_pa='PA01',
            score_band='BAJO', variance_level='ALTA',
            variance_threshold=18.0, weak_pa_id=None
        )


class TestIntegration:
    """Integration tests for recommendation engine."""

    def test_full_pipeline_micro(self, recommendation_engine):
        """Test full MICRO recommendation pipeline."""
        scores = {
            'PA01-DIM01': 1.5,
            'PA02-DIM01': 2.5,
            'PA03-DIM02': 1.0
        }

        result = recommendation_engine.generate_micro_recommendations(scores)

        assert isinstance(result, RecommendationSet)
        assert result.generated_at is not None
        assert result.total_rules_evaluated > 0

    def test_full_pipeline_meso(self, recommendation_engine):
        """Test full MESO recommendation pipeline."""
        cluster_data = {
            'CL01': {'score': 45.0, 'variance': 0.25, 'weak_pa': 'PA01'},
            'CL02': {'score': 75.0, 'variance': 0.05, 'weak_pa': 'PA02'}
        }

        result = recommendation_engine.generate_meso_recommendations(cluster_data)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MESO'

    def test_full_pipeline_macro(self, recommendation_engine):
        """Test full MACRO recommendation pipeline."""
        plan_metrics = {
            'overall_score': 60.0,
            'coverage': 0.70,
            'coherence': 0.75
        }

        result = recommendation_engine.generate_macro_recommendations(plan_metrics)

        assert isinstance(result, RecommendationSet)
        assert result.level == 'MACRO'
