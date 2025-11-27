"""
Configuration loaders for penalties and thresholds.

Provides utilities to load all penalty and threshold values from JSON files,
eliminating hardcoded values throughout the calibration system.

ZERO TOLERANCE COMPLIANCE: All values MUST be loaded from JSON.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Repository root (4 levels up from this file)
_REPO_ROOT = Path(__file__).resolve().parents[4]


class PenaltyLoader:
    """
    Singleton loader for all calibration penalty values.

    Loads from config/calibration_penalties.json
    """

    _instance = None
    _penalties: Dict[str, Any] = None

    @classmethod
    def get_instance(cls) -> 'PenaltyLoader':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load penalties from JSON."""
        penalties_file = _REPO_ROOT / "config" / "calibration_penalties.json"

        if not penalties_file.exists():
            raise FileNotFoundError(
                f"Penalties JSON not found: {penalties_file}\n"
                f"This file is REQUIRED for ZERO TOLERANCE compliance."
            )

        with open(penalties_file, 'r') as f:
            self._penalties = json.load(f)

        logger.info("penalty_loader_initialized", extra={"source": str(penalties_file)})

    def get_base_layer_penalty(self, key: str, default: float = 0.1) -> float:
        """
        Get base layer penalty value.

        Args:
            key: Penalty key (e.g., 'uncalibrated_method')
            default: Default value if not found

        Returns:
            Penalty value
        """
        penalties = self._penalties.get("base_layer_penalties", {})
        penalty_data = penalties.get(key, {})

        if isinstance(penalty_data, dict):
            return penalty_data.get("value", default)
        return default

    def get_contextual_layer_penalty(self, key: str, default: float = 0.1) -> float:
        """
        Get contextual layer penalty value.

        Args:
            key: Penalty key (e.g., 'no_compatibility_data_question')
            default: Default value if not found

        Returns:
            Penalty value
        """
        penalties = self._penalties.get("contextual_layer_penalties", {})
        penalty_data = penalties.get(key, {})

        if isinstance(penalty_data, dict):
            return penalty_data.get("value", default)
        return default

    def get_chain_layer_penalty(self, key: str, default: float = 0.0) -> float:
        """Get chain layer penalty value."""
        penalties = self._penalties.get("chain_layer_penalties", {})
        penalty_data = penalties.get(key, {})

        if isinstance(penalty_data, dict):
            return penalty_data.get("value", default)
        return default

    def get_meta_layer_penalty(self, key: str, default: float = 0.0) -> float:
        """Get meta layer penalty value."""
        penalties = self._penalties.get("meta_layer_penalties", {})
        penalty_data = penalties.get(key, {})

        if isinstance(penalty_data, dict):
            return penalty_data.get("value", default)
        return default


class ThresholdLoader:
    """
    Singleton loader for all quality threshold values.

    Loads from config/quality_thresholds.json
    """

    _instance = None
    _thresholds: Dict[str, Any] = None

    @classmethod
    def get_instance(cls) -> 'ThresholdLoader':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """Load thresholds from JSON."""
        thresholds_file = _REPO_ROOT / "config" / "quality_thresholds.json"

        if not thresholds_file.exists():
            raise FileNotFoundError(
                f"Thresholds JSON not found: {thresholds_file}\n"
                f"This file is REQUIRED for ZERO TOLERANCE compliance."
            )

        with open(thresholds_file, 'r') as f:
            self._thresholds = json.load(f)

        logger.info("threshold_loader_initialized", extra={"source": str(thresholds_file)})

    def get_base_layer_quality_thresholds(self) -> Dict[str, float]:
        """
        Get base layer quality thresholds.

        Returns:
            Dict with keys: excellent, good, acceptable, needs_improvement
        """
        base_quality = self._thresholds.get("base_layer_quality", {})

        return {
            "excellent": base_quality.get("excellent", {}).get("value", 0.8),
            "good": base_quality.get("good", {}).get("value", 0.6),
            "acceptable": base_quality.get("acceptable", {}).get("value", 0.4),
            "needs_improvement": base_quality.get("needs_improvement", {}).get("value", 0.0)
        }

    def get_final_calibration_quality_thresholds(self) -> Dict[str, float]:
        """
        Get final calibration quality thresholds.

        Returns:
            Dict with keys: excellent, good, acceptable, insufficient
        """
        final_quality = self._thresholds.get("final_calibration_quality", {})

        return {
            "excellent": final_quality.get("excellent", {}).get("value", 0.85),
            "good": final_quality.get("good", {}).get("value", 0.70),
            "acceptable": final_quality.get("acceptable", {}).get("value", 0.55),
            "insufficient": final_quality.get("insufficient", {}).get("value", 0.0)
        }

    def get_executor_threshold(self, executor_name: str, default: float = 0.70) -> float:
        """
        Get validation threshold for specific executor.

        Args:
            executor_name: Executor name (e.g., "D1Q1_Executor")
            default: Default threshold

        Returns:
            Threshold value
        """
        executor_thresholds = self._thresholds.get("executor_specific_thresholds", {})
        executors = executor_thresholds.get("executors", {})

        executor_data = executors.get(executor_name, {})

        if isinstance(executor_data, dict):
            return executor_data.get("value", default)

        # Try default executor threshold
        default_threshold = executor_thresholds.get("default_executor_threshold", {})
        if isinstance(default_threshold, dict):
            return default_threshold.get("value", default)

        return default
