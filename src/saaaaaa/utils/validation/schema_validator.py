"""
Schema validation for monolith initialization.

This module implements the Monolith Initialization Validator (MIV) that scans
and verifies the integrity of the global schema before runtime execution.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonschema
from pydantic import BaseModel, ConfigDict, Field
from saaaaaa.core.calibration.decorators import calibrated_method


class SchemaInitializationError(Exception):
    """Raised when schema initialization validation fails."""
    pass

class MonolithIntegrityReport(BaseModel):
    """Report of monolith integrity validation."""

    model_config = ConfigDict(extra='allow')

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: str
    validation_passed: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    schema_hash: str
    question_counts: dict[str, int]
    referential_integrity: dict[str, bool]

class MonolithSchemaValidator:
    """
    Monolith Initialization Validator (MIV).

    Bootstrapping process that scans and verifies the integrity of the
    global schema before runtime execution.
    """

    EXPECTED_SCHEMA_VERSION = "2.0.0"
    EXPECTED_MICRO_QUESTIONS = 300
    EXPECTED_MESO_QUESTIONS = 4
    EXPECTED_MACRO_QUESTIONS = 1
    EXPECTED_POLICY_AREAS = 10
    EXPECTED_DIMENSIONS = 6
    EXPECTED_CLUSTERS = 4

    def __init__(self, schema_path: str | None = None) -> None:
        """
        Initialize validator.

        Args:
            schema_path: Path to JSON schema file (optional)
        """
        self.schema_path = schema_path
        self.schema: dict[str, Any] | None = None
        self.errors: list[str] = []
        self.warnings: list[str] = []

        if schema_path:
            self._load_schema()

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._load_schema")
    def _load_schema(self) -> None:
        """Load JSON schema from file."""
        if not self.schema_path:
            return

        schema_file = Path(self.schema_path)
        if not schema_file.exists():
            self.warnings.append(f"Schema file not found: {self.schema_path}")
            return

        try:
            with open(schema_file, encoding='utf-8') as f:
                self.schema = json.load(f)
        except Exception as e:
            self.warnings.append(f"Failed to load schema: {e}")

    def validate_monolith(
        self,
        monolith: dict[str, Any],
        strict: bool = True
    ) -> MonolithIntegrityReport:
        """
        Validate monolith structure and integrity.

        Args:
            monolith: Monolith configuration dictionary
            strict: If True, raises exception on validation failure

        Returns:
            MonolithIntegrityReport with validation results

        Raises:
            SchemaInitializationError: If validation fails and strict=True
        """
        self.errors = []
        self.warnings = []

        # 1. Validate structure
        self._validate_structure(monolith)

        # 2. Validate schema version
        schema_version = self._validate_schema_version(monolith)

        # 3. Validate question counts
        question_counts = self._validate_question_counts(monolith)

        # 4. Validate referential integrity
        referential_integrity = self._validate_referential_integrity(monolith)

        # 5. Validate against JSON schema if available
        if self.schema:
            self._validate_against_schema(monolith)

        # 6. Calculate schema hash
        schema_hash = self._calculate_schema_hash(monolith)

        # Build report
        validation_passed = len(self.errors) == 0

        report = MonolithIntegrityReport(
            schema_version=schema_version,
            validation_passed=validation_passed,
            errors=self.errors,
            warnings=self.warnings,
            schema_hash=schema_hash,
            question_counts=question_counts,
            referential_integrity=referential_integrity
        )

        # Raise error if strict mode and validation failed
        if strict and not validation_passed:
            error_msg = "Schema initialization failed:\n" + "\n".join(
                f"  - {e}" for e in self.errors
            )
            raise SchemaInitializationError(error_msg)

        return report

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._validate_structure")
    def _validate_structure(self, monolith: dict[str, Any]) -> None:
        """Validate top-level structure."""
        required_keys = ['schema_version', 'version', 'blocks', 'integrity']

        for key in required_keys:
            if key not in monolith:
                self.errors.append(f"Missing required top-level key: {key}")

        if 'blocks' in monolith:
            blocks = monolith['blocks']
            required_blocks = [
                'niveles_abstraccion',
                'micro_questions',
                'meso_questions',
                'macro_question',
                'scoring'
            ]

            for block in required_blocks:
                if block not in blocks:
                    self.errors.append(f"Missing required block: {block}")

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._validate_schema_version")
    def _validate_schema_version(self, monolith: dict[str, Any]) -> str:
        """Validate schema version."""
        schema_version = monolith.get('schema_version', '')

        if not schema_version:
            self.errors.append("Missing schema_version")
            return ''

        # Allow any version but warn if not expected
        if schema_version != self.EXPECTED_SCHEMA_VERSION:
            self.warnings.append(
                f"Schema version {schema_version} differs from expected "
                f"{self.EXPECTED_SCHEMA_VERSION}"
            )

        return schema_version

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._validate_question_counts")
    def _validate_question_counts(self, monolith: dict[str, Any]) -> dict[str, int]:
        """Validate question counts."""
        blocks = monolith.get('blocks', {})

        micro_count = len(blocks.get('micro_questions', []))
        meso_count = len(blocks.get('meso_questions', []))
        macro_exists = 1 if blocks.get('macro_question') else 0
        total_count = micro_count + meso_count + macro_exists

        # Validate counts
        if micro_count != self.EXPECTED_MICRO_QUESTIONS:
            self.errors.append(
                f"Expected {self.EXPECTED_MICRO_QUESTIONS} micro questions, "
                f"got {micro_count}"
            )

        if meso_count != self.EXPECTED_MESO_QUESTIONS:
            self.errors.append(
                f"Expected {self.EXPECTED_MESO_QUESTIONS} meso questions, "
                f"got {meso_count}"
            )

        if not macro_exists:
            self.errors.append("Missing macro question")

        expected_total = (
            self.EXPECTED_MICRO_QUESTIONS +
            self.EXPECTED_MESO_QUESTIONS +
            self.EXPECTED_MACRO_QUESTIONS
        )

        if total_count != expected_total:
            self.errors.append(
                f"Expected {expected_total} total questions, got {total_count}"
            )

        return {
            'micro': micro_count,
            'meso': meso_count,
            'macro': macro_exists,
            'total': total_count
        }

    def _validate_referential_integrity(
        self,
        monolith: dict[str, Any]
    ) -> dict[str, bool]:
        """
        Validate referential integrity.

        Ensures no dangling foreign keys or invalid cross-references.
        """
        results = {
            'policy_areas': True,
            'dimensions': True,
            'clusters': True,
            'micro_questions': True
        }

        blocks = monolith.get('blocks', {})
        niveles = blocks.get('niveles_abstraccion', {})

        # Get all valid IDs
        valid_policy_areas = {
            pa['policy_area_id']
            for pa in niveles.get('policy_areas', [])
        }

        valid_dimensions = {
            dim['dimension_id']
            for dim in niveles.get('dimensions', [])
        }

        valid_clusters = {
            cl['cluster_id']
            for cl in niveles.get('clusters', [])
        }

        # Validate cluster references to policy areas
        for cluster in niveles.get('clusters', []):
            cluster_id = cluster.get('cluster_id', 'UNKNOWN')
            for pa_id in cluster.get('policy_area_ids', []):
                if pa_id not in valid_policy_areas:
                    self.errors.append(
                        f"Cluster {cluster_id} references invalid policy area: {pa_id}"
                    )
                    results['clusters'] = False

        # Validate micro questions reference valid areas/dimensions
        for question in blocks.get('micro_questions', []):
            q_id = question.get('question_id', 'UNKNOWN')
            pa_id = question.get('policy_area_id')
            dim_id = question.get('dimension_id')

            if pa_id and pa_id not in valid_policy_areas:
                self.errors.append(
                    f"Question {q_id} references invalid policy area: {pa_id}"
                )
                results['micro_questions'] = False

            if dim_id and dim_id not in valid_dimensions:
                self.errors.append(
                    f"Question {q_id} references invalid dimension: {dim_id}"
                )
                results['micro_questions'] = False

        # Validate meso questions reference valid clusters
        for question in blocks.get('meso_questions', []):
            q_id = question.get('question_id', 'UNKNOWN')
            cl_id = question.get('cluster_id')

            if cl_id and cl_id not in valid_clusters:
                self.errors.append(
                    f"Meso question {q_id} references invalid cluster: {cl_id}"
                )

        return results

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._validate_against_schema")
    def _validate_against_schema(self, monolith: dict[str, Any]) -> None:
        """Validate monolith against JSON schema."""
        if not self.schema:
            return

        try:
            jsonschema.validate(instance=monolith, schema=self.schema)
        except jsonschema.ValidationError as e:
            self.errors.append(f"Schema validation error: {e.message}")
        except Exception as e:
            self.warnings.append(f"Schema validation failed: {e}")

    @calibrated_method("saaaaaa.utils.validation.schema_validator.MonolithSchemaValidator._calculate_schema_hash")
    def _calculate_schema_hash(self, monolith: dict[str, Any]) -> str:
        """Calculate deterministic hash of monolith schema."""
        # Create canonical JSON representation
        canonical = json.dumps(monolith, sort_keys=True, ensure_ascii=True)

        # Calculate SHA-256 hash
        hash_obj = hashlib.sha256(canonical.encode('utf-8'))
        return hash_obj.hexdigest()

    def generate_validation_report(
        self,
        report: MonolithIntegrityReport,
        output_path: str
    ) -> None:
        """
        Generate and save validation report artifact.

        Args:
            report: Validation report
            output_path: Path to save report JSON
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(
                report.model_dump(),
                f,
                indent=2,
                ensure_ascii=False
            )

def validate_monolith_schema(
    monolith: dict[str, Any],
    schema_path: str | None = None,
    strict: bool = True
) -> MonolithIntegrityReport:
    """
    Convenience function to validate monolith schema.

    Args:
        monolith: Monolith configuration
        schema_path: Optional path to JSON schema
        strict: If True, raises exception on failure

    Returns:
        MonolithIntegrityReport

    Raises:
        SchemaInitializationError: If validation fails and strict=True
    """
    validator = MonolithSchemaValidator(schema_path=schema_path)
    return validator.validate_monolith(monolith, strict=strict)
