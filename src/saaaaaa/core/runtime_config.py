"""
Global runtime configuration system for F.A.R.F.A.N.

This module provides runtime mode enforcement (PROD/DEV/EXPLORATORY) with strict
fallback policies, configuration validation, and environment variable parsing.

Environment Variables:
    SAAAAAA_RUNTIME_MODE: Runtime mode (prod/dev/exploratory), default: prod
    ALLOW_CONTRADICTION_FALLBACK: Allow contradiction detection fallback, default: false
    ALLOW_EXECUTION_ESTIMATES: Allow execution metric estimation, default: false
    ALLOW_DEV_INGESTION_FALLBACKS: Allow dev ingestion fallbacks, default: false
    ALLOW_AGGREGATION_DEFAULTS: Allow aggregation defaults, default: false
    STRICT_CALIBRATION: Require complete calibration files, default: true
    ALLOW_VALIDATOR_DISABLE: Allow validator disabling, default: false
    ALLOW_HASH_FALLBACK: Allow hash algorithm fallback, default: true
    PREFERRED_SPACY_MODEL: Preferred spaCy model, default: es_core_news_lg

Example:
    >>> config = RuntimeConfig.from_env()
    >>> if config.mode == RuntimeMode.PROD:
    ...     assert not config.allow_dev_ingestion_fallbacks
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Final, ClassVar, Dict


class RuntimeMode(Enum):
    """Runtime execution mode with different strictness levels."""
    
    PROD = "prod"
    """Production mode: strict enforcement, no fallbacks unless explicitly allowed."""
    
    DEV = "dev"
    """Development mode: permissive with flags, allows controlled degradation."""
    
    EXPLORATORY = "exploratory"
    """Exploratory mode: maximum flexibility for research and experimentation."""


class ConfigurationError(Exception):
    """Raised when runtime configuration is invalid or contains illegal combinations."""
    
    def __init__(self, message: str, illegal_combo: str | None = None):
        self.illegal_combo = illegal_combo
        super().__init__(message)


@dataclass(frozen=True)
class RuntimeConfig:
    """
    Immutable runtime configuration parsed from environment variables.
    
    This configuration controls system behavior across all components, enforcing
    strict policies in PROD mode and allowing controlled degradation in DEV/EXPLORATORY.
    
    Attributes:
        mode: Runtime execution mode
        allow_contradiction_fallback: Allow fallback when contradiction module unavailable
        allow_execution_estimates: Allow execution metric estimation
        allow_dev_ingestion_fallbacks: Allow development ingestion fallbacks
        allow_aggregation_defaults: Allow aggregation default values
        strict_calibration: Require complete calibration files with _base_weights
        allow_validator_disable: Allow disabling wiring validator
        allow_hash_fallback: Allow hash algorithm fallback
        preferred_spacy_model: Preferred spaCy model name
    """
    
    mode: RuntimeMode
    allow_contradiction_fallback: bool
    allow_execution_estimates: bool
    allow_dev_ingestion_fallbacks: bool
    allow_aggregation_defaults: bool
    strict_calibration: bool
    allow_validator_disable: bool
    allow_hash_fallback: bool
    preferred_spacy_model: str
    
    # Illegal combinations in PROD mode
    _PROD_ILLEGAL_COMBOS: ClassVar[Dict[str, str]] = {
        "ALLOW_DEV_INGESTION_FALLBACKS": "Development ingestion fallbacks not allowed in PROD",
        "ALLOW_EXECUTION_ESTIMATES": "Execution metric estimation not allowed in PROD",
        "ALLOW_AGGREGATION_DEFAULTS": "Aggregation defaults not allowed in PROD",
    }
    
    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        """
        Parse runtime configuration from environment variables.
        
        Returns:
            RuntimeConfig: Validated configuration instance
            
        Raises:
            ConfigurationError: If configuration is invalid or contains illegal combinations
            
        Example:
            >>> os.environ['SAAAAAA_RUNTIME_MODE'] = 'prod'
            >>> config = RuntimeConfig.from_env()
            >>> assert config.mode == RuntimeMode.PROD
        """
        # Parse runtime mode
        mode_str = os.getenv("SAAAAAA_RUNTIME_MODE", "prod").lower()
        try:
            mode = RuntimeMode(mode_str)
        except ValueError:
            raise ConfigurationError(
                f"Invalid SAAAAAA_RUNTIME_MODE: {mode_str}. "
                f"Must be one of: {', '.join(m.value for m in RuntimeMode)}"
            )
        
        # Parse boolean flags with defaults
        allow_contradiction_fallback = _parse_bool_env("ALLOW_CONTRADICTION_FALLBACK", False)
        allow_execution_estimates = _parse_bool_env("ALLOW_EXECUTION_ESTIMATES", False)
        allow_dev_ingestion_fallbacks = _parse_bool_env("ALLOW_DEV_INGESTION_FALLBACKS", False)
        allow_aggregation_defaults = _parse_bool_env("ALLOW_AGGREGATION_DEFAULTS", False)
        strict_calibration = _parse_bool_env("STRICT_CALIBRATION", True)
        allow_validator_disable = _parse_bool_env("ALLOW_VALIDATOR_DISABLE", False)
        allow_hash_fallback = _parse_bool_env("ALLOW_HASH_FALLBACK", True)
        
        # Parse string config
        preferred_spacy_model = os.getenv("PREFERRED_SPACY_MODEL", "es_core_news_lg")
        
        # Create config instance
        config = cls(
            mode=mode,
            allow_contradiction_fallback=allow_contradiction_fallback,
            allow_execution_estimates=allow_execution_estimates,
            allow_dev_ingestion_fallbacks=allow_dev_ingestion_fallbacks,
            allow_aggregation_defaults=allow_aggregation_defaults,
            strict_calibration=strict_calibration,
            allow_validator_disable=allow_validator_disable,
            allow_hash_fallback=allow_hash_fallback,
            preferred_spacy_model=preferred_spacy_model,
        )
        
        # Validate configuration
        config._validate()
        
        return config
    
    def _validate(self) -> None:
        """
        Validate configuration for illegal combinations.
        
        In PROD mode, certain ALLOW_* flags are prohibited to ensure strict behavior.
        
        Raises:
            ConfigurationError: If illegal combination detected
        """
        if self.mode != RuntimeMode.PROD:
            return  # DEV/EXPLORATORY modes allow all combinations
        
        # Check for illegal PROD combinations
        violations = []
        
        if self.allow_dev_ingestion_fallbacks:
            violations.append(
                f"PROD + ALLOW_DEV_INGESTION_FALLBACKS=true: {self._PROD_ILLEGAL_COMBOS['ALLOW_DEV_INGESTION_FALLBACKS']}"
            )
        
        if self.allow_execution_estimates:
            violations.append(
                f"PROD + ALLOW_EXECUTION_ESTIMATES=true: {self._PROD_ILLEGAL_COMBOS['ALLOW_EXECUTION_ESTIMATES']}"
            )
        
        if self.allow_aggregation_defaults:
            violations.append(
                f"PROD + ALLOW_AGGREGATION_DEFAULTS=true: {self._PROD_ILLEGAL_COMBOS['ALLOW_AGGREGATION_DEFAULTS']}"
            )
        
        if violations:
            raise ConfigurationError(
                "Illegal configuration combinations detected:\n" + "\n".join(f"  - {v}" for v in violations),
                illegal_combo="; ".join(violations)
            )
    
    def is_strict_mode(self) -> bool:
        """Check if running in strict mode (PROD with no fallbacks allowed)."""
        return (
            self.mode == RuntimeMode.PROD
            and not self.allow_contradiction_fallback
            and not self.allow_validator_disable
        )
    
    def __repr__(self) -> str:
        """String representation showing mode and key flags."""
        flags = []
        if self.allow_contradiction_fallback:
            flags.append("contradiction_fallback")
        if self.allow_execution_estimates:
            flags.append("execution_estimates")
        if self.allow_dev_ingestion_fallbacks:
            flags.append("dev_ingestion_fallbacks")
        if self.allow_aggregation_defaults:
            flags.append("aggregation_defaults")
        if not self.strict_calibration:
            flags.append("relaxed_calibration")
        
        flags_str = f", flags={flags}" if flags else ""
        return f"RuntimeConfig(mode={self.mode.value}{flags_str})"


def _parse_bool_env(var_name: str, default: bool) -> bool:
    """
    Parse boolean environment variable with case-insensitive handling.
    
    Args:
        var_name: Environment variable name
        default: Default value if not set
        
    Returns:
        Parsed boolean value
        
    Raises:
        ConfigurationError: If value is not a valid boolean
    """
    value = os.getenv(var_name)
    if value is None:
        return default
    
    value_lower = value.lower()
    if value_lower in ("true", "1", "yes", "on"):
        return True
    elif value_lower in ("false", "0", "no", "off"):
        return False
    else:
        raise ConfigurationError(
            f"Invalid boolean value for {var_name}: {value}. "
            f"Must be one of: true/false, 1/0, yes/no, on/off"
        )


# Global singleton instance (lazy-initialized)
_global_config: RuntimeConfig | None = None


def get_runtime_config() -> RuntimeConfig:
    """
    Get global runtime configuration instance (lazy-initialized).
    
    Returns:
        RuntimeConfig: Global configuration instance
        
    Note:
        This is initialized once on first call. For testing, use from_env() directly.
    """
    global _global_config
    if _global_config is None:
        _global_config = RuntimeConfig.from_env()
    return _global_config


def reset_runtime_config() -> None:
    """
    Reset global runtime configuration (for testing only).
    
    Warning:
        This should only be used in tests. Production code should never reset config.
    """
    global _global_config
    _global_config = None
