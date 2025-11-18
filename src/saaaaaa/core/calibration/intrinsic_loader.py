"""
Intrinsic calibration score loader.

This module provides thread-safe, lazy-loaded access to intrinsic calibration scores
from the base layer (@b) JSON file.

Design:
- Singleton-like behavior with lazy initialization
- Thread-safe loading using locks
- Caches all scores in memory for O(1) access
- Filters by calibration_status to distinguish computed vs excluded methods
- Computes intrinsic_score from b_theory, b_impl, b_deploy components
"""
import json
import logging
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class IntrinsicScoreLoader:
    """
    Loads and caches intrinsic calibration scores from JSON.

    The intrinsic score represents the base layer (@b) quality and is computed as:
        intrinsic_score = w_th * b_theory + w_imp * b_impl + w_dep * b_deploy

    Weights are read from the JSON file's "_base_weights" section at load time.
    Default fallback weights (if not in JSON):
        - w_th = 0.4 (theoretical foundation quality)
        - w_imp = 0.35 (implementation quality)
        - w_dep = 0.25 (deployment maturity)

    Thread-safe and lazy-loaded for optimal performance.

    Usage:
        loader = IntrinsicScoreLoader("config/intrinsic_calibration.json")

        # Get score (returns default if not calibrated)
        score = loader.get_score("my_module.MyClass.my_method", default=0.5)

        # Get full method data
        data = loader.get_method_data("my_module.MyClass.my_method")

        # Check calibration status
        if loader.is_calibrated("my_module.MyClass.my_method"):
            print("Method is calibrated!")
    """

    # Default weights (used if not specified in JSON)
    DEFAULT_W_THEORY = 0.4
    DEFAULT_W_IMPL = 0.35
    DEFAULT_W_DEPLOY = 0.25

    def __init__(self, calibration_path: Path | str = "config/intrinsic_calibration.json") -> None:
        """
        Initialize the loader.

        Args:
            calibration_path: Path to intrinsic_calibration.json

        Note: The JSON is NOT loaded at initialization. It will be loaded
        lazily on first access for optimal performance.
        """
        self.calibration_path = Path(calibration_path)
        self._data: dict[str, Any] | None = None
        self._methods: dict[str, dict[str, Any]] | None = None
        self._lock = threading.Lock()
        self._loaded = False

        # Weights (loaded from JSON, fallback to defaults)
        self.w_theory: float = self.DEFAULT_W_THEORY
        self.w_impl: float = self.DEFAULT_W_IMPL
        self.w_deploy: float = self.DEFAULT_W_DEPLOY

        logger.debug(
            "intrinsic_loader_initialized",
            extra={"calibration_path": str(self.calibration_path)}
        )

    def _ensure_loaded(self) -> None:
        """
        Load the JSON file if not already loaded (thread-safe).

        This implements lazy loading with double-checked locking pattern.
        """
        if self._loaded:
            return

        with self._lock:
            # Double-check after acquiring lock
            if self._loaded:
                return

            logger.info(
                "loading_intrinsic_calibration",
                extra={"path": str(self.calibration_path)}
            )

            if not self.calibration_path.exists():
                logger.error(
                    "intrinsic_calibration_not_found",
                    extra={"path": str(self.calibration_path)}
                )
                raise FileNotFoundError(
                    f"Intrinsic calibration file not found: {self.calibration_path}"
                )

            with open(self.calibration_path) as f:
                self._data = json.load(f)

            self._methods = self._data.get("methods", {})

            # Load weights from JSON
            base_weights = self._data.get("_base_weights", {})
            if base_weights:
                self.w_theory = float(base_weights.get("w_th", self.DEFAULT_W_THEORY))
                self.w_impl = float(base_weights.get("w_imp", self.DEFAULT_W_IMPL))
                self.w_deploy = float(base_weights.get("w_dep", self.DEFAULT_W_DEPLOY))

                # Validate weights sum to 1.0
                weight_sum = self.w_theory + self.w_impl + self.w_deploy
                if abs(weight_sum - 1.0) > 1e-6:
                    logger.warning(
                        "intrinsic_weights_not_normalized",
                        extra={
                            "w_theory": self.w_theory,
                            "w_impl": self.w_impl,
                            "w_deploy": self.w_deploy,
                            "sum": weight_sum
                        }
                    )
            else:
                logger.info(
                    "using_default_weights",
                    extra={
                        "w_theory": self.w_theory,
                        "w_impl": self.w_impl,
                        "w_deploy": self.w_deploy
                    }
                )

            # Compute statistics
            stats = self._compute_statistics()

            logger.info(
                "intrinsic_calibration_loaded",
                extra={
                    "path": str(self.calibration_path),
                    "total_methods": stats["total"],
                    "computed": stats["computed"],
                    "excluded": stats["excluded"],
                    "unknown_status": stats["unknown_status"],
                    "version": self._data.get("_metadata", {}).get("version", "unknown"),
                    "weights": {
                        "w_theory": self.w_theory,
                        "w_impl": self.w_impl,
                        "w_deploy": self.w_deploy
                    }
                }
            )

            # Validate a sample of computed methods
            self._validate_computed_methods()

            self._loaded = True

    def _compute_statistics(self) -> dict[str, int]:
        """Compute statistics about the loaded calibration data."""
        stats = {
            "total": len(self._methods),
            "computed": 0,
            "excluded": 0,
            "unknown_status": 0
        }

        for method_data in self._methods.values():
            status = method_data.get("calibration_status", "unknown")
            if status == "computed":
                stats["computed"] += 1
            elif status == "excluded":
                stats["excluded"] += 1
            else:
                stats["unknown_status"] += 1

        return stats

    def _validate_computed_methods(self) -> None:
        """
        Validate that computed methods have all required fields.

        Logs warnings for any inconsistencies found.
        """
        required_fields = ["b_theory", "b_impl", "b_deploy"]
        warning_count = 0

        for method_id, method_data in self._methods.items():
            if method_data.get("calibration_status") == "computed":
                missing = [f for f in required_fields if f not in method_data]
                if missing:
                    warning_count += 1
                    if warning_count <= 10:  # Limit warnings to avoid spam
                        logger.warning(
                            "computed_method_missing_fields",
                            extra={
                                "method_id": method_id,
                                "missing_fields": missing
                            }
                        )

        if warning_count > 10:
            logger.warning(
                "multiple_validation_warnings",
                extra={"total_warnings": warning_count}
            )

    def _compute_intrinsic_score(self, method_data: dict[str, Any]) -> float:
        """
        Compute intrinsic score from b_theory, b_impl, b_deploy.

        Args:
            method_data: Dictionary containing b_theory, b_impl, b_deploy

        Returns:
            Intrinsic score in [0.0, 1.0]
        """
        try:
            b_theory = float(method_data.get("b_theory", 0.0))
            b_impl = float(method_data.get("b_impl", 0.0))
            b_deploy = float(method_data.get("b_deploy", 0.0))

            # Weighted average using JSON-loaded weights
            intrinsic_score = (
                self.w_theory * b_theory +
                self.w_impl * b_impl +
                self.w_deploy * b_deploy
            )

            # Clamp to [0.0, 1.0]
            return max(0.0, min(1.0, intrinsic_score))

        except (ValueError, TypeError) as e:
            logger.warning(
                "intrinsic_score_computation_failed",
                extra={
                    "method_id": method_data.get("method_id", "unknown"),
                    "error": str(e)
                }
            )
            return 0.0

    def get_score(self, method_id: str, default: float = 0.5) -> float:
        """
        Get intrinsic calibration score for a method.

        Args:
            method_id: Full method identifier (e.g., "module.Class.method")
            default: Default score to return if method not calibrated

        Returns:
            Intrinsic score in [0.0, 1.0], or default if not calibrated

        Examples:
            >>> loader.get_score("my_module.MyClass.analyze", default=0.5)
            0.73

            >>> loader.get_score("unknown.method", default=0.4)
            0.4
        """
        self._ensure_loaded()

        if method_id not in self._methods:
            logger.debug(
                "method_not_in_calibration",
                extra={"method_id": method_id, "returning": default}
            )
            return default

        method_data = self._methods[method_id]
        status = method_data.get("calibration_status", "unknown")

        if status == "computed":
            score = self._compute_intrinsic_score(method_data)
            logger.debug(
                "intrinsic_score_retrieved",
                extra={
                    "method_id": method_id,
                    "score": score,
                    "b_theory": method_data.get("b_theory"),
                    "b_impl": method_data.get("b_impl"),
                    "b_deploy": method_data.get("b_deploy")
                }
            )
            return score

        elif status == "excluded":
            logger.debug(
                "method_excluded_from_calibration",
                extra={"method_id": method_id, "returning": default}
            )
            return default

        else:
            logger.warning(
                "unknown_calibration_status",
                extra={
                    "method_id": method_id,
                    "status": status,
                    "returning": default
                }
            )
            return default

    def get_method_data(self, method_id: str) -> dict[str, Any] | None:
        """
        Get full calibration data for a method.

        Args:
            method_id: Full method identifier

        Returns:
            Dictionary with all calibration data, or None if not found

        Example:
            >>> data = loader.get_method_data("my_module.MyClass.analyze")
            >>> print(data["b_theory"], data["b_impl"], data["b_deploy"])
            0.8 0.75 0.7
        """
        self._ensure_loaded()
        return self._methods.get(method_id)

    def is_calibrated(self, method_id: str) -> bool:
        """
        Check if a method has a computed calibration score.

        Args:
            method_id: Full method identifier

        Returns:
            True if method has calibration_status == "computed"
        """
        self._ensure_loaded()

        if method_id not in self._methods:
            return False

        return self._methods[method_id].get("calibration_status") == "computed"

    def is_excluded(self, method_id: str) -> bool:
        """
        Check if a method was explicitly excluded from saaaaaa.core.calibration.

        Args:
            method_id: Full method identifier

        Returns:
            True if method has calibration_status == "excluded"
        """
        self._ensure_loaded()

        if method_id not in self._methods:
            return False

        return self._methods[method_id].get("calibration_status") == "excluded"

    def get_layer(self, method_id: str) -> str | None:
        """
        Get the layer/role designation for a method.

        Args:
            method_id: Full method identifier

        Returns:
            Layer name (e.g., "analyzer", "processor"), or None if not found
        """
        self._ensure_loaded()

        if method_id not in self._methods:
            return None

        return self._methods[method_id].get("layer")

    def get_statistics(self) -> dict[str, int]:
        """
        Get statistics about the loaded calibration data.

        Returns:
            Dictionary with counts:
                - total: Total number of methods
                - computed: Methods with computed scores
                - excluded: Methods explicitly excluded
                - unknown_status: Methods with unknown status

        Example:
            >>> stats = loader.get_statistics()
            >>> print(f"Calibrated: {stats['computed']} / {stats['total']}")
            Calibrated: 1470 / 1995
        """
        self._ensure_loaded()
        return self._compute_statistics()
