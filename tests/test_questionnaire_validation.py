"""Test questionnaire structure validation in factory.py."""
import pytest

from saaaaaa.core.orchestrator.factory import validate_questionnaire_structure


def test_valid_questionnaire_structure():
    """Test validation passes for valid questionnaire."""
    valid_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "blocks": {
            "micro_questions": [
                {
                    "question_id": "Q1",
                    "question_global": 1,  # Must be int, not str
                    "base_slot": "slot1"
                }
            ]
        }
    }
    
    # Should not raise
    validate_questionnaire_structure(valid_data)


def test_missing_top_level_keys():
    """Test validation fails when top-level keys are missing."""
    invalid_data = {
        "version": "1.0.0",
        # Missing schema_version and blocks
    }
    
    with pytest.raises(ValueError, match="Questionnaire missing keys"):
        validate_questionnaire_structure(invalid_data)


def test_missing_micro_questions():
    """Test validation fails when micro_questions is missing."""
    invalid_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "blocks": {}  # Missing micro_questions
    }
    
    with pytest.raises(ValueError, match="blocks.micro_questions is required"):
        validate_questionnaire_structure(invalid_data)


def test_micro_questions_not_list():
    """Test validation fails when micro_questions is not a list."""
    invalid_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "blocks": {
            "micro_questions": "not a list"
        }
    }
    
    with pytest.raises(ValueError, match="blocks.micro_questions must be a list"):
        validate_questionnaire_structure(invalid_data)


def test_question_not_dict():
    """Test validation fails when a question is not a dict."""
    invalid_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "blocks": {
            "micro_questions": [
                "not a dict"
            ]
        }
    }
    
    with pytest.raises(ValueError, match="Question 0 must be a dict"):
        validate_questionnaire_structure(invalid_data)


def test_question_missing_required_fields():
    """Test validation fails when question is missing required fields."""
    invalid_data = {
        "version": "1.0.0",
        "schema_version": "1.0",
        "blocks": {
            "micro_questions": [
                {
                    "question_id": "Q1"
                    # Missing question_global and base_slot
                }
            ]
        }
    }
    
    with pytest.raises(ValueError, match="Question 0 missing keys"):
        validate_questionnaire_structure(invalid_data)
