"""Comprehensive edge case tests for questionnaire validation."""

import pytest
import time

# Add src to path for imports
import sys
from pathlib import Path

from saaaaaa.core.orchestrator.factory import validate_questionnaire_structure


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


def test_validate_null_question_id():
    """Should fail on null question_id."""
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


def test_validate_null_question_global():
    """Should fail on null question_global."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': None, 'base_slot': 'D1-Q1'}
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="question_global cannot be None"):
        validate_questionnaire_structure(data)


def test_validate_null_base_slot():
    """Should fail on null base_slot."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {'question_id': 'Q1', 'question_global': 1, 'base_slot': None}
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="base_slot cannot be None"):
        validate_questionnaire_structure(data)


def test_validate_very_large_questionnaire():
    """Should handle large questionnaires efficiently."""
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


def test_validate_not_dict():
    """Should fail if data is not a dictionary."""
    with pytest.raises(TypeError, match="must be a dictionary"):
        validate_questionnaire_structure("not a dict")  # type: ignore


def test_validate_question_not_dict():
    """Should fail if question is not a dict."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                "not a dict"  # Should be dict
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="Question 0 must be a dict"):
        validate_questionnaire_structure(data)


def test_validate_question_id_not_string():
    """Should fail if question_id is not a string."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': 123,  # Should be string
                    'question_global': 1,
                    'base_slot': 'D1-Q1'
                }
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="question_id must be string"):
        validate_questionnaire_structure(data)


def test_validate_base_slot_not_string():
    """Should fail if base_slot is not a string."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': 'Q1',
                    'question_global': 1,
                    'base_slot': 123  # Should be string
                }
            ]
        },
        'schema_version': '1.0'
    }
    with pytest.raises(ValueError, match="base_slot must be string"):
        validate_questionnaire_structure(data)


def test_validate_empty_micro_questions():
    """Should fail with empty micro_questions list (at least 1 required)."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': []
        },
        'schema_version': '1.0'
    }
    # Should raise because empty questionnaires are not allowed
    with pytest.raises(ValueError, match="at least 1 micro question"):
        validate_questionnaire_structure(data)


def test_validate_single_question():
    """Should pass with single valid question."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': 'Q1',
                    'question_global': 1,
                    'base_slot': 'D1-Q1'
                }
            ]
        },
        'schema_version': '1.0'
    }
    # Should not raise
    validate_questionnaire_structure(data)


def test_validate_many_questions():
    """Should pass with many valid questions."""
    data = {
        'version': '1.0',
        'blocks': {
            'micro_questions': [
                {
                    'question_id': f'Q{i}',
                    'question_global': i,
                    'base_slot': f'D{i//5 + 1}-Q{i%5 + 1}'
                }
                for i in range(1, 301)  # 300 questions
            ]
        },
        'schema_version': '1.0'
    }
    # Should not raise
    validate_questionnaire_structure(data)
