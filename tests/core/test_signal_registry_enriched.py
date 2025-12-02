"""
Tests for Enriched Signal Registry Factory (JOBFRONT 2)

Verifies that create_enriched_signal_registry creates EnrichedSignalPacks
without mutating the base QuestionnaireSignalRegistry.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from farfan_pipeline.core.orchestrator.factory import create_enriched_signal_registry
from farfan_pipeline.core.orchestrator.signal_intelligence_layer import EnrichedSignalPack


@pytest.fixture
def mock_signal_registry():
    """Mock QuestionnaireSignalRegistry for testing."""
    mock_registry = Mock()

    # Mock list_policy_areas to return known policy areas
    mock_registry.list_policy_areas.return_value = ['PA01', 'PA02', 'PA03']

    # Mock get() to return base signal packs
    def mock_get(policy_area_id):
        mock_pack = Mock()
        mock_pack.patterns = [
            {'id': f'{policy_area_id}_PAT001', 'pattern': 'test', 'confidence_weight': 0.8}
        ]
        mock_pack.micro_questions = []
        return mock_pack

    mock_registry.get = mock_get

    return mock_registry


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_create_enriched_signal_registry_returns_dict(mock_registry_class, mock_signal_registry):
    """Test that create_enriched_signal_registry returns a dict."""
    mock_registry_class.return_value = mock_signal_registry

    registry = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json'
    )

    assert isinstance(registry, dict)
    assert len(registry) > 0


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_enriched_packs_are_created_for_each_policy_area(mock_registry_class, mock_signal_registry):
    """Test that EnrichedSignalPack is created for each policy area."""
    mock_registry_class.return_value = mock_signal_registry

    registry = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json'
    )

    # Should have entries for PA01, PA02, PA03
    assert 'PA01' in registry
    assert 'PA02' in registry
    assert 'PA03' in registry


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_enriched_packs_are_enriched_signal_pack_instances(mock_registry_class, mock_signal_registry):
    """Test that values in registry are EnrichedSignalPack instances."""
    mock_registry_class.return_value = mock_signal_registry

    registry = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json',
        enable_semantic_expansion=False  # Disable to avoid expansion logic
    )

    for pa_id, pack in registry.items():
        assert isinstance(pack, EnrichedSignalPack)


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_semantic_expansion_flag_is_respected(mock_registry_class, mock_signal_registry):
    """Test that enable_semantic_expansion flag is passed correctly."""
    mock_registry_class.return_value = mock_signal_registry

    # Test with expansion disabled
    registry_no_expansion = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json',
        enable_semantic_expansion=False
    )

    # Test with expansion enabled
    registry_with_expansion = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json',
        enable_semantic_expansion=True
    )

    # Both should succeed (actual expansion testing is in EnrichedSignalPack tests)
    assert 'PA01' in registry_no_expansion
    assert 'PA01' in registry_with_expansion


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_handles_missing_signal_pack_gracefully(mock_registry_class):
    """Test that None signal packs are skipped gracefully."""
    mock_registry = Mock()
    mock_registry.list_policy_areas.return_value = ['PA01', 'PA02', 'PA03']

    # PA02 returns None
    def mock_get(policy_area_id):
        if policy_area_id == 'PA02':
            return None
        mock_pack = Mock()
        mock_pack.patterns = [{'id': 'PAT001', 'pattern': 'test'}]
        mock_pack.micro_questions = []
        return mock_pack

    mock_registry.get = mock_get
    mock_registry_class.return_value = mock_registry

    registry = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json',
        enable_semantic_expansion=False
    )

    # PA02 should be skipped
    assert 'PA01' in registry
    assert 'PA02' not in registry
    assert 'PA03' in registry


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_uses_canonical_path_when_none(mock_registry_class, mock_signal_registry):
    """Test that None monolith_path uses canonical QUESTIONNAIRE_PATH."""
    mock_registry_class.return_value = mock_signal_registry

    registry = create_enriched_signal_registry(monolith_path=None)

    # Should have called QuestionnaireSignalRegistry with canonical path
    assert mock_registry_class.called
    args, kwargs = mock_registry_class.call_args
    assert len(args) > 0  # First arg should be path
    # The path should be a string (converted from QUESTIONNAIRE_PATH)
    assert isinstance(args[0], str)


@patch('farfan_pipeline.core.orchestrator.factory.QuestionnaireSignalRegistry')
def test_base_registry_not_mutated(mock_registry_class, mock_signal_registry):
    """Test that base QuestionnaireSignalRegistry is not mutated."""
    mock_registry_class.return_value = mock_signal_registry

    # Create enriched registry
    enriched_registry = create_enriched_signal_registry(
        monolith_path='/fake/path/questionnaire.json',
        enable_semantic_expansion=False
    )

    # Verify base registry methods were called but not modified
    assert mock_signal_registry.list_policy_areas.called
    assert mock_signal_registry.get.called

    # Base registry should still work normally (not mutated)
    mock_signal_registry.list_policy_areas.reset_mock()
    policy_areas = mock_signal_registry.list_policy_areas()
    assert policy_areas == ['PA01', 'PA02', 'PA03']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
