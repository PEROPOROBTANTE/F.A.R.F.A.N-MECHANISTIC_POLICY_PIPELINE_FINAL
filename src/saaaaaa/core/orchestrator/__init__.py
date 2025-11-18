"""Orchestrator utilities with contract validation on import."""
from __future__ import annotations

import inspect
from threading import RLock
from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from .questionnaire import CanonicalQuestionnaire

# Import utilities from submodules
from .contract_loader import (
    JSONContractLoader,
    LoadError,
    LoadResult,
)

# Import core classes from the refactored package
from .core import (
    AbortRequested,
    AbortSignal,
    Evidence,
    MethodExecutor,
    MicroQuestionRun,
    Orchestrator,
    PhaseInstrumentation,
    PhaseResult,
    PreprocessedDocument,
    ResourceLimits,
    ScoredMicroQuestion,
)
from .evidence_registry import (
    EvidenceRecord,
    EvidenceRegistry,
    ProvenanceDAG,
    ProvenanceNode,
    get_global_registry,
)

class _QuestionnaireProvider:
    """Centralized access to the questionnaire monolith payload.

    This is now a pure data holder - I/O operations have been moved to factory.py.
    The provider receives pre-loaded data and manages caching.

    Thread Safety: All methods are protected by RLock for concurrent access.
    Type Safety: Accepts CanonicalQuestionnaire (preferred) or dict (legacy).
    """

    def __init__(self, initial_data: dict[str, Any] | None = None) -> None:
        """Initialize provider with optional pre-loaded data.

        Args:
            initial_data: Pre-loaded questionnaire data. If None, data must be
                         set via set_data() before calling get_data().
        """
        self._cache: dict[str, Any] | None = initial_data
        self._canonical: CanonicalQuestionnaire | None = None
        self._lock = RLock()

    def set_data(self, data: dict[str, Any] | CanonicalQuestionnaire) -> None:
        """Set questionnaire data (typically called by factory).

        Args:
            data: Questionnaire payload (CanonicalQuestionnaire preferred, dict for legacy)
        """
        from .questionnaire import CanonicalQuestionnaire

        with self._lock:
            if isinstance(data, CanonicalQuestionnaire):
                # Type-safe path: store canonical and extract dict
                self._canonical = data
                self._cache = dict(data.data)
            elif isinstance(data, dict):
                # Legacy path: dict without validation
                import warnings
                warnings.warn(
                    "Setting questionnaire provider with dict is deprecated. "
                    "Use CanonicalQuestionnaire from load_questionnaire().",
                    DeprecationWarning,
                    stacklevel=2
                )
                self._canonical = None
                self._cache = data
            else:
                raise TypeError(
                    f"data must be CanonicalQuestionnaire or dict, got {type(data).__name__}"
                )

    def get_data(self) -> dict[str, Any]:
        """Get cached questionnaire data as dict.

        Returns:
            Questionnaire payload dictionary

        Raises:
            RuntimeError: If no data has been loaded yet
        """
        with self._lock:
            if self._cache is None:
                raise RuntimeError(
                    "Questionnaire data not loaded. Use factory.py to load data first."
                )
            return self._cache

    def get_canonical(self) -> CanonicalQuestionnaire | None:
        """Get canonical questionnaire if available.

        Returns:
            CanonicalQuestionnaire if set via set_data(), None if set via legacy dict

        Raises:
            RuntimeError: If no data has been loaded yet
        """
        with self._lock:
            if self._cache is None:
                raise RuntimeError(
                    "Questionnaire data not loaded. Use factory.py to load data first."
                )
            return self._canonical

    def has_data(self) -> bool:
        """Check if data is loaded.

        Returns:
            True if data is available, False otherwise
        """
        with self._lock:
            return self._cache is not None

    def exists(self) -> bool:
        """Alias for has_data() for backward compatibility.

        Returns:
            True if data is available, False otherwise
        """
        return self.has_data()

_questionnaire_provider = _QuestionnaireProvider()

def get_questionnaire_provider() -> _QuestionnaireProvider:
    """Get the global questionnaire provider instance."""
    return _questionnaire_provider

def get_questionnaire_payload() -> dict[str, Any]:
    """Get questionnaire payload with caller boundary enforcement.

    Note: Data must be pre-loaded via factory.py before calling this function.

    Returns:
        Questionnaire payload dictionary

    Raises:
        RuntimeError: If called from outside orchestrator package or if data not loaded
    """
    caller_frame = inspect.currentframe().f_back
    caller_module = caller_frame.f_globals.get('__name__', '')
    if not caller_module.startswith('saaaaaa.core.orchestrator'):
        raise RuntimeError("Questionnaire provider access restricted to orchestrator package")
    return _questionnaire_provider.get_data()

__all__ = [
    "EvidenceRecord",
    "EvidenceRegistry",
    "ProvenanceDAG",
    "ProvenanceNode",
    "get_global_registry",
    "JSONContractLoader",
    "LoadError",
    "LoadResult",
    "get_questionnaire_provider",
    "get_questionnaire_payload",
    "Orchestrator",
    "MethodExecutor",
    "PreprocessedDocument",
    "Evidence",
    "AbortSignal",
    "AbortRequested",
    "ResourceLimits",
    "PhaseInstrumentation",
    "PhaseResult",
    "MicroQuestionRun",
    "ScoredMicroQuestion",
]
