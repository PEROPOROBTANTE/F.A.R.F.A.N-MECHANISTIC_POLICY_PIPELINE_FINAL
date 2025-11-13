"""Orchestrator utilities with contract validation on import."""
import inspect
from threading import RLock
from typing import Any, Dict, Optional

class _QuestionnaireProvider:
    """Centralized access to the questionnaire monolith payload.

    This is now a pure data holder - I/O operations have been moved to factory.py.
    The provider receives pre-loaded data and manages caching.
    """

    def __init__(self, initial_data: dict[str, Any] | None = None) -> None:
        """Initialize provider with optional pre-loaded data.

        Args:
            initial_data: Pre-loaded questionnaire data. If None, data must be
                         set via set_data() before calling get_data().
        """
        self._cache: dict[str, Any] | None = initial_data
        self._lock = RLock()

    def set_data(self, data: dict[str, Any]) -> None:
        """Set questionnaire data (typically called by factory).

        Args:
            data: Questionnaire payload dictionary
        """
        with self._lock:
            self._cache = data

    def get_data(self) -> dict[str, Any]:
        """Get cached questionnaire data.

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
