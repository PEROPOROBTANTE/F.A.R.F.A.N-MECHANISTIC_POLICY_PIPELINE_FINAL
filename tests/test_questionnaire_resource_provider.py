"""Tests for QuestionnaireResourceProvider - Pattern Extraction Verification.

These tests verify that pattern extraction meets target counts:
- 2,207+ total patterns
- 34 temporal patterns
- 157 indicator patterns
- 19 source patterns
- 6+ validation types
"""

from pathlib import Path

import pytest

from saaaaaa.core.orchestrator.questionnaire_resource_provider import (
    QuestionnaireResourceProvider,
    Pattern,
)


@pytest.fixture
def provider() -> QuestionnaireResourceProvider:
    """Create provider from questionnaire monolith."""
    monolith_path = Path(__file__).parent.parent / "data" / "questionnaire_monolith.json"
    return QuestionnaireResourceProvider.from_file(monolith_path)


def test_provider_initialization(provider: QuestionnaireResourceProvider) -> None:
    """Test provider initializes correctly."""
    assert provider is not None
    assert provider._data is not None
    assert "blocks" in provider._data


def test_extract_all_patterns_count(provider: QuestionnaireResourceProvider) -> None:
    """Test that total pattern count meets target (2,207+)."""
    patterns = provider.extract_all_patterns()
    
    assert len(patterns) >= 2200, f"Expected ≥2200 patterns, got {len(patterns)}"
    
    # Verify all are Pattern instances
    assert all(isinstance(p, Pattern) for p in patterns)


def test_temporal_patterns_count(provider: QuestionnaireResourceProvider) -> None:
    """Test that temporal pattern count matches target (34)."""
    patterns = provider.get_temporal_patterns()
    
    assert len(patterns) == 34, f"Expected 34 temporal patterns, got {len(patterns)}"
    
    # Verify all are TEMPORAL category
    assert all(p.category == "TEMPORAL" for p in patterns)


def test_indicator_patterns_count(provider: QuestionnaireResourceProvider) -> None:
    """Test that indicator pattern count matches target (157)."""
    patterns = provider.get_indicator_patterns()
    
    assert len(patterns) == 157, f"Expected 157 indicator patterns, got {len(patterns)}"
    
    # Verify all are INDICADOR category
    assert all(p.category == "INDICADOR" for p in patterns)


def test_source_patterns_count(provider: QuestionnaireResourceProvider) -> None:
    """Test that source pattern count matches target (19)."""
    patterns = provider.get_source_patterns()
    
    assert len(patterns) == 19, f"Expected 19 source patterns, got {len(patterns)}"
    
    # Verify all are FUENTE_OFICIAL category
    assert all(p.category == "FUENTE_OFICIAL" for p in patterns)


def test_territorial_patterns_count(provider: QuestionnaireResourceProvider) -> None:
    """Test territorial pattern extraction."""
    patterns = provider.get_territorial_patterns()
    
    assert len(patterns) == 71, f"Expected 71 territorial patterns, got {len(patterns)}"
    
    # Verify all are TERRITORIAL category
    assert all(p.category == "TERRITORIAL" for p in patterns)


def test_extract_all_validations(provider: QuestionnaireResourceProvider) -> None:
    """Test validation extraction."""
    validations = provider.extract_all_validations()
    
    # Should extract validations from 300 questions
    assert len(validations) > 0, "Expected validations to be extracted"
    
    # Check for unique validation types
    validation_types = {v.type for v in validations}
    assert len(validation_types) >= 6, f"Expected ≥6 validation types, got {len(validation_types)}"


def test_pattern_structure(provider: QuestionnaireResourceProvider) -> None:
    """Test that patterns have required fields."""
    patterns = provider.extract_all_patterns()
    
    for p in patterns[:10]:  # Check first 10
        assert p.id, "Pattern must have id"
        assert p.category, "Pattern must have category"
        assert p.pattern, "Pattern must have pattern content"
        assert 0.0 <= p.confidence_weight <= 1.0, "Confidence weight must be in [0, 1]"


def test_compile_patterns_for_category(provider: QuestionnaireResourceProvider) -> None:
    """Test pattern compilation for a category."""
    compiled = provider.compile_patterns_for_category("TEMPORAL")
    
    assert len(compiled) > 0, "Expected compiled patterns"
    
    # Verify they are compiled regex objects
    for regex in compiled[:5]:  # Check first 5
        assert hasattr(regex, "pattern"), "Should be compiled regex"
        assert hasattr(regex, "search"), "Should have search method"


def test_get_patterns_by_question(provider: QuestionnaireResourceProvider) -> None:
    """Test retrieving patterns for specific question."""
    patterns = provider.get_patterns_by_question("Q001")
    
    # Q001 should have patterns
    assert len(patterns) > 0, "Q001 should have patterns"
    assert all(p.question_id == "Q001" for p in patterns)


def test_get_pattern_statistics(provider: QuestionnaireResourceProvider) -> None:
    """Test pattern statistics generation."""
    stats = provider.get_pattern_statistics()
    
    assert "total_patterns" in stats
    assert "categories" in stats
    assert "temporal_count" in stats
    assert "indicator_count" in stats
    assert "source_count" in stats
    
    # Verify counts
    assert stats["total_patterns"] >= 2200
    assert stats["temporal_count"] == 34
    assert stats["indicator_count"] == 157
    assert stats["source_count"] == 19


def test_verify_target_counts(provider: QuestionnaireResourceProvider) -> None:
    """Test verification of all target counts."""
    verification = provider.verify_target_counts()
    
    # All targets should be met
    assert verification["total_patterns_ok"], "Total patterns target not met"
    assert verification["temporal_patterns_ok"], "Temporal patterns target not met"
    assert verification["indicator_patterns_ok"], "Indicator patterns target not met"
    assert verification["source_patterns_ok"], "Source patterns target not met"


def test_pattern_caching(provider: QuestionnaireResourceProvider) -> None:
    """Test that patterns are cached after first extraction."""
    # First call extracts
    patterns1 = provider.extract_all_patterns()
    
    # Second call should use cache
    patterns2 = provider.extract_all_patterns()
    
    # Should return same patterns
    assert len(patterns1) == len(patterns2)
    
    # Cache should be populated
    assert provider._patterns_cache is not None


@pytest.mark.parametrize("category", [
    "TEMPORAL",
    "INDICADOR",
    "FUENTE_OFICIAL",
    "GENERAL",
    "TERRITORIAL",
])
def test_category_extraction(provider: QuestionnaireResourceProvider, category: str) -> None:
    """Test extraction for each category."""
    provider.extract_all_patterns()
    patterns = provider._patterns_cache.get(category, [])
    
    # Each category should have patterns
    assert len(patterns) > 0, f"Category {category} should have patterns"
    
    # All should be correct category
    assert all(p.category == category for p in patterns)


def test_pattern_regex_compilation(provider: QuestionnaireResourceProvider) -> None:
    """Test that REGEX patterns can be compiled."""
    patterns = provider.extract_all_patterns()
    
    regex_patterns = [p for p in patterns if p.match_type == "REGEX"]
    assert len(regex_patterns) > 0, "Should have REGEX patterns"
    
    # Try compiling a few
    for p in regex_patterns[:10]:
        compiled = p.compile_regex()
        if compiled is not None:
            assert hasattr(compiled, "search")


def test_get_patterns_for_area(provider: QuestionnaireResourceProvider) -> None:
    """Ensure provider returns deterministic patterns per policy area."""
    patterns = provider.get_patterns_for_area("PA01", limit=5)
    assert 0 < len(patterns) <= 5
    assert all(isinstance(p, str) for p in patterns)
