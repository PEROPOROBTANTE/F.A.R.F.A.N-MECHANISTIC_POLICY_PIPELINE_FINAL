"""Dependency lockdown enforcement to prevent magic downloads and hidden behavior.

This module enforces explicit dependency management by:
1. Checking if online model downloads are allowed via HF_ONLINE env var
2. Setting HuggingFace offline mode when online access is disabled
3. Providing early failure for missing critical dependencies
4. Allowing explicit degraded mode marking for optional dependencies

No fallback logic, no "best effort" embeddings. Either dependencies are present
and configured correctly, or the system fails fast with clear error messages.
"""

import logging
import os

logger = logging.getLogger(__name__)


def _is_model_cached(model_name: str) -> bool:
    """Check if a HuggingFace model is cached locally.

    Uses a heuristic check of common cache locations to determine if a model
    is likely available offline. This is a best-effort check - false positives
    are acceptable (will fail later when model actually loads), but false negatives
    should be minimized to avoid blocking offline usage of cached models.

    Args:
        model_name: HuggingFace model name (e.g., "sentence-transformers/model")

    Returns:
        True if model appears to be cached locally, False otherwise
    """
    from pathlib import Path

    # Check common HuggingFace cache locations
    cache_dirs = [
        os.path.expanduser("~/.cache/huggingface/hub"),
        os.path.expanduser("~/.cache/torch/sentence_transformers"),
        os.getenv("HF_HOME"),
        os.getenv("TRANSFORMERS_CACHE"),
    ]

    # Convert model name to cache directory pattern
    # HF uses "models--org--name" format in cache
    model_slug = model_name.replace("/", "--")

    for cache_dir in cache_dirs:
        if cache_dir and os.path.exists(cache_dir):
            cache_path = Path(cache_dir)
            # Use glob with specific pattern instead of rglob for efficiency
            # Check just the top-level directories, not recursive
            if any(model_slug in p.name for p in cache_path.iterdir()):
                return True

    return False


class DependencyLockdownError(RuntimeError):
    """Raised when a dependency constraint is violated."""
    pass


class DependencyLockdown:
    """Enforces strict dependency controls to prevent hidden/magic behavior.

    This class ensures that:
    - Online model downloads are explicitly controlled via HF_ONLINE env var
    - HuggingFace models only download when explicitly allowed
    - Critical dependencies fail fast if missing
    - Optional dependencies are clearly marked as degraded when missing
    """

    def __init__(self) -> None:
        """Initialize dependency lockdown based on environment configuration."""
        self.hf_allowed = os.getenv("HF_ONLINE", "0") == "1"
        self._enforce_offline_mode()
        self._log_configuration()

    def _enforce_offline_mode(self) -> None:
        """Enforce HuggingFace offline mode if HF_ONLINE is not enabled."""
        if not self.hf_allowed:
            # Set HuggingFace environment variables to prevent downloads
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            logger.info(
                "Dependency lockdown: HuggingFace offline mode ENFORCED "
                "(HF_ONLINE=0 or not set)"
            )
        else:
            logger.warning(
                "Dependency lockdown: HuggingFace online mode ENABLED "
                "(HF_ONLINE=1). Models may be downloaded from HuggingFace Hub."
            )

    def _log_configuration(self) -> None:
        """Log current dependency lockdown configuration."""
        logger.info(
            f"Dependency lockdown initialized: "
            f"HF_ONLINE={self.hf_allowed}, "
            f"HF_HUB_OFFLINE={os.getenv('HF_HUB_OFFLINE', 'unset')}, "
            f"TRANSFORMERS_OFFLINE={os.getenv('TRANSFORMERS_OFFLINE', 'unset')}"
        )

    def check_online_model_access(
        self,
        model_name: str,
        operation: str = "model download"
    ) -> None:
        """Check if online model access is allowed, raise if not.

        Args:
            model_name: Name of the model being accessed
            operation: Description of the operation (for error message)

        Raises:
            DependencyLockdownError: If online access is not allowed
        """
        if not self.hf_allowed:
            raise DependencyLockdownError(
                f"Online model download disabled in this environment. "
                f"Attempted operation: {operation} for model '{model_name}'. "
                f"To enable online downloads, set HF_ONLINE=1 environment variable. "
                f"No fallback to degraded mode - this is a hard failure."
            )

    def check_critical_dependency(
        self,
        module_name: str,
        pip_package: str,
        phase: str | None = None
    ) -> None:
        """Check if a critical dependency is available, fail fast if not.

        Args:
            module_name: Python module name to import
            pip_package: pip package name for installation instructions
            phase: Optional phase name where dependency is required

        Raises:
            DependencyLockdownError: If critical dependency is missing
        """
        try:
            __import__(module_name)
        except ImportError as e:
            phase_info = f" for phase '{phase}'" if phase else ""
            raise DependencyLockdownError(
                f"Critical dependency '{module_name}' is missing{phase_info}. "
                f"Install it with: pip install {pip_package}. "
                f"No degraded mode available - this is a mandatory dependency. "
                f"Original error: {e}"
            ) from e

    def check_optional_dependency(
        self,
        module_name: str,
        pip_package: str,
        feature: str
    ) -> bool:
        """Check if an optional dependency is available.

        Args:
            module_name: Python module name to import
            pip_package: pip package name for installation instructions
            feature: Feature name that requires this dependency

        Returns:
            True if dependency is available, False otherwise

        Note:
            This does NOT raise an error, but logs a warning about degraded mode.
            Caller must explicitly handle degraded mode and log it clearly.
        """
        try:
            __import__(module_name)
            return True
        except ImportError:
            logger.warning(
                f"DEGRADED MODE: Optional dependency '{module_name}' not available. "
                f"Feature '{feature}' will be disabled. "
                f"Install with: pip install {pip_package}"
            )
            return False

    def get_mode_description(self) -> dict[str, str | bool]:
        """Get current dependency lockdown mode description.

        Returns:
            Dictionary with mode information for logging/debugging
        """
        return {
            "hf_online_allowed": self.hf_allowed,
            "hf_hub_offline": os.getenv("HF_HUB_OFFLINE", "unset"),
            "transformers_offline": os.getenv("TRANSFORMERS_OFFLINE", "unset"),
            "mode": "online" if self.hf_allowed else "offline_enforced",
        }


# Global singleton instance
_lockdown_instance: DependencyLockdown | None = None


def get_dependency_lockdown() -> DependencyLockdown:
    """Get or create the global dependency lockdown instance.

    Returns:
        Global DependencyLockdown instance
    """
    global _lockdown_instance
    if _lockdown_instance is None:
        _lockdown_instance = DependencyLockdown()
    return _lockdown_instance


def reset_dependency_lockdown() -> None:
    """Reset the global dependency lockdown instance (for testing)."""
    global _lockdown_instance
    _lockdown_instance = None
