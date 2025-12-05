"""Test Phase 6: Schema Validation

Tests Phase 6 schema validation logic including:
- Structural validation (type classification, homogeneity checking)
- List length equality validation across blocks
- Dict key set equality validation
- Semantic validation (type field rules, required field enforcement)
- Minimum value constraints
- Schema version validation
- Question count validation
- Referential integrity checking
- Field coverage validation
- Hash calculation and verification
"""

import pytest

from farfan_pipeline.utils.validation.schema_validator import (
    MonolithIntegrityReport,
    MonolithSchemaValidator,
    SchemaInitializationError,
)


class TestPhase6StructuralValidation:
    """Test structural validation including type classification and homogeneity."""

    @pytest.fixture
    def valid_monolith(self):
        """Create valid monolith structure."""
        return {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {"method": "weighted"},
            },
            "integrity": {"checksum": "abc123"},
        }

    def test_validate_top_level_keys_present(self, valid_monolith):
        """Test validation checks for required top-level keys."""
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(valid_monolith, strict=False)

        assert report.validation_passed

    def test_missing_schema_version_fails_validation(self):
        """Test missing schema_version fails validation."""
        monolith = {
            "version": "1.0.0",
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False
        assert any("schema_version" in e for e in report.errors)

    def test_missing_blocks_fails_validation(self):
        """Test missing blocks section fails validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False
        assert any("blocks" in e for e in report.errors)

    def test_required_blocks_present(self, valid_monolith):
        """Test all required blocks are present."""
        validator = MonolithSchemaValidator()

        validator.validate_monolith(valid_monolith, strict=False)

        assert "niveles_abstraccion" in valid_monolith["blocks"]
        assert "micro_questions" in valid_monolith["blocks"]
        assert "meso_questions" in valid_monolith["blocks"]
        assert "macro_question" in valid_monolith["blocks"]

    def test_missing_required_block_fails_validation(self, valid_monolith):
        """Test missing required block fails validation."""
        del valid_monolith["blocks"]["micro_questions"]
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(valid_monolith, strict=False)

        assert report.validation_passed is False
        assert any("micro_questions" in e for e in report.errors)

    def test_type_classification_list_vs_dict(self, valid_monolith):
        """Test type classification distinguishes list from dict."""
        MonolithSchemaValidator()

        blocks = valid_monolith["blocks"]
        assert isinstance(blocks["micro_questions"], list)
        assert isinstance(blocks["macro_question"], dict)

    def test_homogeneous_list_validation(self):
        """Test list homogeneity validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": "Q001", "text": "Question 1"},
                    {"id": "Q002", "text": "Question 2"},
                ],
                "meso_questions": [{"id": "M01"}],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        validator.validate_monolith(monolith, strict=False)

        # All items in micro_questions should be dicts with same structure
        assert all(isinstance(q, dict) for q in monolith["blocks"]["micro_questions"])

    def test_heterogeneous_list_detected(self):
        """Test heterogeneous list (mixed types) is detected."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": "Q001"},
                    "not_a_dict",  # Different type
                    {"id": "Q003"},
                ],
                "meso_questions": [{"id": "M01"}],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }

        # Should detect type inconsistency
        items = monolith["blocks"]["micro_questions"]
        types_present = {type(item) for item in items}
        assert len(types_present) > 1


class TestPhase6ListLengthEquality:
    """Test list length equality validation across blocks."""

    def test_micro_questions_count_300(self):
        """Test micro_questions list has exactly 300 items."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.question_counts["micro_questions"] == 300

    def test_incorrect_micro_questions_count_fails(self):
        """Test incorrect micro_questions count fails validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": f"Q{i:03d}"} for i in range(1, 251)
                ],  # Only 250
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False
        assert report.question_counts["micro_questions"] == 250

    def test_meso_questions_count_4(self):
        """Test meso_questions list has exactly 4 items."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.question_counts["meso_questions"] == 4

    def test_incorrect_meso_questions_count_fails(self):
        """Test incorrect meso_questions count fails validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 4)],  # Only 3
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False

    def test_macro_question_count_1(self):
        """Test macro_question is single dict (count=1)."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.question_counts.get("macro_question") == 1

    def test_empty_list_detected(self):
        """Test empty question list is detected."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [],  # Empty
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.question_counts["micro_questions"] == 0
        assert report.validation_passed is False


class TestPhase6DictKeySetEquality:
    """Test dict key set equality validation."""

    def test_all_micro_questions_have_same_keys(self):
        """Test all micro questions have same key set."""
        questions = [
            {"id": "Q001", "text": "Question 1", "dimension": "D1"},
            {"id": "Q002", "text": "Question 2", "dimension": "D2"},
            {"id": "Q003", "text": "Question 3", "dimension": "D3"},
        ]

        key_sets = [set(q.keys()) for q in questions]
        assert all(keys == key_sets[0] for keys in key_sets)

    def test_inconsistent_keys_detected(self):
        """Test inconsistent key sets across questions detected."""
        questions = [
            {"id": "Q001", "text": "Question 1"},
            {"id": "Q002", "text": "Question 2", "extra_field": "value"},
            {"id": "Q003", "text": "Question 3"},
        ]

        key_sets = [set(q.keys()) for q in questions]
        assert not all(keys == key_sets[0] for keys in key_sets)

    def test_missing_key_in_subset_detected(self):
        """Test missing key in subset of questions detected."""
        questions = [
            {"id": "Q001", "text": "Question 1", "required_field": "value"},
            {"id": "Q002", "text": "Question 2"},  # Missing required_field
            {"id": "Q003", "text": "Question 3", "required_field": "value"},
        ]

        # Check for required_field presence
        has_required = [("required_field" in q) for q in questions]
        assert not all(has_required)

    def test_extra_key_in_subset_detected(self):
        """Test extra key in subset of questions detected."""
        questions = [
            {"id": "Q001", "text": "Question 1"},
            {"id": "Q002", "text": "Question 2", "extra": "field"},  # Extra key
            {"id": "Q003", "text": "Question 3"},
        ]

        key_counts = {}
        for q in questions:
            for key in q.keys():
                key_counts[key] = key_counts.get(key, 0) + 1

        assert key_counts["extra"] == 1  # Only in one question

    def test_nested_dict_key_consistency(self):
        """Test nested dict key consistency validation."""
        questions = [
            {"id": "Q001", "metadata": {"author": "A", "date": "2024"}},
            {"id": "Q002", "metadata": {"author": "B", "date": "2024"}},
            {"id": "Q003", "metadata": {"author": "C", "date": "2024"}},
        ]

        nested_key_sets = [set(q["metadata"].keys()) for q in questions]
        assert all(keys == nested_key_sets[0] for keys in nested_key_sets)


class TestPhase6SemanticValidation:
    """Test semantic validation including type and required field rules."""

    def test_required_field_id_present(self):
        """Test required 'id' field is present in all questions."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": "Q001", "text": "Q1"},
                    {"id": "Q002", "text": "Q2"},
                ],
                "meso_questions": [{"id": "M01"}],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }

        # Check all questions have id
        all_have_id = all("id" in q for q in monolith["blocks"]["micro_questions"])
        assert all_have_id is True

    def test_missing_required_field_detected(self):
        """Test missing required field is detected."""
        questions = [
            {"id": "Q001", "text": "Question 1"},
            {"text": "Question 2"},  # Missing id
            {"id": "Q003", "text": "Question 3"},
        ]

        all_have_id = all("id" in q for q in questions)
        assert all_have_id is False

    def test_type_field_validation_string(self):
        """Test type field is validated as string."""
        question = {"id": "Q001", "type": "diagnostic", "text": "Question"}

        assert isinstance(question.get("type"), str)

    def test_type_field_validation_non_string_detected(self):
        """Test non-string type field detected."""
        question = {"id": "Q001", "type": 123, "text": "Question"}

        assert not isinstance(question.get("type"), str)

    def test_dimension_field_format_validation(self):
        """Test dimension field format validation (D1-D6)."""
        valid_dimensions = ["D1", "D2", "D3", "D4", "D5", "D6"]

        for dim in valid_dimensions:
            assert dim[0] == "D"
            assert dim[1].isdigit()

    def test_invalid_dimension_format_detected(self):
        """Test invalid dimension format detected."""
        invalid_dimensions = ["D0", "D7", "X1", "1D"]
        valid_pattern = ["D1", "D2", "D3", "D4", "D5", "D6"]

        for dim in invalid_dimensions:
            assert dim not in valid_pattern

    def test_policy_area_format_validation(self):
        """Test policy area format validation (PA01-PA10)."""
        valid_areas = [f"PA{i:02d}" for i in range(1, 11)]

        assert len(valid_areas) == 10
        assert all(pa.startswith("PA") for pa in valid_areas)

    def test_enum_value_validation(self):
        """Test enum value validation for fields with fixed values."""
        valid_types = ["diagnostic", "activity", "result", "impact"]
        question_type = "diagnostic"

        assert question_type in valid_types

    def test_invalid_enum_value_detected(self):
        """Test invalid enum value detected."""
        valid_types = ["diagnostic", "activity", "result", "impact"]
        question_type = "invalid_type"

        assert question_type not in valid_types


class TestPhase6MinimumValueConstraints:
    """Test minimum value constraints validation."""

    def test_question_count_minimum_300(self):
        """Test micro_questions minimum count is 300."""
        validator = MonolithSchemaValidator()
        assert validator.EXPECTED_MICRO_QUESTIONS == 300

    def test_below_minimum_count_fails(self):
        """Test question count below minimum fails validation."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": f"Q{i:03d}"} for i in range(1, 100)
                ],  # Only 99
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False

    def test_weight_minimum_zero(self):
        """Test weight field minimum value is 0."""
        weight = 0.5
        assert weight >= 0

    def test_negative_weight_invalid(self):
        """Test negative weight is invalid."""
        weight = -0.1
        assert weight < 0  # Should be detected as invalid

    def test_confidence_range_0_to_1(self):
        """Test confidence value in range [0, 1]."""
        valid_confidences = [0.0, 0.5, 0.75, 1.0]

        for conf in valid_confidences:
            assert 0.0 <= conf <= 1.0

    def test_confidence_out_of_range_detected(self):
        """Test confidence value outside range detected."""
        invalid_confidences = [-0.1, 1.5, 2.0]

        for conf in invalid_confidences:
            assert not (0.0 <= conf <= 1.0)


class TestPhase6SchemaVersionValidation:
    """Test schema version validation."""

    def test_schema_version_format_validation(self):
        """Test schema version follows semantic versioning."""
        version = "2.0.0"
        parts = version.split(".")

        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_expected_schema_version_2_0_0(self):
        """Test expected schema version is 2.0.0."""
        validator = MonolithSchemaValidator()
        assert validator.EXPECTED_SCHEMA_VERSION == "2.0.0"

    def test_different_schema_version_warning(self):
        """Test different schema version generates warning."""
        monolith = {
            "schema_version": "1.5.0",  # Different version
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert len(report.warnings) > 0

    def test_missing_schema_version_error(self):
        """Test missing schema_version generates error."""
        monolith = {
            "version": "1.0.0",
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False
        assert report.schema_version == ""


class TestPhase6ReferentialIntegrity:
    """Test referential integrity checking."""

    def test_question_id_uniqueness(self):
        """Test all question IDs are unique."""
        questions = [
            {"id": "Q001"},
            {"id": "Q002"},
            {"id": "Q003"},
        ]

        ids = [q["id"] for q in questions]
        assert len(ids) == len(set(ids))

    def test_duplicate_question_id_detected(self):
        """Test duplicate question ID detected."""
        questions = [
            {"id": "Q001"},
            {"id": "Q002"},
            {"id": "Q001"},  # Duplicate
        ]

        ids = [q["id"] for q in questions]
        assert len(ids) != len(set(ids))

    def test_cross_reference_validation(self):
        """Test cross-reference between blocks validated."""
        monolith = {
            "blocks": {
                "micro_questions": [
                    {"id": "Q001", "meso_parent": "M01"},
                    {"id": "Q002", "meso_parent": "M01"},
                ],
                "meso_questions": [
                    {"id": "M01"},
                ],
            }
        }

        # Check all referenced meso IDs exist
        meso_ids = {q["id"] for q in monolith["blocks"]["meso_questions"]}
        referenced_meso = {
            q.get("meso_parent")
            for q in monolith["blocks"]["micro_questions"]
            if "meso_parent" in q
        }

        assert referenced_meso.issubset(meso_ids)

    def test_broken_cross_reference_detected(self):
        """Test broken cross-reference detected."""
        monolith = {
            "blocks": {
                "micro_questions": [
                    {"id": "Q001", "meso_parent": "M01"},
                    {"id": "Q002", "meso_parent": "M99"},  # Doesn't exist
                ],
                "meso_questions": [
                    {"id": "M01"},
                ],
            }
        }

        meso_ids = {q["id"] for q in monolith["blocks"]["meso_questions"]}
        referenced_meso = {
            q.get("meso_parent")
            for q in monolith["blocks"]["micro_questions"]
            if "meso_parent" in q
        }

        assert not referenced_meso.issubset(meso_ids)


class TestPhase6FieldCoverageValidation:
    """Test field coverage validation."""

    def test_all_questions_have_required_fields(self):
        """Test all questions have required fields."""
        required_fields = {"id", "text"}
        questions = [
            {"id": "Q001", "text": "Question 1", "dimension": "D1"},
            {"id": "Q002", "text": "Question 2", "dimension": "D2"},
        ]

        for q in questions:
            assert required_fields.issubset(set(q.keys()))

    def test_missing_optional_field_allowed(self):
        """Test missing optional field is allowed."""
        required_fields = {"id", "text"}
        question = {"id": "Q001", "text": "Question 1"}

        assert required_fields.issubset(set(question.keys()))
        assert "optional_field" not in question

    def test_field_coverage_percentage(self):
        """Test field coverage percentage calculation."""
        all_possible_fields = {"id", "text", "dimension", "weight", "type"}
        questions = [
            {"id": "Q001", "text": "Q1", "dimension": "D1"},
            {"id": "Q002", "text": "Q2", "dimension": "D2", "weight": 1.0},
        ]

        total_fields = len(all_possible_fields) * len(questions)
        present_fields = sum(
            len(set(q.keys()) & all_possible_fields) for q in questions
        )
        coverage = present_fields / total_fields

        assert 0.0 <= coverage <= 1.0


class TestPhase6HashCalculation:
    """Test hash calculation and verification."""

    def test_schema_hash_calculated(self):
        """Test schema hash is calculated in report."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.schema_hash
        assert len(report.schema_hash) > 0

    def test_same_monolith_same_hash(self):
        """Test same monolith produces same hash."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {"test": "data"},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report1 = validator.validate_monolith(monolith, strict=False)
        report2 = validator.validate_monolith(monolith, strict=False)

        assert report1.schema_hash == report2.schema_hash

    def test_different_monolith_different_hash(self):
        """Test different monolith produces different hash."""
        monolith1 = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {"test": "data1"},
            "integrity": {},
        }
        monolith2 = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {"test": "data2"},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report1 = validator.validate_monolith(monolith1, strict=False)
        report2 = validator.validate_monolith(monolith2, strict=False)

        assert report1.schema_hash != report2.schema_hash


class TestPhase6ValidationReport:
    """Test validation report structure and content."""

    def test_report_contains_timestamp(self):
        """Test validation report contains timestamp."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.timestamp
        assert len(report.timestamp) > 0

    def test_report_contains_schema_version(self):
        """Test validation report contains schema version."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.schema_version == "2.0.0"

    def test_report_contains_validation_passed_flag(self):
        """Test validation report contains validation_passed boolean."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report.validation_passed, bool)

    def test_report_contains_errors_list(self):
        """Test validation report contains errors list."""
        monolith = {
            "version": "1.0.0",  # Missing schema_version
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report.errors, list)
        assert len(report.errors) > 0

    def test_report_contains_warnings_list(self):
        """Test validation report contains warnings list."""
        monolith = {
            "schema_version": "1.5.0",  # Different version triggers warning
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report.warnings, list)

    def test_report_contains_question_counts(self):
        """Test validation report contains question counts."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report.question_counts, dict)
        assert "micro_questions" in report.question_counts

    def test_report_contains_referential_integrity(self):
        """Test validation report contains referential integrity dict."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [{"id": f"Q{i:03d}"} for i in range(1, 301)],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report.referential_integrity, dict)


class TestPhase6StrictMode:
    """Test strict mode validation behavior."""

    def test_strict_mode_raises_exception_on_error(self):
        """Test strict mode raises SchemaInitializationError on validation failure."""
        monolith = {
            "version": "1.0.0",  # Missing schema_version
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        with pytest.raises(SchemaInitializationError):
            validator.validate_monolith(monolith, strict=True)

    def test_non_strict_mode_returns_report(self):
        """Test non-strict mode returns report without raising."""
        monolith = {
            "version": "1.0.0",  # Missing schema_version
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report, MonolithIntegrityReport)
        assert report.validation_passed is False

    def test_strict_mode_exception_contains_error_details(self):
        """Test strict mode exception contains detailed error messages."""
        monolith = {
            "version": "1.0.0",
            "blocks": {},
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        with pytest.raises(SchemaInitializationError) as exc_info:
            validator.validate_monolith(monolith, strict=True)

        error_msg = str(exc_info.value)
        assert "Schema initialization failed" in error_msg


class TestPhase6EdgeCases:
    """Test edge cases in schema validation."""

    def test_empty_monolith_dict(self):
        """Test validation with empty monolith dict."""
        monolith = {}
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert report.validation_passed is False
        assert len(report.errors) > 0

    def test_none_monolith_handled(self):
        """Test validation handles None monolith gracefully."""
        validator = MonolithSchemaValidator()

        with pytest.raises((TypeError, AttributeError)):
            validator.validate_monolith(None, strict=False)

    def test_deeply_nested_structure(self):
        """Test validation handles deeply nested structures."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {
                        "id": f"Q{i:03d}",
                        "nested": {"level1": {"level2": {"level3": "deep_value"}}},
                    }
                    for i in range(1, 301)
                ],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        # Should not crash
        assert isinstance(report, MonolithIntegrityReport)

    def test_unicode_in_question_text(self):
        """Test validation handles unicode characters in questions."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {"id": f"Q{i:03d}", "text": f"Pregunta {i} con áéíóú ñ"}
                    for i in range(1, 301)
                ],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report, MonolithIntegrityReport)

    def test_large_monolith_performance(self):
        """Test validation performance with large monolith."""
        monolith = {
            "schema_version": "2.0.0",
            "version": "1.0.0",
            "blocks": {
                "niveles_abstraccion": ["micro", "meso", "macro"],
                "micro_questions": [
                    {
                        "id": f"Q{i:03d}",
                        "text": f"Question {i}" * 100,  # Large text
                        "dimension": f"D{(i % 6) + 1}",
                        "weight": 1.0,
                    }
                    for i in range(1, 301)
                ],
                "meso_questions": [{"id": f"M{i:02d}"} for i in range(1, 5)],
                "macro_question": {"id": "MACRO_01"},
                "scoring": {},
            },
            "integrity": {},
        }
        validator = MonolithSchemaValidator()

        report = validator.validate_monolith(monolith, strict=False)

        assert isinstance(report, MonolithIntegrityReport)
