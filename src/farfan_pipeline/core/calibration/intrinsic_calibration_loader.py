"""
intrinsic_calibration_loader.py - Single source loader for @b-layer intrinsic calibration

This module provides the ONLY interface for loading intrinsic calibration data.
Enforces strict @b-only access with fallback behavior:
- pending → @b = 0.5 (neutral baseline)
- excluded → @b = None (causes method skip)
- none → @b = 0.3 (low confidence with warning)
- computed → actual @b values from JSON

CRITICAL: This is the single source of truth for intrinsic calibration.
"""
import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IntrinsicCalibration:
    """Intrinsic calibration data for a single method."""
    method_id: str
    intrinsic_score: tuple[float, float]
    b_theory: float
    b_impl: float
    b_deploy: float
    calibration_status: str
    layer: str
    last_updated: str

    def get_composite_b(self) -> float:
        """Calculate composite @b score from theory, impl, deploy."""
        return (self.b_theory + self.b_impl + self.b_deploy) / 3.0


class IntrinsicCalibrationLoader:
    """
    Single source loader for intrinsic calibration with fallback behavior.

    Fallback rules:
    - computed: Use actual values from JSON
    - pending: b_theory=0.5, b_impl=0.5, b_deploy=0.5 (neutral baseline)
    - excluded: Return None (signals method should be skipped)
    - none: b_theory=0.3, b_impl=0.3, b_deploy=0.3 (low confidence + warning)
    """

    def __init__(self, config_path: str = "config/intrinsic_calibration.json") -> None:
        self.config_path = Path(config_path)
        self._data: dict = {}
        self._load()

    def _load(self) -> None:
        """Load calibration data from JSON."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Intrinsic calibration file not found: {self.config_path}. "
                "Intrinsic calibration incomplete or contaminated."
            )

        with open(self.config_path) as f:
            self._data = json.load(f)

        metadata = self._data.get("_metadata", {})
        coverage = metadata.get("coverage_percent", 0)

        if coverage < 25.0:
            raise ValueError(
                f"Intrinsic calibration coverage {coverage}% < 25%. "
                "Intrinsic calibration incomplete or contaminated."
            )

        logger.info(
            f"Loaded intrinsic calibration: {metadata.get('computed_methods')} methods, "
            f"{coverage}% coverage"
        )

    def get_calibration(self, method_id: str) -> IntrinsicCalibration | None:
        """
        Get intrinsic calibration for a method with fallback behavior.

        Args:
            method_id: Method identifier (e.g., "ClassName.method_name")

        Returns:
            IntrinsicCalibration object or None if method is excluded

        Raises:
            ValueError: If calibration data is contaminated
        """
        if method_id not in self._data:
            logger.warning(
                f"Method '{method_id}' not in calibration registry. "
                f"Applying fallback: status='none', @b=0.3"
            )
            return IntrinsicCalibration(
                method_id=method_id,
                intrinsic_score=(0.28, 0.32),
                b_theory=0.3,
                b_impl=0.3,
                b_deploy=0.3,
                calibration_status="none",
                layer="utility",
                last_updated="unknown"
            )

        method_data = self._data[method_id]

        # Verify no contamination
        allowed_keys = {"intrinsic_score", "b_theory", "b_impl", "b_deploy",
                       "calibration_status", "layer", "last_updated"}
        extra_keys = set(method_data.keys()) - allowed_keys
        if extra_keys:
            raise ValueError(
                f"CONTAMINATION DETECTED in method '{method_id}': {extra_keys}. "
                "Intrinsic calibration incomplete or contaminated."
            )

        status = method_data["calibration_status"]

        # Handle fallback cases
        if status == "excluded":
            logger.info(f"Method '{method_id}' is excluded, returning None (skip method)")
            return None

        if status == "pending":
            logger.info(f"Method '{method_id}' is pending, applying fallback @b=0.5")
            return IntrinsicCalibration(
                method_id=method_id,
                intrinsic_score=(0.48, 0.52),
                b_theory=0.5,
                b_impl=0.5,
                b_deploy=0.5,
                calibration_status=status,
                layer=method_data["layer"],
                last_updated=method_data["last_updated"]
            )

        if status == "none":
            logger.warning(
                f"Method '{method_id}' has status='none', applying fallback @b=0.3"
            )
            return IntrinsicCalibration(
                method_id=method_id,
                intrinsic_score=(0.28, 0.32),
                b_theory=0.3,
                b_impl=0.3,
                b_deploy=0.3,
                calibration_status=status,
                layer=method_data["layer"],
                last_updated=method_data["last_updated"]
            )

        # status == "computed": return actual values
        return IntrinsicCalibration(
            method_id=method_id,
            intrinsic_score=tuple(method_data["intrinsic_score"]),
            b_theory=method_data["b_theory"],
            b_impl=method_data["b_impl"],
            b_deploy=method_data["b_deploy"],
            calibration_status=status,
            layer=method_data["layer"],
            last_updated=method_data["last_updated"]
        )

    def get_metadata(self) -> dict:
        """Get calibration metadata."""
        return self._data.get("_metadata", {})

    def verify_purity(self) -> bool:
        """
        Verify no contamination from other calibration layers.

        Returns:
            True if pure @b-only data

        Raises:
            ValueError: If contamination detected
        """
        forbidden_patterns = ["@chain", "@q", "@d", "@p", "@C", "@u", "@m",
                             "final_score", "layer_scores", "chain_", "queue_"]

        for method_id, method_data in self._data.items():
            if method_id == "_metadata":
                continue

            for key in method_data:
                for pattern in forbidden_patterns:
                    if pattern in key.lower():
                        raise ValueError(
                            f"CONTAMINATION DETECTED: method '{method_id}' contains "
                            f"forbidden key '{key}' matching pattern '{pattern}'. "
                            "Intrinsic calibration incomplete or contaminated."
                        )

        return True


# Singleton instance
_loader: IntrinsicCalibrationLoader | None = None


def get_intrinsic_calibration_loader(
    config_path: str = "config/intrinsic_calibration.json"
) -> IntrinsicCalibrationLoader:
    """Get singleton instance of intrinsic calibration loader."""
    global _loader
    if _loader is None:
        _loader = IntrinsicCalibrationLoader(config_path)
        _loader.verify_purity()
    return _loader


def get_method_calibration(method_id: str) -> IntrinsicCalibration | None:
    """
    Convenience function to get calibration for a method.

    Args:
        method_id: Method identifier (e.g., "ClassName.method_name")

    Returns:
        IntrinsicCalibration object or None if excluded
    """
    loader = get_intrinsic_calibration_loader()
    return loader.get_calibration(method_id)
