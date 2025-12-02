"""Test evidence extraction for all element types.

Tests:
- Structured evidence extraction using monolith patterns
- Element type matching and filtering
- Confidence score propagation
- Required element validation
- Minimum cardinality checking
- Completeness score computation
- Evidence deduplication
- Pattern relevance filtering
"""

import pytest
from farfan_pipeline.core.orchestrator.signal_evidence_extractor import (
    extract_structured_evidence,
    extract_evidence_for_element_type,
    compute_completeness,
    EvidenceExtractionResult,
    _infer_pattern_categories_for_element,
    _is_pattern_relevant_to_element,
    _deduplicate_matches,
)


class TestStructuredEvidenceExtraction:
    """Test main evidence extraction function."""

    def test_extract_with_simple_signal_node(self):
        """Extract evidence with simple signal node."""
        signal_node = {
            'expected_elements': [
                {'type': 'budget_amount', 'required': True}
            ],
            'patterns': [
                {
                    'pattern': 'presupuesto|recursos',
                    'id': 'PAT-001',
                    'confidence_weight': 0.85,
                    'category': 'QUANTITATIVE',
                    'match_type': 'substring'
                }
            ],
            'validations': {}
        }

        text = "El presupuesto asignado es COP 1,000,000"

        result = extract_structured_evidence(text, signal_node)

        assert isinstance(result, EvidenceExtractionResult)
        assert 'budget_amount' in result.evidence
        assert len(result.evidence['budget_amount']) > 0

    def test_returns_evidence_extraction_result(self):
        """Returns EvidenceExtractionResult with all fields."""
        signal_node = {
            'expected_elements': [],
            'patterns': [],
            'validations': {}
        }

        result = extract_structured_evidence("", signal_node)

        assert hasattr(result, 'evidence')
        assert hasattr(result, 'completeness')
        assert hasattr(result, 'missing_required')
        assert hasattr(result, 'under_minimum')
        assert hasattr(result, 'extraction_metadata')

    def test_tracks_missing_required_elements(self):
        """Tracks required elements that are missing."""
        signal_node = {
            'expected_elements': [
                {'type': 'budget_amount', 'required': True},
                {'type': 'currency', 'required': True}
            ],
            'patterns': [],
            'validations': {}
        }

        text = "Some text without required elements"

        result = extract_structured_evidence(text, signal_node)

        assert len(result.missing_required) == 2
        assert 'budget_amount' in result.missing_required
        assert 'currency' in result.missing_required

    def test_tracks_elements_under_minimum(self):
        """Tracks elements that don't meet minimum count."""
        signal_node = {
            'expected_elements': [
                {'type': 'sources', 'minimum': 3}
            ],
            'patterns': [
                {
                    'pattern': 'DANE',
                    'id': 'PAT-001',
                    'confidence_weight': 0.9,
                    'category': 'ENTITY',
                    'match_type': 'substring'
                }
            ],
            'validations': {}
        }

        text = "Source: DANE"

        result = extract_structured_evidence(text, signal_node)

        assert len(result.under_minimum) == 1
        element_type, found, minimum = result.under_minimum[0]
        assert element_type == 'sources'
        assert found == 1
        assert minimum == 3

    def test_extracts_multiple_element_types(self):
        """Extracts multiple different element types."""
        signal_node = {
            'expected_elements': [
                {'type': 'temporal', 'required': False},
                {'type': 'quantitative', 'required': False}
            ],
            'patterns': [
                {
                    'pattern': r'20\d{2}',
                    'id': 'PAT-YEAR',
                    'confidence_weight': 0.9,
                    'category': 'TEMPORAL',
                    'match_type': 'regex'
                },
                {
                    'pattern': r'\d+%',
                    'id': 'PAT-PCT',
                    'confidence_weight': 0.85,
                    'category': 'QUANTITATIVE',
                    'match_type': 'regex'
                }
            ],
            'validations': {}
        }

        text = "En 2023, el 85% de los recursos fueron ejecutados"

        result = extract_structured_evidence(text, signal_node)

        assert 'temporal' in result.evidence
        assert 'quantitative' in result.evidence
        assert len(result.evidence['temporal']) > 0
        assert len(result.evidence['quantitative']) > 0

    def test_supports_legacy_string_element_format(self):
        """Supports legacy format with element types as strings."""
        signal_node = {
            'expected_elements': ['budget_amount', 'currency'],
            'patterns': [],
            'validations': {}
        }

        result = extract_structured_evidence("", signal_node)

        assert 'budget_amount' in result.evidence
        assert 'currency' in result.evidence


class TestCompletenessComputation:
    """Test completeness score calculation."""

    def test_perfect_completeness(self):
        """100% completeness when all elements found."""
        evidence = {
            'element1': [{'value': 'found'}],
            'element2': [{'value': 'found'}]
        }
        expected_elements = [
            {'type': 'element1', 'required': True},
            {'type': 'element2', 'required': True}
        ]

        score = compute_completeness(evidence, expected_elements)

        assert score == 1.0

    def test_zero_completeness(self):
        """0% completeness when no required elements found."""
        evidence = {}
        expected_elements = [
            {'type': 'element1', 'required': True},
            {'type': 'element2', 'required': True}
        ]

        score = compute_completeness(evidence, expected_elements)

        assert score == 0.0

    def test_partial_completeness(self):
        """Partial completeness with mixed results."""
        evidence = {
            'element1': [{'value': 'found'}],
            'element2': []
        }
        expected_elements = [
            {'type': 'element1', 'required': True},
            {'type': 'element2', 'required': True}
        ]

        score = compute_completeness(evidence, expected_elements)

        assert 0.0 < score < 1.0
        assert score == 0.5

    def test_minimum_count_proportional(self):
        """Minimum count uses proportional scoring."""
        evidence = {
            'sources': [{'value': 'src1'}, {'value': 'src2'}]
        }
        expected_elements = [
            {'type': 'sources', 'minimum': 4}
        ]

        score = compute_completeness(evidence, expected_elements)

        assert score == 0.5

    def test_optional_elements_bonus(self):
        """Optional elements provide bonus when present."""
        evidence = {
            'optional1': [{'value': 'found'}]
        }
        expected_elements = [
            {'type': 'optional1', 'required': False, 'minimum': 0}
        ]

        score = compute_completeness(evidence, expected_elements)

        assert score == 1.0


class TestPatternRelevanceFiltering:
    """Test pattern relevance to element types."""

    def test_infer_temporal_categories(self):
        """Infer TEMPORAL category for temporal elements."""
        categories = _infer_pattern_categories_for_element('temporal_year')

        assert categories is not None
        assert 'TEMPORAL' in categories

    def test_infer_quantitative_categories(self):
        """Infer QUANTITATIVE category for quantitative elements."""
        categories = _infer_pattern_categories_for_element('indicador_cuantitativo')

        assert categories is not None
        assert 'QUANTITATIVE' in categories

    def test_infer_entity_categories(self):
        """Infer ENTITY category for entity elements."""
        categories = _infer_pattern_categories_for_element('entidad_responsable')

        assert categories is not None
        assert 'ENTITY' in categories

    def test_infer_geographic_categories(self):
        """Infer GEOGRAPHIC category for territorial elements."""
        categories = _infer_pattern_categories_for_element('cobertura_territorial')

        assert categories is not None
        assert 'GEOGRAPHIC' in categories

    def test_accept_all_for_generic_elements(self):
        """Accept all categories for generic elements."""
        categories = _infer_pattern_categories_for_element('generic_element')

        assert categories is None

    def test_pattern_relevance_by_keyword_overlap(self):
        """Pattern relevance determined by keyword overlap."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'validation_rule': 'budget_validation',
            'context_requirement': ''
        }

        is_relevant = _is_pattern_relevant_to_element(
            'presupuesto asignado',
            'presupuesto_municipal',
            pattern_spec
        )

        assert is_relevant is True

    def test_pattern_not_relevant_no_overlap(self):
        """Pattern not relevant when no keyword overlap."""
        pattern_spec = {
            'pattern': 'indicador',
            'validation_rule': '',
            'context_requirement': ''
        }

        is_relevant = _is_pattern_relevant_to_element(
            'indicador',
            'presupuesto_municipal',
            pattern_spec
        )

        assert is_relevant is False


class TestEvidenceDeduplication:
    """Test evidence match deduplication."""

    def test_removes_overlapping_matches(self):
        """Removes overlapping matches keeping highest confidence."""
        matches = [
            {'value': 'presupuesto', 'confidence': 0.8, 'span': (0, 11)},
            {'value': 'presupuesto asignado', 'confidence': 0.9, 'span': (0, 20)}
        ]

        deduplicated = _deduplicate_matches(matches)

        assert len(deduplicated) == 1
        assert deduplicated[0]['confidence'] == 0.9

    def test_keeps_non_overlapping_matches(self):
        """Keeps non-overlapping matches."""
        matches = [
            {'value': 'presupuesto', 'confidence': 0.8, 'span': (0, 11)},
            {'value': 'recursos', 'confidence': 0.85, 'span': (20, 28)}
        ]

        deduplicated = _deduplicate_matches(matches)

        assert len(deduplicated) == 2

    def test_handles_empty_list(self):
        """Handles empty match list."""
        deduplicated = _deduplicate_matches([])

        assert deduplicated == []

    def test_replaces_with_higher_confidence(self):
        """Replaces overlapping match if significantly higher confidence."""
        matches = [
            {'value': 'test1', 'confidence': 0.5, 'span': (0, 5)},
            {'value': 'test2', 'confidence': 0.9, 'span': (2, 7)}
        ]

        deduplicated = _deduplicate_matches(matches)

        assert len(deduplicated) == 1
        assert deduplicated[0]['confidence'] == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
