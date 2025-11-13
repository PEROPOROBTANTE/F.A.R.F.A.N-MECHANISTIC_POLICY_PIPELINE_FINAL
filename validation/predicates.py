"""Compatibility shim for validation predicates."""
from pathlib import Path

# Ensure src/ is in path for imports
from saaaaaa.utils.validation.predicates import (  # noqa: F401, E402
    ValidationPredicates,
    ValidationResult,
)

__all__ = [
    "ValidationPredicates",
    "ValidationResult",
]
