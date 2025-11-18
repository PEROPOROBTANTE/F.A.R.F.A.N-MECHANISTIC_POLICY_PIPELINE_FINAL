"""Feature flags for wiring system configuration.

All flags are typed and have explicit defaults. Flags control conditional
wiring paths and validation strictness.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class WiringFeatureFlags:
    """Feature flags for wiring configuration.

    Attributes:
        use_spc_ingestion: Use SPC (Smart Policy Chunks) ingestion pipeline - canonical phase-one (default: True)
        enable_http_signals: Enable HTTP signal fetching (default: False)
        allow_threshold_override: Allow runtime threshold overrides (default: False)
        wiring_strict_mode: Enforce strict contract validation (default: True)
        enable_observability: Enable OpenTelemetry tracing (default: True)
        enable_metrics: Enable metrics collection (default: True)
        deterministic_mode: Force deterministic execution (default: True)
    """

    use_spc_ingestion: bool = True
    # Legacy alias for backwards compatibility
    use_cpp_ingestion: bool = True
    enable_http_signals: bool = False
    allow_threshold_override: bool = False
    wiring_strict_mode: bool = True
    enable_observability: bool = True
    enable_metrics: bool = True
    deterministic_mode: bool = True

    @classmethod
    def from_env(cls) -> WiringFeatureFlags:
        """Load feature flags from environment variables.

        Environment variables:
        - SAAAAAA_USE_SPC_INGESTION: "true" or "false" (canonical phase-one)
        - SAAAAAA_USE_CPP_INGESTION: "true" or "false" (legacy alias)
        - SAAAAAA_ENABLE_HTTP_SIGNALS: "true" or "false"
        - SAAAAAA_ALLOW_THRESHOLD_OVERRIDE: "true" or "false"
        - SAAAAAA_WIRING_STRICT_MODE: "true" or "false"
        - SAAAAAA_ENABLE_OBSERVABILITY: "true" or "false"
        - SAAAAAA_ENABLE_METRICS: "true" or "false"
        - SAAAAAA_DETERMINISTIC_MODE: "true" or "false"

        Returns:
            WiringFeatureFlags with values from environment
        """
        def get_bool(key: str, default: bool) -> bool:
            value = os.getenv(key, str(default)).lower()
            return value in ("true", "1", "yes", "on")

        # Prefer new SPC name, fallback to legacy CPP name
        spc_flag = get_bool("SAAAAAA_USE_SPC_INGESTION",
                           get_bool("SAAAAAA_USE_CPP_INGESTION", True))

        return cls(
            use_spc_ingestion=spc_flag,
            use_cpp_ingestion=spc_flag,  # Keep in sync for backwards compatibility
            enable_http_signals=get_bool("SAAAAAA_ENABLE_HTTP_SIGNALS", False),
            allow_threshold_override=get_bool("SAAAAAA_ALLOW_THRESHOLD_OVERRIDE", False),
            wiring_strict_mode=get_bool("SAAAAAA_WIRING_STRICT_MODE", True),
            enable_observability=get_bool("SAAAAAA_ENABLE_OBSERVABILITY", True),
            enable_metrics=get_bool("SAAAAAA_ENABLE_METRICS", True),
            deterministic_mode=get_bool("SAAAAAA_DETERMINISTIC_MODE", True),
        )

    def to_dict(self) -> dict[str, bool]:
        """Convert flags to dictionary.

        Returns:
            Dictionary of flag names to values
        """
        return {
            "use_spc_ingestion": self.use_spc_ingestion,
            "use_cpp_ingestion": self.use_cpp_ingestion,  # Legacy compatibility
            "enable_http_signals": self.enable_http_signals,
            "allow_threshold_override": self.allow_threshold_override,
            "wiring_strict_mode": self.wiring_strict_mode,
            "enable_observability": self.enable_observability,
            "enable_metrics": self.enable_metrics,
            "deterministic_mode": self.deterministic_mode,
        }

    def validate(self) -> list[str]:
        """Validate flag combinations for conflicts.

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        if self.enable_http_signals and self.deterministic_mode:
            warnings.append(
                "enable_http_signals=True with deterministic_mode=True may cause "
                "non-determinism due to HTTP variability. Consider using memory:// only."
            )

        if not self.wiring_strict_mode:
            warnings.append(
                "wiring_strict_mode=False disables contract validation. "
                "This is NOT recommended for production."
            )

        if not self.enable_observability and not self.enable_metrics:
            warnings.append(
                "Both observability and metrics are disabled. "
                "Debugging will be difficult without instrumentation."
            )

        return warnings


# Default flags instance for convenience
DEFAULT_FLAGS = WiringFeatureFlags()


__all__ = [
    'WiringFeatureFlags',
    'DEFAULT_FLAGS',
]
