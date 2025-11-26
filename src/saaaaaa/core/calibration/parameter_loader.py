"""
Method parameters loader.

This module provides thread-safe, lazy-loaded access to method-specific parameters
including thresholds, priors, and configuration values from method_parameters.json.

Design:
- SINGLETON PATTERN enforced (only ONE instance system-wide)
- Thread-safe loading using locks
- Caches all parameters in memory for O(1) access
- Provides typed access to common parameter types (thresholds, quality levels, etc.)
"""
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class MethodParameterLoader:
    """
    Loads and caches method parameters from JSON.

    **SINGLETON PATTERN**: Only ONE instance allowed system-wide.
    Use MethodParameterLoader.get_instance() to access the singleton.

    Thread-safe and lazy-loaded for optimal performance.

    Usage:
        # CORRECT: Use singleton instance
        loader = MethodParameterLoader.get_instance("config/method_parameters.json")

        # INCORRECT: Direct instantiation raises error
        # loader = MethodParameterLoader()  # Raises RuntimeError!

        # Get executor threshold
        threshold = loader.get_executor_threshold("D1Q1_Executor")

        # Get quality level thresholds
        quality = loader.get_quality_thresholds()

        # Get method-specific parameter
        param = loader.get_method_parameter(
            "semantic_chunking_policy.SemanticChunker.chunk",
            "similarity_threshold"
        )

        # Get validation threshold by role
        threshold = loader.get_validation_threshold_for_role("analyzer")
    """

    # Singleton instance storage
    _instance: Optional['MethodParameterLoader'] = None
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """
        Prevent direct instantiation.

        Use MethodParameterLoader.get_instance() instead.
        """
        raise RuntimeError(
            "MethodParameterLoader is a singleton. "
            "Use MethodParameterLoader.get_instance() instead of direct instantiation."
        )

    @classmethod
    def get_instance(
        cls,
        parameters_path: Path | str = "config/method_parameters.json"
    ) -> 'MethodParameterLoader':
        """
        Get the singleton instance of MethodParameterLoader.

        Thread-safe singleton access with double-checked locking.

        Args:
            parameters_path: Path to method_parameters.json
                           (only used on first call, ignored afterwards)

        Returns:
            The singleton MethodParameterLoader instance

        Example:
            >>> loader = MethodParameterLoader.get_instance()
            >>> threshold = loader.get_executor_threshold("D1Q1_Executor")
        """
        if cls._instance is not None:
            return cls._instance

        with cls._instance_lock:
            # Double-check after acquiring lock
            if cls._instance is not None:
                return cls._instance

            # Create instance bypassing __new__ check
            instance = object.__new__(cls)
            instance._init_singleton(parameters_path)
            cls._instance = instance

            logger.info(
                "parameter_loader_singleton_created",
                extra={"parameters_path": str(instance.parameters_path)}
            )

            return cls._instance

    def _init_singleton(self, parameters_path: Path | str) -> None:
        """
        Initialize the singleton instance.

        Args:
            parameters_path: Path to method_parameters.json

        Note: The JSON is NOT loaded at initialization. It will be loaded
        lazily on first access for optimal performance.
        """
        self.parameters_path = Path(parameters_path)
        self._data: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._loaded = False

        logger.debug(
            "parameter_loader_initialized",
            extra={"parameters_path": str(self.parameters_path)}
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
                "loading_method_parameters",
                extra={"path": str(self.parameters_path)}
            )

            if not self.parameters_path.exists():
                logger.error(
                    "method_parameters_not_found",
                    extra={"path": str(self.parameters_path)}
                )
                raise FileNotFoundError(
                    f"Method parameters file not found: {self.parameters_path}"
                )

            with open(self.parameters_path, 'r') as f:
                self._data = json.load(f)

            # Validate structure
            if "_metadata" not in self._data:
                logger.warning(
                    "method_parameters_missing_metadata",
                    extra={"path": str(self.parameters_path)}
                )

            # Log statistics
            method_count = len(self._data.get("methods", {}))
            executor_count = len(
                self._data.get("_executor_thresholds", {}).get("executors", {})
            )

            logger.info(
                "method_parameters_loaded",
                extra={
                    "path": str(self.parameters_path),
                    "methods": method_count,
                    "executors": executor_count,
                    "version": self._data.get("_metadata", {}).get("version", "unknown")
                }
            )

            self._loaded = True

    def get_quality_thresholds(self) -> Dict[str, float]:
        """
        Get global quality level thresholds.

        Returns:
            Dictionary with keys: excellent, good, acceptable, insufficient
            Each value is a float threshold in [0.0, 1.0]

        Example:
            >>> loader.get_quality_thresholds()
            {'excellent': 0.85, 'good': 0.70, 'acceptable': 0.55, 'insufficient': 0.0}
        """
        self._ensure_loaded()

        quality_levels = self._data.get("_global_thresholds", {}).get("quality_levels", {})

        if not quality_levels:
            logger.warning(
                "quality_thresholds_not_found_using_defaults",
                extra={"using_defaults": True}
            )
            return {
                "excellent": 0.85,
                "good": 0.70,
                "acceptable": 0.55,
                "insufficient": 0.0
            }

        return {
            "excellent": float(quality_levels.get("excellent", 0.85)),
            "good": float(quality_levels.get("good", 0.70)),
            "acceptable": float(quality_levels.get("acceptable", 0.55)),
            "insufficient": float(quality_levels.get("insufficient", 0.0))
        }

    def get_base_layer_quality_thresholds(self) -> Dict[str, float]:
        """
        Get BASE LAYER specific quality thresholds.

        These differ from global quality thresholds as they apply specifically
        to intrinsic method quality (base layer @b), not final calibration scores.

        Returns:
            Dictionary with keys: excellent, good, acceptable, needs_improvement
            Each value is a float threshold in [0.0, 1.0]

        Example:
            >>> loader.get_base_layer_quality_thresholds()
            {'excellent': 0.8, 'good': 0.6, 'acceptable': 0.4, 'needs_improvement': 0.0}
        """
        self._ensure_loaded()

        base_thresholds = self._data.get("_global_thresholds", {}).get("base_layer_quality_levels", {})

        if not base_thresholds:
            logger.warning(
                "base_layer_quality_thresholds_not_found_using_defaults",
                extra={"using_defaults": True}
            )
            return {
                "excellent": 0.8,
                "good": 0.6,
                "acceptable": 0.4,
                "needs_improvement": 0.0
            }

        return {
            "excellent": float(base_thresholds.get("excellent", 0.8)),
            "good": float(base_thresholds.get("good", 0.6)),
            "acceptable": float(base_thresholds.get("acceptable", 0.4)),
            "needs_improvement": float(base_thresholds.get("needs_improvement", 0.0))
        }

    def get_validation_threshold_for_role(self, role: str, default: float = 0.70) -> float:
        """
        Get validation threshold for a method role type.

        Args:
            role: Method role (analyzer, processor, ingest, etc.)
            default: Default threshold if role not found

        Returns:
            Threshold value in [0.0, 1.0]

        Example:
            >>> loader.get_validation_threshold_for_role("analyzer")
            0.70
            >>> loader.get_validation_threshold_for_role("utility")
            0.30
        """
        self._ensure_loaded()

        thresholds_by_role = self._data.get("_global_thresholds", {}).get(
            "validation_thresholds_by_role", {}
        )

        role_lower = role.lower()

        if role_lower not in thresholds_by_role:
            logger.debug(
                "role_threshold_not_found_using_default",
                extra={"role": role, "default": default}
            )
            return default

        threshold = float(thresholds_by_role[role_lower])

        logger.debug(
            "role_threshold_retrieved",
            extra={"role": role, "threshold": threshold}
        )

        return threshold

    def get_executor_threshold(self, executor_name: str, default: float = 0.70) -> float:
        """
        Get validation threshold for a specific executor.

        Args:
            executor_name: Name of executor (e.g., "D1Q1_Executor")
            default: Default threshold if executor not found

        Returns:
            Threshold value in [0.0, 1.0]

        Example:
            >>> loader.get_executor_threshold("D1Q1_Executor")
            0.70
            >>> loader.get_executor_threshold("D4Q1_Executor")
            0.80  # Financial questions have higher threshold
        """
        self._ensure_loaded()

        executors = self._data.get("_executor_thresholds", {}).get("executors", {})

        if executor_name not in executors:
            # Try default executor threshold
            default_exec_threshold = self._data.get("_executor_thresholds", {}).get(
                "default_executor_threshold", default
            )
            logger.debug(
                "executor_threshold_not_found_using_default",
                extra={"executor": executor_name, "default": default_exec_threshold}
            )
            return float(default_exec_threshold)

        executor_config = executors[executor_name]
        threshold = float(executor_config.get("threshold", default))

        logger.debug(
            "executor_threshold_retrieved",
            extra={
                "executor": executor_name,
                "threshold": threshold,
                "rationale": executor_config.get("rationale", "")
            }
        )

        return threshold

    def executor_requires_all_layers(self, executor_name: str) -> bool:
        """
        Check if an executor requires all 8 calibration layers.

        Args:
            executor_name: Name of executor (e.g., "D1Q1_Executor")

        Returns:
            True if executor requires all 8 layers, False otherwise

        Note:
            All 30 executors should require all 8 layers by design.
        """
        self._ensure_loaded()

        executors = self._data.get("_executor_thresholds", {}).get("executors", {})

        if executor_name not in executors:
            # Conservative: assume all layers required
            logger.debug(
                "executor_config_not_found_assuming_all_layers",
                extra={"executor": executor_name}
            )
            return True

        requires_all = executors[executor_name].get("requires_all_8_layers", True)

        logger.debug(
            "executor_layer_requirement_retrieved",
            extra={"executor": executor_name, "requires_all_layers": requires_all}
        )

        return requires_all

    def get_method_parameter(
        self,
        method_id: str,
        parameter_name: str,
        default: Any = None
    ) -> Any:
        """
        Get a specific parameter for a method.

        Args:
            method_id: Full method identifier (e.g., "module.Class.method")
            parameter_name: Name of the parameter to retrieve
            default: Default value if parameter not found

        Returns:
            Parameter value (type depends on parameter), or default if not found

        Example:
            >>> loader.get_method_parameter(
            ...     "semantic_chunking_policy.SemanticChunker.chunk",
            ...     "similarity_threshold"
            ... )
            {'value': 0.80, 'source': '...', 'description': '...'}
        """
        self._ensure_loaded()

        methods = self._data.get("methods", {})

        if method_id not in methods:
            logger.debug(
                "method_not_in_parameters",
                extra={"method_id": method_id, "parameter": parameter_name, "returning": default}
            )
            return default

        method_params = methods[method_id]

        if parameter_name not in method_params:
            logger.debug(
                "parameter_not_found_for_method",
                extra={"method_id": method_id, "parameter": parameter_name, "returning": default}
            )
            return default

        param_value = method_params[parameter_name]

        logger.debug(
            "method_parameter_retrieved",
            extra={"method_id": method_id, "parameter": parameter_name}
        )

        return param_value

    def get_method_parameter_value(
        self,
        method_id: str,
        parameter_name: str,
        default: Any = None
    ) -> Any:
        """
        Get the 'value' field of a method parameter (convenience method).

        This is useful when parameters are stored as dicts with 'value', 'source', etc.

        Args:
            method_id: Full method identifier
            parameter_name: Name of the parameter
            default: Default value if parameter or 'value' field not found

        Returns:
            The 'value' field, or the entire parameter if not a dict, or default

        Example:
            >>> loader.get_method_parameter_value(
            ...     "semantic_chunking_policy.SemanticChunker.chunk",
            ...     "similarity_threshold"
            ... )
            0.80
        """
        param = self.get_method_parameter(method_id, parameter_name, default=None)

        if param is None:
            return default

        # If param is a dict with 'value' field, return that
        if isinstance(param, dict) and "value" in param:
            return param["value"]

        # Otherwise return the param itself
        return param

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded parameters.

        Returns:
            Dictionary with statistics:
                - total_methods: Number of methods with parameters
                - total_executors: Number of executors configured
                - version: Version from metadata
                - migration_status: Migration status from metadata

        Example:
            >>> stats = loader.get_statistics()
            >>> print(f"Methods configured: {stats['total_methods']}")
            Methods configured: 8
        """
        self._ensure_loaded()

        return {
            "total_methods": len(self._data.get("methods", {})),
            "total_executors": len(
                self._data.get("_executor_thresholds", {}).get("executors", {})
            ),
            "version": self._data.get("_metadata", {}).get("version", "unknown"),
            "migration_status": self._data.get("_metadata", {}).get("migration_status", "unknown"),
            "last_updated": self._data.get("_metadata", {}).get("last_updated", "unknown")
        }
