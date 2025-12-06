"""Phase 5: Signal Resolution

This module implements Phase 5 signal resolution that accepts question dictionaries
and resolves required signals by looking them up in a signal registry.

Key Features:
- Iterates over question's signal_requirements list
- Looks up each signal type in registry (maps types to handler instances)
- Raises ValueError if any signal type is missing (hard-stop)
- Validates signal_requirements entries contain signal_type string field via dict get
- Returns immutable tuple of resolved signal objects
- Handles missing/empty signal_requirements by returning empty tuple
- Structured debug logging with question ID, counts, and correlation ID

Design:
- Signal registry passed as constructor parameter or stored as instance state
- Signal handlers cannot be mutated after resolution completes (immutable tuple)
- No fallbacks or degraded modes - missing signals cause immediate failure
- Registry is a dict-like mapping or object where signal types are lookup keys

Example Usage:
    >>> # Create a signal registry with handler instances
    >>> class SignalRegistry:
    ...     def __init__(self):
    ...         self.budget_signal = BudgetSignalHandler()
    ...         self.actor_signal = ActorSignalHandler()
    ...         self.timeline_signal = TimelineSignalHandler()
    >>>
    >>> registry = SignalRegistry()
    >>> resolver = SignalResolver(registry)
    >>>
    >>> # Question with signal requirements
    >>> question = {
    ...     "question_id": "Q001",
    ...     "signal_requirements": [
    ...         {"signal_type": "budget_signal"},
    ...         {"signal_type": "actor_signal"}
    ...     ]
    ... }
    >>>
    >>> # Resolve signals - returns immutable tuple
    >>> signals = resolver.resolve_signals_for_question(
    ...     question=question,
    ...     correlation_id="corr-123"
    ... )
    >>>
    >>> # signals is now an immutable tuple of handlers
    >>> assert isinstance(signals, tuple)
    >>> assert len(signals) == 2
    >>>
    >>> # Missing signal raises ValueError
    >>> question_missing = {
    ...     "question_id": "Q002",
    ...     "signal_requirements": [{"signal_type": "missing_signal"}]
    ... }
    >>> try:
    ...     resolver.resolve_signals_for_question(question_missing, "corr-124")
    ... except ValueError as e:
    ...     print(f"Hard-stop error: {e}")
    ...
    Hard-stop error: Signal type 'missing_signal' missing from registry...
    >>>
    >>> # Question without requirements returns empty tuple
    >>> question_no_signals = {"question_id": "Q003"}
    >>> result = resolver.resolve_signals_for_question(question_no_signals, "corr-125")
    >>> assert result == ()

Alternative Usage with Dict Registry:
    >>> # Registry as a dict
    >>> registry_dict = {
    ...     "budget_signal": BudgetSignalHandler(),
    ...     "actor_signal": ActorSignalHandler()
    ... }
    >>> resolver = SignalResolver(registry_dict)
    >>>
    >>> # Signal requirements as simple list of strings
    >>> question = {
    ...     "question_id": "Q004",
    ...     "signal_requirements": ["budget_signal", "actor_signal"]
    ... }
    >>> signals = resolver.resolve_signals_for_question(question, "corr-126")
"""

from __future__ import annotations

import contextlib
from typing import Any

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class SignalResolver:
    """Phase 5 signal resolver with registry-based signal lookup.

    This class encapsulates the signal resolution logic for Phase 5,
    accepting a signal registry at construction time and using it to
    resolve signals for questions during execution.

    The signal registry can be:
    - A dict mapping signal types to handler instances
    - An object with signal types as attributes
    - Any object that supports item access or attribute access

    Attributes:
        signal_registry: Registry that maps signal types to handler instances
    """

    def __init__(self, signal_registry: Any) -> None:
        """Initialize signal resolver with registry.

        Args:
            signal_registry: Registry mapping signal types to handler instances.
                           Can be a dict, object with attributes, or similar.
        """
        self.signal_registry = signal_registry

    def resolve_signals_for_question(
        self,
        question: dict[str, Any],
        correlation_id: str,
    ) -> tuple[Any, ...]:
        """Resolve signals for a question by iterating over signal_requirements.

        This method:
        1. Extracts signal_requirements from question dictionary via get()
        2. Returns empty tuple if signal_requirements is missing or empty
        3. Validates each entry contains signal_type string field via dict get with None-checking
        4. Iterates over signal_requirements list
        5. Looks up each signal type in registry as a key
        6. Raises ValueError if any signal type is missing (hard-stop, no fallback)
        7. Collects resolved signal handlers into a list
        8. Converts list to immutable tuple before returning
        9. Logs debug info with question ID, required count, resolved count, correlation ID

        Args:
            question: Question dict with optional signal_requirements field
            correlation_id: Correlation ID for tracing and logging

        Returns:
            Immutable tuple of resolved signal handler objects. Empty tuple if
            signal_requirements is missing or empty.

        Raises:
            ValueError: When any signal type is missing from registry, since unresolved
                       signals would cause executor failures. Also raised when
                       signal_requirements entry does not contain signal_type string field.
        """
        question_id = question.get("question_id", "UNKNOWN")

        signal_requirements = question.get("signal_requirements")

        if signal_requirements is None or not signal_requirements:
            return ()

        if not isinstance(signal_requirements, list):
            if isinstance(signal_requirements, set | tuple):
                signal_requirements = list(signal_requirements)
            elif isinstance(signal_requirements, dict):
                signal_requirements = list(signal_requirements.keys())
            else:
                return ()

        if not signal_requirements:
            return ()

        resolved_signals_list: list[Any] = []
        required_types_list: list[str] = []

        for idx, requirement in enumerate(signal_requirements):
            signal_type: str | None = None

            if isinstance(requirement, dict):
                signal_type = requirement.get("signal_type")
                if signal_type is None:
                    raise ValueError(
                        f"Signal requirement at index {idx} missing signal_type field "
                        f"for question {question_id}"
                    )
                if not isinstance(signal_type, str):
                    raise ValueError(
                        f"Signal requirement at index {idx} has non-string signal_type "
                        f"for question {question_id}: {type(signal_type).__name__}"
                    )
            elif isinstance(requirement, str):
                signal_type = requirement
            else:
                raise ValueError(
                    f"Signal requirement at index {idx} has invalid type "
                    f"for question {question_id}: {type(requirement).__name__}"
                )

            required_types_list.append(signal_type)

            signal_handler = None

            if isinstance(self.signal_registry, dict):
                signal_handler = self.signal_registry.get(signal_type)
            elif hasattr(self.signal_registry, signal_type):
                signal_handler = getattr(self.signal_registry, signal_type)
            elif hasattr(self.signal_registry, "__getitem__"):
                with contextlib.suppress(KeyError, TypeError):
                    signal_handler = self.signal_registry[signal_type]

            if signal_handler is None:
                raise ValueError(
                    f"Signal type '{signal_type}' missing from registry "
                    f"for question {question_id}. "
                    f"Unresolved signals would cause executor failures."
                )

            resolved_signals_list.append(signal_handler)

        resolved_count = len(resolved_signals_list)
        required_count = len(required_types_list)

        logger.debug(
            "signals_resolved_for_question",
            question_id=question_id,
            required_signals=required_count,
            resolved_signals=resolved_count,
            correlation_id=correlation_id,
        )

        return tuple(resolved_signals_list)


def resolve_signals_for_question(
    question: dict[str, Any],
    signal_registry: Any,
    correlation_id: str,
) -> tuple[Any, ...]:
    """Standalone function for resolving signals for a question.

    This is a convenience function that creates a SignalResolver and calls
    its resolve_signals_for_question method. Use this when you don't need
    to maintain resolver state across multiple calls.

    Args:
        question: Question dict with optional signal_requirements field
        signal_registry: Registry that maps signal types to handler instances
        correlation_id: Correlation ID for tracing and logging

    Returns:
        Immutable tuple of resolved signal handler objects

    Raises:
        ValueError: When any signal type is missing from registry or
                   when signal_requirements entry is invalid
    """
    resolver = SignalResolver(signal_registry)
    return resolver.resolve_signals_for_question(question, correlation_id)


__all__ = [
    "SignalResolver",
    "resolve_signals_for_question",
]
