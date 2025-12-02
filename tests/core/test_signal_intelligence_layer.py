"""
Tests for Signal Intelligence Layer (JOBFRONT 1)

Verifies that EnrichedSignalPack and related types are correctly defined
and have the expected API surface.
"""

import pytest
from unittest.mock import Mock

from farfan_pipeline.core.orchestrator.signal_intelligence_layer import (
    EnrichedSignalPack,
    create_enriched_signal_pack,
    create_document_context,
)
from farfan_pipeline.core.orchestrator.signal_evidence_extractor import (
    EvidenceExtractionResult,
)
from farfan_pipeline.core.orchestrator.signal_contract_validator import (
    ValidationResult,
)


@pytest.fixture
def mock_base_signal_pack():
    """Mock base signal pack for testing."""
    mock_pack = Mock(spec=['patterns', 'micro_questions'])
    mock_pack.patterns = [
        {
            'id': 'PAT_001',
            'pattern': 'presupuesto',
            'confidence_weight': 0.85,
            'category': 'BUDGET'
        },
        {
            'id': 'PAT_002',
            'pattern': 'indicador',
            'confidence_weight': 0.75,
            'category': 'INDICATOR'
        }
    ]
    mock_pack.micro_questions = [
        {
            'id': 'Q001',
            'question': 'Test question',
            'patterns': mock_pack.patterns
        }
    ]
    return mock_pack


def test_enriched_signal_pack_instantiation(mock_base_signal_pack):
    """Test that EnrichedSignalPack can be instantiated."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    assert enriched is not None
    assert enriched.base_pack == mock_base_signal_pack
    assert len(enriched.patterns) == 2


def test_enriched_signal_pack_has_required_methods(mock_base_signal_pack):
    """Test that EnrichedSignalPack has all required methods."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    # Check all methods exist
    assert hasattr(enriched, 'get_patterns_for_context')
    assert hasattr(enriched, 'expand_patterns')
    assert hasattr(enriched, 'extract_evidence')
    assert hasattr(enriched, 'validate_result')
    assert hasattr(enriched, 'get_average_confidence')
    assert hasattr(enriched, 'get_node')

    # Check they are callable
    assert callable(enriched.get_patterns_for_context)
    assert callable(enriched.expand_patterns)
    assert callable(enriched.extract_evidence)
    assert callable(enriched.validate_result)
    assert callable(enriched.get_average_confidence)
    assert callable(enriched.get_node)


def test_get_patterns_for_context(mock_base_signal_pack):
    """Test context filtering of patterns."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    doc_context = {'section': 'budget', 'chapter': 1}
    filtered_patterns = enriched.get_patterns_for_context(doc_context)

    # Should return a list
    assert isinstance(filtered_patterns, list)


def test_expand_patterns(mock_base_signal_pack):
    """Test pattern expansion."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=True)

    base_patterns = ['presupuesto', 'recursos']
    expanded = enriched.expand_patterns(base_patterns)

    # Should return a list
    assert isinstance(expanded, list)


def test_get_average_confidence(mock_base_signal_pack):
    """Test average confidence calculation."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    # Test with known patterns
    patterns_used = ['PAT_001', 'PAT_002']
    avg_confidence = enriched.get_average_confidence(patterns_used)

    assert isinstance(avg_confidence, float)
    assert 0.0 <= avg_confidence <= 1.0
    # Expected: (0.85 + 0.75) / 2 = 0.80
    assert avg_confidence == pytest.approx(0.80, abs=0.01)


def test_get_average_confidence_empty_list(mock_base_signal_pack):
    """Test average confidence with empty patterns list."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    avg_confidence = enriched.get_average_confidence([])

    # Should return default 0.5
    assert avg_confidence == 0.5


def test_get_node(mock_base_signal_pack):
    """Test getting signal node by ID."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    node = enriched.get_node('Q001')

    # Should find the node
    assert node is not None
    assert isinstance(node, dict)
    assert node['id'] == 'Q001'


def test_get_node_not_found(mock_base_signal_pack):
    """Test getting non-existent signal node."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    node = enriched.get_node('NONEXISTENT')

    # Should return None
    assert node is None


def test_extract_evidence_returns_result_object(mock_base_signal_pack):
    """Test that extract_evidence returns EvidenceExtractionResult."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    signal_node = {
        'id': 'Q001',
        'expected_elements': [
            {'type': 'budget_amount', 'required': True}
        ],
        'patterns': mock_base_signal_pack.patterns
    }

    result = enriched.extract_evidence(
        text="El presupuesto asignado es COP 1,000,000",
        signal_node=signal_node,
        document_context={'section': 'budget'}
    )

    # Should return EvidenceExtractionResult
    assert isinstance(result, EvidenceExtractionResult)
    assert hasattr(result, 'evidence')
    assert hasattr(result, 'completeness')
    assert hasattr(result, 'missing_required')
    assert hasattr(result, 'extraction_metadata')


def test_validate_result_returns_validation_result(mock_base_signal_pack):
    """Test that validate_result returns ValidationResult."""
    enriched = EnrichedSignalPack(mock_base_signal_pack, enable_semantic_expansion=False)

    analysis_result = {
        'amount': 1000000,
        'currency': 'COP',
        'confidence': 0.85
    }

    signal_node = {
        'id': 'Q001',
        'failure_contract': {
            'abort_if': ['missing_currency'],
            'emit_code': 'ERR_TEST_001'
        }
    }

    validation = enriched.validate_result(analysis_result, signal_node)

    # Should return ValidationResult
    assert isinstance(validation, ValidationResult)
    assert hasattr(validation, 'status')
    assert hasattr(validation, 'passed')
    assert hasattr(validation, 'error_code')
    assert hasattr(validation, 'remediation')

    # This result should pass (currency is present)
    assert validation.passed is True


def test_create_enriched_signal_pack_factory(mock_base_signal_pack):
    """Test factory function for creating enriched signal pack."""
    enriched = create_enriched_signal_pack(
        mock_base_signal_pack,
        enable_semantic_expansion=False
    )

    assert isinstance(enriched, EnrichedSignalPack)
    assert enriched.base_pack == mock_base_signal_pack


def test_create_document_context():
    """Test document context creation helper."""
    ctx = create_document_context(
        section='budget',
        chapter=3,
        page=47,
        policy_area='PA01'
    )

    assert isinstance(ctx, dict)
    assert ctx['section'] == 'budget'
    assert ctx['chapter'] == 3
    assert ctx['page'] == 47
    assert ctx['policy_area'] == 'PA01'


def test_create_document_context_optional_fields():
    """Test document context with only some fields."""
    ctx = create_document_context(
        section='indicators',
        custom_field='custom_value'
    )

    assert isinstance(ctx, dict)
    assert ctx['section'] == 'indicators'
    assert 'chapter' not in ctx
    assert ctx['custom_field'] == 'custom_value'


def test_evidence_extraction_result_has_expected_fields():
    """Test that EvidenceExtractionResult has expected structure."""
    result = EvidenceExtractionResult(
        evidence={'budget': [{'value': 1000}]},
        completeness=0.85,
        missing_required=['currency'],
        under_minimum=[('sources', 1, 2)],
        extraction_metadata={'pattern_count': 10}
    )

    assert result.evidence == {'budget': [{'value': 1000}]}
    assert result.completeness == 0.85
    assert result.missing_required == ['currency']
    assert result.under_minimum == [('sources', 1, 2)]
    assert result.extraction_metadata == {'pattern_count': 10}


def test_validation_result_has_expected_fields():
    """Test that ValidationResult has expected structure."""
    result = ValidationResult(
        status='failed',
        passed=False,
        error_code='ERR_TEST_001',
        condition_violated='missing_currency',
        validation_failures=['currency field missing'],
        remediation='Check source document for currency field',
        details={'amount': 1000}
    )

    assert result.status == 'failed'
    assert result.passed is False
    assert result.error_code == 'ERR_TEST_001'
    assert result.condition_violated == 'missing_currency'
    assert result.validation_failures == ['currency field missing']
    assert result.remediation == 'Check source document for currency field'
    assert result.details == {'amount': 1000}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
