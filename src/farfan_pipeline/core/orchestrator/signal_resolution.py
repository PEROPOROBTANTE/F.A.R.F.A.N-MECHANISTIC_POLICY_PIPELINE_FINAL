"""Signal Resolution with Hard-Fail Semantics

This module implements signal resolution for chunks with strict validation
and no fallback mechanisms. When required signals are missing, the system
fails immediately with explicit error messages.

Key Features:
- Hard-fail semantics: no fallbacks or degraded modes
- Set-based signal validation
- Per-chunk signal caching in SignalRegistry
- Immutable signal tuples for safety
- Explicit error messages for missing signals
"""

from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from farfan_pipeline.core.orchestrator.signals import SignalPack, SignalRegistry

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class Signal(NamedTuple):
    """Immutable signal with type and content."""

    signal_type: str
    content: SignalPack | None


class Question(NamedTuple):
    """Question with signal requirements."""

    question_id: str
    signal_requirements: set[str]


class Chunk(NamedTuple):
    """Policy chunk for analysis."""

    chunk_id: str
    text: str


def _resolve_signals(
    chunk: Chunk,
    question: Question,
    signal_registry: SignalRegistry,
) -> tuple[Signal, ...]:
    """Resolve signals for a chunk with hard-fail semantics.

    This function queries the signal registry for all signals required by the
    question, validates that all required signals are present, and returns an
    immutable tuple of Signal objects. No fallbacks or degraded modes are
    supported - missing signals result in immediate failure.

    Args:
        chunk: Policy chunk to resolve signals for
        question: Question with signal_requirements set
        signal_registry: Registry with get_signals_for_chunk method

    Returns:
        Immutable tuple of Signal objects, one per required signal type

    Raises:
        ValueError: When any required signals are missing, with explicit
                   message listing the missing signal types
    """
    required_types = question.signal_requirements

    signals = signal_registry.get_signals_for_chunk(chunk, required_types)

    resolved_types = {sig.signal_type for sig in signals}

    missing_signals = required_types - resolved_types

    if missing_signals:
        sorted_missing = sorted(missing_signals)
        raise ValueError(f"Missing signals {set(sorted_missing)}")

    logger.debug(
        "signals_resolved",
        chunk_id=chunk.chunk_id,
        question_id=question.question_id,
        resolved_count=len(signals),
        signal_types=sorted(resolved_types),
    )

    return tuple(signals)
