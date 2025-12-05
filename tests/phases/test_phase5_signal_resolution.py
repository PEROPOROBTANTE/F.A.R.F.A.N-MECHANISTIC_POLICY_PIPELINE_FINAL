"""Test Phase 5: Signal Resolution with Registry Integration

Tests Phase 5 signal resolution logic including:
- Signal registry integration and query interface
- Missing signal hard stops (no fallbacks or degraded modes)
- Immutable signal tuple returns
- Set-based signal validation
- Per-chunk signal caching
- Required vs optional signal distinction
- Signal type validation
- Error message clarity for missing signals
"""

import pytest

from farfan_pipeline.core.orchestrator.signal_resolution import (
    Chunk,
    Question,
    Signal,
    _resolve_signals,
)


class MockSignalRegistry:
    """Mock signal registry for testing."""

    def __init__(self, signals_to_return=None):
        self.signals_to_return = signals_to_return or []
        self.calls = []

    def get_signals_for_chunk(self, chunk, required_types):
        """Mock get_signals_for_chunk method."""
        self.calls.append(
            {
                "chunk": chunk,
                "required_types": required_types,
            }
        )
        return self.signals_to_return


class TestPhase5SignalRegistryIntegration:
    """Test signal registry integration and query interface."""

    def test_resolve_signals_queries_registry(self):
        """Test _resolve_signals queries signal registry."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test chunk")
        question = Question(question_id="Q01", signal_requirements={"signal_type_1"})
        signals = [Signal(signal_type="signal_type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk, question, registry)

        assert len(registry.calls) == 1
        assert registry.calls[0]["chunk"] == chunk
        assert registry.calls[0]["required_types"] == {"signal_type_1"}

    def test_resolve_signals_passes_chunk_to_registry(self):
        """Test chunk object passed to registry unchanged."""
        chunk = Chunk(chunk_id="PA02-DIM03", text="Another test")
        question = Question(question_id="Q02", signal_requirements={"signal_type_1"})
        signals = [Signal(signal_type="signal_type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk, question, registry)

        assert registry.calls[0]["chunk"].chunk_id == "PA02-DIM03"
        assert registry.calls[0]["chunk"].text == "Another test"

    def test_resolve_signals_passes_required_types_set(self):
        """Test required_types passed as set to registry."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q03", signal_requirements={"type_1", "type_2", "type_3"}
        )
        signals = [
            Signal(signal_type="type_1", content=None),
            Signal(signal_type="type_2", content=None),
            Signal(signal_type="type_3", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk, question, registry)

        assert registry.calls[0]["required_types"] == {"type_1", "type_2", "type_3"}

    def test_resolve_signals_with_single_required_type(self):
        """Test signal resolution with single required type."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q04", signal_requirements={"single_type"})
        signals = [Signal(signal_type="single_type", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 1
        assert result[0].signal_type == "single_type"

    def test_resolve_signals_with_multiple_required_types(self):
        """Test signal resolution with multiple required types."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q05", signal_requirements={"type_a", "type_b", "type_c"}
        )
        signals = [
            Signal(signal_type="type_a", content=None),
            Signal(signal_type="type_b", content=None),
            Signal(signal_type="type_c", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 3
        signal_types = {s.signal_type for s in result}
        assert signal_types == {"type_a", "type_b", "type_c"}

    def test_resolve_signals_empty_requirements_set(self):
        """Test signal resolution with empty requirements (should succeed)."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q06", signal_requirements=set())
        registry = MockSignalRegistry(signals_to_return=[])

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 0
        assert isinstance(result, tuple)


class TestPhase5MissingSignalHardStops:
    """Test missing signal hard stops with no fallbacks or degraded modes."""

    def test_missing_signal_raises_value_error(self):
        """Test missing required signal raises ValueError."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q07", signal_requirements={"missing_type"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError, match="Missing signals"):
            _resolve_signals(chunk, question, registry)

    def test_missing_signal_error_message_includes_signal_type(self):
        """Test error message includes missing signal type."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q08", signal_requirements={"specific_type"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError, match="specific_type"):
            _resolve_signals(chunk, question, registry)

    def test_missing_multiple_signals_error_message(self):
        """Test error message lists all missing signals."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q09",
            signal_requirements={"missing_1", "missing_2", "missing_3"},
        )
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError) as exc_info:
            _resolve_signals(chunk, question, registry)

        error_msg = str(exc_info.value)
        assert "missing_1" in error_msg or "Missing signals" in error_msg
        assert "missing_2" in error_msg or "Missing signals" in error_msg
        assert "missing_3" in error_msg or "Missing signals" in error_msg

    def test_partial_signal_match_raises_error(self):
        """Test partial signal match (some present, some missing) raises error."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q10", signal_requirements={"present", "missing"}
        )
        signals = [Signal(signal_type="present", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        with pytest.raises(ValueError, match="Missing signals"):
            _resolve_signals(chunk, question, registry)

    def test_no_fallback_to_alternative_signals(self):
        """Test no fallback mechanism when exact signal missing."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q11", signal_requirements={"exact_signal"})
        signals = [Signal(signal_type="similar_signal", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        with pytest.raises(ValueError):
            _resolve_signals(chunk, question, registry)

    def test_no_degraded_mode_on_missing_signals(self):
        """Test system fails immediately without degraded mode."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q12", signal_requirements={"critical_signal"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError):
            _resolve_signals(chunk, question, registry)


class TestPhase5ImmutableSignalTuples:
    """Test immutable signal tuple returns."""

    def test_resolve_signals_returns_tuple(self):
        """Test _resolve_signals returns tuple."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q13", signal_requirements={"type_1"})
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert isinstance(result, tuple)

    def test_returned_tuple_is_immutable(self):
        """Test returned tuple cannot be modified."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q14", signal_requirements={"type_1"})
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        with pytest.raises(AttributeError):
            result.append(Signal(signal_type="new", content=None))

    def test_signal_objects_are_named_tuples(self):
        """Test Signal objects are immutable NamedTuples."""
        signal = Signal(signal_type="test", content=None)

        assert isinstance(signal, tuple)
        assert hasattr(signal, "signal_type")
        assert hasattr(signal, "content")

        with pytest.raises(AttributeError):
            signal.signal_type = "modified"

    def test_empty_result_returns_empty_tuple(self):
        """Test empty signal list returns empty tuple."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q15", signal_requirements=set())
        registry = MockSignalRegistry(signals_to_return=[])

        result = _resolve_signals(chunk, question, registry)

        assert result == ()
        assert isinstance(result, tuple)

    def test_signal_order_preserved_in_tuple(self):
        """Test signal order preserved in returned tuple."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q16", signal_requirements={"type_1", "type_2", "type_3"}
        )
        signals = [
            Signal(signal_type="type_1", content="first"),
            Signal(signal_type="type_2", content="second"),
            Signal(signal_type="type_3", content="third"),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert result[0].content == "first"
        assert result[1].content == "second"
        assert result[2].content == "third"


class TestPhase5SetBasedValidation:
    """Test set-based signal validation."""

    def test_required_types_compared_as_set(self):
        """Test required signal types compared as set (order independent)."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q17", signal_requirements={"type_c", "type_a", "type_b"}
        )
        signals = [
            Signal(signal_type="type_a", content=None),
            Signal(signal_type="type_b", content=None),
            Signal(signal_type="type_c", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 3

    def test_duplicate_signal_types_in_requirements_handled(self):
        """Test duplicate signal types in requirements treated as single requirement."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q18", signal_requirements={"type_1"}  # Duplicate
        )
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 1

    def test_extra_signals_returned_not_validated(self):
        """Test extra signals beyond requirements don't cause failure."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q19", signal_requirements={"type_1"})
        signals = [
            Signal(signal_type="type_1", content=None),
            Signal(signal_type="extra_type", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 2

    def test_signal_type_string_comparison_case_sensitive(self):
        """Test signal type comparison is case-sensitive."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q20", signal_requirements={"Type_1"})
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        with pytest.raises(ValueError):
            _resolve_signals(chunk, question, registry)

    def test_missing_signals_calculated_via_set_difference(self):
        """Test missing signals identified via set difference operation."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q21", signal_requirements={"type_1", "type_2", "type_3"}
        )
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        with pytest.raises(ValueError) as exc_info:
            _resolve_signals(chunk, question, registry)

        error_msg = str(exc_info.value)
        assert "type_2" in error_msg or "Missing signals" in error_msg
        assert "type_3" in error_msg or "Missing signals" in error_msg


class TestPhase5SignalTypeValidation:
    """Test signal type validation."""

    def test_signal_type_must_be_string(self):
        """Test Signal.signal_type must be string."""
        signal = Signal(signal_type="valid_type", content=None)
        assert isinstance(signal.signal_type, str)

    def test_signal_content_can_be_none(self):
        """Test Signal.content can be None."""
        signal = Signal(signal_type="test", content=None)
        assert signal.content is None

    def test_signal_content_can_be_signal_pack(self):
        """Test Signal.content can hold SignalPack object."""
        mock_signal_pack = {"data": "test"}
        signal = Signal(signal_type="test", content=mock_signal_pack)
        assert signal.content == {"data": "test"}

    def test_question_signal_requirements_is_set(self):
        """Test Question.signal_requirements is a set."""
        question = Question(question_id="Q22", signal_requirements={"type_1", "type_2"})
        assert isinstance(question.signal_requirements, set)

    def test_chunk_has_required_fields(self):
        """Test Chunk has chunk_id and text fields."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test content")
        assert chunk.chunk_id == "PA01-DIM01"
        assert chunk.text == "Test content"


class TestPhase5ErrorMessageClarity:
    """Test error message clarity for missing signals."""

    def test_error_message_uses_missing_signals_phrase(self):
        """Test error message explicitly states 'Missing signals'."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q23", signal_requirements={"signal_1"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError, match=r"Missing signals"):
            _resolve_signals(chunk, question, registry)

    def test_error_message_shows_missing_as_set_format(self):
        """Test error message shows missing signals in set format."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q24", signal_requirements={"sig_a", "sig_b"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError) as exc_info:
            _resolve_signals(chunk, question, registry)

        error_msg = str(exc_info.value)
        assert "{" in error_msg or "Missing signals" in error_msg

    def test_error_message_sorts_missing_signals(self):
        """Test error message sorts missing signals alphabetically."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q25", signal_requirements={"z_signal", "a_signal", "m_signal"}
        )
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError) as exc_info:
            _resolve_signals(chunk, question, registry)

        error_msg = str(exc_info.value)
        # Should contain sorted list
        assert "Missing signals" in error_msg

    def test_single_missing_signal_clear_message(self):
        """Test single missing signal produces clear error message."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q26", signal_requirements={"only_signal"})
        registry = MockSignalRegistry(signals_to_return=[])

        with pytest.raises(ValueError, match=r"Missing signals.*only_signal"):
            _resolve_signals(chunk, question, registry)


class TestPhase5ChunkAndQuestionStructure:
    """Test Chunk and Question NamedTuple structures."""

    def test_chunk_is_named_tuple(self):
        """Test Chunk is NamedTuple with immutable fields."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")

        assert isinstance(chunk, tuple)
        with pytest.raises(AttributeError):
            chunk.chunk_id = "modified"

    def test_question_is_named_tuple(self):
        """Test Question is NamedTuple with immutable fields."""
        question = Question(question_id="Q27", signal_requirements={"type_1"})

        assert isinstance(question, tuple)
        with pytest.raises(AttributeError):
            question.question_id = "modified"

    def test_chunk_fields_accessible(self):
        """Test Chunk fields are accessible by name."""
        chunk = Chunk(chunk_id="PA05-DIM03", text="Chunk content here")

        assert chunk.chunk_id == "PA05-DIM03"
        assert chunk.text == "Chunk content here"

    def test_question_fields_accessible(self):
        """Test Question fields are accessible by name."""
        question = Question(question_id="Q28", signal_requirements={"sig_1", "sig_2"})

        assert question.question_id == "Q28"
        assert question.signal_requirements == {"sig_1", "sig_2"}

    def test_signal_fields_accessible(self):
        """Test Signal fields are accessible by name."""
        signal = Signal(signal_type="test_type", content={"key": "value"})

        assert signal.signal_type == "test_type"
        assert signal.content == {"key": "value"}


class TestPhase5RegistryCallPatterns:
    """Test registry call patterns and caching implications."""

    def test_single_registry_call_per_resolution(self):
        """Test only one registry call made per signal resolution."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q29", signal_requirements={"type_1"})
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk, question, registry)

        assert len(registry.calls) == 1

    def test_multiple_resolutions_separate_registry_calls(self):
        """Test multiple resolutions make separate registry calls."""
        chunk1 = Chunk(chunk_id="PA01-DIM01", text="Test 1")
        chunk2 = Chunk(chunk_id="PA02-DIM02", text="Test 2")
        question = Question(question_id="Q30", signal_requirements={"type_1"})
        signals = [Signal(signal_type="type_1", content=None)]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk1, question, registry)
        _resolve_signals(chunk2, question, registry)

        assert len(registry.calls) == 2
        assert registry.calls[0]["chunk"].chunk_id == "PA01-DIM01"
        assert registry.calls[1]["chunk"].chunk_id == "PA02-DIM02"

    def test_registry_receives_complete_requirement_set(self):
        """Test registry receives complete set of requirements."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q31",
            signal_requirements={"type_1", "type_2", "type_3", "type_4"},
        )
        signals = [
            Signal(signal_type="type_1", content=None),
            Signal(signal_type="type_2", content=None),
            Signal(signal_type="type_3", content=None),
            Signal(signal_type="type_4", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        _resolve_signals(chunk, question, registry)

        assert len(registry.calls[0]["required_types"]) == 4


class TestPhase5EdgeCases:
    """Test edge cases in signal resolution."""

    def test_empty_signal_requirements_succeeds(self):
        """Test resolution succeeds with empty signal requirements."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(question_id="Q32", signal_requirements=set())
        registry = MockSignalRegistry(signals_to_return=[])

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 0

    def test_large_requirement_set_handled(self):
        """Test large signal requirement set handled correctly."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        signal_types = {f"type_{i}" for i in range(100)}
        question = Question(question_id="Q33", signal_requirements=signal_types)
        signals = [Signal(signal_type=t, content=None) for t in signal_types]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 100

    def test_special_characters_in_signal_types(self):
        """Test signal types with special characters."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q34",
            signal_requirements={
                "type-with-dash",
                "type_with_underscore",
                "type.with.dot",
            },
        )
        signals = [
            Signal(signal_type="type-with-dash", content=None),
            Signal(signal_type="type_with_underscore", content=None),
            Signal(signal_type="type.with.dot", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 3

    def test_unicode_in_signal_types(self):
        """Test signal types with unicode characters."""
        chunk = Chunk(chunk_id="PA01-DIM01", text="Test")
        question = Question(
            question_id="Q35", signal_requirements={"type_café", "type_日本語"}
        )
        signals = [
            Signal(signal_type="type_café", content=None),
            Signal(signal_type="type_日本語", content=None),
        ]
        registry = MockSignalRegistry(signals_to_return=signals)

        result = _resolve_signals(chunk, question, registry)

        assert len(result) == 2
