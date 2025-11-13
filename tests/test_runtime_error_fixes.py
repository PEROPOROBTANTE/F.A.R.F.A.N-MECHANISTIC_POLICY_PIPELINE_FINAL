"""
Tests for runtime error fixes in policy analysis.

These tests verify that the three critical runtime errors are prevented:
1. 'bool' object is not iterable
2. 'str' object has no attribute 'text'
3. can't multiply sequence by non-int of type 'float'
"""

from pathlib import Path

import pytest

# Add parent directory to path
from saaaaaa.utils.runtime_error_fixes import (
    ensure_list_return,
    safe_list_iteration,
    safe_text_extract,
    safe_weighted_multiply,
)

class TestEnsureListReturn:
    """Test ensure_list_return function for bool-to-list conversion."""

    def test_false_returns_empty_list(self):
        """False should return empty list, not cause 'bool not iterable' error."""
        result = ensure_list_return(False)
        assert result == []
        assert isinstance(result, list)

    def test_true_returns_empty_list(self):
        """True should return empty list, not cause 'bool not iterable' error."""
        result = ensure_list_return(True)
        assert result == []
        assert isinstance(result, list)

    def test_none_returns_empty_list(self):
        """None should return empty list."""
        result = ensure_list_return(None)
        assert result == []

    def test_list_returns_unchanged(self):
        """Actual lists should pass through unchanged."""
        input_list = [1, 2, 3]
        result = ensure_list_return(input_list)
        assert result == input_list

    def test_tuple_converts_to_list(self):
        """Tuples should be converted to lists."""
        result = ensure_list_return((1, 2, 3))
        assert result == [1, 2, 3]
        assert isinstance(result, list)

class TestSafeTextExtract:
    """Test safe_text_extract function for handling text vs spacy objects."""

    def test_string_returns_unchanged(self):
        """Plain strings should return unchanged."""
        text = "Plain text"
        result = safe_text_extract(text)
        assert result == text

    def test_object_with_text_attribute(self):
        """Objects with .text attribute should have it extracted."""
        class MockSpacyDoc:
            text = "Document text"

        doc = MockSpacyDoc()
        result = safe_text_extract(doc)
        assert result == "Document text"

    def test_object_without_text_converts_to_string(self):
        """Objects without .text should convert to string."""
        obj = 12345
        result = safe_text_extract(obj)
        assert result == "12345"

    def test_nested_object_with_text_property(self):
        """Handle objects where .text might be a property."""
        class MockDoc:
            def __init__(self):
                self._text = "Property text"

            @property
            def text(self):
                return self._text

        doc = MockDoc()
        result = safe_text_extract(doc)
        assert result == "Property text"

class TestSafeWeightedMultiply:
    """Test safe_weighted_multiply for list * float operations."""

    def test_list_multiply_by_float(self):
        """Lists should multiply element-wise, not cause 'can't multiply sequence' error."""
        items = [1.0, 2.0, 3.0]
        weight = 0.5
        result = safe_weighted_multiply(items, weight)
        assert result == [0.5, 1.0, 1.5]

    def test_list_multiply_by_int(self):
        """Lists should work with int weights too."""
        items = [1.0, 2.0, 3.0]
        weight = 2
        result = safe_weighted_multiply(items, weight)
        assert result == [2.0, 4.0, 6.0]

    def test_empty_list_returns_empty(self):
        """Empty lists should return empty."""
        result = safe_weighted_multiply([], 0.5)
        assert result == []

    def test_numpy_array_multiply(self):
        """Numpy arrays should use numpy multiplication."""
        try:
            import numpy as np
            items = np.array([1.0, 2.0, 3.0])
            weight = 0.5
            result = safe_weighted_multiply(items, weight)
            assert isinstance(result, np.ndarray)
            assert list(result) == [0.5, 1.0, 1.5]
        except ImportError:
            pytest.skip("numpy not available")

    def test_zero_weight(self):
        """Multiplying by zero should work."""
        items = [1.0, 2.0, 3.0]
        result = safe_weighted_multiply(items, 0.0)
        assert result == [0.0, 0.0, 0.0]

    def test_negative_weight(self):
        """Negative weights should work."""
        items = [1.0, 2.0]
        result = safe_weighted_multiply(items, -1.0)
        assert result == [-1.0, -2.0]

class TestSafeListIteration:
    """Test safe_list_iteration for preventing iteration errors."""

    def test_bool_not_iterable_error_prevented(self):
        """Iterating over bool should not raise error."""
        result = safe_list_iteration(False)
        assert result == []

        result = safe_list_iteration(True)
        assert result == []

    def test_none_returns_empty(self):
        """None should return empty list."""
        result = safe_list_iteration(None)
        assert result == []

    def test_list_returns_unchanged(self):
        """Lists should pass through."""
        input_list = [1, 2, 3]
        result = safe_list_iteration(input_list)
        assert result == input_list

    def test_string_becomes_single_item_list(self):
        """Strings should become single-item lists, not char iteration."""
        result = safe_list_iteration("text")
        assert result == ["text"]

    def test_tuple_converts(self):
        """Tuples should convert to lists."""
        result = safe_list_iteration((1, 2, 3))
        assert result == [1, 2, 3]

    def test_range_converts(self):
        """Ranges should convert to lists."""
        result = safe_list_iteration(range(3))
        assert result == [0, 1, 2]

class TestIntegrationScenarios:
    """Integration tests for common error scenarios."""

    def test_contradiction_detection_returning_false(self):
        """Simulate a detect function returning False instead of list."""
        # This would cause: for c in contradictions: TypeError: 'bool' object is not iterable
        contradictions = False  # Bug: should be []

        # Fix: use ensure_list_return
        contradictions = ensure_list_return(contradictions)

        # Should not raise error
        count = 0
        for _c in contradictions:
            count += 1

        assert count == 0

    def test_spacy_text_extraction_on_string(self):
        """Simulate passing string where spacy Doc expected."""
        # This would cause: AttributeError: 'str' object has no attribute 'text'
        text_or_doc = "Plain string"  # Bug: should be nlp(text)

        # Fix: use safe_text_extract
        extracted = safe_text_extract(text_or_doc)

        assert extracted == "Plain string"

    def test_list_multiplication_by_float(self):
        """Simulate multiplying list by float weight."""
        # This would cause: TypeError: can't multiply sequence by non-int of type 'float'
        penalties = [0.1, 0.2, 0.3]
        weight = 0.5

        # Bug: weighted_penalties = penalties * weight
        # Fix: use safe_weighted_multiply
        weighted_penalties = safe_weighted_multiply(penalties, weight)

        assert weighted_penalties == [0.05, 0.1, 0.15]

    def test_posterior_calculation_with_lists(self):
        """Simulate Bayesian posterior calculation that might multiply lists."""
        prior_beliefs = [0.5, 0.6, 0.7]
        likelihood_ratio = 1.2

        # Apply likelihood ratio to each belief
        posteriors = safe_weighted_multiply(prior_beliefs, likelihood_ratio)

        assert len(posteriors) == 3
        assert all(isinstance(p, float) for p in posteriors)
