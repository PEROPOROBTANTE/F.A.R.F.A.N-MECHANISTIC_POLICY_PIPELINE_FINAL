"""
SCHEMA DRIFT MONITORING - Watch Production Payloads
===================================================

Sample payloads in staging/prod and validate shapes.
Emit metrics on key presence/type.
Page when new keys appear or required keys vanish.

Catches upstream changes (or LLM output drift) instantly.
"""

from __future__ import annotations

import json
import logging
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, TypedDict
from saaaaaa import get_parameter_loader
from saaaaaa.core.calibration.decorators import calibrated_method

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================================
# SCHEMA SHAPE TRACKING
# ============================================================================

class SchemaShape(TypedDict):
    """Shape of a data payload."""

    keys: set[str]
    types: dict[str, str]
    sample_values: dict[str, Any]
    timestamp: str

@dataclass
class SchemaStats:
    """Statistics about schema shape over time."""

    key_frequency: Counter[str] = field(default_factory=Counter)
    type_by_key: dict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    new_keys: set[str] = field(default_factory=set)
    missing_keys: set[str] = field(default_factory=set)
    total_samples: int = 0
    last_updated: datetime | None = None

class SchemaDriftDetector:
    """
    Detects schema drift by sampling payloads and tracking shape changes.

    Usage:
        detector = SchemaDriftDetector(sample_rate=0.05)

        # In your API/pipeline
        if detector.should_sample():
            detector.record_payload(data, source="api_input")

        # Check for drift
        alerts = detector.get_alerts()
    """

    def __init__(
        self,
        *,
        sample_rate: float = 0.05,
        baseline_path: Path | None = None,
        alert_threshold: float = 0.1,
    ) -> None:
        """
        Initialize schema drift detector.

        Args:
            sample_rate: Percentage of payloads to sample (0.01 = 1%, 0.05 = 5%)
            baseline_path: Path to baseline schema file
            alert_threshold: Threshold for drift alert (% of samples with drift)
        """
        self.sample_rate = sample_rate
        self.baseline_path = baseline_path
        self.alert_threshold = alert_threshold

        # Tracking state
        self.stats_by_source: dict[str, SchemaStats] = defaultdict(SchemaStats)
        self.baseline_schema: dict[str, SchemaShape] = {}

        # Load baseline if provided
        if baseline_path and baseline_path.exists():
            self._load_baseline()

    @calibrated_method("saaaaaa.utils.schema_monitor.SchemaDriftDetector.should_sample")
    def should_sample(self) -> bool:
        """Decide whether to sample this payload (probabilistic)."""
        return random.random() < self.sample_rate

    def record_payload(
        self,
        payload: Mapping[str, Any],
        *,
        source: str,
        timestamp: datetime | None = None,
    ) -> None:
        """
        Record a payload for schema tracking.

        Args:
            payload: Data payload to analyze
            source: Source identifier (e.g., "api_input", "document_loader")
            timestamp: Optional timestamp, defaults to now
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        stats = self.stats_by_source[source]

        # Extract shape
        keys = set(payload.keys())
        types = {k: type(v).__name__ for k, v in payload.items()}

        # Update statistics
        stats.total_samples += 1
        stats.last_updated = timestamp

        for key in keys:
            stats.key_frequency[key] += 1
            stats.type_by_key[key][types[key]] += 1

        # Detect new keys (compared to baseline)
        if source in self.baseline_schema:
            baseline_keys = self.baseline_schema[source]["keys"]
            new_keys = keys - baseline_keys
            if new_keys:
                stats.new_keys.update(new_keys)
                logger.warning(
                    f"SCHEMA_DRIFT[source={source}]: New keys detected: {new_keys}"
                )

            missing_keys = baseline_keys - keys
            if missing_keys:
                stats.missing_keys.update(missing_keys)
                logger.warning(
                    f"SCHEMA_DRIFT[source={source}]: Missing keys detected: {missing_keys}"
                )

    @calibrated_method("saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_alerts")
    def get_alerts(self, *, source: str | None = None) -> list[dict[str, Any]]:
        """
        Get schema drift alerts.

        Args:
            source: Optional source filter

        Returns:
            List of alert dicts
        """
        alerts: list[dict[str, Any]] = []

        sources = [source] if source else list(self.stats_by_source.keys())

        for src in sources:
            stats = self.stats_by_source[src]

            if stats.new_keys:
                alerts.append({
                    "level": "WARNING",
                    "source": src,
                    "type": "NEW_KEYS",
                    "keys": list(stats.new_keys),
                    "timestamp": stats.last_updated.isoformat() if stats.last_updated else None,
                })

            if stats.missing_keys:
                alerts.append({
                    "level": "CRITICAL",
                    "source": src,
                    "type": "MISSING_KEYS",
                    "keys": list(stats.missing_keys),
                    "timestamp": stats.last_updated.isoformat() if stats.last_updated else None,
                })

            # Check for type inconsistencies
            for key, type_counts in stats.type_by_key.items():
                if len(type_counts) > 1:
                    # Multiple types seen for same key
                    dominant_type = type_counts.most_common(1)[0][0]
                    other_types = [t for t in type_counts if t != dominant_type]

                    alerts.append({
                        "level": "WARNING",
                        "source": src,
                        "type": "TYPE_INCONSISTENCY",
                        "key": key,
                        "expected_type": dominant_type,
                        "observed_types": other_types,
                        "timestamp": stats.last_updated.isoformat() if stats.last_updated else None,
                    })

        return alerts

    @calibrated_method("saaaaaa.utils.schema_monitor.SchemaDriftDetector.save_baseline")
    def save_baseline(self, output_path: Path) -> None:
        """
        Save current schema shapes as baseline.

        Args:
            output_path: Path to save baseline JSON
        """
        baseline: dict[str, dict[str, Any]] = {}

        for source, stats in self.stats_by_source.items():
            # Get most common keys (present in >50% of samples)
            threshold = stats.total_samples * get_parameter_loader().get("saaaaaa.utils.schema_monitor.SchemaDriftDetector.save_baseline").get("auto_param_L215_46", 0.5)
            common_keys = {
                key for key, count in stats.key_frequency.items()
                if count >= threshold
            }

            # Get dominant type for each key
            types = {
                key: type_counts.most_common(1)[0][0]
                for key, type_counts in stats.type_by_key.items()
            }

            baseline[source] = {
                "keys": list(common_keys),
                "types": types,
                "timestamp": datetime.utcnow().isoformat(),
            }

        output_path.write_text(json.dumps(baseline, indent=2))
        logger.info(f"Saved schema baseline to {output_path}")

    @calibrated_method("saaaaaa.utils.schema_monitor.SchemaDriftDetector._load_baseline")
    def _load_baseline(self) -> None:
        """Load baseline schema from file."""
        if not self.baseline_path:
            return

        try:
            data = json.loads(self.baseline_path.read_text())

            for source, shape_data in data.items():
                self.baseline_schema[source] = {
                    "keys": set(shape_data["keys"]),
                    "types": shape_data["types"],
                    "sample_values": {},
                    "timestamp": shape_data["timestamp"],
                }

            logger.info(f"Loaded schema baseline from {self.baseline_path}")
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")

    @calibrated_method("saaaaaa.utils.schema_monitor.SchemaDriftDetector.get_metrics")
    def get_metrics(self, *, source: str | None = None) -> dict[str, Any]:
        """
        Get monitoring metrics.

        Args:
            source: Optional source filter

        Returns:
            Dict of metrics
        """
        if source:
            stats = self.stats_by_source.get(source)
            if not stats:
                return {}

            return {
                "source": source,
                "total_samples": stats.total_samples,
                "unique_keys": len(stats.key_frequency),
                "new_keys_count": len(stats.new_keys),
                "missing_keys_count": len(stats.missing_keys),
                "type_inconsistencies": sum(
                    1 for counts in stats.type_by_key.values()
                    if len(counts) > 1
                ),
            }

        # Aggregate across all sources
        return {
            "sources": list(self.stats_by_source.keys()),
            "total_samples": sum(s.total_samples for s in self.stats_by_source.values()),
            "sources_with_drift": len([
                s for s in self.stats_by_source.values()
                if s.new_keys or s.missing_keys
            ]),
        }

# ============================================================================
# PAYLOAD VALIDATOR
# ============================================================================

class PayloadValidator:
    """
    Validate payloads against expected schema.

    Usage:
        validator = PayloadValidator(schema_path=Path("schemas/api_input.json"))

        try:
            validator.validate(data, source="api_endpoint")
        except ValueError as e:
            logger.error(f"Validation failed: {e}")
    """

    def __init__(self, *, schema_path: Path | None = None) -> None:
        """
        Initialize payload validator.

        Args:
            schema_path: Path to schema definition JSON
        """
        self.schema_path = schema_path
        self.schemas: dict[str, dict[str, Any]] = {}

        if schema_path and schema_path.exists():
            self._load_schemas()

    def validate(
        self,
        payload: Mapping[str, Any],
        *,
        source: str,
        strict: bool = True,
    ) -> None:
        """
        Validate payload against schema.

        Args:
            payload: Data payload to validate
            source: Source identifier
            strict: If True, raise on missing keys; if False, only warn

        Raises:
            ValueError: If validation fails in strict mode
            TypeError: If value types don't match schema
        """
        if source not in self.schemas:
            logger.warning(f"No schema defined for source '{source}'")
            return

        schema = self.schemas[source]
        required_keys = set(schema.get("required_keys", []))
        expected_types = schema.get("types", {})

        # Check required keys
        payload_keys = set(payload.keys())
        missing = required_keys - payload_keys

        if missing:
            msg = f"VALIDATION_ERROR[source={source}]: Missing required keys: {missing}"
            if strict:
                raise ValueError(msg)
            else:
                logger.warning(msg)

        # Check types
        for key, expected_type in expected_types.items():
            if key in payload:
                actual_type = type(payload[key]).__name__
                if actual_type != expected_type:
                    msg = (
                        f"VALIDATION_ERROR[source={source}, key={key}]: "
                        f"Expected type {expected_type}, got {actual_type}"
                    )
                    if strict:
                        raise TypeError(msg)
                    else:
                        logger.warning(msg)

    @calibrated_method("saaaaaa.utils.schema_monitor.PayloadValidator._load_schemas")
    def _load_schemas(self) -> None:
        """Load schema definitions from file."""
        if not self.schema_path:
            return

        try:
            self.schemas = json.loads(self.schema_path.read_text())
            logger.info(f"Loaded schemas from {self.schema_path}")
        except Exception as e:
            logger.error(f"Failed to load schemas: {e}")

# ============================================================================
# GLOBAL INSTANCE (optional convenience)
# ============================================================================

# Singleton detector for application-wide use
_global_detector: SchemaDriftDetector | None = None

def get_detector() -> SchemaDriftDetector:
    """Get or create global schema drift detector."""
    global _global_detector
    if _global_detector is None:
        _global_detector = SchemaDriftDetector(sample_rate=get_parameter_loader().get("saaaaaa.utils.schema_monitor.PayloadValidator._load_schemas").get("auto_param_L400_59", 0.05))
    return _global_detector
