#!/usr/bin/env python3
"""
Validation Predicates - Precondition Checks for Execution
=========================================================

Provides reusable predicates for validating preconditions before
executing analysis steps.

Author: Integration Team - Agent 3
Version: 1.0.0
Python: 3.10+
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    severity: str  # ERROR, WARNING, INFO
    message: str
    context: dict[str, Any]

class ValidationPredicates:
    """
    Collection of validation predicates for precondition checking.

    These predicates verify that all required preconditions are met
    before executing specific analysis steps.
    """

    @staticmethod
    def verify_scoring_preconditions(
        question_spec: dict[str, Any],
        execution_results: dict[str, Any],
        plan_text: str
    ) -> ValidationResult:
        """
        Verify preconditions for TYPE_A scoring modality.

        PRECONDITIONS for TYPE_A (Binary presence/absence):
        - question_spec must have expected_elements list
        - execution_results must be non-empty dict
        - plan_text must be non-empty string

        Args:
            question_spec: Question specification from rubric
            execution_results: Results from execution pipeline
            plan_text: Full plan document text

        Returns:
            ValidationResult indicating if preconditions are met
        """
        errors = []

        # Check question_spec has expected_elements
        if not isinstance(question_spec, dict):
            errors.append("question_spec must be a dictionary")
        elif "expected_elements" not in question_spec:
            errors.append("question_spec must have 'expected_elements' field")
        elif not isinstance(question_spec.get("expected_elements"), list):
            errors.append("expected_elements must be a list")
        elif len(question_spec.get("expected_elements", [])) == 0:
            errors.append("expected_elements cannot be empty")

        # Check execution_results
        if not isinstance(execution_results, dict):
            errors.append("execution_results must be a dictionary")
        elif len(execution_results) == 0:
            errors.append("execution_results cannot be empty")

        # Check plan_text
        if not isinstance(plan_text, str):
            errors.append("plan_text must be a string")
        elif len(plan_text.strip()) == 0:
            errors.append("plan_text cannot be empty")

        if errors:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message="; ".join(errors),
                context={
                    "question_id": question_spec.get("id", "UNKNOWN"),
                    "errors": errors
                }
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message="All scoring preconditions met",
            context={
                "question_id": question_spec.get("id"),
                "expected_elements_count": len(question_spec.get("expected_elements", [])),
                "execution_results_keys": list(execution_results.keys())
            }
        )

    @staticmethod
    def verify_expected_elements(
        question_spec: dict[str, Any],
        cuestionario_data: dict[str, Any]
    ) -> ValidationResult:
        """
        Verify that expected_elements are defined correctly.

        Args:
            question_spec: Question specification from rubric
            cuestionario_data: Full cuestionario metadata

        Returns:
            ValidationResult indicating if expected_elements are valid
        """
        question_id = question_spec.get("id", "UNKNOWN")

        # Check if expected_elements exist
        expected_elements = question_spec.get("expected_elements")

        if expected_elements is None:
            return ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"Question {question_id} has no expected_elements defined",
                context={"question_id": question_id}
            )

        if not isinstance(expected_elements, list):
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"Question {question_id} expected_elements is not a list",
                context={
                    "question_id": question_id,
                    "type": type(expected_elements).__name__
                }
            )

        if len(expected_elements) == 0:
            return ValidationResult(
                is_valid=False,
                severity="WARNING",
                message=f"Question {question_id} has empty expected_elements",
                context={"question_id": question_id}
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message=f"Question {question_id} has valid expected_elements",
            context={
                "question_id": question_id,
                "expected_elements": expected_elements,
                "count": len(expected_elements)
            }
        )

    @staticmethod
    def verify_execution_context(
        question_id: str,
        policy_area: str,
        dimension: str
    ) -> ValidationResult:
        """
        Verify execution context parameters are valid.

        Args:
            question_id: Canonical question ID (P#-D#-Q#)
            policy_area: Policy area (P1-P10)
            dimension: Dimension (D1-D6)

        Returns:
            ValidationResult indicating if context is valid
        """
        errors = []

        # Validate question_id format
        if not question_id or not isinstance(question_id, str):
            errors.append("question_id must be a non-empty string")
        elif not question_id.startswith("P"):
            errors.append(f"question_id '{question_id}' must start with 'P'")

        # Validate policy_area
        if not policy_area or not isinstance(policy_area, str):
            errors.append("policy_area must be a non-empty string")
        elif not policy_area.startswith("P"):
            errors.append(f"policy_area '{policy_area}' must start with 'P'")
        else:
            try:
                area_num = int(policy_area[1:])
                if not (1 <= area_num <= 10):
                    errors.append(f"policy_area '{policy_area}' must be P1-P10")
            except ValueError:
                errors.append(f"Invalid policy_area format: '{policy_area}'")

        # Validate dimension
        if not dimension or not isinstance(dimension, str):
            errors.append("dimension must be a non-empty string")
        elif not dimension.startswith("D"):
            errors.append(f"dimension '{dimension}' must start with 'D'")
        else:
            try:
                dim_num = int(dimension[1:])
                if not (1 <= dim_num <= 6):
                    errors.append(f"dimension '{dimension}' must be D1-D6")
            except ValueError:
                errors.append(f"Invalid dimension format: '{dimension}'")

        if errors:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message="; ".join(errors),
                context={
                    "question_id": question_id,
                    "policy_area": policy_area,
                    "dimension": dimension,
                    "errors": errors
                }
            )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message="Execution context is valid",
            context={
                "question_id": question_id,
                "policy_area": policy_area,
                "dimension": dimension
            }
        )

    @staticmethod
    def verify_producer_availability(
        producer_name: str,
        producers_dict: dict[str, Any]
    ) -> ValidationResult:
        """
        Verify that a producer module is available and initialized.

        Args:
            producer_name: Name of the producer (e.g., 'derek_beach')
            producers_dict: Dictionary of initialized producers

        Returns:
            ValidationResult indicating if producer is available
        """
        if producer_name not in producers_dict:
            return ValidationResult(
                is_valid=False,
                severity="ERROR",
                message=f"Producer '{producer_name}' not found in initialized producers",
                context={
                    "producer_name": producer_name,
                    "available_producers": list(producers_dict.keys())
                }
            )

        producer = producers_dict[producer_name]

        # Check if producer is initialized
        if isinstance(producer, dict):
            status = producer.get("status")
            if status != "initialized":
                return ValidationResult(
                    is_valid=False,
                    severity="ERROR",
                    message=f"Producer '{producer_name}' status is '{status}'",
                    context={
                        "producer_name": producer_name,
                        "status": status,
                        "error": producer.get("error")
                    }
                )

        return ValidationResult(
            is_valid=True,
            severity="INFO",
            message=f"Producer '{producer_name}' is available and initialized",
            context={
                "producer_name": producer_name,
                "status": "initialized"
            }
        )
