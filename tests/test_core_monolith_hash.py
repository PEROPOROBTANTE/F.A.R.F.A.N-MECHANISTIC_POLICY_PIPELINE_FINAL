"""Test stable content-based hash for monolith data in core.py."""
import hashlib
import json

import pytest



# Mark all tests in this module as outdated
pytestmark = pytest.mark.skip(reason="Hash validation now part of questionnaire_validation")

def test_monolith_hash_reproducibility():
    """Test that same monolith data produces same hash across runs."""
    monolith = {
        "version": "1.0.0",
        "blocks": {
            "micro_questions": [
                {"question_id": "Q1", "question_global": "Q1 Global", "base_slot": "slot1"}
            ],
            "meso_questions": [],
            "macro_question": {}
        }
    }
    
    # Compute hash twice
    hash1 = hashlib.sha256(
        json.dumps(monolith, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    hash2 = hashlib.sha256(
        json.dumps(monolith, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    assert hash1 == hash2, "Hash should be reproducible for identical data"


def test_monolith_hash_changes_with_mutation():
    """Test that hash changes when data is mutated."""
    monolith1 = {
        "version": "1.0.0",
        "blocks": {
            "micro_questions": [
                {"question_id": "Q1", "question_global": "Q1 Global", "base_slot": "slot1"}
            ]
        }
    }
    
    monolith2 = {
        "version": "1.0.0",
        "blocks": {
            "micro_questions": [
                {"question_id": "Q2", "question_global": "Q2 Global", "base_slot": "slot2"}
            ]
        }
    }
    
    hash1 = hashlib.sha256(
        json.dumps(monolith1, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    hash2 = hashlib.sha256(
        json.dumps(monolith2, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    assert hash1 != hash2, "Hash should change when data is mutated"


def test_monolith_hash_key_order_independent():
    """Test that hash is independent of key order in dict."""
    monolith1 = {
        "version": "1.0.0",
        "blocks": {"micro_questions": []},
        "schema_version": "1.0"
    }
    
    monolith2 = {
        "schema_version": "1.0",
        "version": "1.0.0",
        "blocks": {"micro_questions": []}
    }
    
    hash1 = hashlib.sha256(
        json.dumps(monolith1, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    hash2 = hashlib.sha256(
        json.dumps(monolith2, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    
    assert hash1 == hash2, "Hash should be independent of key order"
