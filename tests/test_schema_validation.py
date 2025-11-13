"""
Tests for monolith schema validation at initialization.

Tests the Monolith Initialization Validator (MIV).
"""

import json

import pytest

from saaaaaa.utils.validation.schema_validator import (
    MonolithIntegrityReport,
    MonolithSchemaValidator,
    SchemaInitializationError,
    validate_monolith_schema,
)

class TestMonolithSchemaValidator:
    """Test MonolithSchemaValidator."""

    def test_valid_monolith_passes(self):
        """Test that a valid monolith passes validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "generated_at": "2024-01-01T00:00:00Z",
            "integrity": {
                "monolith_hash": "abc123",
                "question_count": {
                    "micro": 300,
                    "meso": 4,
                    "macro": 1,
                    "total": 305
                }
            },
            "blocks": {
                "niveles_abstraccion": {
                    "policy_areas": [
                        {"policy_area_id": f"PA{i:02d}"}
                        for i in range(1, 11)
                    ],
                    "dimensions": [
                        {"dimension_id": f"DIM{i:02d}"}
                        for i in range(1, 7)
                    ],
                    "clusters": [
                        {
                            "cluster_id": "CL01",
                            "policy_area_ids": ["PA02", "PA03", "PA07"],
                            "i18n": {"keys": {"label_es": "Cluster 1"}}
                        },
                        {
                            "cluster_id": "CL02",
                            "policy_area_ids": ["PA01", "PA05", "PA06"],
                            "i18n": {"keys": {"label_es": "Cluster 2"}}
                        },
                        {
                            "cluster_id": "CL03",
                            "policy_area_ids": ["PA04", "PA08"],
                            "i18n": {"keys": {"label_es": "Cluster 3"}}
                        },
                        {
                            "cluster_id": "CL04",
                            "policy_area_ids": ["PA09", "PA10"],
                            "i18n": {"keys": {"label_es": "Cluster 4"}}
                        }
                    ]
                },
                "micro_questions": [
                    {
                        "question_id": f"Q{i:03d}",
                        "question_global": i,
                        "policy_area_id": f"PA{((i-1)//30)+1:02d}",
                        "dimension_id": f"DIM{((i-1)%6)+1:02d}"
                    }
                    for i in range(1, 301)
                ],
                "meso_questions": [
                    {
                        "question_id": f"Q{i:03d}",
                        "cluster_id": f"CL{i-300:02d}",
                        "type": "MESO"
                    }
                    for i in range(301, 305)
                ],
                "macro_question": {
                    "question_id": "Q305",
                    "question_global": 305,
                    "type": "MACRO"
                },
                "scoring": {}
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed
        assert len(report.errors) == 0
        assert report.schema_hash is not None
        assert report.question_counts['micro'] == 300
        assert report.question_counts['meso'] == 4
        assert report.question_counts['macro'] == 1

    def test_missing_top_level_key_fails(self):
        """Test that missing top-level keys cause validation failure."""
        monolith = {
            "version": "1.0.0",
            # Missing schema_version
            "blocks": {}
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("schema_version" in e for e in report.errors)

    def test_missing_required_block_fails(self):
        """Test that missing required blocks cause validation failure."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {},
                # Missing micro_questions, meso_questions, etc.
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("micro_questions" in e for e in report.errors)

    def test_incorrect_question_count_fails(self):
        """Test that incorrect question counts cause validation failure."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {},
                "micro_questions": [{"question_id": f"Q{i:03d}"} for i in range(1, 100)],  # Only 99
                "meso_questions": [],
                "macro_question": None,
                "scoring": {}
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("300 micro questions" in e for e in report.errors)

    def test_invalid_policy_area_reference_fails(self):
        """Test that invalid policy area references fail validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {
                    "policy_areas": [{"policy_area_id": "PA01"}],
                    "dimensions": [],
                    "clusters": [
                        {
                            "cluster_id": "CL01",
                            "policy_area_ids": ["PA01", "PA99"]  # PA99 doesn't exist
                        }
                    ]
                },
                "micro_questions": [],
                "meso_questions": [],
                "macro_question": {},
                "scoring": {}
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("PA99" in e for e in report.errors)

    def test_strict_mode_raises_exception(self):
        """Test that strict mode raises exception on validation failure."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {}  # Missing required blocks
        }

        validator = MonolithSchemaValidator()

        with pytest.raises(SchemaInitializationError) as exc_info:
            validator.validate_monolith(monolith, strict=True)

        assert "Schema initialization failed" in str(exc_info.value)

    def test_schema_hash_calculation(self):
        """Test that schema hash is calculated correctly."""
        monolith = {
            "schema_version": "2.0.0",
            "blocks": {}
        }

        validator = MonolithSchemaValidator()
        report1 = validator.validate_monolith(monolith, strict=False)
        report2 = validator.validate_monolith(monolith, strict=False)

        # Same monolith should produce same hash
        assert report1.schema_hash == report2.schema_hash

        # Different monolith should produce different hash
        monolith_modified = {
            "schema_version": "3.0.0",
            "blocks": {}
        }
        report3 = validator.validate_monolith(monolith_modified, strict=False)
        assert report1.schema_hash != report3.schema_hash

    def test_referential_integrity_micro_questions(self):
        """Test referential integrity for micro questions."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {
                    "policy_areas": [{"policy_area_id": "PA01"}],
                    "dimensions": [{"dimension_id": "DIM01"}],
                    "clusters": []
                },
                "micro_questions": [
                    {
                        "question_id": "Q001",
                        "policy_area_id": "PA99",  # Invalid reference
                        "dimension_id": "DIM01"
                    }
                ],
                "meso_questions": [],
                "macro_question": {},
                "scoring": {}
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("PA99" in e and "Q001" in e for e in report.errors)

    def test_referential_integrity_meso_questions(self):
        """Test referential integrity for meso questions."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {
                    "policy_areas": [],
                    "dimensions": [],
                    "clusters": [{"cluster_id": "CL01"}]
                },
                "micro_questions": [],
                "meso_questions": [
                    {
                        "question_id": "Q301",
                        "cluster_id": "CL99"  # Invalid reference
                    }
                ],
                "macro_question": {},
                "scoring": {}
            }
        }

        validator = MonolithSchemaValidator()
        report = validator.validate_monolith(monolith, strict=False)

        assert not report.validation_passed
        assert any("CL99" in e and "Q301" in e for e in report.errors)

class TestValidateMonolithSchemaHelper:
    """Test the validate_monolith_schema helper function."""

    def test_helper_function_strict_mode(self):
        """Test helper function in strict mode."""
        invalid_monolith = {
            "schema_version": "2.0.0",
            "blocks": {}
        }

        with pytest.raises(SchemaInitializationError):
            validate_monolith_schema(invalid_monolith, strict=True)

    def test_helper_function_non_strict_mode(self):
        """Test helper function in non-strict mode."""
        invalid_monolith = {
            "schema_version": "2.0.0",
            "blocks": {}
        }

        report = validate_monolith_schema(invalid_monolith, strict=False)
        assert not report.validation_passed
        assert isinstance(report, MonolithIntegrityReport)

class TestIntegrityReportGeneration:
    """Test integrity report generation."""

    def test_report_contains_timestamp(self):
        """Test that report contains timestamp."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {},
                "micro_questions": [],
                "meso_questions": [],
                "macro_question": {},
                "scoring": {}
            }
        }

        report = validate_monolith_schema(monolith, strict=False)
        assert report.timestamp is not None
        # Verify it's in ISO format
        from datetime import datetime
        datetime.fromisoformat(report.timestamp.replace('Z', '+00:00'))

    def test_report_serializable_to_json(self):
        """Test that report can be serialized to JSON."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
            "blocks": {
                "niveles_abstraccion": {},
                "micro_questions": [],
                "meso_questions": [],
                "macro_question": {},
                "scoring": {}
            }
        }

        report = validate_monolith_schema(monolith, strict=False)

        # Should be able to serialize to JSON
        json_str = json.dumps(report.model_dump())
        assert json_str is not None

        # Should be able to deserialize
        data = json.loads(json_str)
        assert data['schema_version'] == "2.0.0"
        assert 'timestamp' in data
        assert 'validation_passed' in data
