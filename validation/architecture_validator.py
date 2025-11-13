"""Compatibility wrapper for architecture validator."""
from pathlib import Path

# Ensure src/ is in path for imports
from saaaaaa.utils.validation.architecture_validator import (  # noqa: F401, E402
    ArchitectureValidationResult,
    extract_architecture_methods,
    load_architecture_spec,
    load_method_inventory,
    main,
    validate_architecture,
    write_validation_report,
)

__all__ = [
    "ArchitectureValidationResult",
    "extract_architecture_methods",
    "load_architecture_spec",
    "load_method_inventory",
    "main",
    "validate_architecture",
    "write_validation_report",
]
