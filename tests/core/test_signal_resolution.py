"""Tests for Signal Resolution with Hard-Fail Semantics

This module tests the signal resolution system including:
- Resolution with all required signals available
- Hard-fail behavior when signals are missing
- Per-chunk caching in SignalRegistry
"""

from unittest.mock import Mock

import pytest

from farfan_pipeline.core.orchestrator.signal_resolution import (
    Chunk,
    Question,
    Signal,
    _resolve_signals,
)
from farfan_pipeline.core.orchestrator.signals import SignalPack, SignalRegistry

EXPECTED_TWO_SIGNALS = 2


@pytest.fixture
def mock_signal_registry():
    """Create a mock signal registry for testing."""
    registry = Mock()
    registry._chunk_cache = {}
    return registry


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return Chunk(chunk_id="chunk_001", text="Sample policy text")


@pytest.fixture
def sample_question_two_signals():
    """Create a question requiring two signal types."""
    return Question(question_id="Q001", signal_requirements={"budget", "actor"})


@pytest.fixture
def sample_question_one_signal():
    """Create a question requiring one signal type."""
    return Question(question_id="Q002", signal_requirements={"budget"})


def test_resolve_signals_with_all_available(
    sample_chunk, sample_question_two_signals, mock_signal_registry
):
    """Test signal resolution succeeds when all required signals are available."""
    budget_signal = Signal(signal_type="budget", content={"amount": 1000000})
    actor_signal = Signal(signal_type="actor", content={"name": "Ministry of Finance"})

    mock_signal_registry.get_signals_for_chunk.return_value = [
        budget_signal,
        actor_signal,
    ]

    result = _resolve_signals(
        sample_chunk, sample_question_two_signals, mock_signal_registry
    )

    assert isinstance(result, tuple)
    assert len(result) == EXPECTED_TWO_SIGNALS
    assert budget_signal in result
    assert actor_signal in result

    mock_signal_registry.get_signals_for_chunk.assert_called_once_with(
        sample_chunk, {"budget", "actor"}
    )


def test_resolve_signals_fails_on_missing(
    sample_chunk, sample_question_two_signals, mock_signal_registry
):
    """Test signal resolution fails with ValueError when signals are missing."""
    budget_signal = Signal(signal_type="budget", content={"amount": 1000000})

    mock_signal_registry.get_signals_for_chunk.return_value = [budget_signal]

    with pytest.raises(ValueError) as exc_info:
        _resolve_signals(
            sample_chunk, sample_question_two_signals, mock_signal_registry
        )

    error_message = str(exc_info.value)
    assert "Missing signals" in error_message
    assert "actor" in error_message


def test_resolve_signals_error_message_format(
    sample_chunk, sample_question_two_signals, mock_signal_registry
):
    """Test that error message correctly formats missing signal types."""
    mock_signal_registry.get_signals_for_chunk.return_value = []

    with pytest.raises(ValueError) as exc_info:
        _resolve_signals(
            sample_chunk, sample_question_two_signals, mock_signal_registry
        )

    error_message = str(exc_info.value)
    assert "Missing signals" in error_message
    assert "actor" in error_message or "budget" in error_message


def test_resolve_signals_returns_immutable_tuple(
    sample_chunk, sample_question_one_signal, mock_signal_registry
):
    """Test that resolved signals are returned as an immutable tuple."""
    budget_signal = Signal(signal_type="budget", content={"amount": 1000000})

    mock_signal_registry.get_signals_for_chunk.return_value = [budget_signal]

    result = _resolve_signals(
        sample_chunk, sample_question_one_signal, mock_signal_registry
    )

    assert isinstance(result, tuple)
    assert len(result) == 1
    assert result[0] == budget_signal

    with pytest.raises((TypeError, AttributeError)):
        result[0] = Signal(signal_type="other", content={})


def test_signal_registry_caching(mock_signal_registry, sample_chunk):
    """Test that SignalRegistry caches signals per chunk."""
    registry = SignalRegistry()

    budget_pack = SignalPack(
        version="1.0.0",
        policy_area="PA01",
        patterns=["budget", "allocation"],
        source_fingerprint="abc123" * 8,
    )
    registry.put("budget", budget_pack)

    chunk = Chunk(chunk_id="chunk_001", text="Sample text")
    required_types = {"budget"}

    signals_first = registry.get_signals_for_chunk(chunk, required_types)

    assert len(signals_first) == 1
    assert signals_first[0].signal_type == "budget"

    signals_second = registry.get_signals_for_chunk(chunk, required_types)

    assert len(signals_second) == 1
    assert signals_second[0].signal_type == "budget"

    assert chunk.chunk_id in registry._chunk_cache
    assert signals_first == signals_second


def test_signal_registry_cache_per_chunk(mock_signal_registry):
    """Test that cache is maintained separately for different chunks."""
    registry = SignalRegistry()

    budget_pack = SignalPack(
        version="1.0.0",
        policy_area="PA01",
        patterns=["budget"],
        source_fingerprint="abc123" * 8,
    )
    registry.put("budget", budget_pack)

    chunk1 = Chunk(chunk_id="chunk_001", text="Sample text 1")
    chunk2 = Chunk(chunk_id="chunk_002", text="Sample text 2")

    required_types = {"budget"}

    signals1 = registry.get_signals_for_chunk(chunk1, required_types)
    signals2 = registry.get_signals_for_chunk(chunk2, required_types)

    assert chunk1.chunk_id in registry._chunk_cache
    assert chunk2.chunk_id in registry._chunk_cache

    assert len(signals1) == 1
    assert len(signals2) == 1


def test_signal_registry_cache_cleared_on_clear():
    """Test that chunk cache is cleared when registry.clear() is called."""
    registry = SignalRegistry()

    budget_pack = SignalPack(
        version="1.0.0",
        policy_area="PA01",
        patterns=["budget"],
        source_fingerprint="abc123" * 8,
    )
    registry.put("budget", budget_pack)

    chunk = Chunk(chunk_id="chunk_001", text="Sample text")
    required_types = {"budget"}

    signals = registry.get_signals_for_chunk(chunk, required_types)
    assert len(signals) == 1
    assert chunk.chunk_id in registry._chunk_cache

    registry.clear()

    assert len(registry._chunk_cache) == 0


def test_resolve_signals_with_no_requirements(sample_chunk, mock_signal_registry):
    """Test signal resolution with empty requirements set."""
    question = Question(question_id="Q003", signal_requirements=set())

    mock_signal_registry.get_signals_for_chunk.return_value = []

    result = _resolve_signals(sample_chunk, question, mock_signal_registry)

    assert isinstance(result, tuple)
    assert len(result) == 0

    mock_signal_registry.get_signals_for_chunk.assert_called_once_with(
        sample_chunk, set()
    )


def test_resolve_signals_with_extra_signals_available(
    sample_chunk, sample_question_one_signal, mock_signal_registry
):
    """Test that extra signals beyond requirements don't cause issues."""
    budget_signal = Signal(signal_type="budget", content={"amount": 1000000})
    actor_signal = Signal(signal_type="actor", content={"name": "Ministry"})

    mock_signal_registry.get_signals_for_chunk.return_value = [
        budget_signal,
        actor_signal,
    ]

    result = _resolve_signals(
        sample_chunk, sample_question_one_signal, mock_signal_registry
    )

    assert isinstance(result, tuple)
    assert len(result) == EXPECTED_TWO_SIGNALS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
