#!/usr/bin/env python3
"""
Validation Engine - Centralized Rule-Based Validation
=====================================================

Provides a centralized validation engine with:
- Severity levels (ERROR/WARNING/INFO)
- Structured logging
- Context-aware precondition checking
- Integration with validation/predicates.py

Author: Integration Team - Agent 3
Version: 1.0.0
Python: 3.10+
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from saaaaaa.utils.validation.predicates import ValidationPredicates, ValidationResult
from saaaaaa.core.calibration.decorators import calibrated_method

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationReport:
    """Complete validation report with all checks."""
    timestamp: str
    total_checks: int
    passed: int
    failed: int
    warnings: int
    results: list[ValidationResult] = field(default_factory=list)

    @calibrated_method("saaaaaa.utils.validation_engine.ValidationReport.add_result")
    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report."""
        self.results.append(result)
        self.total_checks += 1

        if result.severity == "ERROR" and not result.is_valid:
            self.failed += 1
        elif result.severity == "WARNING":
            self.warnings += 1
        elif result.is_valid:
            self.passed += 1

    @calibrated_method("saaaaaa.utils.validation_engine.ValidationReport.has_errors")
    def has_errors(self) -> bool:
        """Check if report contains any errors."""
        return self.failed > 0

    @calibrated_method("saaaaaa.utils.validation_engine.ValidationReport.summary")
    def summary(self) -> str:
        """Generate summary string."""
        return (f"Validation Summary: {self.passed}/{self.total_checks} passed, "
                f"{self.failed} errors, {self.warnings} warnings")

class ValidationEngine:
    """
    Centralized validation engine for precondition checking.

    Integrates with validation/predicates.py to provide:
    - Precondition verification before execution steps
    - Structured validation reporting
    - Context-aware error messages
    - Severity-based logging (ERROR/WARNING/INFO)
    """

    def __init__(self, questionnaire_provider=None) -> None:
        """
        Initialize validation engine.

        Args:
            questionnaire_provider: QuestionnaireResourceProvider instance (injected via DI)
                                   If None, validation operations requiring questionnaire
                                   data will use ValidationPredicates without provider.

        ARCHITECTURAL NOTE: Direct cuestionario_data parameter REMOVED.
        Questionnaire access must go through QuestionnaireResourceProvider.
        """
        self.questionnaire_provider = questionnaire_provider
        self.predicates = ValidationPredicates()
        logger.info("ValidationEngine initialized")

    def validate_scoring_preconditions(
        self,
        question_spec: dict[str, Any],
        execution_results: dict[str, Any],
        plan_text: str
    ) -> ValidationResult:
        """
        Validate preconditions for scoring operations.

        Wraps ValidationPredicates.verify_scoring_preconditions with logging.

        Args:
            question_spec: Question specification from rubric
            execution_results: Results from execution pipeline
            plan_text: Full plan document text

        Returns:
            ValidationResult
        """
        logger.debug(f"Validating scoring preconditions for question: "
                    f"{question_spec.get('id', 'UNKNOWN')}")

        result = self.predicates.verify_scoring_preconditions(
            question_spec, execution_results, plan_text
        )

        self._log_result(result)
        return result

    def validate_expected_elements(
        self,
        question_spec: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate expected_elements from questionnaire provider.

        Args:
            question_spec: Question specification

        Returns:
            ValidationResult
        """
        logger.debug(f"Validating expected_elements for question: "
                    f"{question_spec.get('id', 'UNKNOWN')}")

        # Get questionnaire data from provider if available
        questionnaire_data = {}
        if self.questionnaire_provider is not None:
            questionnaire_data = self.questionnaire_provider.get_data()

        result = self.predicates.verify_expected_elements(
            question_spec, questionnaire_data
        )

        self._log_result(result)
        return result

    def validate_execution_context(
        self,
        question_id: str,
        policy_area: str,
        dimension: str
    ) -> ValidationResult:
        """
        Validate execution context parameters.

        Args:
            question_id: Canonical question ID
            policy_area: Policy area (P1-P10)
            dimension: Dimension (D1-D6)

        Returns:
            ValidationResult
        """
        logger.debug(f"Validating execution context: {question_id}")

        result = self.predicates.verify_execution_context(
            question_id, policy_area, dimension
        )

        self._log_result(result)
        return result

    def validate_producer_availability(
        self,
        producer_name: str,
        producers_dict: dict[str, Any]
    ) -> ValidationResult:
        """
        Validate that producer is available and initialized.

        Args:
            producer_name: Name of the producer
            producers_dict: Dictionary of initialized producers

        Returns:
            ValidationResult
        """
        logger.debug(f"Validating producer availability: {producer_name}")

        result = self.predicates.verify_producer_availability(
            producer_name, producers_dict
        )

        self._log_result(result)
        return result

    def validate_all_preconditions(
        self,
        question_spec: dict[str, Any],
        execution_results: dict[str, Any],
        plan_text: str,
        producers_dict: dict[str, Any]
    ) -> ValidationReport:
        """
        Run all validation checks for a question execution.

        Args:
            question_spec: Question specification
            execution_results: Execution results
            plan_text: Plan document text
            producers_dict: Initialized producers

        Returns:
            ValidationReport with all checks
        """
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_checks=0,
            passed=0,
            failed=0,
            warnings=0
        )

        logger.info("=" * 80)
        logger.info(f"Running validation checks for: {question_spec.get('id', 'UNKNOWN')}")
        logger.info("=" * 80)

        # Check 1: Execution context
        question_id = question_spec.get("id", "")
        policy_area = question_spec.get("policy_area", "")
        dimension = question_spec.get("dimension", "")

        result = self.validate_execution_context(question_id, policy_area, dimension)
        report.add_result(result)

        # Check 2: Expected elements
        result = self.validate_expected_elements(question_spec)
        report.add_result(result)

        # Check 3: Scoring preconditions
        result = self.validate_scoring_preconditions(
            question_spec, execution_results, plan_text
        )
        report.add_result(result)

        # Check 4: Producer availability (if specified)
        evidence_sources = question_spec.get("evidence_sources", {})
        orchestrator_key = evidence_sources.get("orchestrator_key", "")

        if orchestrator_key:
            # Handle both string and list formats
            if isinstance(orchestrator_key, str):
                result = self.validate_producer_availability(
                    orchestrator_key, producers_dict
                )
                report.add_result(result)
            elif isinstance(orchestrator_key, list):
                for producer in orchestrator_key:
                    result = self.validate_producer_availability(
                        producer, producers_dict
                    )
                    report.add_result(result)

        logger.info("=" * 80)
        logger.info(report.summary())
        logger.info("=" * 80)

        return report

    @calibrated_method("saaaaaa.utils.validation_engine.ValidationEngine._log_result")
    def _log_result(self, result: ValidationResult) -> None:
        """Log validation result with appropriate severity."""
        if result.severity == "ERROR":
            if result.is_valid:
                logger.debug(f"✓ {result.message}")
            else:
                logger.error(f"✗ {result.message}")
        elif result.severity == "WARNING":
            logger.warning(f"⚠ {result.message}")
        else:
            logger.debug(f"ℹ {result.message}")

    def create_validation_report(
        self,
        results: list[ValidationResult]
    ) -> ValidationReport:
        """
        Create a validation report from a list of results.

        Args:
            results: List of ValidationResult objects

        Returns:
            ValidationReport
        """
        report = ValidationReport(
            timestamp=datetime.now().isoformat(),
            total_checks=0,
            passed=0,
            failed=0,
            warnings=0
        )

        for result in results:
            report.add_result(result)

        return report
