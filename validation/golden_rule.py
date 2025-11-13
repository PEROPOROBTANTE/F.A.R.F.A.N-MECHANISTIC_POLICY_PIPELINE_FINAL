"""Compatibility shim for golden rule validator."""
from pathlib import Path

# Ensure src/ is in path for imports
from saaaaaa.utils.validation.golden_rule import (  # noqa: F401, E402
    GoldenRuleValidator,
    GoldenRuleViolation,
)

__all__ = [
    "GoldenRuleValidator",
    "GoldenRuleViolation",
]
