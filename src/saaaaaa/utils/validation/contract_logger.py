#!/usr/bin/env python3
"""
Contract Error Logger - Structured logging for contract validation errors.

Provides a unified interface for logging contract violations in a machine-readable
format conforming to schemas/contract_error_log.schema.json.

Usage:
    from saaaaaa.utils.validation.contract_logger import ContractErrorLogger

    logger = ContractErrorLogger(module_name="scoring")
    logger.log_contract_mismatch(
        function="apply_scoring",
        key="confidence",
        needed="float",
        got=evidence.get("confidence"),
        file=__file__,
        line=234,
        remediation="Convert confidence to float between 0.0 and 1.0"
    )
"""

import json
import sys
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

class ContractErrorLogger:
    """Structured logger for contract validation errors."""

    # Standard error codes
    ERR_CONTRACT_MISMATCH = "ERR_CONTRACT_MISMATCH"
    ERR_TYPE_VIOLATION = "ERR_TYPE_VIOLATION"
    ERR_SCHEMA_VALIDATION = "ERR_SCHEMA_VALIDATION"
    ERR_MISSING_REQUIRED_FIELD = "ERR_MISSING_REQUIRED_FIELD"
    ERR_INVALID_MODALITY = "ERR_INVALID_MODALITY"
    ERR_DETERMINISM_VIOLATION = "ERR_DETERMINISM_VIOLATION"

    # Severity levels
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"

    def __init__(self, module_name: str, enable_stdout: bool = True) -> None:
        """
        Initialize contract error logger.

        Args:
            module_name: Name of the module using this logger
            enable_stdout: Whether to output to stdout (default: True)
        """
        self.module_name = module_name
        self.enable_stdout = enable_stdout
        self.request_id = str(uuid.uuid4())

    def _log(
        self,
        error_code: str,
        function: str,
        message: str,
        severity: str,
        context: dict,
        remediation: str | None = None,
        stack_trace: list[str] | None = None
    ) -> None:
        """
        Internal method to log structured error.

        Args:
            error_code: Standard error code
            function: Function name where error occurred
            message: Human-readable error message
            severity: Error severity level
            context: Structured context dictionary
            remediation: Optional remediation steps
            stack_trace: Optional stack trace
        """
        log_entry = {
            "error_code": error_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": severity,
            "function": f"{self.module_name}.{function}",
            "message": message,
            "context": context,
            "request_id": self.request_id
        }

        if remediation:
            log_entry["remediation"] = remediation

        if stack_trace:
            log_entry["stack_trace"] = stack_trace

        # Output as single-line JSON
        log_line = json.dumps(log_entry, separators=(',', ':'))

        if self.enable_stdout:
            print(log_line, file=sys.stderr)

    def log_contract_mismatch(
        self,
        function: str,
        key: str,
        needed: Any,
        got: Any,
        index: int | None = None,
        file: str | None = None,
        line: int | None = None,
        remediation: str | None = None
    ) -> None:
        """
        Log a contract mismatch error (ERR_CONTRACT_MISMATCH).

        Args:
            function: Function name where error occurred
            key: Parameter/field name that failed
            needed: Expected type/value
            got: Actual value received
            index: Optional index in collection
            file: Optional source file
            line: Optional line number
            remediation: Optional remediation steps
        """
        context = {
            "key": key,
            "needed": needed,
            "got": got
        }

        if index is not None:
            context["index"] = index
        if file:
            context["file"] = file
        if line:
            context["line"] = line

        message = f"Contract violation: required parameter '{key}' is missing or invalid"
        if got is None:
            message = f"Contract violation: required parameter '{key}' is missing"

        self._log(
            error_code=self.ERR_CONTRACT_MISMATCH,
            function=function,
            message=message,
            severity=self.ERROR,
            context=context,
            remediation=remediation
        )

    def log_type_violation(
        self,
        function: str,
        key: str,
        expected_type: str,
        got: Any,
        file: str | None = None,
        line: int | None = None,
        remediation: str | None = None
    ) -> None:
        """
        Log a type violation error (ERR_TYPE_VIOLATION).

        Args:
            function: Function name where error occurred
            key: Parameter/field name with wrong type
            expected_type: Expected type name
            got: Actual value received
            file: Optional source file
            line: Optional line number
            remediation: Optional remediation steps
        """
        actual_type = type(got).__name__

        context = {
            "key": key,
            "needed": expected_type,
            "got": str(got) if got is not None else None
        }

        if file:
            context["file"] = file
        if line:
            context["line"] = line

        message = f"Type violation: expected {expected_type} for '{key}', got {actual_type}"

        self._log(
            error_code=self.ERR_TYPE_VIOLATION,
            function=function,
            message=message,
            severity=self.ERROR,
            context=context,
            remediation=remediation
        )

    def log_invalid_modality(
        self,
        function: str,
        modality: str,
        allowed_modalities: list[str],
        file: str | None = None,
        line: int | None = None
    ) -> None:
        """
        Log an invalid modality error (ERR_INVALID_MODALITY).

        Args:
            function: Function name where error occurred
            modality: Invalid modality value
            allowed_modalities: List of allowed modalities
            file: Optional source file
            line: Optional line number
        """
        context = {
            "key": "modality",
            "needed": "|".join(allowed_modalities),
            "got": modality
        }

        if file:
            context["file"] = file
        if line:
            context["line"] = line

        message = f"Invalid modality: {modality} is not in allowed modalities"
        remediation = f"Use one of the allowed modality types: {', '.join(allowed_modalities)}"

        self._log(
            error_code=self.ERR_INVALID_MODALITY,
            function=function,
            message=message,
            severity=self.ERROR,
            context=context,
            remediation=remediation
        )

    def log_determinism_violation(
        self,
        function: str,
        description: str,
        expected_hash: str,
        actual_hash: str,
        file: str | None = None,
        line: int | None = None
    ) -> None:
        """
        Log a determinism violation (ERR_DETERMINISM_VIOLATION).

        Args:
            function: Function name where error occurred
            description: Description of what failed determinism check
            expected_hash: Expected hash value
            actual_hash: Actual hash value
            file: Optional source file
            line: Optional line number
        """
        context = {
            "key": "determinism_check",
            "needed": expected_hash,
            "got": actual_hash
        }

        if file:
            context["file"] = file
        if line:
            context["line"] = line

        message = f"Determinism violation: {description}"
        remediation = "Check for non-deterministic operations (random, time, concurrency)"

        # Include stack trace for determinism violations
        stack_trace = traceback.format_stack()

        self._log(
            error_code=self.ERR_DETERMINISM_VIOLATION,
            function=function,
            message=message,
            severity=self.CRITICAL,
            context=context,
            remediation=remediation,
            stack_trace=stack_trace
        )

# Example usage
# Note: Example usage removed to maintain I/O boundary separation.
# For usage examples, see examples/ directory.
