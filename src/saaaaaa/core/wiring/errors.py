"""Typed error classes for wiring system.

All wiring errors include prescriptive fix information to guide remediation.
Errors are loud and explicit - no silent degradation is permitted.
"""

from __future__ import annotations

from typing import Any


class WiringError(Exception):
    """Base class for all wiring errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class WiringContractError(WiringError):
    """Raised when a contract between two links is violated.

    Attributes:
        link: Name of the violated link (e.g., "cpp->adapter")
        expected_schema: Expected schema/type
        received_schema: Actual schema/type received
        field: Specific field that failed (if applicable)
        fix: Prescriptive fix instructions
    """

    def __init__(
        self,
        link: str,
        expected_schema: str,
        received_schema: str,
        field: str | None = None,
        fix: str | None = None,
    ) -> None:
        field_info = f" (field: {field})" if field else ""
        fix_info = f"\n\nFix: {fix}" if fix else ""

        message = (
            f"Contract violation in link '{link}'{field_info}\n"
            f"Expected: {expected_schema}\n"
            f"Received: {received_schema}"
            f"{fix_info}"
        )

        super().__init__(
            message,
            details={
                "link": link,
                "expected_schema": expected_schema,
                "received_schema": received_schema,
                "field": field,
                "fix": fix,
            }
        )


class MissingDependencyError(WiringError):
    """Raised when a required dependency is not available.

    Attributes:
        dependency: Name of missing dependency
        required_by: Module/component that requires it
        fix: How to resolve the missing dependency
    """

    def __init__(
        self,
        dependency: str,
        required_by: str,
        fix: str | None = None,
    ) -> None:
        fix_info = f"\n\nFix: {fix}" if fix else ""

        message = (
            f"Missing dependency '{dependency}' required by '{required_by}'"
            f"{fix_info}"
        )

        super().__init__(
            message,
            details={
                "dependency": dependency,
                "required_by": required_by,
                "fix": fix,
            }
        )


class ArgumentValidationError(WiringError):
    """Raised when argument routing validation fails.

    Attributes:
        class_name: Class being routed to
        method_name: Method being called
        issue: Description of validation issue
        provided_args: Arguments that were provided
        expected_args: Arguments that were expected
        fix: How to fix the argument mismatch
    """

    def __init__(
        self,
        class_name: str,
        method_name: str,
        issue: str,
        provided_args: list[str] | None = None,
        expected_args: list[str] | None = None,
        fix: str | None = None,
    ) -> None:
        fix_info = f"\n\nFix: {fix}" if fix else ""

        message = (
            f"Argument validation failed for {class_name}.{method_name}\n"
            f"Issue: {issue}"
        )

        if provided_args is not None:
            message += f"\nProvided: {', '.join(provided_args)}"
        if expected_args is not None:
            message += f"\nExpected: {', '.join(expected_args)}"

        message += fix_info

        super().__init__(
            message,
            details={
                "class_name": class_name,
                "method_name": method_name,
                "issue": issue,
                "provided_args": provided_args,
                "expected_args": expected_args,
                "fix": fix,
            }
        )


class SignalUnavailableError(WiringError):
    """Raised when required signals are unavailable.

    Attributes:
        policy_area: Policy area for which signals were requested
        reason: Why signals are unavailable
        breaker_state: Circuit breaker state if applicable
    """

    def __init__(
        self,
        policy_area: str,
        reason: str,
        breaker_state: str | None = None,
    ) -> None:
        breaker_info = f" (breaker: {breaker_state})" if breaker_state else ""

        message = (
            f"Signals unavailable for policy area '{policy_area}'{breaker_info}\n"
            f"Reason: {reason}"
        )

        super().__init__(
            message,
            details={
                "policy_area": policy_area,
                "reason": reason,
                "breaker_state": breaker_state,
            }
        )


class SignalSchemaError(WiringError):
    """Raised when signal pack schema is invalid.

    Attributes:
        pack_version: Signal pack version
        schema_issue: Description of schema problem
        field: Field with schema issue
    """

    def __init__(
        self,
        pack_version: str,
        schema_issue: str,
        field: str | None = None,
    ) -> None:
        field_info = f" (field: {field})" if field else ""

        message = (
            f"Invalid signal pack schema{field_info}\n"
            f"Version: {pack_version}\n"
            f"Issue: {schema_issue}"
        )

        super().__init__(
            message,
            details={
                "pack_version": pack_version,
                "schema_issue": schema_issue,
                "field": field,
            }
        )


class WiringInitializationError(WiringError):
    """Raised when wiring initialization fails.

    Attributes:
        phase: Initialization phase that failed
        component: Component being initialized
        reason: Why initialization failed
    """

    def __init__(
        self,
        phase: str,
        component: str,
        reason: str,
    ) -> None:
        message = (
            f"Wiring initialization failed in phase '{phase}'\n"
            f"Component: {component}\n"
            f"Reason: {reason}"
        )

        super().__init__(
            message,
            details={
                "phase": phase,
                "component": component,
                "reason": reason,
            }
        )


__all__ = [
    'WiringError',
    'WiringContractError',
    'MissingDependencyError',
    'ArgumentValidationError',
    'SignalUnavailableError',
    'SignalSchemaError',
    'WiringInitializationError',
]
