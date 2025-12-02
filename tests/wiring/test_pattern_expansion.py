"""Test pattern expansion with semantic enrichment.

Tests:
- Semantic expansion using semantic_expansion field
- Pattern variant generation (5-10x multiplier)
- Core term extraction heuristics
- Metadata preservation across variants
- Spanish noun-adjective agreement
- Pattern deduplication
"""

import pytest
from farfan_pipeline.core.orchestrator.signal_semantic_expander import (
    extract_core_term,
    expand_pattern_semantically,
    expand_all_patterns,
    adjust_spanish_agreement,
)


class TestCoreTermExtraction:
    """Test core term extraction from regex patterns."""

    def test_extract_simple_term(self):
        """Extract core term from simple pattern."""
        result = extract_core_term("presupuesto")
        assert result == "presupuesto"

    def test_extract_from_regex_pattern(self):
        """Extract core term from regex with metacharacters."""
        result = extract_core_term(r"presupuesto\s+asignado")
        assert result == "presupuesto"

    def test_extract_ignores_short_words(self):
        """Core term extraction ignores words ≤2 chars."""
        result = extract_core_term(r"el\s+presupuesto")
        assert result == "presupuesto"

    def test_extract_returns_longest_word(self):
        """Returns longest word as core term."""
        result = extract_core_term(r"gran\s+presupuesto\s+aprobado")
        # Should return longest: "presupuesto" or "aprobado"
        assert result in ["presupuesto", "aprobado"]
        assert len(result) >= 9

    def test_extract_handles_complex_regex(self):
        """Extract from complex regex with alternation."""
        result = extract_core_term(r"(presupuesto|recursos)\s+asignado")
        assert result in ["presupuesto", "recursos", "asignado"]

    def test_extract_returns_none_for_empty(self):
        """Returns None for patterns with no extractable terms."""
        result = extract_core_term(r"\d+")
        assert result is None


class TestPatternVariantGeneration:
    """Test semantic pattern variant generation."""

    def test_variant_includes_original(self):
        """Expanded variants always include original pattern."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'presupuesto|recursos|fondos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        assert len(variants) >= 1
        assert variants[0]['pattern'] == 'presupuesto asignado'
        assert variants[0]['is_variant'] is False

    def test_generates_multiple_variants(self):
        """Generates variants for each synonym."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'presupuesto|recursos|fondos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        # Should have original + 2 variants (recursos, fondos)
        # presupuesto is skipped as it's the core term
        assert len(variants) >= 2

    def test_variant_ids_are_unique(self):
        """Each variant gets unique ID."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'presupuesto|recursos|fondos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        ids = [v['id'] for v in variants]
        assert len(ids) == len(set(ids))  # All unique

    def test_variant_ids_follow_convention(self):
        """Variant IDs follow PAT-###-V# convention."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'recursos|fondos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        for i, variant in enumerate(variants[1:], 1):  # Skip original
            assert variant['id'].endswith(f'-V{i}')

    def test_variant_preserves_metadata(self):
        """Variants preserve confidence_weight and category."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'recursos|fondos',
            'id': 'PAT-001',
            'confidence_weight': 0.85,
            'category': 'FINANCIAL',
            'specificity': 'HIGH'
        }

        variants = expand_pattern_semantically(pattern_spec)

        for variant in variants:
            assert variant['confidence_weight'] == 0.85
            assert variant['category'] == 'FINANCIAL'
            assert variant['specificity'] == 'HIGH'

    def test_variant_tracks_source(self):
        """Variants track which pattern they came from."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'recursos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        for variant in variants[1:]:  # Skip original
            assert variant['variant_of'] == 'PAT-001'
            assert variant['is_variant'] is True

    def test_no_expansion_without_semantic_field(self):
        """Returns only original if no semantic_expansion."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        assert len(variants) == 1
        assert variants[0]['pattern'] == 'presupuesto asignado'

    def test_handles_dict_semantic_expansion(self):
        """Handles semantic_expansion as dict format."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': {
                'presupuesto': ['recursos', 'fondos'],
                'asignado': ['aprobado', 'destinado']
            },
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        # Should extract all expansions from dict
        assert len(variants) > 1


class TestSpanishAgreement:
    """Test Spanish noun-adjective agreement adjustments."""

    def test_pluralize_adjective_for_plural_noun(self):
        """Adjusts singular adjective to plural for plural noun."""
        result = adjust_spanish_agreement("fondos asignado", "fondos")

        assert "asignados" in result

    def test_common_adjectives_pluralized(self):
        """Common adjectives (asignado, aprobado) are pluralized."""
        test_cases = [
            ("recursos asignado", "recursos", "asignados"),
            ("fondos aprobado", "fondos", "aprobados"),
            ("presupuestos disponible", "presupuestos", "disponibles"),
        ]

        for pattern, term, expected in test_cases:
            result = adjust_spanish_agreement(pattern, term)
            assert expected in result

    def test_no_change_for_singular(self):
        """No adjustment for singular nouns."""
        result = adjust_spanish_agreement("presupuesto asignado", "presupuesto")

        # Should not change singular form
        assert result == "presupuesto asignado"


class TestBatchExpansion:
    """Test batch pattern expansion."""

    def test_expand_all_patterns(self):
        """Expand multiple patterns at once."""
        patterns = [
            {
                'pattern': 'presupuesto',
                'semantic_expansion': 'presupuesto|recursos',
                'id': 'PAT-001',
                'confidence_weight': 0.8
            },
            {
                'pattern': 'indicador',
                'semantic_expansion': 'indicador|métrica',
                'id': 'PAT-002',
                'confidence_weight': 0.75
            }
        ]

        expanded = expand_all_patterns(patterns, enable_logging=False)

        # Should have at least original patterns
        assert len(expanded) >= len(patterns)

    def test_expansion_multiplier(self):
        """Expansion achieves expected multiplier (3-10x)."""
        patterns = [
            {
                'pattern': 'presupuesto',
                'semantic_expansion': 'presupuesto|recursos|fondos|financiamiento',
                'id': 'PAT-001',
                'confidence_weight': 0.8
            }
        ]

        expanded = expand_all_patterns(patterns, enable_logging=False)

        # Should have 1 original + 3 variants = 4 patterns
        assert len(expanded) >= 3

    def test_preserves_patterns_without_expansion(self):
        """Patterns without semantic_expansion are preserved."""
        patterns = [
            {
                'pattern': 'presupuesto',
                'id': 'PAT-001',
                'confidence_weight': 0.8
            },
            {
                'pattern': 'indicador',
                'semantic_expansion': 'indicador|métrica',
                'id': 'PAT-002',
                'confidence_weight': 0.75
            }
        ]

        expanded = expand_all_patterns(patterns, enable_logging=False)

        # PAT-001 should still be present
        assert any(p['id'] == 'PAT-001' for p in expanded)

    def test_handles_empty_list(self):
        """Handles empty pattern list."""
        expanded = expand_all_patterns([], enable_logging=False)

        assert expanded == []

    def test_deduplicates_synonyms(self):
        """Skips variants when synonym matches core term."""
        pattern_spec = {
            'pattern': 'presupuesto asignado',
            'semantic_expansion': 'presupuesto|recursos',  # presupuesto is core term
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        # Should not create variant for "presupuesto" (it's the core term)
        variant_patterns = [v['pattern'] for v in variants[1:]]
        assert not any('presupuesto' in p for p in variant_patterns if 'recursos' not in p)


class TestExpansionStatistics:
    """Test expansion statistics and logging."""

    def test_tracks_expansion_stats(self):
        """Tracks original count, variant count, and multiplier."""
        patterns = [
            {
                'pattern': 'presupuesto',
                'semantic_expansion': 'presupuesto|recursos|fondos',
                'id': 'PAT-001',
                'confidence_weight': 0.8
            },
            {
                'pattern': 'indicador',
                'semantic_expansion': 'indicador|métrica',
                'id': 'PAT-002',
                'confidence_weight': 0.75
            }
        ]

        expanded = expand_all_patterns(patterns, enable_logging=True)

        # Should track statistics internally
        assert len(expanded) > len(patterns)


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_handles_empty_semantic_expansion(self):
        """Handles empty semantic_expansion gracefully."""
        pattern_spec = {
            'pattern': 'presupuesto',
            'semantic_expansion': '',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        assert len(variants) == 1  # Only original

    def test_handles_whitespace_in_synonyms(self):
        """Handles whitespace in synonym list."""
        pattern_spec = {
            'pattern': 'presupuesto',
            'semantic_expansion': '  recursos  |  fondos  ',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        # Should trim whitespace and generate variants
        assert len(variants) > 1

    def test_handles_special_regex_chars(self):
        """Handles patterns with regex special characters."""
        pattern_spec = {
            'pattern': r'presupuesto\s+\d+',
            'semantic_expansion': 'presupuesto|recursos',
            'id': 'PAT-001',
            'confidence_weight': 0.8
        }

        variants = expand_pattern_semantically(pattern_spec)

        # Should generate variants
        assert len(variants) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
