"""
Phase 0 Configuration Validator

This module provides a dedicated validator to enforce the C0-CONFIG-V1.0 contract,
as specified in docs/contracts/C0-CONFIG-V1.0.md. It is executed at the very
beginning of the wiring bootstrap process to ensure the system starts in a
known, valid state.
"""

import os
from pathlib import Path
from typing import Any, Dict, List

class Phase0ValidationError(ValueError):
    """Custom exception for Phase 0 validation errors."""
    def __init__(self, message: str, missing_keys: List[str] | None = None, invalid_paths: Dict[str, str] | None = None):
        super().__init__(message)
        self.missing_keys = missing_keys or []
        self.invalid_paths = invalid_paths or {}

class Phase0Validator:
    """
    Enforces the Phase 0 configuration contract.
    """
    REQUIRED_KEYS = {
        "monolith_path",
        "questionnaire_hash",
        "executor_config_path",
        "calibration_profile",
        "abort_on_insufficient",
        "resource_limits",
    }

    def validate(self, config: Dict[str, Any]) -> None:
        """
        Validates the raw configuration dictionary against the Phase 0 contract.

        Args:
            config: The raw configuration dictionary.

        Raises:
            Phase0ValidationError: If the configuration is invalid.
        """
        self._check_mandatory_keys(config)
        self._check_paths_and_permissions(config)

    def _check_mandatory_keys(self, config: Dict[str, Any]) -> None:
        """Ensures all required configuration keys are present."""
        missing_keys = self.REQUIRED_KEYS - set(config.keys())
        if missing_keys:
            raise Phase0ValidationError(
                "Missing mandatory configuration keys.",
                missing_keys=sorted(list(missing_keys))
            )

    def _check_paths_and_permissions(self, config: Dict[str, Any]) -> None:
        """Validates that file paths exist and have the correct permissions."""
        monolith_path = Path(config["monolith_path"])
        executor_path = Path(config["executor_config_path"])
        invalid_paths = {}

        # Check for existence
        if not monolith_path.exists():
            invalid_paths["monolith_path"] = f"File not found at {monolith_path}"
        if not executor_path.exists():
            invalid_paths["executor_config_path"] = f"File not found at {executor_path}"

        if invalid_paths:
            raise Phase0ValidationError("Invalid file paths in configuration.", invalid_paths=invalid_paths)

        # Check monolith permissions (must be read-only)
        if not os.access(monolith_path, os.R_OK):
            invalid_paths["monolith_path"] = f"File at {monolith_path} is not readable."
            raise Phase0ValidationError(
                "Invalid file permissions in configuration.",
                invalid_paths=invalid_paths
            )
        elif os.access(monolith_path, os.W_OK):
            invalid_paths["monolith_path"] = f"File at {monolith_path} must be read-only."
            raise Phase0ValidationError(
                "Invalid file permissions in configuration.",
                invalid_paths=invalid_paths
            )
