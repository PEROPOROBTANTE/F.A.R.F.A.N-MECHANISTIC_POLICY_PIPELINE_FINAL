"""Tests for SHA-256 hash determinism and questionnaire validation."""

import json
import hashlib
from copy import deepcopy
import pytest

# Add src to path for imports
import sys
from pathlib import Path

from saaaaaa.core.orchestrator.factory import (
    compute_monolith_hash,
    validate_questionnaire_structure,
)


def test_monolith_hash_deterministic():
    """Hash should be identical for same content."""
    monolith = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': 'D1-Q1'},
                {'question_id': 'Q2', 'question_global': 2, 'base_slot': 'D1-Q2'},
            ]
        },
        'schema_version': '1.0'
    }

    # Compute hash 10 times
    hashes = []
    for _ in range(10):
        hash_val = compute_monolith_hash(monolith)
        hashes.append(hash_val)

    # All should be identical
    assert len(set(hashes)) == 1, "Hash should be deterministic"
    assert len(hashes[0]) == 64, "SHA-256 hash should be 64 hex characters"


def test_monolith_hash_key_order_invariant():
    """Hash should ignore key order."""
    monolith1 = {'a': 1, 'b': 2, 'c': 3}
    monolith2 = {'c': 3, 'a': 1, 'b': 2}

    hash1 = compute_monolith_hash(monolith1)
    hash2 = compute_monolith_hash(monolith2)

    assert hash1 == hash2, "Hash should be order-independent"


def test_monolith_hash_deep_copy_equal():
    """Hash should be equal for deep copies."""
    original = {
        'nested': {
            'list': [1, 2, {'key': 'value'}],
            'dict': {'x': 10, 'y': 20}
        }
    }

    copy = deepcopy(original)

    hash_original = compute_monolith_hash(original)
    hash_copy = compute_monolith_hash(copy)

    assert hash_original == hash_copy


def test_monolith_hash_float_precision():
    """Hash should handle float precision consistently."""
    monolith1 = {'score': 0.1 + 0.2}  # 0.30000000000000004
    monolith2 = {'score': 0.3}

    # Should be DIFFERENT (precision matters for integrity)
    hash1 = compute_monolith_hash(monolith1)
    hash2 = compute_monolith_hash(monolith2)

    # Document the behavior
    assert hash1 != hash2, "Float precision affects hash (expected behavior)"


def test_monolith_hash_unicode_normalization():
    """Hash should handle unicode consistently."""
    # Same string, different representations (if different)
    monolith1 = {'text': 'café'}  # NFC form
    monolith2 = {'text': 'café'}  # NFD form (may be same in Python)

    hash1 = compute_monolith_hash(monolith1)
    hash2 = compute_monolith_hash(monolith2)

    # With ensure_ascii=True, should be identical
    assert hash1 == hash2


@pytest.mark.parametrize('execution', range(100))
def test_monolith_hash_stability_under_load(execution):
    """Hash should be stable under repeated computation."""
    monolith = {
        'execution': execution,
        'data': list(range(100)),
        'nested': {'values': [x ** 2 for x in range(10)]}
    }

    hash_val = compute_monolith_hash(monolith)

    # Re-compute immediately
    hash_val2 = compute_monolith_hash(monolith)

    assert hash_val == hash_val2


def test_monolith_hash_empty_dict():
    """Hash should work for empty dict."""
    hash1 = compute_monolith_hash({})
    hash2 = compute_monolith_hash({})
    assert hash1 == hash2
    assert len(hash1) == 64


def test_monolith_hash_complex_nesting():
    """Hash should handle deeply nested structures."""
    monolith = {
        'level1': {
            'level2': {
                'level3': {
                    'level4': {
                        'data': [1, 2, 3],
                        'more': {'x': 'y'}
                    }
                }
            }
        }
    }
    
    hash1 = compute_monolith_hash(monolith)
    hash2 = compute_monolith_hash(monolith)
    assert hash1 == hash2


def test_monolith_hash_different_content():
    """Hash should be different for different content."""
    monolith1 = {'version': '1.0'}
    monolith2 = {'version': '2.0'}
    
    hash1 = compute_monolith_hash(monolith1)
    hash2 = compute_monolith_hash(monolith2)
    
    assert hash1 != hash2


# ============================================================================
# Validation Tests
# ============================================================================

def test_validate_empty_questionnaire():
    """Should fail on empty dict."""
    with pytest.raises(ValueError, match="missing keys"):
        validate_questionnaire_structure({})


def test_validate_missing_version():
    """Should fail if version is missing."""
    data = {
        'blocks': {'micro_questions': []},
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="missing keys"):
        validate_questionnaire_structure(data)


def test_validate_blocks_not_dict():
    """Should fail if blocks is not a dict."""
    data = {
        'version': '1.0',
        'blocks': [],  # Should be dict
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="blocks must be a dict"):
        validate_questionnaire_structure(data)


def test_validate_micro_questions_not_list():
    """Should fail if micro_questions is not a list."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': {}  # Should be list
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="must be a list"):
        validate_questionnaire_structure(data)


def test_validate_question_missing_required_fields():
    """Should fail if question lacks required fields."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1'}  # Missing question_global, base_slot
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="Question 0 missing keys"):
        validate_questionnaire_structure(data)


def test_validate_question_invalid_types():
    """Should fail if question fields have wrong types."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': 'Q1',
                    'question_global': 'not_an_int',  # Should be int
                    'base_slot': 'D1-Q1'
                }
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="question_global must be an integer"):
        validate_questionnaire_structure(data)


def test_validate_duplicate_question_ids():
    """Should fail on duplicate question_id."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': 'D1-Q1'},
                {'question_id': 'Q1', 'question_global': 2, 'base_slot': 'D1-Q2'},  # Duplicate
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="Duplicate question_id"):
        validate_questionnaire_structure(data)


def test_validate_duplicate_question_globals():
    """Should fail on duplicate question_global."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': 'D1-Q1'},
                {'question_id': 'Q2', 'question_global': 1, 'base_slot': 'D1-Q2'},  # Duplicate
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="Duplicate question_global"):
        validate_questionnaire_structure(data)


def test_validate_null_values():
    """Should fail on null values in required fields."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': None, 'question_global': 1, 'base_slot': 'D1-Q1'}
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="question_id cannot be None"):
        validate_questionnaire_structure(data)


def test_validate_very_large_questionnaire():
    """Should handle large questionnaires efficiently."""
    import time
    
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': f'Q{i}',
                    'question_global': i,
                    'base_slot': f'D1-Q{i}'
                }
                for i in range(10000)
            ]
        },
        'schema_version': '1.0'
    }

    # Should complete in reasonable time
    start = time.time()
    validate_questionnaire_structure(data)
    elapsed = time.time() - start

    assert elapsed < 1.0, f"Validation took {elapsed}s, should be <1s"


def test_validate_valid_questionnaire():
    """Should pass for valid questionnaire."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': 'D1-Q1'},
                {'question_id': 'Q2', 'question_global': 2, 'base_slot': 'D1-Q2'},
                {'question_id': 'Q3', 'question_global': 3, 'base_slot': 'D1-Q3'},
            ]
        },
        'schema_version': '1.0'
    }
    
    # Should not raise
    validate_questionnaire_structure(data)


def test_validate_question_not_dict():
    """Should fail if question is not a dict."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                "not a dict"
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="Question 0 must be a dict"):
        validate_questionnaire_structure(data)


def test_validate_not_dict():
    """Should fail if top-level is not a dict."""
    with pytest.raises(TypeError, match="must be a dictionary"):
        validate_questionnaire_structure([])  # List instead of dict


def test_validate_base_slot_wrong_type():
    """Should fail if base_slot is wrong type."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': 123}  # Should be str
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="base_slot must be string"):
        validate_questionnaire_structure(data)


def test_validate_question_id_wrong_type():
    """Should fail if question_id is wrong type."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 123, 'question_global': 1, 'base_slot': 'D1-Q1'}  # Should be str
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="question_id must be string"):
        validate_questionnaire_structure(data)
